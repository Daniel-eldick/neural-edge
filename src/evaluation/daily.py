"""Verify official monthly daily archives and reconcile overlapping intraday candles."""

from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.agents.market_context import DAY, MarketContext
from src.replay.engine import Candle

if TYPE_CHECKING:
    from pathlib import Path


def convert_daily(
    archives: list[Path], symbol: str, start: int, end: int, output: Path
) -> dict[str, Any]:
    if (
        type(start) is not int
        or type(end) is not int
        or start < 0
        or end <= start
        or start % DAY
        or end % DAY
        or (end - start) // DAY > 10000
        or not re.fullmatch(r"[A-Z0-9]+/[A-Z0-9]+", symbol)
    ):
        raise ValueError("Daily import requires a bounded UTC daily range and spot symbol")
    manifest_path = output.with_suffix(".manifest.json")
    if output.exists() or manifest_path.exists() or output == manifest_path:
        raise FileExistsError("Daily output/manifest must be new files")
    months = {datetime.fromtimestamp(t, UTC).strftime("%Y-%m") for t in range(start, end, DAY)}
    expected = {f"{symbol.replace('/', '')}-1d-{month}.zip" for month in months}
    if (
        not 1 <= len(archives) <= 12
        or len(archives) != len(expected)
        or {p.name for p in archives} != expected
    ):
        raise ValueError("Daily archives must exactly match distinct requested months")
    bars: list[Candle] = []
    sources = []
    for path in sorted(archives):
        with path.open("rb") as f:
            raw = f.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Daily ZIP exceeds 4 MiB")
        sha = hashlib.sha256(raw).hexdigest()
        if path.with_name(path.name + ".CHECKSUM").read_text().split() != [sha, path.name]:
            raise ValueError("Daily archive checksum or filename mismatch")
        month = path.stem[-7:]
        beginning = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
        first = int(beginning.timestamp())
        days = calendar.monthrange(beginning.year, beginning.month)[1]
        monthly = []
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            member = path.stem + ".csv"
            if z.namelist() != [member] or z.getinfo(member).file_size > 4 * 1024 * 1024:
                raise ValueError("Daily archive must contain one bounded CSV")
            with z.open(member) as stream, io.TextIOWrapper(stream, encoding="utf-8") as text:
                for i, row in enumerate(csv.reader(text)):
                    if len(row) != 12 or i >= days:
                        raise ValueError("Invalid daily kline rows")
                    timestamp = int(row[0])
                    factor = 1000000 if timestamp >= 100000000000000 else 1000
                    opened = timestamp // factor
                    if (
                        timestamp % factor
                        or opened != first + i * DAY
                        or int(row[6]) != timestamp + DAY * factor - 1
                    ):
                        raise ValueError("Invalid or missing daily candle boundary")
                    monthly.append(Candle(symbol, opened, *[float(v) for v in row[1:6]]))
        if len(monthly) != days:
            raise ValueError("Incomplete daily archive month")
        bars.extend(c for c in monthly if start <= c.opened_at < end)
        sources.append(
            {
                "source": path.name,
                "sha256": sha,
                "checksum_verified": True,
                "url": f"https://data.binance.vision/data/spot/monthly/klines/"
                f"{symbol.replace('/', '')}/1d/{path.name}",
            }
        )
    if len(bars) != (end - start) // DAY:
        raise ValueError("Missing daily coverage")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(asdict(bars[0])), lineterminator="\n")
    writer.writeheader()
    writer.writerows(asdict(c) for c in bars)
    data = buffer.getvalue().encode()
    sha = hashlib.sha256(data).hexdigest()
    MarketContext(tuple(bars), sha)  # Validate before any output is written.
    manifest = {
        "sources": sources,
        "interval": DAY,
        "symbol": symbol,
        "start_inclusive": start,
        "end_exclusive": end,
        "rows": len(bars),
        "csv_sha256": sha,
        "repairs": [],
    }
    with output.open("xb") as f:
        f.write(data)
    with manifest_path.open("x") as f:
        json.dump(manifest, f, indent=2, allow_nan=False)
    return manifest


def reconcile(market: MarketContext, bars: list[Candle]) -> None:
    """Compare every complete replay day to the visible daily source, without repairs."""
    if (
        not bars
        or bars[0].opened_at % DAY
        or len(bars) % 288
        or any(
            c.symbol != market.symbol or c.opened_at != bars[0].opened_at + i * 300
            for i, c in enumerate(bars)
        )
    ):
        raise ValueError("Daily reconciliation requires complete contiguous UTC replay days")
    for i in range(0, len(bars), 288):
        chunk = bars[i : i + 288]
        end = chunk[0].opened_at + DAY
        rows = market.snapshot(market.symbol, end)["daily"]["candles"]
        if not rows or rows[-1]["opened_at"] != chunk[0].opened_at:
            raise ValueError("Missing matching daily candle")
        actual = (
            chunk[0].open,
            max(c.high for c in chunk),
            min(c.low for c in chunk),
            chunk[-1].close,
            sum(c.volume for c in chunk),
        )
        expected = tuple(rows[-1][k] for k in ("open", "high", "low", "close", "volume"))
        if not all(
            math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-8)
            for a, b in zip(actual, expected, strict=True)
        ):
            raise ValueError("Intraday OHLCV differs from verified daily candle")
