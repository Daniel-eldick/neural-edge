"""A real context comparison needs verified daily data and exact model-input evidence."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sqlite3
import sys
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from src.agents.contextual import ContextPolicy
from src.agents.learning import LearningPolicy
from src.agents.market_context import MarketContext
from src.agents.responses import ResponseStore
from src.evaluation import __main__ as cli
from src.evaluation.daily import convert_daily, reconcile
from src.evaluation.screen import window_runs
from src.replay.__main__ import BreakoutBaseline
from src.replay.engine import Candle, Policy, Replay, Settings
from src.replay.journal import Journal
from tests.test_learning_memory import Provider

if TYPE_CHECKING:
    from pathlib import Path

DAY = 86400
START = int(datetime(2022, 1, 1, tzinfo=UTC).timestamp())


def archive(root: Path, *, bad_close: bool = False, gap: bool = False) -> Path:
    path = root / "BTCUSDT-1d-2022-01.zip"
    rows = [
        [
            (START + i * DAY) * 1000,
            100,
            101,
            99,
            100,
            288,
            (START + (i + 1) * DAY) * 1000 - 1,
            0,
            0,
            0,
            0,
            0,
        ]
        for i in range(31)
    ]
    if bad_close:
        rows[0][6] += 1
    if gap:
        rows.pop(1)
    content = io.StringIO()
    csv.writer(content).writerows(rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(path.stem + ".csv", content.getvalue())
    path.with_name(path.name + ".CHECKSUM").write_text(
        hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n"
    )
    return path


def test_verified_daily_import_and_exact_overlap(tmp_path: Path) -> None:
    source = archive(tmp_path)
    out = tmp_path / "daily.csv"
    manifest = convert_daily([source], "BTC/USDT", START, START + 3 * DAY, out)
    assert manifest["rows"] == 3 and manifest["repairs"] == []
    assert manifest["csv_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    market = MarketContext.from_csv(out)
    bars = [Candle("BTC/USDT", START + i * 300, 100, 101, 99, 100, 1) for i in range(288 * 3)]
    reconcile(market, bars)
    bars[8] = Candle("BTC/USDT", bars[8].opened_at, 100, 102, 99, 100, 1)
    with pytest.raises(ValueError, match="daily"):
        reconcile(market, bars)
    with pytest.raises(FileExistsError):
        convert_daily([source], "BTC/USDT", START, START + 3 * DAY, out)


@pytest.mark.parametrize("case", ["checksum", "close", "gap", "name", "duplicate", "range"])
def test_daily_source_integrity_blocks_import(tmp_path: Path, case: str) -> None:
    source = archive(tmp_path, bad_close=case == "close", gap=case == "gap")
    if case == "checksum":
        source.with_name(source.name + ".CHECKSUM").write_text("0" * 64 + " " + source.name)
    if case == "name":
        renamed = source.with_name("ETHUSDT-1d-2022-01.zip")
        source.rename(renamed)
        source = renamed
    with pytest.raises((ValueError, OSError)):
        convert_daily(
            [source, source] if case == "duplicate" else [source],
            "BTC/USDT",
            START + 1 if case == "range" else START,
            START + 3 * DAY,
            tmp_path / "daily.csv",
        )
    assert not (tmp_path / "daily.csv").exists()


def write(path: Path, bars: list[Candle]) -> None:
    with path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(Candle.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(c) for c in bars)


def fixture(root: Path) -> None:
    # Earlier complete weeks; a full replay day with a closed-trade opportunity.
    start = START + 70 * DAY
    prices = [100.0] * 20 + [101.0, 102.0, 90.0] + [100.0] * 265
    bars = [Candle("BTC/USDT", start + i * 300, p, p, p, p, 1.0) for i, p in enumerate(prices)]
    daily = [Candle("BTC/USDT", START + i * DAY, 100, 100, 100, 100, 288) for i in range(70)]
    daily.append(Candle("BTC/USDT", start, 100, 102, 90, 100, 288))
    write(root / "daily.csv", daily)
    write(root / "candles.csv", bars)
    market = MarketContext.from_csv(root / "daily.csv")
    for file, name in [
        ("baseline", "breakout-baseline-v1"),
        ("memory", "jev-memory-filter-v1"),
        ("context", "jev-context-filter-v1"),
    ]:
        journal = Journal(root / f"{file}.sqlite")
        store = (
            ResponseStore(root / f"{file}.sqlite.responses.sqlite") if file != "baseline" else None
        )
        try:
            manifest: dict[str, object] = {
                "kind": "MANIFEST",
                "sha256": hashlib.sha256((root / "candles.csv").read_bytes()).hexdigest(),
                "policy": name,
            }
            if file == "context":
                manifest["context_sha256"] = market.source_sha256
            journal.record(manifest)
            policy: Policy
            if file == "baseline":
                policy = BreakoutBaseline()
            elif file == "memory":
                assert store is not None
                policy = LearningPolicy(Provider(), store, journal, interval=300)
            else:
                assert store is not None
                policy = ContextPolicy(Provider(), store, journal, interval=300, market=market)
            Replay(Settings(), journal).run(bars, policy)
        finally:
            journal.close()
            if store is not None:
                store.close()


def test_context_comparison_and_cli_preserve_old_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture(tmp_path)
    runs = window_runs(tmp_path, with_context=True)
    assert [r.name for r in runs][-2:] == ["jev-memory-filter-v1", "jev-context-filter-v1"]
    assert len({r.comparison_key for r in runs}) == 1
    with pytest.raises(FileNotFoundError):
        window_runs(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluation",
            "--with-context",
            "--window",
            str(tmp_path),
            "--output",
            str(tmp_path / "report.json"),
            "--html",
            str(tmp_path / "page.html"),
        ],
    )
    cli.main()
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["windows"][0]["context_minus_memory_percentage_points"] == 0
    assert "Return vs memory-only Jev" in (tmp_path / "page.html").read_text()


@pytest.mark.parametrize("case", ["future", "missing", "manifest", "checkpoint", "daily_file"])
def test_context_evidence_cannot_be_forged(tmp_path: Path, case: str) -> None:
    fixture(tmp_path)
    if case in {"future", "missing"}:
        with sqlite3.connect(tmp_path / "context.sqlite.responses.sqlite") as c:
            key, request = c.execute("SELECT key,request FROM attempts LIMIT 1").fetchone()
            payload = json.loads(request)
            state = json.loads(payload["state"])
            if case == "missing":
                del state["market_context"]
            else:
                state["market_context"]["daily"]["candles"][-1]["close"] = 999999
            payload["state"] = json.dumps(state)
            c.execute("UPDATE attempts SET request=? WHERE key=?", (json.dumps(payload), key))
    elif case == "manifest":
        with sqlite3.connect(tmp_path / "context.sqlite") as c:
            seq, payload = c.execute(
                "SELECT sequence,payload FROM events ORDER BY sequence LIMIT 1"
            ).fetchone()
            event = json.loads(payload)
            event["context_sha256"] = "0" * 64
            c.execute("UPDATE events SET payload=? WHERE sequence=?", (json.dumps(event), seq))
    elif case == "checkpoint":
        with sqlite3.connect(tmp_path / "context.sqlite") as c:
            payload = c.execute("SELECT state FROM checkpoint").fetchone()[0]
            state = json.loads(payload)
            state["contract"]["policy"] = "wrong-context-contract"
            changed = json.dumps(state)
            c.execute(
                "UPDATE checkpoint SET state=?,checksum=?",
                (changed, hashlib.sha256(changed.encode()).hexdigest()),
            )
    else:
        (tmp_path / "daily.csv").write_text((tmp_path / "daily.csv").read_text() + "\n")
    with pytest.raises(ValueError):
        window_runs(tmp_path, with_context=True)
