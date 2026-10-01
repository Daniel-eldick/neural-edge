"""Streaming complete-UTC-day returns; descriptive statistics, not promotion gates."""

from __future__ import annotations

import math
from typing import Any

DAY = 86400


def finite(value: Any, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected finite numeric state")
    number = float(value)
    if not math.isfinite(number) or (positive and number <= 0):
        raise ValueError("Expected finite positive equity" if positive else "Non-finite state")
    return number


def integer(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Expected nonnegative integer state")
    return value


class DailyPerformance:
    def __init__(self, start: int, initial_equity: float, interval: int) -> None:
        self.start = integer(start)
        self.initial_equity = finite(initial_equity, positive=True)
        if interval not in (60, 300) or start % interval:
            raise ValueError("Daily measurement requires aligned 60s/300s candles")
        self.interval = interval
        self.last_time = start
        self.anchor = initial_equity if start % DAY == 0 else None
        self.days = 0
        self.mean = 0.0
        self.m2 = 0.0

    def observe(self, now: int, equity: float) -> float | None:
        now = integer(now)
        equity = finite(equity, positive=True)
        if now != self.last_time + self.interval:
            raise ValueError("Daily samples must follow every candle in sequence")
        daily_return = None
        if now % DAY == 0:
            if self.anchor is not None:
                daily_return = finite(equity / self.anchor - 1)
                days = self.days + 1
                delta = daily_return - self.mean
                mean = finite(self.mean + delta / days)
                m2 = finite(self.m2 + delta * (daily_return - mean))
                self.days, self.mean, self.m2 = days, mean, m2
            self.anchor = equity
        self.last_time = now
        return daily_return

    def summary(self) -> tuple[float | None, int, str | None]:
        if self.days < 30:
            return None, self.days, "fewer_than_30_complete_days"
        if self.m2 <= 0:
            return None, self.days, "zero_variance"
        sharpe = math.sqrt(365) * self.mean / math.sqrt(self.m2 / (self.days - 1))
        if not math.isfinite(sharpe):
            raise ValueError("Non-finite daily Sharpe")
        return sharpe, self.days, None

    def snapshot(self) -> dict[str, Any]:
        return {"start": self.start, "initial_equity": self.initial_equity,
                "interval": self.interval, "last_time": self.last_time,
                "anchor": self.anchor, "days": self.days, "mean": self.mean, "m2": self.m2}

    @classmethod
    def restore(cls, state: dict[str, Any]) -> DailyPerformance:
        try:
            value = cls(integer(state["start"]), finite(state["initial_equity"], positive=True),
                        integer(state["interval"]))
            value.last_time = integer(state["last_time"])
            value.days = integer(state["days"])
            value.mean, value.m2 = finite(state["mean"]), finite(state["m2"])
            value.anchor = (None if state["anchor"] is None
                            else finite(state["anchor"], positive=True))
            first_boundary = (value.start + DAY - 1) // DAY
            expected_days = max(0, value.last_time // DAY - first_boundary)
            has_anchor = value.last_time >= first_boundary * DAY
            if (value.last_time < value.start or value.last_time % value.interval
                    or value.days != expected_days or value.m2 < 0
                    or has_anchor != (value.anchor is not None)
                    or (not value.days and (value.mean != 0 or value.m2 != 0))):
                raise ValueError("Inconsistent daily state")
            return value
        except (KeyError, TypeError):
            raise ValueError("Invalid daily checkpoint") from None
