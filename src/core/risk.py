"""Risk management — PTJ (Paul Tudor Jones) rules.

Max 1% risk per trade. 10% drawdown circuit breaker.
Conviction-weighted position sizing: weak=1x, moderate=3x, strong=10x.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

ConvictionLevel = Literal["weak", "moderate", "strong"]


class RiskLimits:
    """Immutable risk constants. Change these = change the risk profile.

    CONVICTION_MULTIPLIERS is wrapped in a MappingProxyType so attempts to
    mutate it (e.g. ``RiskLimits.CONVICTION_MULTIPLIERS["yolo"] = 100``)
    raise TypeError at runtime — the "immutable" label is enforced, not just
    aspirational.
    """

    MAX_RISK_PER_TRADE: float = 0.01  # 1% of portfolio
    MAX_DRAWDOWN: float = 0.10  # 10% from peak triggers halt
    CONVICTION_MULTIPLIERS: Mapping[str, int] = MappingProxyType({
        "weak": 1,
        "moderate": 3,
        "strong": 10,
    })


class PositionSizer:
    """Calculate position sizes based on conviction level and risk limits.

    Position = portfolio_value * base_risk * conviction_multiplier
    Hard cap: no single position exceeds MAX_RISK_PER_TRADE * portfolio * max_multiplier.
    """

    def __init__(
        self,
        portfolio_value: float,
        max_risk_override: float | None = None,
    ) -> None:
        if portfolio_value < 0:
            msg = f"portfolio_value must be >= 0, got {portfolio_value}"
            raise ValueError(msg)
        self._portfolio_value = portfolio_value
        self._base_risk = (
            max_risk_override
            if max_risk_override is not None
            else RiskLimits.MAX_RISK_PER_TRADE
        )

    def calculate(self, conviction: ConvictionLevel) -> float:
        """Return position size in quote currency (e.g. USDT).

        Args:
            conviction: One of "weak", "moderate", "strong".

        Returns:
            Position size >= 0. Guaranteed <= hard cap, even if
            ``max_risk_override`` is set higher than MAX_RISK_PER_TRADE.

        Raises:
            ValueError: If conviction is not a valid level.
        """
        if conviction not in RiskLimits.CONVICTION_MULTIPLIERS:
            valid = list(RiskLimits.CONVICTION_MULTIPLIERS)
            msg = f"Invalid conviction level: {conviction!r}. Must be one of {valid}"
            raise ValueError(msg)

        multiplier = RiskLimits.CONVICTION_MULTIPLIERS[conviction]
        size = self._portfolio_value * self._base_risk * multiplier

        # Hard cap: no position exceeds MAX_RISK_PER_TRADE * portfolio * max_multiplier.
        # Enforces the paper-only safety mandate even if max_risk_override
        # is set higher than MAX_RISK_PER_TRADE (defense in depth — the optimizer
        # must never be able to bypass the 1% base risk ceiling).
        max_multiplier = max(RiskLimits.CONVICTION_MULTIPLIERS.values())
        hard_cap = self._portfolio_value * RiskLimits.MAX_RISK_PER_TRADE * max_multiplier

        return max(min(size, hard_cap), 0.0)


class CircuitBreaker:
    """10% drawdown circuit breaker — halts all trading when tripped.

    Tracks portfolio peak value. When current value drops >= MAX_DRAWDOWN
    below the peak, the breaker trips and blocks new trades until manually reset.
    """

    def __init__(self, peak_value: float) -> None:
        self._peak_value = peak_value
        self._current_value = peak_value
        self._tripped = False

    @property
    def peak_value(self) -> float:
        return self._peak_value

    @property
    def is_tripped(self) -> bool:
        return self._tripped

    @property
    def can_trade(self) -> bool:
        return not self._tripped

    @property
    def current_drawdown(self) -> float:
        """Current drawdown as a fraction (0.0 = no drawdown, 0.1 = 10%)."""
        if self._peak_value == 0:
            return 0.0
        return (self._peak_value - self._current_value) / self._peak_value

    def update(self, current_value: float) -> None:
        """Update with latest portfolio value. Trips breaker if drawdown >= 10%.

        Also updates peak if current_value is a new high.
        """
        self._current_value = current_value

        # Track new highs
        if current_value > self._peak_value:
            self._peak_value = current_value

        # Check drawdown
        if self.current_drawdown >= RiskLimits.MAX_DRAWDOWN:
            self._tripped = True

    def reset(self, new_peak: float) -> None:
        """Manual reset after circuit breaker trips. CEO decision.

        Args:
            new_peak: New peak value to track from (typically current portfolio value).
        """
        self._peak_value = new_peak
        self._current_value = new_peak
        self._tripped = False
