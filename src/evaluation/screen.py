"""Validate paired replay evidence and calculate explicitly ungoverned references."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from src.agents.jev import PRICE_NANO_USD_PER_TOKEN, parse_response
from src.agents.policy import OPTIONS
from src.cockpit.report import Activity, Run, date, load_journal
from src.replay.engine import Candle, Settings
from src.replay.performance import DailyPerformance

if TYPE_CHECKING:
    from pathlib import Path

POLICIES = (
    ("baseline", "breakout-baseline-v1"),
    ("jev", "jev-breakout-filter-v1"),
    ("memory", "jev-memory-filter-v1"),
)


def load_candles(path: Path) -> list[Candle]:
    with path.open(newline="") as source:
        bars = [
            Candle(
                row["symbol"],
                int(row["opened_at"]),
                *[float(row[k]) for k in ("open", "high", "low", "close", "volume")],
            )
            for row in csv.DictReader(source)
        ]
    if (
        not 22 <= len(bars) <= 100_000
        or bars[0].opened_at % 300
        or any(
            c.symbol != bars[0].symbol or c.opened_at != bars[0].opened_at + i * 300
            for i, c in enumerate(bars)
        )
    ):
        raise ValueError("Expected bounded contiguous single-symbol five-minute data")
    return bars


def candidates(bars: list[Candle]) -> int:
    """Upper bound before position/risk gates; never uses future outcomes."""
    return sum(bars[i].close > max(c.high for c in bars[i - 20 : i]) for i in range(20, len(bars)))


def references(bars: list[Candle], baseline: Run, settings: Settings) -> list[Run]:
    """Cash and full-allocation holding; these are not tradable risk-governed policies."""
    if len(bars) < 22 or settings.interval != 300:
        raise ValueError("Reference requires a warmup and common five-minute entry open")
    controls = []
    for hold in (False, True):
        points: list[tuple[int, float]] = []
        close_dips: list[tuple[int, float]] = []
        daily: list[tuple[int, float]] = []
        entry = bars[21]
        price = entry.open * (1 + settings.slippage)
        quantity = settings.balance / (price * (1 + settings.fee)) if hold else 0
        peak = settings.balance
        worst = 0.0
        performance = DailyPerformance(bars[0].opened_at, settings.balance, 300)
        for index, bar in enumerate(bars):
            active = hold and index >= 21
            open_value = quantity * bar.open if active else settings.balance
            value = quantity * bar.close if active else settings.balance
            peak = max(peak, open_value)
            worst = max(worst, 1 - open_value / peak)
            peak = max(peak, value)
            dip = 1 - value / peak
            worst = max(worst, dip)
            now = bar.opened_at + 300
            points.append((now, value))
            close_dips.append((now, dip))
            change = performance.observe(now, value)
            if change is not None:
                daily.append((now, change))
        sharpe, days, reason = performance.summary()
        controls.append(
            Run(
                name="Buy & hold reference" if hold else "Cash reference",
                source=baseline.source,
                kind="Reference · not risk-governed",
                period=baseline.period,
                starting_equity=settings.balance,
                ending_equity=points[-1][1],
                drawdown=worst,
                closed_trades=0,
                open_positions=int(hold),
                win_rate=None,
                equity=points,
                details=(
                    [f"{date(entry.opened_at)} · Full allocation at first common tradable open"]
                    if hold
                    else []
                ),
                note=(
                    "Analytical reference, not risk-governed: no stop, sizing cap or 24h exit. "
                    "Buy-and-hold enters at bar index 21 after common warmup; "
                    f"{settings.fee:.2%} entry fee and {settings.slippage:.2%} adverse slippage. "
                    "Holdings marked to final close; no hypothetical exit fee. Cash remains flat. "
                    "Drawdown sampled at opens and closes; not intrabar. No inference cost."
                ),
                daily_sharpe=sharpe,
                complete_days=days,
                sharpe_unavailable_reason=str(reason).replace("_", " "),
                comparison_key=baseline.comparison_key,
                model_choices=0,
                policy_errors=0,
                inference_cost_usd=0,
                started_at=baseline.started_at,
                ended_at=baseline.ended_at,
                symbols=baseline.symbols,
                daily_returns=daily,
                close_drawdowns=close_dips,
                activity=[Activity(entry.opened_at, "ENTER", entry.symbol, price)] if hold else [],
                halted=None,
            )
        )
    return controls


def checkpoint(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT state,checksum,sequence FROM checkpoint WHERE id=1"
        ).fetchone()
        maximum = connection.execute("SELECT MAX(sequence) FROM events").fetchone()[0]
        if (
            row is None
            or row[2] != maximum
            or hashlib.sha256(row[0].encode()).hexdigest() != row[1]
        ):
            raise ValueError("Comparison checkpoint integrity failed")
        state: dict[str, Any] = json.loads(row[0])
        if state.get("completed") is not True:
            raise ValueError("Comparison requires completed checkpoints")
        return state
    finally:
        connection.close()


def receipt_evidence(path: Path, run: Run, identity: str) -> dict[str, int]:
    """Cross-check saved receipts without reopening a writable response store."""
    journal = sqlite3.connect((path.parent / run.source).resolve().as_uri() + "?mode=ro", uri=True)
    events: dict[str, dict[str, Any]] = {}
    try:
        for (payload,) in journal.execute("SELECT payload FROM events ORDER BY sequence"):
            event = json.loads(payload)
            if event["kind"] == "MODEL_CHOICE":
                if event["receipt"] in events or len(events) >= 100:
                    raise ValueError("Duplicate or excessive model-choice events")
                events[event["receipt"]] = event
    finally:
        journal.close()
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    choices = cost = exposed = 0
    try:
        if connection.execute("SELECT id FROM identity").fetchall() != [(identity,)]:
            raise ValueError("Response store identity differs from run")
        for key, request, status, response, checksum in connection.execute(
            "SELECT key,request,status,response,checksum FROM attempts"
        ):
            if (
                status != "done"
                or response is None
                or hashlib.sha256(response.encode()).hexdigest() != checksum
            ):
                raise ValueError("Comparison has failed, uncertain or corrupt receipts")
            payload = json.loads(request)
            state = json.loads(payload["state"])
            answer = parse_response(json.loads(response), OPTIONS)
            event = events.pop(key, None)
            if (
                event is None
                or any(event.get(k) != v for k, v in asdict(answer).items())
                or event["time"] != state["now"]
                or event["symbol"] != state["candles"][-1]["symbol"]
            ):
                raise ValueError("Receipt decision differs from journal")
            choices += 1
            cost += answer.input_tokens * PRICE_NANO_USD_PER_TOKEN
            if any(c["opened_at"] + 300 > state["now"] for c in state["candles"]):
                raise ValueError("Receipt contains a future candle")
            memory = state.get("memory")
            if (run.name == "jev-memory-filter-v1") != isinstance(memory, dict):
                raise ValueError("Receipt memory mode differs from declared policy")
            if memory:
                exposed += bool(memory["cases"])
                if any(
                    c["closed_at"] + 300 > state["now"]
                    or c["reviewed_at"] > state["now"]
                    or c["available_at"] > state["now"]
                    for c in memory["cases"]
                ):
                    raise ValueError("Receipt contains an unavailable outcome")
                if any(c["available_at"] > state["now"] for c in memory["curriculum"]):
                    raise ValueError("Receipt contains unavailable curriculum")
        if (
            events
            or choices != run.model_choices
            or not math.isclose(
                cost / 1e9,
                run.inference_cost_usd or 0,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("Response counts/costs differ from journal")
        return {"choices": choices, "cost_nano_usd": cost, "choices_with_trade_memory": exposed}
    finally:
        connection.close()


def window_runs(directory: Path) -> list[Run]:
    source = directory / "candles.csv"
    bars = load_candles(source)
    if candidates(bars) > 100:
        raise ValueError("Candidate upper bound exceeds frozen 100-attempt coverage")
    settings = Settings()
    data_digest = hashlib.sha256()
    for bar in bars:
        data_digest.update(json.dumps(asdict(bar), sort_keys=True, allow_nan=False).encode())
    key = json.dumps(
        [
            hashlib.sha256(source.read_bytes()).hexdigest(),
            asdict(settings),
            bars[0].opened_at,
            bars[-1].opened_at + 300,
        ],
        sort_keys=True,
    )
    runs = []
    for filename, policy in POLICIES:
        path = directory / f"{filename}.sqlite"
        if not path.is_file():
            raise FileNotFoundError(f"Missing comparison journal: {filename}")
        run = load_journal(path)
        state = checkpoint(path)
        if run.name != policy:
            raise ValueError("Unexpected comparison policy")
        if json.loads(run.comparison_key or "null") != json.loads(key) or state[
            "next_index"
        ] != len(bars):
            raise ValueError("Comparison data, dates or settings differ")
        if state["contract"]["dataset"] != data_digest.hexdigest() or state["contract"][
            "settings"
        ] != asdict(settings):
            raise ValueError("Comparison checkpoint data/settings differ from supplied candles")
        if run.policy_errors:
            raise ValueError("Comparison candidate coverage is incomplete")
        if filename != "baseline":
            receipt_evidence(
                path.with_name(path.name + ".responses.sqlite"),
                run,
                state["policy_state"]["response_store"],
            )
        # Numeric-equivalent JSON must also group identically in the read-only cockpit.
        run.comparison_key = key
        runs.append(run)
    return [runs[0], *references(bars, runs[0], settings), *runs[1:]]
