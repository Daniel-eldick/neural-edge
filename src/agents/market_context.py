"""Bounded point-in-time daily/weekly OHLCV context, not a predictive regime model."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from bisect import bisect_right
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from src.replay.engine import Candle

if TYPE_CHECKING:
    from pathlib import Path

DAY = 86400
WEEK = 7 * DAY
MONDAY = 4 * DAY  # First Monday after Unix epoch (Thursday).
VERSION = "closed-market-context-v1"


def monday(timestamp: int) -> int:
    return (timestamp - MONDAY) // WEEK * WEEK + MONDAY


class MarketContext:
    """Immutable candle tuples, selected only by closed-time cutoffs at request time."""

    def __init__(self, bars: tuple[Candle, ...], source_sha256: str) -> None:
        if not 1 <= len(bars) <= 10000:
            raise ValueError("Daily context needs 1–10000 rows")
        for index, bar in enumerate(bars):
            if (
                bar.symbol != bars[0].symbol
                or bar.opened_at % DAY
                or (index and bar.opened_at - bars[index - 1].opened_at != DAY)
            ):
                raise ValueError("Daily context needs one symbol and contiguous UTC-midnight rows")
        weeks = []
        for index, bar in enumerate(bars):
            if bar.opened_at != monday(bar.opened_at) or index + 7 > len(bars):
                continue
            chunk = bars[index : index + 7]
            weeks.append(
                Candle(
                    bar.symbol,
                    bar.opened_at,
                    bar.open,
                    max(c.high for c in chunk),
                    min(c.low for c in chunk),
                    chunk[-1].close,
                    sum(c.volume for c in chunk),
                )
            )
        self.symbol = bars[0].symbol
        self.source_sha256 = source_sha256
        self._daily = bars
        self._weekly = tuple(weeks)
        self._daily_closes = tuple(c.opened_at + DAY for c in bars)
        self._weekly_closes = tuple(c.opened_at + WEEK for c in weeks)

    @classmethod
    def from_csv(cls, path: Path) -> MarketContext:
        # Read at most the bound + 1, rather than trusting a racy stat before read_bytes().
        with path.open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Daily context file exceeds 4 MiB")
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        if reader.fieldnames != list(Candle.__dataclass_fields__):
            raise ValueError("Daily context CSV columns do not match the OHLCV schema")
        bars: list[Candle] = []
        for row in reader:
            if len(bars) >= 10000 or None in row or any(v is None for v in row.values()):
                raise ValueError("Invalid or excessive daily context rows")
            bars.append(
                Candle(
                    row["symbol"],
                    int(row["opened_at"]),
                    *[float(row[k]) for k in ("open", "high", "low", "close", "volume")],
                )
            )
        return cls(tuple(bars), hashlib.sha256(raw).hexdigest())

    @staticmethod
    def _frame(
        bars: tuple[Candle, ...],
        closes: tuple[int, ...],
        now: int,
        *,
        interval: int,
        limit: int,
        samples: int,
        expected: int,
    ) -> dict[str, Any]:
        end = bisect_right(closes, now)
        selected = bars[max(0, end - limit) : end]
        last = selected[-1].opened_at + interval if selected else None
        reason = (
            "stale_history"
            if last is not None and last != expected
            else "insufficient_history"
            if len(selected) < samples
            else None
        )
        change = mean_range = direction = None
        if reason is None:
            window = selected[-samples:]
            change = window[-1].close / window[0].open - 1
            mean_range = sum((c.high - c.low) / c.open for c in window) / samples
            if not math.isfinite(change) or not math.isfinite(mean_range):
                raise ValueError("Nonfinite market context descriptor")
            direction = "up" if change > 0 else "down" if change < 0 else "flat"
        return {
            "status": "unknown" if reason else "available",
            "reason": reason,
            "last_closed_at": last,
            "required_bars": samples,
            "candles": [{**asdict(c), "available_at": c.opened_at + interval} for c in selected],
            "return": change,
            "direction": direction,
            "mean_range": mean_range,
        }

    def snapshot(self, symbol: str, now: int) -> dict[str, Any]:
        if symbol != self.symbol:
            raise ValueError("Context symbol differs from observation symbol")
        if type(now) is not int or now < 0:
            raise ValueError("Context cutoff must be nonnegative UTC integer seconds")
        return {
            "version": VERSION,
            "as_of": now,
            "symbol": symbol,
            "daily": self._frame(
                self._daily,
                self._daily_closes,
                now,
                interval=DAY,
                limit=30,
                samples=20,
                expected=now // DAY * DAY,
            ),
            "weekly": self._frame(
                self._weekly,
                self._weekly_closes,
                now,
                interval=WEEK,
                limit=12,
                samples=8,
                expected=monday(now),
            ),
        }
