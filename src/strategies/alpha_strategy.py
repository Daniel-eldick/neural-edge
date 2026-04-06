"""AlphaStrategy — Layer 1 classic technical analysis.

Entry: RSI < 30 (oversold) + fast EMA above slow EMA + volume above average.
Exit:  RSI > 70 (overbought) OR fast EMA crosses below slow EMA.

Note: entry checks EMA *state* (fast > slow), while exit checks EMA *crossover*
(fast crossing below slow). The asymmetry is intentional — requiring a true
bullish crossover + RSI < 30 on the same candle would fire extremely rarely.

This is the foundation strategy. Layers 2-5 (sensory, signals, autoresearch)
will enhance it with additional convergence gates and conviction-weighted sizing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import talib.abstract as ta
from freqtrade.strategy import IStrategy

if TYPE_CHECKING:
    from pandas import DataFrame


class AlphaStrategy(IStrategy):  # type: ignore[misc]
    """RSI + EMA crossover + volume confirmation strategy.

    Paper trading only. This strategy provides the technical analysis
    foundation that higher layers (sensory, signal aggregator) build upon.
    """

    INTERFACE_VERSION: int = 3

    # --- Risk parameters ---
    stoploss: float = -0.10  # 10% max loss per trade
    minimal_roi: dict[str, float] = {
        "0": 0.04,    # 4% take profit immediately
        "30": 0.02,   # 2% after 30 minutes
        "60": 0.01,   # 1% after 60 minutes
    }

    # --- Timeframe ---
    timeframe: str = "5m"

    # --- Behavior ---
    can_short: bool = False  # Long-only for paper trading safety
    process_only_new_candles: bool = True
    startup_candle_count: int = 200  # Warmup for EMA/RSI stability

    # --- Indicator parameters (autoresearch can tune these) ---
    rsi_period: int = 14
    ema_fast_period: int = 12
    ema_slow_period: int = 26
    volume_ma_period: int = 20
    rsi_buy_threshold: float = 30.0
    rsi_sell_threshold: float = 70.0

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        """Add RSI, EMA fast/slow, and volume moving average."""
        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=self.rsi_period)  # type: ignore[attr-defined]

        # Exponential Moving Averages
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.ema_fast_period)  # type: ignore[attr-defined]
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.ema_slow_period)  # type: ignore[attr-defined]

        # Volume moving average for confirmation
        dataframe["volume_ma"] = ta.SMA(  # type: ignore[attr-defined]
            dataframe["volume"], timeperiod=self.volume_ma_period
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        """Generate buy signals: RSI < 30 + EMA bullish state + volume spike.

        All three conditions must be true simultaneously:
        1. RSI below oversold threshold (default 30)
        2. Fast EMA above slow EMA — *state*, not crossover (uptrend in place)
        3. Volume above its moving average (confirming momentum)
        """
        dataframe.loc[
            (dataframe["rsi"] < self.rsi_buy_threshold)
            & (dataframe["ema_fast"] > dataframe["ema_slow"])
            & (dataframe["volume"] > dataframe["volume_ma"])
            & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi_ema_volume")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict[str, Any]) -> DataFrame:
        """Generate sell signals: RSI > 70 OR bearish EMA cross.

        Either condition triggers an exit:
        1. RSI above overbought threshold (default 70)
        2. Fast EMA crosses below slow EMA (trend reversal)
        """
        dataframe.loc[
            (dataframe["rsi"] > self.rsi_sell_threshold)
            | (
                (dataframe["ema_fast"] < dataframe["ema_slow"])
                & (dataframe["ema_fast"].shift(1) >= dataframe["ema_slow"].shift(1))
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "rsi_overbought_or_ema_cross")

        return dataframe
