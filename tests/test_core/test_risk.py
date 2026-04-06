"""Tests for risk management — PTJ rules.

Max 1% risk per trade, 10% drawdown circuit breaker, conviction-based sizing.
"""

import pytest

from src.core.risk import (
    CircuitBreaker,
    PositionSizer,
    RiskLimits,
)


class TestRiskLimits:
    """Core risk constants and validation."""

    def test_max_risk_per_trade(self) -> None:
        """No single trade can risk more than 1% of portfolio."""
        assert RiskLimits.MAX_RISK_PER_TRADE == 0.01

    def test_max_drawdown(self) -> None:
        """Circuit breaker triggers at 10% drawdown from peak."""
        assert RiskLimits.MAX_DRAWDOWN == 0.10

    def test_conviction_levels(self) -> None:
        """Three conviction tiers: weak=1x, moderate=3x, strong=10x."""
        assert RiskLimits.CONVICTION_MULTIPLIERS == {
            "weak": 1,
            "moderate": 3,
            "strong": 10,
        }

    def test_conviction_multipliers_are_immutable(self) -> None:
        """CONVICTION_MULTIPLIERS must reject mutation at runtime."""
        with pytest.raises(TypeError):
            RiskLimits.CONVICTION_MULTIPLIERS["yolo"] = 100  # type: ignore[index]


class TestPositionSizer:
    """Conviction-weighted position sizing with risk cap."""

    @pytest.fixture()
    def sizer(self) -> PositionSizer:
        return PositionSizer(portfolio_value=10_000.0)

    def test_weak_conviction_base_size(self, sizer: PositionSizer) -> None:
        """Weak conviction = 1x base size."""
        size = sizer.calculate("weak")
        # 1% of 10k = 100, times 1x = 100
        assert size == pytest.approx(100.0)

    def test_moderate_conviction_3x(self, sizer: PositionSizer) -> None:
        """Moderate conviction = 3x base size, still capped at 1% risk."""
        size = sizer.calculate("moderate")
        # 1% of 10k = 100, times 3x = 300
        assert size == pytest.approx(300.0)

    def test_strong_conviction_10x(self, sizer: PositionSizer) -> None:
        """Strong conviction = 10x base size, still capped at 1% risk."""
        size = sizer.calculate("strong")
        # 1% of 10k = 100, times 10x = 1000
        assert size == pytest.approx(1000.0)

    def test_lower_override_reduces_size(self) -> None:
        """Override below MAX_RISK_PER_TRADE reduces the base risk unit."""
        sizer = PositionSizer(portfolio_value=10_000.0, max_risk_override=0.005)
        size = sizer.calculate("strong")
        # 0.5% of 10k = 50, times 10x = 500
        assert size == pytest.approx(500.0)

    def test_hard_cap_enforced_on_excessive_override(self) -> None:
        """Override above MAX_RISK_PER_TRADE must be capped at the hard ceiling.

        Defense in depth: the optimizer must never be able to bypass the
        1% base risk ceiling by passing a larger max_risk_override.
        """
        sizer = PositionSizer(portfolio_value=10_000.0, max_risk_override=0.5)
        size = sizer.calculate("strong")
        # Without cap: 10000 * 0.5 * 10 = 50000 (500% of portfolio — dangerous)
        # With cap:    10000 * 0.01 * 10 = 1000 (10% of portfolio — safe)
        hard_cap = 10_000.0 * RiskLimits.MAX_RISK_PER_TRADE * 10
        assert size == pytest.approx(hard_cap)
        assert size == pytest.approx(1000.0)

    def test_zero_portfolio_returns_zero(self) -> None:
        """Zero portfolio = zero position size (not an error)."""
        sizer = PositionSizer(portfolio_value=0.0)
        assert sizer.calculate("strong") == 0.0

    def test_negative_portfolio_raises(self) -> None:
        """Negative portfolio value is invalid."""
        with pytest.raises(ValueError, match="portfolio_value"):
            PositionSizer(portfolio_value=-1000.0)

    def test_unknown_conviction_raises(self) -> None:
        """Invalid conviction level must raise, not silently default."""
        sizer = PositionSizer(portfolio_value=10_000.0)
        with pytest.raises(ValueError, match="conviction"):
            sizer.calculate("yolo")  # type: ignore[arg-type]

    def test_position_size_always_non_negative(self, sizer: PositionSizer) -> None:
        """Position sizes are always >= 0."""
        for level in ("weak", "moderate", "strong"):
            assert sizer.calculate(level) >= 0


class TestCircuitBreaker:
    """10% drawdown circuit breaker — halts all trading."""

    @pytest.fixture()
    def breaker(self) -> CircuitBreaker:
        return CircuitBreaker(peak_value=10_000.0)

    def test_not_tripped_initially(self, breaker: CircuitBreaker) -> None:
        assert breaker.is_tripped is False

    def test_trips_at_10_percent_drawdown(self, breaker: CircuitBreaker) -> None:
        """Triggers when current value drops 10% below peak."""
        breaker.update(9_000.0)  # 10% drawdown
        assert breaker.is_tripped is True

    def test_trips_below_10_percent(self, breaker: CircuitBreaker) -> None:
        """Triggers on any drawdown >= 10%."""
        breaker.update(8_000.0)  # 20% drawdown
        assert breaker.is_tripped is True

    def test_not_tripped_at_9_percent(self, breaker: CircuitBreaker) -> None:
        """9% drawdown should NOT trip the breaker."""
        breaker.update(9_100.0)  # 9% drawdown
        assert breaker.is_tripped is False

    def test_peak_updates_on_new_high(self, breaker: CircuitBreaker) -> None:
        """Peak tracks the highest portfolio value seen."""
        breaker.update(11_000.0)
        assert breaker.peak_value == 11_000.0
        # Now 10% of new peak is 1100
        breaker.update(9_900.0)  # 10% of 11k
        assert breaker.is_tripped is True

    def test_drawdown_percentage(self, breaker: CircuitBreaker) -> None:
        """Reports current drawdown as a percentage."""
        breaker.update(9_500.0)
        assert breaker.current_drawdown == pytest.approx(0.05)

    def test_zero_drawdown_at_peak(self, breaker: CircuitBreaker) -> None:
        breaker.update(10_000.0)
        assert breaker.current_drawdown == pytest.approx(0.0)

    def test_reset(self, breaker: CircuitBreaker) -> None:
        """Reset clears the tripped state (manual intervention)."""
        breaker.update(8_000.0)
        assert breaker.is_tripped is True
        breaker.reset(new_peak=8_000.0)
        assert breaker.is_tripped is False
        assert breaker.peak_value == 8_000.0

    def test_tripped_blocks_trading(self, breaker: CircuitBreaker) -> None:
        """can_trade returns False when breaker is tripped."""
        breaker.update(9_000.0)
        assert breaker.can_trade is False

    def test_can_trade_when_healthy(self, breaker: CircuitBreaker) -> None:
        breaker.update(10_500.0)
        assert breaker.can_trade is True
