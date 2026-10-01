"""Independent examples pin the daily-return convention and undefined statistics."""

from __future__ import annotations

import math
import statistics

import pytest

from src.replay.performance import DailyPerformance


def observe_day(performance: DailyPerformance, start: int, end_equity: float) -> float | None:
    result = None
    for now in range(start + 300, start + 86401, 300):
        result = performance.observe(now, end_equity)
    return result


def test_daily_returns_and_sample_sharpe_use_full_days() -> None:
    performance = DailyPerformance(0, 1000, 300)
    equity = 1000.0
    returns = [0.01, -0.005, 0.0] * 10
    for i, daily_return in enumerate(returns):
        equity *= 1 + daily_return
        assert observe_day(performance, i * 86400, equity) == pytest.approx(daily_return)
        if i == 28:
            assert performance.summary() == (None, 29, "fewer_than_30_complete_days")
    sharpe, days, reason = performance.summary()
    assert days == 30
    assert reason is None
    assert sharpe == pytest.approx(math.sqrt(365) * statistics.mean(returns)
                                   / statistics.stdev(returns))


def test_partial_days_are_excluded_and_flat_days_remain() -> None:
    performance = DailyPerformance(300, 1000, 300)
    for now in range(600, 86401, 300):
        assert performance.observe(now, 1100) is None
    assert performance.summary()[1] == 0
    assert observe_day(performance, 86400, 1100) == 0
    performance.observe(173100, 1200)
    assert performance.summary()[1] == 1


def test_zero_variance_is_not_zero_sharpe() -> None:
    performance = DailyPerformance(0, 1000, 300)
    for day in range(30):
        observe_day(performance, day * 86400, 1000)
    assert performance.summary() == (None, 30, "zero_variance")


def test_accumulator_restore_preserves_next_day_and_statistics() -> None:
    performance = DailyPerformance(0, 1000, 300)
    observe_day(performance, 0, 1010)
    restored = DailyPerformance.restore(performance.snapshot())
    for p in (performance, restored):
        observe_day(p, 86400, 990)
    assert restored.snapshot() == performance.snapshot()


@pytest.mark.parametrize("time,equity", [(600, 1000), (300, float("nan")), (300, 0)])
def test_invalid_samples_fail_without_advancing(time: int, equity: float) -> None:
    performance = DailyPerformance(0, 1000, 300)
    before = performance.snapshot()
    with pytest.raises(ValueError):
        performance.observe(time, equity)
    assert performance.snapshot() == before


def test_overflowing_return_does_not_corrupt_accumulator() -> None:
    performance = DailyPerformance(0, 1e-300, 300)
    for now in range(300, 86400, 300):
        performance.observe(now, 1e-300)
    before = performance.snapshot()
    with pytest.raises(ValueError):
        performance.observe(86400, 1e300)
    assert performance.snapshot() == before
