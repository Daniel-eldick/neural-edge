"""Tests for the strategy search harness (synthetic data, no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest import search
from src.backtest.search import Config


def candles(closes: list[float]) -> pd.DataFrame:
    index = pd.date_range("2021-01-01", periods=len(closes), freq="1D", tz="UTC")
    c = pd.Series(closes, index=index)
    return pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1.0})


def test_position_is_applied_one_bar_late_and_costs_are_charged() -> None:
    df = candles([100.0, 100.0, 110.0, 121.0, 121.0])
    pos = pd.Series([0.0, 1.0, 1.0, 0.0, 0.0], index=df.index)
    net, entries = search.pair_returns(df, pos)
    assert net.iloc[1] == 0.0
    assert net.iloc[2] == pytest.approx(0.10 - search.COST)
    assert net.iloc[3] == pytest.approx(0.10)
    assert net.iloc[4] == pytest.approx(-search.COST)
    assert int(entries.sum()) == 1


def test_no_lookahead_in_sma_signal() -> None:
    closes = list(np.linspace(100.0, 200.0, 80))
    df = candles(closes)
    full = search.position(df, Config("x", "sma", "1D", 50))
    partial = search.position(df.iloc[:60], Config("x", "sma", "1D", 50))
    assert full.iloc[:60].equals(partial)


def test_stateful_holds_until_exit() -> None:
    enter = np.array([False, True, False, False, True])
    leave = np.array([False, False, False, True, False])
    assert search.stateful(enter, leave).tolist() == [0.0, 1.0, 1.0, 0.0, 1.0]


def test_metrics_drawdown_and_return() -> None:
    daily = pd.Series([0.10, -0.50, 0.0])
    m = search.metrics(daily)
    assert m["return"] == pytest.approx(-0.45)
    assert m["max_drawdown"] == pytest.approx(0.50)


def test_pass_rule_names_first_failure() -> None:
    bench = {"holdout": {"return": 0.1, "sharpe": 0.5, "max_drawdown": 0.6}}
    good = {"train": {"return": 0.5},
            "holdout": {"return": 0.3, "sharpe": 1.0, "max_drawdown": 0.2, "trades": 25}}
    assert search.passes(good, bench) == (True, "passes all checks")
    few = {**good, "holdout": {**good["holdout"], "trades": 5}}
    assert search.passes(few, bench) == (False, "fewer than 20 holdout trades")
