"""Tests for AlphaStrategy — RSI + EMA crossover + volume confirmation.

Test-first: these define expected behavior before implementation.
"""

import numpy as np
import pandas as pd


def _make_ohlcv(
    rows: int = 300,
    *,
    base_price: float = 100.0,
    trend: str = "flat",
) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing.

    Args:
        rows: Number of candles to generate.
        base_price: Starting price.
        trend: One of "flat", "up", "down" — controls price drift.

    Returns:
        DataFrame with date, open, high, low, close, volume columns.
    """
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=rows, freq="5min", tz="UTC")

    if trend == "up":
        drift = np.linspace(0, 30, rows)
    elif trend == "down":
        drift = np.linspace(0, -30, rows)
    else:
        drift = np.zeros(rows)

    noise = rng.normal(0, 1, rows).cumsum()
    close = base_price + drift + noise
    close = np.maximum(close, 1.0)  # Price can't go below 1

    return pd.DataFrame({
        "date": dates,
        "open": close * (1 + rng.uniform(-0.005, 0.005, rows)),
        "high": close * (1 + rng.uniform(0, 0.01, rows)),
        "low": close * (1 - rng.uniform(0, 0.01, rows)),
        "close": close,
        "volume": rng.uniform(100, 10000, rows),
    })


def _make_oversold_crossover_data() -> pd.DataFrame:
    """Generate data that guarantees an RSI < 30 + EMA crossover buy signal.

    Pattern: strong uptrend (EMAs bullish, fast > slow) → sudden 11% dip
    over 14 candles (RSI craters). At the transition point (~candle 205),
    RSI just crosses below 30 while fast EMA is still barely above slow EMA.
    Volume spikes during the dip to satisfy the volume > volume_ma condition.
    """
    rows = 300
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=rows, freq="5min", tz="UTC")

    # Phase 1: Strong uptrend (200 candles) — builds EMA bullish momentum
    phase1 = np.linspace(80, 110, 200) + rng.normal(0, 0.2, 200)
    # Phase 2: Sharp dip (14 candles) — RSI craters, EMAs start converging
    phase2 = np.linspace(110, 98, 14)
    # Phase 3: Recovery (86 candles)
    phase3 = np.linspace(98, 108, 86) + rng.normal(0, 0.2, 86)

    close = np.concatenate([phase1, phase2, phase3])
    close = np.maximum(close, 1.0)

    # Volume spike during dip so volume > volume_ma fires
    volume = rng.uniform(500, 3000, rows)
    volume[200:220] = rng.uniform(4000, 8000, 20)

    return pd.DataFrame({
        "date": dates,
        "open": close * (1 + rng.uniform(-0.002, 0.002, rows)),
        "high": close * (1 + rng.uniform(0, 0.005, rows)),
        "low": close * (1 - rng.uniform(0, 0.005, rows)),
        "close": close,
        "volume": volume,
    })


def _make_overbought_data() -> pd.DataFrame:
    """Generate data that guarantees RSI > 70 for exit signal testing."""
    rows = 250
    rng = np.random.default_rng(456)
    dates = pd.date_range("2024-01-01", periods=rows, freq="5min", tz="UTC")

    # Sustained strong uptrend — RSI goes above 70
    close = np.linspace(50, 120, rows) + rng.normal(0, 0.1, rows)
    close = np.maximum(close, 1.0)

    return pd.DataFrame({
        "date": dates,
        "open": close * (1 + rng.uniform(-0.002, 0.002, rows)),
        "high": close * (1 + rng.uniform(0, 0.005, rows)),
        "low": close * (1 - rng.uniform(0, 0.005, rows)),
        "close": close,
        "volume": rng.uniform(500, 5000, rows),
    })


class TestAlphaStrategyLoads:
    """Strategy must be importable and instantiable."""

    def test_import(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy is not None

    def test_instantiate(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        assert strategy is not None

    def test_interface_version(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy.INTERFACE_VERSION == 3

    def test_timeframe(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy.timeframe == "5m"

    def test_stoploss_is_negative(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy.stoploss < 0

    def test_dry_run_compatible(self) -> None:
        """Strategy must not require exchange keys."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        assert strategy.timeframe is not None


class TestPopulateIndicators:
    """populate_indicators adds RSI, EMA fast/slow, and volume MA."""

    def test_adds_rsi_column(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_ohlcv(300)
        result = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        assert "rsi" in result.columns

    def test_adds_ema_columns(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_ohlcv(300)
        result = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        assert "ema_fast" in result.columns
        assert "ema_slow" in result.columns

    def test_adds_volume_ma(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_ohlcv(300)
        result = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        assert "volume_ma" in result.columns

    def test_rsi_values_in_range(self) -> None:
        """RSI must be between 0 and 100 (NaN for warmup is ok)."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_ohlcv(300)
        result = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        rsi = result["rsi"].dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_startup_candle_count_sufficient(self) -> None:
        """startup_candle_count must cover the longest indicator period."""
        from src.strategies.alpha_strategy import AlphaStrategy

        # EMA 26 needs ~52 candles for stability, RSI 14 needs ~28.
        # 200 is generous and standard.
        assert AlphaStrategy.startup_candle_count >= 50


class TestEntrySignals:
    """Buy signal: RSI < 30 AND fast EMA > slow EMA AND volume above average."""

    def test_entry_on_oversold_crossover(self) -> None:
        """Must generate at least one buy signal on oversold + EMA crossover data."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_oversold_crossover_data()
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_entry_trend(df, {"pair": "BTC/USDT"})
        assert (df["enter_long"] == 1).any(), "Expected at least one buy signal"

    def test_no_entry_on_strong_uptrend(self) -> None:
        """Pure uptrend should NOT trigger RSI < 30 buy signals."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_ohlcv(300, trend="up")
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_entry_trend(df, {"pair": "BTC/USDT"})
        # In a strong uptrend, RSI should stay above 30 — no buys expected
        entries = df["enter_long"].fillna(0).sum()
        assert entries == 0, f"Expected no buy signals in uptrend, got {entries}"

    def test_entry_requires_volume(self) -> None:
        """Zero-volume candles must never generate buy signals."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_oversold_crossover_data()
        df["volume"] = 0  # Kill all volume
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_entry_trend(df, {"pair": "BTC/USDT"})
        entries = df["enter_long"].fillna(0).sum()
        assert entries == 0, "Must not buy on zero volume"

    def test_enter_tag_present(self) -> None:
        """Entry signals should have a descriptive tag for position sizing."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_oversold_crossover_data()
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_entry_trend(df, {"pair": "BTC/USDT"})
        entries = df[df["enter_long"] == 1]
        if len(entries) > 0:
            assert "enter_tag" in df.columns
            tags = entries["enter_tag"].dropna()
            assert len(tags) > 0, "Entry signals must have tags"


class TestExitSignals:
    """Sell signal: RSI > 70 OR fast EMA crosses below slow EMA."""

    def test_exit_on_overbought(self) -> None:
        """Must generate exit signals when RSI > 70."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        df = _make_overbought_data()
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_exit_trend(df, {"pair": "BTC/USDT"})
        assert (df["exit_long"] == 1).any(), "Expected exit on RSI > 70"

    def test_exit_on_ema_bearish_cross(self) -> None:
        """Must exit when fast EMA crosses below slow EMA."""
        from src.strategies.alpha_strategy import AlphaStrategy

        strategy = AlphaStrategy(config={"trading_mode": "spot"})
        # Downtrend will produce EMA bearish cross
        df = _make_ohlcv(300, trend="down")
        df = strategy.populate_indicators(df, {"pair": "BTC/USDT"})
        df = strategy.populate_exit_trend(df, {"pair": "BTC/USDT"})
        assert (df["exit_long"] == 1).any(), "Expected exit on bearish EMA cross"


class TestStrategyDefaults:
    """Verify safe defaults that protect paper trading."""

    def test_minimal_roi_defined(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert hasattr(AlphaStrategy, "minimal_roi")
        assert isinstance(AlphaStrategy.minimal_roi, dict)
        assert len(AlphaStrategy.minimal_roi) > 0

    def test_stoploss_reasonable(self) -> None:
        """Stoploss between -5% and -20% (not too tight, not too loose)."""
        from src.strategies.alpha_strategy import AlphaStrategy

        assert -0.20 <= AlphaStrategy.stoploss <= -0.05

    def test_process_only_new_candles(self) -> None:
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy.process_only_new_candles is True

    def test_can_short_disabled(self) -> None:
        """Paper trading starts long-only for safety."""
        from src.strategies.alpha_strategy import AlphaStrategy

        assert AlphaStrategy.can_short is False
