"""Download public Binance candles and backtest AlphaStrategy variants.

Usage: python -m src.backtest.run --data-dir DATA --out OUT [--skip-download]

Data comes from Binance's public archive (data.binance.vision): monthly 5m
kline zips, no API key. Variants and the pass rule are declared here, before
any result was seen, and must not be tuned after the fact.
"""

from __future__ import annotations

import argparse
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.engine import (
    Params,
    max_drawdown,
    simulate_pair,
    trade_stats,
    verdict,
)

PAIRS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
FIRST_MONTH = (2024, 11)
MONTHS = 24
BASE = "https://data.binance.vision/data/spot/monthly/klines"
COLUMNS = ["time", "open", "high", "low", "close", "volume"]

VARIANTS = (
    Params(name="as_is"),
    Params(name="tight_stop", stoploss=-0.02),
    Params(name="symmetric", stoploss=-0.04, roi=((0, 0.04),)),
)


def months() -> list[str]:
    year, month = FIRST_MONTH
    out = []
    for _ in range(MONTHS):
        out.append(f"{year}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def download(data_dir: Path) -> None:
    """Fetch every monthly zip. Fails loudly on a missing month."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for pair in PAIRS:
        for m in months():
            name = f"{pair}-5m-{m}.zip"
            target = data_dir / name
            if target.exists():
                continue
            url = f"{BASE}/{pair}/5m/{name}"
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
                        target.write_bytes(response.read())
                    break
                except (urllib.error.URLError, TimeoutError) as error:
                    if attempt == 2:
                        msg = f"Could not download {url}: {error}"
                        raise RuntimeError(msg) from error
                    time.sleep(3)


def load(data_dir: Path, pair: str) -> pd.DataFrame:
    """Load and concatenate one pair's monthly files into a clean candle frame."""
    frames = []
    for m in months():
        with zipfile.ZipFile(data_dir / f"{pair}-5m-{m}.zip") as archive:
            raw = archive.read(archive.namelist()[0])
        frame = pd.read_csv(io.BytesIO(raw), header=None, usecols=range(6), names=COLUMNS)
        frame = frame[pd.to_numeric(frame["time"], errors="coerce").notna()].astype(float)
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    # Binance switched spot archives from milliseconds to microseconds in 2025.
    micro = df["time"] > 1e14
    df.loc[micro, "time"] = df.loc[micro, "time"] // 1000
    df["time"] = df["time"].astype(np.int64)
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    if df.empty or not df["time"].is_monotonic_increasing:
        msg = f"No usable candles for {pair}"
        raise RuntimeError(msg)
    return df


def run_variant(data: dict[str, pd.DataFrame], p: Params) -> dict[str, Any]:
    """Backtest one variant across all pairs and summarise it."""
    results = {pair: simulate_pair(pair, df, p) for pair, df in data.items()}
    trades = sorted((t for r in results.values() for t in r.trades), key=lambda t: t.exit_time)
    start = min(int(df["time"].iloc[0]) for df in data.values())
    end = max(int(df["time"].iloc[-1]) for df in data.values())
    middle = (start + end) // 2

    curves = [
        pd.Series(r.equity, index=data[pair]["time"].to_numpy()) for pair, r in results.items()
    ]
    portfolio = pd.concat(curves, axis=1).sort_index().ffill().bfill().mean(axis=1).to_numpy()
    hold = [float(df["close"].iloc[-1] / df["open"].iloc[0]) * (1 - p.fee) ** 2 for df in data.values()]

    stats = trade_stats([t.profit for t in trades])
    first = sum(t.profit for t in trades if t.exit_time <= middle)
    second = sum(t.profit for t in trades if t.exit_time > middle)
    passed, reason = verdict(stats, first, second)
    reasons: dict[str, int] = {}
    for t in trades:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    return {
        "name": p.name,
        "stoploss": p.stoploss,
        "roi": dict(p.roi),
        **stats,
        "net_return": float(portfolio[-1] - 1.0),
        "max_drawdown": max_drawdown(portfolio),
        "buy_and_hold_return": float(np.mean(hold) - 1.0),
        "first_half_sum": first,
        "second_half_sum": second,
        "exit_reasons": reasons,
        "per_pair_trades": {pair: len(r.trades) for pair, r in results.items()},
        "passed": passed,
        "reason": reason,
    }


def report(rows: list[dict[str, Any]], span: str) -> str:
    """Render a markdown summary."""
    lines = [
        "# AlphaStrategy backtest",
        "",
        f"Period: {span}. Pairs: BTC, ETH, SOL vs USDT, 5m candles. Fee: 0.1% per side.",
        "",
        "| Variant | Trades | Win rate | Avg trade | t-stat | Net return | Max drawdown | Buy & hold | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['trades']} | {r['win_rate']:.1%} | {r['mean']:.3%} | "
            f"{r['t_stat']:.2f} | {r['net_return']:.1%} | {r['max_drawdown']:.1%} | "
            f"{r['buy_and_hold_return']:.1%} | {'PASS' if r['passed'] else 'FAIL'}: {r['reason']} |"
        )
    lines += [
        "",
        "Pass rule (declared before running): at least 200 trades, positive average trade",
        "after fees with t-stat of 2 or more, and positive in both halves of the period.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    if not args.skip_download:
        download(args.data_dir)
    data = {pair: load(args.data_dir, pair) for pair in PAIRS}
    rows = [run_variant(data, p) for p in VARIANTS]
    all_months = months()
    span = f"{all_months[0]} to {all_months[-1]} ({sum(len(d) for d in data.values())} candles)"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    text = report(rows, span)
    (args.out / "results.md").write_text(text)
    print(text)
    print("RESULTS_JSON=" + json.dumps(rows))


if __name__ == "__main__":
    main()
