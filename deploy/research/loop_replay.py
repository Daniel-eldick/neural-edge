"""Matched fresh replay using the unchanged frozen runtime and risk engine."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from deploy.research.learning import encoded
from src.agents.lessons import LessonPack, LessonPolicy
from src.agents.policy import JevPolicy
from src.agents.responses import Chooser, ResponseStore
from src.cockpit.report import load_journal
from src.evaluation.lesson_screen import (
    choice_records,
    csv_bytes,
    decision_comparison,
    execution_metrics,
    parse_page,
    public_get,
)
from src.evaluation.lesson_week import SYMBOLS, ScheduledPolicy, selected_candidates, trade_metrics
from src.replay.__main__ import BreakoutBaseline
from src.replay.engine import Candle, Replay, Settings
from src.replay.journal import Journal

MAX_ATTEMPTS = 48


def acquire(directory: Path, protocol: dict[str, Any]) -> list[Candle]:
    start_at, ready_at = protocol["start"], protocol["ready"]
    clock, received = public_get("/api/v3/time", {})
    if received < ready_at or json.loads(clock)["serverTime"] < ready_at * 1000:
        raise ValueError("Fresh data incomplete")
    (directory / "server-time.json").write_bytes(clock)
    sources = []
    for symbol in SYMBOLS:
        for i, start in enumerate(range(start_at, ready_at, 300_000)):
            end = min(start + 300_000, ready_at)
            params = {
                "symbol": symbol.replace("/", ""),
                "interval": "5m",
                "startTime": str(start * 1000),
                "endTime": str(end * 1000 - 1),
                "limit": "1000",
            }
            raw, received = public_get("/api/v3/klines", params)
            if received < ready_at or len(raw) > 1_000_000:
                raise ValueError("Fresh page early/large")
            name = f"{symbol.replace('/', '')}-{i}.json"
            with (directory / name).open("xb") as handle:
                handle.write(raw)
            sources.append(
                {
                    "symbol": symbol,
                    "start": start,
                    "end": end,
                    "file": name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "received_at": received,
                }
            )
    (directory / "data.json").write_bytes(
        encoded(
            {"sources": sources, "clock_sha256": hashlib.sha256(clock).hexdigest(), "repairs": []}
        )
    )
    bars = verify_data(directory, protocol)
    (directory / "candles.csv").write_bytes(csv_bytes(bars))
    return bars


def verify_data(directory: Path, protocol: dict[str, Any]) -> list[Candle]:
    start_at, ready_at = protocol["start"], protocol["ready"]
    manifest = json.loads((directory / "data.json").read_bytes())
    clock = (directory / "server-time.json").read_bytes()
    expected = [
        (s, i, t, min(t + 300_000, ready_at))
        for s in SYMBOLS
        for i, t in enumerate(range(start_at, ready_at, 300_000))
    ]
    if (
        manifest["repairs"]
        or manifest["clock_sha256"] != hashlib.sha256(clock).hexdigest()
        or json.loads(clock)["serverTime"] < ready_at * 1000
        or len(manifest["sources"]) != len(expected)
    ):
        raise ValueError("Fresh data manifest differs")
    bars = []
    for source, (symbol, i, start, end) in zip(manifest["sources"], expected, strict=True):
        name = f"{symbol.replace('/', '')}-{i}.json"
        if (source["symbol"], source["start"], source["end"], source["file"]) != (
            symbol,
            start,
            end,
            name,
        ) or source["received_at"] < ready_at:
            raise ValueError("Fresh source grid differs")
        raw = (directory / name).read_bytes()
        if len(raw) > 1_000_000 or hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("Fresh page hash differs")
        bars.extend(parse_page(raw, symbol, start, end))
    bars.sort(key=lambda c: (c.opened_at, c.symbol))
    if len(bars) != (ready_at - start_at) // 300 * len(SYMBOLS):
        raise ValueError("Incomplete fresh grid")
    csv = directory / "candles.csv"
    if csv.exists() and csv.read_bytes() != csv_bytes(bars):
        raise ValueError("Fresh normalized data differs")
    return bars


def run_variants(
    directory: Path,
    parent: LessonPack,
    candidate: LessonPack,
    client: Chooser,
    bars: list[Candle],
    *,
    verify_only: bool = False,
    cached_from: Path | None = None,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    start_at, end_at, ready_at = protocol["start"], protocol["end"], protocol["ready"]
    if verify_only:
        with tempfile.TemporaryDirectory(prefix="jev-fresh-rebuild-") as temporary:
            return run_variants(
                Path(temporary),
                parent,
                candidate,
                client,
                bars,
                cached_from=directory,
                protocol=protocol,
            )
    selected = selected_candidates(bars, start_at, end_at)
    if len(selected) > MAX_ATTEMPTS:
        raise ValueError("Fresh schedule exceeded")
    raw = 0
    history: dict[str, list[Candle]] = {}
    for bar in bars:
        previous = history.setdefault(bar.symbol, [])
        if (
            start_at <= bar.opened_at + 300 < end_at
            and len(previous) >= 20
            and bar.close > max(c.high for c in previous[-20:])
        ):
            raw += 1
        previous.append(bar)
    runs, choices = [], {}
    status = "complete"
    for variant in ["baseline", "frozen", "original", "candidate"]:
        folder = directory / variant
        name = (
            "baseline" if variant == "baseline" else "frozen" if variant == "frozen" else "lesson"
        )
        path = folder / f"{name}.sqlite"
        pack = candidate if variant == "candidate" else parent
        if not verify_only:
            folder.mkdir()
            journal, store = Journal(path), None
            try:
                journal.record(
                    {
                        "kind": "MANIFEST",
                        "policy": "fresh-" + variant,
                        "sha256": hashlib.sha256(csv_bytes(bars)).hexdigest(),
                    }
                )
                inner: Any
                if variant == "baseline":
                    inner = BreakoutBaseline()
                else:
                    if cached_from is not None:
                        shutil.copyfile(
                            cached_from / variant / f"{name}.responses.sqlite",
                            folder / f"{name}.responses.sqlite",
                        )
                    store = ResponseStore(
                        folder / f"{name}.responses.sqlite", resume=cached_from is not None
                    )
                    inner = (
                        JevPolicy(client, store, journal, max_attempts=48)
                        if variant == "frozen"
                        else LessonPolicy(client, store, journal, lesson=pack, max_attempts=48)
                    )
                policy = ScheduledPolicy(inner, selected, start_at, end_at)
                result = Replay(Settings(), journal).run(bars, policy)
            finally:
                if store:
                    store.close()
                journal.close()
        if cached_from is not None:
            original = cached_from / variant / f"{name}.sqlite"

            def events(p: Path) -> list[Any]:
                with sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True) as db:
                    return db.execute("SELECT payload FROM events ORDER BY sequence").fetchall()

            if events(path) != events(original):
                raise ValueError("Rebuilt replay journal differs")
        run = load_journal(path)
        metrics = trade_metrics(path)
        execution = execution_metrics(path, start_at, ready_at)
        if (
            not result.open_positions
            and abs(metrics["closed_net_profit_usdt"] - result.net_profit) > 1e-7
        ):
            raise ValueError("Closed outcomes differ from account profit")
        runs.append(
            {
                "variant": variant,
                "selected_seen": policy.selected_seen,
                "position_skips": policy.position_skips,
                "halt_skips": policy.halt_skips,
                "closed_trades": run.closed_trades,
                "open_positions": run.open_positions,
                "net_profit_usdt": metrics["closed_net_profit_usdt"],
                "net_return": run.net_return,
                "max_drawdown": run.drawdown,
                "model_choices": run.model_choices,
                "policy_errors": run.policy_errors,
                "inference_cost_usd": run.inference_cost_usd,
                **metrics,
                **execution,
            }
        )
        if run.policy_errors or run.open_positions:
            status = "failed"
            break
        if variant != "baseline":
            records = choice_records(folder, name, bars, pack)
            if (
                len(records) != run.model_choices
                or len(records) > 48
                or any((r["symbol"], r["time"]) not in selected for r in records.values())
                or sum(r["cost_nano_usd"] for r in records.values())
                != round((run.inference_cost_usd or 0) * 1e9)
            ):
                raise ValueError("Fresh receipts differ from journal/schedule")
            choices[variant] = records
    complete = status == "complete"
    return {
        "status": status,
        "promotion_allowed": False,
        "runs": runs,
        "selected_candidates": len(selected),
        "raw_candidates": raw,
        "omitted_raw_candidates": raw - len(selected),
        "candidate_minus_original_percentage_points": (
            runs[3]["net_return"] - runs[2]["net_return"]
        )
        * 100
        if complete
        else None,
        "candidate_minus_frozen_percentage_points": (runs[3]["net_return"] - runs[1]["net_return"])
        * 100
        if complete
        else None,
        "decisions": {
            label: decision_comparison(choices[a], choices[b])
            for label, a, b in [
                ("candidate_vs_original", "original", "candidate"),
                ("candidate_vs_frozen", "frozen", "candidate"),
                ("original_vs_frozen", "frozen", "original"),
            ]
        }
        if complete
        else None,
        "assessment": "inconclusive"
        if not complete or any(r["closed_trades"] < 10 for r in runs[1:])
        else "descriptive fresh recurring pilot; selection requires separate verification",
    }
