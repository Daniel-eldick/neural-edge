"""Failing tests for src.sensory.macro — stablecoin flows + funding rate aggregation.

Task 5 of Phase 2. The macro module aggregates multiple external feeds
(stablecoin supply, aggregate funding rates). If ALL endpoints fail,
the module MUST return an empty list — not a partial result, not an
exception. This prevents a half-blind macro signal from poisoning the
convergence gate.

The behaviour tests are marked ``xfail(strict=True,
raises=NotImplementedError)`` while the module is a skeleton — when
Task 5 lands, xfail becomes XPASS and strict mode forces marker
removal. Self-healing TDD red state that keeps the quality gate green.

The frozen-dataclass immutability test is NOT xfailed — the dataclass
contract is already locked in the skeleton.
"""

from __future__ import annotations

import pytest
import responses

from src.sensory.macro import MacroSignal, fetch_macro

# Opaque URLs — the module may use any provider. Tests mock whatever
# the module calls. We pick two URLs to represent the "stablecoin supply"
# and "funding rate aggregate" endpoints.
STABLECOIN_URL = "https://api.example-macro.com/v1/stablecoins/supply"
FUNDING_URL = "https://api.example-macro.com/v1/derivatives/funding-aggregate"

# Marker applied to every behaviour test below. Removed (and the test
# turned green) as Task 5 implements the real macro aggregation logic.
pending_impl = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="Phase 2 Task 5: src.sensory.macro.fetch_macro not yet implemented",
)


@pending_impl
@responses.activate
def test_fetch_macro_returns_signals_on_valid_data() -> None:
    """Happy path: both endpoints respond → MacroSignal list."""
    responses.add(
        responses.GET,
        STABLECOIN_URL,
        json={"usdt_supply": 100_000_000_000, "usdc_supply": 30_000_000_000},
        status=200,
    )
    responses.add(
        responses.GET,
        FUNDING_URL,
        json={"avg_funding_rate": 0.00015},
        status=200,
    )

    signals = fetch_macro()

    assert isinstance(signals, list)
    assert len(signals) >= 1
    for sig in signals:
        assert isinstance(sig, MacroSignal)
        assert sig.direction in {"bullish", "bearish", "neutral"}
        assert isinstance(sig.metric, str) and sig.metric


@pending_impl
@responses.activate
def test_fetch_macro_returns_empty_list_when_all_endpoints_fail() -> None:
    """Plan mandate: all endpoints failing → empty list, not partial data.

    This is the contract that prevents half-blind macro signals from
    slipping past the convergence gate as "successful" readings.
    """
    responses.add(
        responses.GET,
        STABLECOIN_URL,
        json={"error": "internal"},
        status=500,
    )
    responses.add(
        responses.GET,
        FUNDING_URL,
        json={"error": "service unavailable"},
        status=503,
    )

    signals = fetch_macro()

    assert signals == []


@pending_impl
@responses.activate
def test_fetch_macro_partial_failure_returns_only_successful_signals() -> None:
    """Partial failure: one endpoint down → return only the working signal(s),
    not empty. The "empty on ALL failing" rule is the floor, not the ceiling."""
    responses.add(
        responses.GET,
        STABLECOIN_URL,
        json={"usdt_supply": 100_000_000_000, "usdc_supply": 30_000_000_000},
        status=200,
    )
    responses.add(
        responses.GET,
        FUNDING_URL,
        json={"error": "service unavailable"},
        status=503,
    )

    signals = fetch_macro()

    # At least the stablecoin signal should come through.
    assert isinstance(signals, list)
    assert len(signals) >= 1


def test_macro_signal_is_frozen_dataclass() -> None:
    """MacroSignal must be immutable — signals are values, not state."""
    sig = MacroSignal(metric="stablecoin_supply", value=130e9, direction="bullish")
    with pytest.raises(AttributeError):
        sig.direction = "bearish"  # type: ignore[misc]
