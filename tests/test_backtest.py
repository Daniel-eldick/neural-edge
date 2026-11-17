"""Tests for the standalone backtest engine (synthetic candles, no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest import engine
from src.backtest.engine import Params, max_drawdown, net_profit, roi_target, trade_stats, verdict


def frame(closes: list[float], *, highs: list[float] | None = None,
          lows: list[float] | None = None) -> pd.DataFrame:
    n = len(closes)
    opens = [closes[0], *closes[:-1]]
    return pd.DataFrame({
        "time": np.arange(n, dtype=np.int64) * 300_000,
        "open": opens,
        "high": highs or [max(a, b) for a, b in zip(opens, closes, strict=True)],
        "low": lows or [min(a, b) for a, b in zip(opens, closes, strict=True)],
        "close": closes,
        "volume": [1.0] * n,
    })


def forced(df: pd.DataFrame, enter_at: list[int], exit_at: list[int],
           monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace signal generation with fixed entry/exit candles."""
    def fake(d: pd.DataFrame, p: Params) -> pd.DataFrame:
        out = d.copy()
        out["enter"] = out.index.isin(enter_at)
        out["exit"] = out.index.isin(exit_at)
        return out
    monkeypatch.setattr(engine, "add_signals", fake)


def test_net_profit_pays_fee_on_both_sides() -> None:
    assert net_profit(100.0, 100.0, 0.001) == pytest.approx(-0.001998, abs=1e-6)
    assert net_profit(100.0, 110.0, 0.0) == pytest.approx(0.10)


def test_roi_target_steps_down_over_time() -> None:
    p = Params(name="x")
    assert roi_target(0, p) == 0.04
    assert roi_target(30, p) == 0.02
    assert roi_target(65, p) == 0.01


def test_entry_fills_at_next_open_and_stoploss_exits_at_stop_price(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = frame([100.0, 100.0, 100.0, 85.0, 85.0])
    forced(df, [0], [], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x", fee=0.0))
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_price == 100.0
    assert trade.reason == "stoploss"
    assert trade.exit_price == pytest.approx(90.0)
    assert trade.profit == pytest.approx(-0.10)


def test_gap_through_stop_exits_at_open(monkeypatch: pytest.MonkeyPatch) -> None:
    df = frame([100.0, 100.0, 100.0, 80.0])
    df.loc[3, ["open", "high", "low"]] = [80.0, 80.0, 80.0]
    forced(df, [0], [], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x", fee=0.0))
    assert result.trades[0].exit_price == pytest.approx(80.0)


def test_roi_exit_is_net_of_fees(monkeypatch: pytest.MonkeyPatch) -> None:
    df = frame([100.0, 100.0, 106.0, 106.0])
    forced(df, [0], [], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x"))
    trade = result.trades[0]
    assert trade.reason == "roi"
    assert trade.profit == pytest.approx(0.04, abs=1e-9)


def test_stop_wins_when_stop_and_roi_touch_in_same_candle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = frame([100.0, 100.0, 100.0], highs=[100.0, 110.0, 110.0], lows=[100.0, 85.0, 85.0])
    forced(df, [0], [], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x", fee=0.0))
    assert result.trades[0].reason == "stoploss"


def test_exit_signal_fills_at_next_open(monkeypatch: pytest.MonkeyPatch) -> None:
    df = frame([100.0, 100.0, 101.0, 102.0, 102.0])
    forced(df, [0], [2], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x", fee=0.0))
    trade = result.trades[0]
    assert trade.reason == "exit_signal"
    assert trade.exit_price == pytest.approx(101.0)


def test_equity_curve_tracks_realised_result(monkeypatch: pytest.MonkeyPatch) -> None:
    df = frame([100.0, 100.0, 100.0, 85.0, 85.0])
    forced(df, [0], [], monkeypatch)
    result = engine.simulate_pair("X", df, Params(name="x", fee=0.0))
    assert result.equity[-1] == pytest.approx(0.90)
    assert max_drawdown(result.equity) == pytest.approx(0.10)


def test_rsi_extremes() -> None:
    rising = pd.Series(np.arange(1.0, 60.0))
    falling = pd.Series(np.arange(60.0, 1.0, -1.0))
    assert engine.rsi(rising, 14).iloc[-1] == pytest.approx(100.0)
    assert engine.rsi(falling, 14).iloc[-1] == pytest.approx(0.0)


def test_no_signals_during_warmup() -> None:
    df = frame(list(np.linspace(100.0, 50.0, 260)))
    signals = engine.add_signals(df, Params(name="x"))
    assert not signals["enter"].iloc[: engine.STARTUP_CANDLES].any()
    assert not signals["exit"].iloc[: engine.STARTUP_CANDLES].any()


def test_verdict_requires_every_check() -> None:
    good = trade_stats([0.01, 0.012, 0.008] * 100)
    assert verdict(good, 1.0, 1.0) == (True, "passes all four checks")
    assert not verdict(good, 1.0, -0.1)[0]
    assert not verdict(trade_stats([0.01] * 50), 1.0, 1.0)[0]
    assert not verdict(trade_stats([-0.01, 0.005] * 150), 1.0, 1.0)[0]
    assert not verdict(trade_stats([0.5, -0.49] * 150), 1.0, 1.0)[0]
