"""Dependency-light backtester for AlphaStrategy (pandas + numpy only).

Why this exists: the strategy had never been backtested. Freqtrade's own
backtester needs TA-Lib and live exchange access, which is awkward on a hosted
runner, so this module re-implements the strategy's rules and Freqtrade's
candle-level execution model closely enough to answer one question: does the
plain strategy make money after fees?

Execution model (mirrors Freqtrade backtesting):
- Signals are computed on a closed candle and acted on at the next candle open.
- Exit signals execute at the next open, before that candle's stop/ROI checks.
- Stoploss is checked against the candle low, ROI against the candle high.
- If both stop and ROI are touched in one candle, the stop wins (pessimistic).
- ROI targets are net of fees, as in Freqtrade.

Known approximations: EMA/RSI are seeded slightly differently from TA-Lib
(irrelevant after the 200-candle warm-up), there is no slippage beyond fees,
and each pair trades its own third of the wallet (3 pairs, 3 slots, so slots
never bind).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

CANDLE_MINUTES = 5
STARTUP_CANDLES = 200


@dataclass(frozen=True)
class Params:
    """Strategy and execution parameters for one backtest variant."""

    name: str
    stoploss: float = -0.10
    roi: tuple[tuple[int, float], ...] = ((0, 0.04), (30, 0.02), (60, 0.01))
    fee: float = 0.001
    rsi_period: int = 14
    ema_fast: int = 12
    ema_slow: int = 26
    volume_ma: int = 20
    rsi_buy: float = 30.0
    rsi_sell: float = 70.0


@dataclass
class Trade:
    """One closed trade."""

    pair: str
    entry_time: int  # epoch ms of the entry candle open
    exit_time: int
    entry_price: float
    exit_price: float
    profit: float  # net ratio after both fees
    reason: str


@dataclass
class PairResult:
    """Trades plus a per-candle equity curve (starting at 1.0) for one pair."""

    trades: list[Trade] = field(default_factory=list)
    equity: np.ndarray = field(default_factory=lambda: np.ones(0))


def rsi(close: pd.Series, period: int) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = gain / loss
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.where(loss != 0.0, 100.0).where(gain.notna())


def add_signals(df: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Return a copy of ``df`` with indicator, ``enter`` and ``exit`` columns."""
    out = df.copy()
    out["rsi"] = rsi(out["close"], p.rsi_period)
    out["ema_fast"] = out["close"].ewm(span=p.ema_fast, adjust=False, min_periods=p.ema_fast).mean()
    out["ema_slow"] = out["close"].ewm(span=p.ema_slow, adjust=False, min_periods=p.ema_slow).mean()
    out["volume_ma"] = out["volume"].rolling(p.volume_ma).mean()
    out["enter"] = (
        (out["rsi"] < p.rsi_buy)
        & (out["ema_fast"] > out["ema_slow"])
        & (out["volume"] > out["volume_ma"])
        & (out["volume"] > 0)
    )
    out["exit"] = (out["rsi"] > p.rsi_sell) | (
        (out["ema_fast"] < out["ema_slow"])
        & (out["ema_fast"].shift(1) >= out["ema_slow"].shift(1))
    )
    out.iloc[:STARTUP_CANDLES, out.columns.get_indexer(["enter", "exit"])] = False
    return out


def roi_target(minutes: int, p: Params) -> float:
    """ROI threshold that applies ``minutes`` after entry."""
    current = math.inf
    for start, value in p.roi:
        if minutes >= start:
            current = value
    return current


def net_profit(entry: float, exit_price: float, fee: float) -> float:
    """Net profit ratio of a long trade after paying ``fee`` on both sides."""
    return (exit_price * (1.0 - fee)) / (entry * (1.0 + fee)) - 1.0


def simulate_pair(pair: str, df: pd.DataFrame, p: Params) -> PairResult:
    """Simulate one pair. ``df`` needs open/high/low/close/volume and a ms ``time`` column."""
    sig = add_signals(df, p)
    t = sig["time"].to_numpy(dtype=np.int64)
    o = sig["open"].to_numpy(dtype=float)
    h = sig["high"].to_numpy(dtype=float)
    low = sig["low"].to_numpy(dtype=float)
    c = sig["close"].to_numpy(dtype=float)
    enter = sig["enter"].to_numpy(dtype=bool)
    exit_ = sig["exit"].to_numpy(dtype=bool)
    n = len(sig)

    result = PairResult(equity=np.ones(n))
    realized = 1.0
    in_trade = False
    entry_price = 0.0
    entry_idx = 0

    def close_trade(i: int, price: float, reason: str) -> None:
        nonlocal realized, in_trade
        profit = net_profit(entry_price, price, p.fee)
        realized *= 1.0 + profit
        in_trade = False
        result.trades.append(
            Trade(pair, int(t[entry_idx]), int(t[i]), entry_price, price, profit, reason)
        )

    for i in range(1, n):
        if in_trade and exit_[i - 1] and i > entry_idx:
            close_trade(i, o[i], "exit_signal")
        elif not in_trade and enter[i - 1]:
            in_trade = True
            entry_price = o[i]
            entry_idx = i

        if in_trade:
            stop_price = entry_price * (1.0 + p.stoploss)
            minutes = (i - entry_idx) * CANDLE_MINUTES
            target = roi_target(minutes, p)
            roi_price = entry_price * (1.0 + target) * (1.0 + p.fee) / (1.0 - p.fee)
            if low[i] <= stop_price:
                close_trade(i, min(o[i], stop_price), "stoploss")
            elif h[i] >= roi_price:
                close_trade(i, max(o[i], roi_price) if i > entry_idx else roi_price, "roi")

        result.equity[i] = (
            realized * (1.0 + net_profit(entry_price, c[i], p.fee)) if in_trade else realized
        )
    return result


def max_drawdown(equity: np.ndarray) -> float:
    """Largest peak-to-trough fall of an equity curve, as a positive fraction."""
    if len(equity) == 0:
        return 0.0
    peaks = np.maximum.accumulate(equity)
    return float(np.max((peaks - equity) / peaks))


def trade_stats(profits: list[float]) -> dict[str, float]:
    """Count, win rate, mean, and t-statistic of per-trade net returns."""
    n = len(profits)
    if n == 0:
        return {"trades": 0, "win_rate": 0.0, "mean": 0.0, "median": 0.0, "t_stat": 0.0}
    arr = np.asarray(profits)
    sd = float(arr.std(ddof=1)) if n > 1 else 0.0
    mean = float(arr.mean())
    return {
        "trades": n,
        "win_rate": float((arr > 0).mean()),
        "mean": mean,
        "median": float(np.median(arr)),
        "t_stat": mean / (sd / math.sqrt(n)) if sd > 0 else 0.0,
    }


def verdict(stats: dict[str, float], first_half: float, second_half: float) -> tuple[bool, str]:
    """Pre-declared pass rule: enough trades, significant positive mean, both halves positive."""
    if stats["trades"] < 200:
        return False, "fewer than 200 trades"
    if stats["mean"] <= 0:
        return False, "average trade loses money after fees"
    if stats["t_stat"] < 2.0:
        return False, "average trade is not distinguishable from luck (t < 2)"
    if first_half <= 0 or second_half <= 0:
        return False, "not profitable in both halves of the period"
    return True, "passes all four checks"
