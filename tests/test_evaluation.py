"""Controls and comparison eligibility must follow the declared experiment."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from src.evaluation.screen import candidates, load_candles, references, window_runs
from src.replay.__main__ import BreakoutBaseline
from src.replay.engine import Candle, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


def write_csv(path: Path, prices: list[float]) -> list[Candle]:
    bars = [Candle("BTC/USDT", i * 300, p, p, p, p, 1.0) for i, p in enumerate(prices)]
    with path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(bars[0])), lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(c) for c in bars)
    return bars


def baseline(path: Path, source: Path, bars: list[Candle], balance: float = 1000.0) -> None:
    journal = Journal(path)
    try:
        journal.record(
            {
                "kind": "MANIFEST",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "policy": "breakout-baseline-v1",
            }
        )
        Replay(Settings(balance=balance), journal).run(bars, BreakoutBaseline())
    finally:
        journal.close()


def test_candidate_upper_bound_uses_only_closed_prior_twenty_bars(tmp_path: Path) -> None:
    bars = write_csv(tmp_path / "candles.csv", [100.0] * 20 + [101.0, 102.0, 90.0, 91.0])
    assert candidates(bars) == 2
    assert candidates(bars[:21]) == 1
    assert candidates(bars[:20]) == 0


def test_cash_and_hold_use_common_next_open_and_entry_costs(tmp_path: Path) -> None:
    source = tmp_path / "candles.csv"
    bars = write_csv(source, [100.0] * 21 + [110.0, 120.0])
    path = tmp_path / "baseline.sqlite"
    baseline(path, source, bars)
    from src.cockpit.report import load_journal

    cash, hold = references(bars, load_journal(path), Settings())
    qty = 1000 / (110 * 1.001 * 1.001)
    assert cash.ending_equity == 1000 and cash.net_return == 0
    assert hold.ending_equity == pytest.approx(qty * 120)
    assert hold.equity[20][1] == 1000  # no purchase during warmup
    assert hold.equity[21][1] == pytest.approx(qty * 110)
    assert hold.closed_trades == 0 and hold.open_positions == 1
    assert hold.drawdown == pytest.approx(1 - qty * 110 / 1000)
    assert "not risk-governed" in hold.note
    assert hold.comparison_key == cash.comparison_key
    assert hold.model_choices == 0 and hold.inference_cost_usd == 0


def test_dataset_requires_single_symbol_regular_finite_bars(tmp_path: Path) -> None:
    path = tmp_path / "candles.csv"
    write_csv(path, [100.0] * 25)
    assert len(load_candles(path)) == 25
    path.write_text(path.read_text().replace("BTC/USDT,300,", "ETH/USDT,300,"))
    with pytest.raises(ValueError, match="single-symbol"):
        load_candles(path)


def test_window_rejects_missing_variants_and_wrong_policy(tmp_path: Path) -> None:
    source = tmp_path / "candles.csv"
    bars = write_csv(source, [100.0] * 25)
    baseline(tmp_path / "baseline.sqlite", source, bars)
    with pytest.raises((ValueError, OSError)):
        window_runs(tmp_path)
    baseline(tmp_path / "jev.sqlite", source, bars)
    baseline(tmp_path / "memory.sqlite", source, bars)
    with pytest.raises(ValueError, match="policy"):
        window_runs(tmp_path)


def paired_fixture(
    directory: Path, *, fee: float = 0.001, stop_after: int | None = None, balance: float = 1000.0
) -> None:
    from src.agents.learning import LearningPolicy
    from src.agents.policy import JevPolicy
    from src.agents.responses import ResponseStore
    from tests.test_learning_memory import Provider

    source = directory / "candles.csv"
    bars = write_csv(source, [100.0] * 20 + [101.0, 102.0, 90.0] + [90.0] * 20 + [91.0, 92.0, 80.0])
    baseline(directory / "baseline.sqlite", source, bars)
    for name, klass, label in [
        ("jev", JevPolicy, "jev-breakout-filter-v1"),
        ("memory", LearningPolicy, "jev-memory-filter-v1"),
    ]:
        path = directory / f"{name}.sqlite"
        journal = Journal(path)
        store = ResponseStore(path.with_name(path.name + ".responses.sqlite"))
        try:
            journal.record(
                {
                    "kind": "MANIFEST",
                    "policy": label,
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
            )
            policy = (
                LearningPolicy(Provider(), store, journal, interval=300)
                if klass is LearningPolicy
                else JevPolicy(Provider(), store, journal)
            )
            Replay(Settings(fee=fee, balance=balance), journal).run(
                bars, policy, stop_after=stop_after
            )
        finally:
            journal.close()
            store.close()


def test_complete_paired_evidence_and_cli_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import sys

    from src.evaluation.__main__ import main

    paired_fixture(tmp_path)
    runs = window_runs(tmp_path)
    assert len(runs) == 5
    assert runs[-1].reviewed_cases == 2 and runs[-1].policy_errors == 0
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluation",
            "--window",
            str(tmp_path),
            "--output",
            str(tmp_path / "report.json"),
            "--html",
            str(tmp_path / "cockpit.html"),
        ],
    )
    main()
    import json

    report = json.loads((tmp_path / "report.json").read_text())
    assert report["windows"][0]["memory_exposed_choices"] == 1
    assert report["windows"][0]["memory_minus_frozen_percentage_points"] == 0
    assert "Buy &amp; hold reference" in (tmp_path / "cockpit.html").read_text()
    assert "not proof of improvement" in report["interpretation"]
    capsys.readouterr()


@pytest.mark.parametrize("change", ["fee", "csv", "partial", "receipt"])
def test_mismatched_or_partial_evidence_never_becomes_a_comparison(
    tmp_path: Path, change: str
) -> None:
    import sqlite3

    paired_fixture(
        tmp_path,
        fee=0.002 if change == "fee" else 0.001,
        stop_after=22 if change == "partial" else None,
    )
    if change == "csv":
        p = tmp_path / "candles.csv"
        p.write_text(p.read_text().replace("102.0", "103.0"))
    if change == "receipt":
        with sqlite3.connect(tmp_path / "memory.sqlite.responses.sqlite") as c:
            c.execute("UPDATE attempts SET status='failed'")
    with pytest.raises(ValueError):
        window_runs(tmp_path)


@pytest.mark.parametrize("change", ["response_choice", "checkpoint_data"])
def test_same_cost_receipt_swap_and_forged_dataset_contract_are_rejected(
    tmp_path: Path,
    change: str,
) -> None:
    import json
    import sqlite3

    paired_fixture(tmp_path)
    if change == "response_choice":
        with sqlite3.connect(tmp_path / "memory.sqlite.responses.sqlite") as c:
            key, payload = c.execute("SELECT key,response FROM attempts LIMIT 1").fetchone()
            response = json.loads(payload)
            response["answers"]["decision"]["choice"] = "wait"
            payload = json.dumps(response)
            c.execute(
                "UPDATE attempts SET response=?,checksum=? WHERE key=?",
                (payload, hashlib.sha256(payload.encode()).hexdigest(), key),
            )
    else:
        with sqlite3.connect(tmp_path / "memory.sqlite") as c:
            state = json.loads(c.execute("SELECT state FROM checkpoint").fetchone()[0])
            state["contract"]["dataset"] = "0" * 64
            payload = json.dumps(state)
            c.execute(
                "UPDATE checkpoint SET state=?,checksum=?",
                (payload, hashlib.sha256(payload.encode()).hexdigest()),
            )
    with pytest.raises(ValueError):
        window_runs(tmp_path)


def test_actual_cli_integer_balance_matches_equal_numeric_settings(tmp_path: Path) -> None:
    paired_fixture(tmp_path, balance=1000)  # argparse default serializes as an integer
    runs = window_runs(tmp_path)
    assert len(runs) == 5
    assert len({r.comparison_key for r in runs}) == 1
