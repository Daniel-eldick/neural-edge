"""Bounded search for a tradeable long-only rule on BTC/ETH/SOL.

Usage: python -m src.backtest.search --data-dir DATA --out OUT

Design (fixed before any result was seen; do not tune afterwards):
- Data: public Binance 1h candles, 2020-09 to 2026-10, resampled to 4h and 1d.
- Twelve textbook configurations across four families (trend, breakout,
  momentum, mean reversion). No parameter sweeps beyond what is listed.
- TRAIN = 2020-09-01 .. 2024-06-30. HOLDOUT = 2024-07-01 .. 2026-10-31.
- A signal on a closed bar sets the position for the next bar. Each change of
  position costs 0.15% (0.1% fee + 0.05% slippage).
- Portfolio = equal thirds across the three pairs, long or flat, no leverage.
- Pass rule, judged on HOLDOUT only: positive return, Sharpe >= 0.8 and above
  buy-and-hold, max drawdown < 30% and below buy-and-hold, at least 20 trades,
  and a positive TRAIN return. With twelve tries, one lucky pass is plausible,
  so a pass means "worth paper-trading", never "proven".
"""

from __future__ import annotations

import argparse
import io
import json
import math
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PAIRS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
BASE = "https://data.binance.vision/data/spot/monthly/klines"
START = pd.Timestamp("2020-09-01", tz="UTC")
SPLIT = pd.Timestamp("2024-07-01", tz="UTC")
END = pd.Timestamp("2026-11-01", tz="UTC")
COST = 0.0015


@dataclass(frozen=True)
class Config:
    name: str
    family: str
    timeframe: str
    a: int
    b: int = 0


CONFIGS = (
    Config("sma50_1d", "sma", "1D", 50),
    Config("sma100_1d", "sma", "1D", 100),
    Config("sma200_1d", "sma", "1D", 200),
    Config("ema20_50_1d", "ema_cross", "1D", 20, 50),
    Config("ema50_200_4h", "ema_cross", "4h", 50, 200),
    Config("donchian20_10_1d", "donchian", "1D", 20, 10),
    Config("donchian55_20_1d", "donchian", "1D", 55, 20),
    Config("donchian55_20_4h", "donchian", "4h", 55, 20),
    Config("momentum30_1d", "momentum", "1D", 30),
    Config("momentum90_1d", "momentum", "1D", 90),
    Config("rsi2_dip_1d", "rsi2", "1D", 10, 200),
    Config("rsi14_dip_1h", "rsi14", "1h", 30, 50),
)


def month_list() -> list[str]:
    return [p.strftime("%Y-%m") for p in pd.period_range(START, END - pd.Timedelta(days=1), freq="M")]


def download(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for pair in PAIRS:
        for m in month_list():
            name = f"{pair}-1h-{m}.zip"
            target = data_dir / name
            if target.exists():
                continue
            url = f"{BASE}/{pair}/1h/{name}"
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
    frames = []
    for m in month_list():
        with zipfile.ZipFile(data_dir / f"{pair}-1h-{m}.zip") as archive:
            raw = archive.read(archive.namelist()[0])
        f = pd.read_csv(io.BytesIO(raw), header=None, usecols=range(6),
                        names=["time", "open", "high", "low", "close", "volume"])
        frames.append(f[pd.to_numeric(f["time"], errors="coerce").notna()].astype(float))
    df = pd.concat(frames, ignore_index=True)
    micro = df["time"] > 1e14
    df.loc[micro, "time"] = df.loc[micro, "time"] // 1000
    df.index = pd.to_datetime(df["time"].astype(np.int64), unit="ms", utc=True)
    df = df[~df.index.duplicated()].sort_index().drop(columns="time")
    if len(df) < 40_000:
        msg = f"Too few candles for {pair}: {len(df)}"
        raise RuntimeError(msg)
    return df


def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1h":
        return df
    return df.resample(timeframe).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna()


def wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return (100.0 - 100.0 / (1.0 + gain / loss)).where(loss != 0.0, 100.0).where(gain.notna())


def stateful(enter: np.ndarray, leave: np.ndarray) -> np.ndarray:
    """Hold from an ``enter`` bar until a ``leave`` bar."""
    pos = np.zeros(len(enter))
    held = False
    for i in range(len(enter)):
        if held and leave[i]:
            held = False
        elif not held and enter[i]:
            held = True
        pos[i] = 1.0 if held else 0.0
    return pos


def position(df: pd.DataFrame, c: Config) -> pd.Series:
    """Desired position (0 or 1) decided at each bar's close."""
    close = df["close"]
    if c.family == "sma":
        raw = (close > close.rolling(c.a).mean()).astype(float)
    elif c.family == "ema_cross":
        fast = close.ewm(span=c.a, adjust=False, min_periods=c.a).mean()
        slow = close.ewm(span=c.b, adjust=False, min_periods=c.b).mean()
        raw = (fast > slow).astype(float)
    elif c.family == "momentum":
        raw = (close > close.shift(c.a)).astype(float)
    elif c.family == "donchian":
        upper = df["high"].rolling(c.a).max().shift(1)
        lower = df["low"].rolling(c.b).min().shift(1)
        raw = pd.Series(stateful((close > upper).to_numpy(), (close < lower).to_numpy()), index=df.index)
    elif c.family == "rsi2":
        dip = (wilder_rsi(close, 2) < c.a) & (close > close.rolling(c.b).mean())
        out = close > close.rolling(5).mean()
        raw = pd.Series(stateful(dip.to_numpy(), out.to_numpy()), index=df.index)
    elif c.family == "rsi14":
        r = wilder_rsi(close, 14)
        raw = pd.Series(stateful((r < c.a).to_numpy(), (r > c.b).to_numpy()), index=df.index)
    else:
        msg = f"Unknown family {c.family}"
        raise ValueError(msg)
    return raw.fillna(0.0)


def pair_returns(df: pd.DataFrame, pos: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Per-bar net strategy returns and entry markers. Position lags the signal by one bar."""
    held = pos.shift(1).fillna(0.0)
    change = held.diff().abs().fillna(held.abs())
    net = held * df["close"].pct_change().fillna(0.0) - change * COST
    entries = (held.diff().fillna(held) > 0).astype(int)
    return net, entries


def metrics(daily: pd.Series) -> dict[str, float]:
    equity = (1.0 + daily).cumprod()
    if len(equity) == 0:
        return {"return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}
    sd = float(daily.std(ddof=1))
    peak = equity.cummax()
    return {
        "return": float(equity.iloc[-1] - 1.0),
        "sharpe": float(daily.mean() / sd * math.sqrt(365)) if sd > 0 else 0.0,
        "max_drawdown": float(((peak - equity) / peak).max()),
    }


def to_daily(net_by_pair: dict[str, pd.Series]) -> pd.Series:
    daily = [((1.0 + s).resample("1D").prod() - 1.0) for s in net_by_pair.values()]
    frame = pd.concat(daily, axis=1).fillna(0.0)
    return frame.mean(axis=1).loc[START:END - pd.Timedelta(seconds=1)]


def evaluate(data: dict[str, pd.DataFrame], c: Config) -> dict[str, Any]:
    nets, entries = {}, []
    for pair, hourly in data.items():
        df = resample(hourly, c.timeframe)
        net, ent = pair_returns(df, position(df, c))
        nets[pair] = net
        entries.append(ent)
    daily = to_daily(nets)
    all_entries = pd.concat(entries).sort_index()
    out: dict[str, Any] = {"name": c.name, "family": c.family, "timeframe": c.timeframe}
    for label, lo, hi in (("train", START, SPLIT), ("holdout", SPLIT, END)):
        window = daily.loc[lo:hi - pd.Timedelta(seconds=1)]
        out[label] = metrics(window) | {
            "trades": int(all_entries.loc[lo:hi - pd.Timedelta(seconds=1)].sum())
        }
    return out


def benchmark(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    nets = {}
    for pair, hourly in data.items():
        df = resample(hourly, "1D")
        nets[pair] = df["close"].pct_change().fillna(0.0)
    daily = to_daily(nets)
    return {
        "name": "buy_and_hold",
        "train": metrics(daily.loc[START:SPLIT - pd.Timedelta(seconds=1)]),
        "holdout": metrics(daily.loc[SPLIT:END - pd.Timedelta(seconds=1)]),
    }


def passes(row: dict[str, Any], bench: dict[str, Any]) -> tuple[bool, str]:
    h, b = row["holdout"], bench["holdout"]
    checks = (
        (h["return"] > 0, "holdout return not positive"),
        (h["sharpe"] >= 0.8, "holdout Sharpe below 0.8"),
        (h["sharpe"] > b["sharpe"], "holdout Sharpe not above buy-and-hold"),
        (h["max_drawdown"] < 0.30, "holdout drawdown 30% or more"),
        (h["max_drawdown"] < b["max_drawdown"], "holdout drawdown not below buy-and-hold"),
        (h["trades"] >= 20, "fewer than 20 holdout trades"),
        (row["train"]["return"] > 0, "train return not positive"),
    )
    failed = [reason for ok, reason in checks if not ok]
    return (not failed, "passes all checks" if not failed else failed[0])


def report(rows: list[dict[str, Any]], bench: dict[str, Any]) -> str:
    def cells(m: dict[str, float]) -> str:
        return f"{m['return']:.0%} | {m['sharpe']:.2f} | {m['max_drawdown']:.0%}"
    lines = [
        "# Strategy search",
        "",
        "Train 2020-09 to 2024-06, holdout 2024-07 to 2026-10. BTC/ETH/SOL equal weight,",
        "long or flat, 0.15% cost per position change.",
        "",
        "| Config | Train return | Train Sharpe | Train DD | Holdout return | Holdout Sharpe | Holdout DD | Holdout trades | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        f"| buy_and_hold | {cells(bench['train'])} | {cells(bench['holdout'])} | - | benchmark |",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {cells(r['train'])} | {cells(r['holdout'])} | "
            f"{r['holdout']['trades']} | {'PASS' if r['passed'] else 'FAIL'}: {r['reason']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    if not args.skip_download:
        download(args.data_dir)
    data = {pair: load(args.data_dir, pair) for pair in PAIRS}
    bench = benchmark(data)
    rows = []
    for c in CONFIGS:
        row = evaluate(data, c)
        row["passed"], row["reason"] = passes(row, bench)
        rows.append(row)
    args.out.mkdir(parents=True, exist_ok=True)
    payload = {"benchmark": bench, "configs": rows}
    (args.out / "search.json").write_text(json.dumps(payload, indent=2) + "\n")
    text = report(rows, bench)
    (args.out / "search.md").write_text(text)
    print(text)
    print("SEARCH_JSON=" + json.dumps(payload))


if __name__ == "__main__":
    main()
