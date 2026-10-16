"""Closed higher-timeframe data must never reveal a future candle or outcome."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

import pytest

from src.agents.contextual import ContextPolicy
from src.agents.jev import MODEL, Choice, JevError
from src.agents.market_context import MarketContext
from src.agents.responses import ResponseStore
from src.cockpit.report import load_journal, render
from src.replay.engine import Candle, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path

DAY = 86400
MONDAY = 1578268800  # 2020-01-06 00:00 UTC


def daily(n: int = 80, start: int = 0) -> list[Candle]:
    return [
        Candle("BTC", MONDAY + i * DAY, 100 + i, 102 + i, 99 + i, 100.5 + i, 10 + i)
        for i in range(start, start + n)
    ]


def write(path: Path, bars: list[Candle]) -> Path:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(Candle.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(bar) for bar in bars)
    return path


def test_exact_closed_boundaries_weekly_ohlcv_and_descriptors(tmp_path: Path) -> None:
    context = MarketContext.from_csv(write(tmp_path / "daily.csv", daily()))
    before = context.snapshot("BTC", MONDAY + 56 * DAY - 1)
    at = context.snapshot("BTC", MONDAY + 56 * DAY)
    assert before["weekly"]["status"] == "unknown"
    assert before["weekly"]["reason"] == "insufficient_history"
    assert at["weekly"]["status"] == "available"
    assert len(at["daily"]["candles"]) == 30
    assert len(at["weekly"]["candles"]) == 8
    first = at["weekly"]["candles"][0]
    assert first == {
        "symbol": "BTC",
        "opened_at": MONDAY,
        "open": 100,
        "high": 108,
        "low": 99,
        "close": 106.5,
        "volume": sum(range(10, 17)),
        "available_at": MONDAY + 7 * DAY,
    }
    assert at["daily"]["return"] == pytest.approx(155.5 / 136 - 1)
    assert at["weekly"]["return"] == pytest.approx(155.5 / 100 - 1)
    assert at["daily"]["mean_range"] == pytest.approx(sum(3 / p for p in range(136, 156)) / 20)
    assert at["daily"]["direction"] == "up"
    assert all(
        c["available_at"] <= at["as_of"] for f in ("daily", "weekly") for c in at[f]["candles"]
    )


def test_partial_week_never_becomes_a_week_and_payload_is_bounded(tmp_path: Path) -> None:
    context = MarketContext.from_csv(write(tmp_path / "daily.csv", daily(130, start=1)))
    view = context.snapshot("BTC", MONDAY + 131 * DAY)
    assert len(view["daily"]["candles"]) == 30
    assert len(view["weekly"]["candles"]) == 12
    assert all((c["opened_at"] - MONDAY) % (7 * DAY) == 0 for c in view["weekly"]["candles"])
    early = context.snapshot("BTC", MONDAY + 7 * DAY)
    assert early["weekly"]["candles"] == []


def test_unknown_is_explicit_without_invented_descriptors(tmp_path: Path) -> None:
    context = MarketContext.from_csv(write(tmp_path / "daily.csv", daily()))
    for now, reason in [(MONDAY, "insufficient_history"), (MONDAY + 90 * DAY, "stale_history")]:
        view = context.snapshot("BTC", now)
        for frame in ("daily", "weekly"):
            assert view[frame]["status"] == "unknown"
            assert view[frame]["reason"] == reason
            assert all(view[frame][k] is None for k in ("return", "direction", "mean_range"))
    assert context.snapshot("BTC", MONDAY + 19 * DAY)["daily"]["status"] == "unknown"
    assert context.snapshot("BTC", MONDAY + 20 * DAY)["daily"]["status"] == "available"
    with pytest.raises(ValueError, match="symbol"):
        context.snapshot("ETH", MONDAY)
    with pytest.raises(ValueError):
        context.snapshot("BTC", True)


def test_future_suffix_cannot_change_any_earlier_context(tmp_path: Path) -> None:
    left = MarketContext.from_csv(write(tmp_path / "left.csv", daily()))
    changed = daily(56) + [
        Candle("BTC", MONDAY + i * DAY, 900, 1000, 1, 999, 1e6) for i in range(56, 80)
    ]
    right = MarketContext.from_csv(write(tmp_path / "right.csv", changed))
    assert left.source_sha256 != right.source_sha256
    for now in (MONDAY, MONDAY + 55 * DAY, MONDAY + 56 * DAY):
        assert left.snapshot("BTC", now) == right.snapshot("BTC", now)


@pytest.mark.parametrize(
    "case",
    ["empty", "gap", "duplicate", "misaligned", "symbol", "nan", "oversize", "rows", "overflow"],
)
def test_invalid_daily_sources_fail_explicitly(tmp_path: Path, case: str) -> None:
    bars = daily(10)
    if case == "empty":
        bars = []
    elif case == "gap":
        del bars[4]
    elif case == "duplicate":
        bars.insert(4, bars[4])
    elif case == "misaligned":
        bars[0] = Candle("BTC", MONDAY + 300, 100, 100, 100, 100, 1)
    elif case == "symbol":
        bars[0] = Candle("ETH", MONDAY, 100, 100, 100, 100, 1)
    elif case == "rows":
        bars = daily(10001)
    elif case == "overflow":
        bars = [Candle("BTC", MONDAY + i * DAY, 100, 100, 100, 100, 1e308) for i in range(7)]
    path = write(tmp_path / "invalid.csv", bars)
    if case == "nan":
        path.write_text(path.read_text().replace("100.5", "nan"))
    elif case == "oversize":
        path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    with pytest.raises(ValueError):
        MarketContext.from_csv(path)


class Provider:
    def __init__(self, fail: bool = False) -> None:
        self.states: list[dict[str, Any]] = []
        self.fail = fail

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        self.states.append(json.loads(state))
        if self.fail and len(self.states) > 1:
            raise JevError("provider failed")
        return Choice("enter", 0.8, {"enter": 0.8, "wait": 0.2}, MODEL, 100, 4200)


def intraday() -> list[Candle]:
    return [
        Candle("BTC", MONDAY + 56 * DAY + i * 300, p, p, p, p, 1)
        for i, p in enumerate([100] * 20 + [101, 102, 90] + [90] * 20 + [91, 92, 80])
    ]


def run(
    path: Path,
    history: Path,
    provider: Provider,
    *,
    resume: bool = False,
    stop_after: int | None = None,
    crash: bool = False,
) -> list[dict[str, Any]]:
    class CrashJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            super().record(event)
            if event["kind"] == "MODEL_CHOICE":
                raise SystemExit("saved response before candle commit")

    journal = (CrashJournal if crash else Journal)(path, resume=resume)
    store = ResponseStore(path.with_suffix(".responses.sqlite"), resume=resume)
    try:
        if not resume:
            journal.record({"kind": "MANIFEST", "policy": "jev-context-filter-v1"})
        policy = ContextPolicy(
            provider, store, journal, interval=300, market=MarketContext.from_csv(history)
        )
        Replay(Settings(), journal).run(intraday(), policy, resume=resume, stop_after=stop_after)
        return [
            json.loads(row[0])
            for row in journal.connection.execute("SELECT payload FROM events ORDER BY sequence")
        ]
    finally:
        journal.close()
        store.close()


def test_context_and_memory_requests_resume_identically_and_render(tmp_path: Path) -> None:
    history = write(tmp_path / "daily.csv", daily())
    full_provider, split_provider = Provider(), Provider()
    full = run(tmp_path / "full.sqlite", history, full_provider)
    run(tmp_path / "split.sqlite", history, split_provider, stop_after=23)
    split = run(tmp_path / "split.sqlite", history, split_provider, resume=True)
    assert full == split and full_provider.states == split_provider.states
    assert len(full_provider.states) == 2
    assert full_provider.states[1]["memory"]["cases"]
    assert full_provider.states[0]["market_context"]["weekly"]["status"] == "available"
    reads = [e for e in full if e["kind"] == "CONTEXT_READ"]
    assert len(reads) == 2
    assert reads[0]["as_of"] == full_provider.states[0]["now"]
    page = render([load_journal(tmp_path / "full.sqlite")])
    assert "Jev with context + memory" in page
    assert "On · improvement unproven" in page
    assert "Daily available / weekly available" in page
    assert "Reviewed trades" in page


def test_changed_history_rejects_resume_before_model_call(tmp_path: Path) -> None:
    history = write(tmp_path / "daily.csv", daily())
    provider = Provider()
    path = tmp_path / "run.sqlite"
    run(path, history, provider, stop_after=20)
    history.write_text(history.read_text() + "\n")  # Even formatting binds provenance.
    with pytest.raises(ValueError, match="Checkpoint"):
        run(path, history, provider, resume=True)
    assert not provider.states


def test_context_response_survives_rollback_without_duplicate_request(tmp_path: Path) -> None:
    history = write(tmp_path / "daily.csv", daily())
    provider = Provider()
    path = tmp_path / "crash.sqlite"
    with pytest.raises(SystemExit):
        run(path, history, provider, crash=True)
    assert len(provider.states) == 1
    recovered = run(path, history, provider, resume=True)
    assert recovered == run(tmp_path / "clean.sqlite", history, Provider())
    assert len(provider.states) == 2


def test_context_future_suffix_does_not_change_requests_or_provider_failure_protection(
    tmp_path: Path,
) -> None:
    left_history = write(tmp_path / "left.csv", daily())
    right_history = write(
        tmp_path / "right.csv",
        daily(56)
        + [Candle("BTC", MONDAY + i * DAY, 1000, 1000, 1000, 1000, 1) for i in range(56, 80)],
    )
    left, right = Provider(), Provider()
    run(tmp_path / "left.sqlite", left_history, left)
    run(tmp_path / "right.sqlite", right_history, right)
    assert left.states == right.states
    failed = run(tmp_path / "failed.sqlite", left_history, Provider(fail=True))
    assert any(e["kind"] == "EXIT" for e in failed)
    assert any(e["kind"] == "POLICY_ERROR" for e in failed)
    assert failed[-1]["kind"] == "RESULT" and failed[-1]["open_positions"] == 0


@pytest.mark.parametrize("slope,direction", [(0, "flat"), (-1, "down")])
def test_direction_uses_only_trailing_return_sign(
    tmp_path: Path,
    slope: int,
    direction: str,
) -> None:
    bars = [
        Candle(
            "BTC",
            MONDAY + i * DAY,
            200 + i * slope,
            200 + i * slope,
            200 + i * slope,
            200 + i * slope,
            0,
        )
        for i in range(56)
    ]
    view = MarketContext.from_csv(write(tmp_path / "daily.csv", bars)).snapshot(
        "BTC", MONDAY + 56 * DAY
    )
    for frame in ("daily", "weekly"):
        assert view[frame]["direction"] == direction
    assert view["daily"]["mean_range"] == 0
    expected_weekly_range = sum(6 * abs(slope) / (200 + i * 7 * slope)
                                for i in range(8)) / 8
    assert view["weekly"]["mean_range"] == pytest.approx(expected_weekly_range)


def test_descriptor_overflow_is_rejected_not_sent_as_a_forecast(tmp_path: Path) -> None:
    bars = [Candle("BTC", MONDAY + i * DAY, 1e-300, 1e308, 1e-300, 1e308, 0) for i in range(20)]
    context = MarketContext.from_csv(write(tmp_path / "daily.csv", bars))
    with pytest.raises(ValueError, match="Nonfinite"):
        context.snapshot("BTC", MONDAY + 20 * DAY)
