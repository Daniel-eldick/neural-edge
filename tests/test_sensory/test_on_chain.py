"""Failing tests for src.sensory.on_chain — CryptoQuant funding rates + flows.

These tests define the contract for Task 3 of Phase 2. The behaviour
tests are marked ``xfail(strict=True, raises=NotImplementedError)``
while the module is a skeleton — when Task 3 lands, xfail becomes
XPASS and strict mode forces marker removal. Self-healing TDD red
state that keeps the quality gate green.

Plan mandate: on 429 rate-limit response → return empty list + log a
warning. Verify the warning with `caplog`.

The frozen-dataclass immutability test is NOT xfailed — the dataclass
contract is already locked in the skeleton.
"""

from __future__ import annotations

import logging

import pytest
import responses

from src.sensory.on_chain import OnChainSignal, fetch_on_chain

# CryptoQuant REST base — the real endpoint shape varies by plan,
# so we treat the URL as opaque and mock whatever the module calls.
# Task 3 must confirm the actual CryptoQuant URL pattern before shipping.
CRYPTOQUANT_BASE = "https://api.cryptoquant.com/v1"

# Marker applied to every behaviour test below. Removed (and the test
# turned green) as Task 3 implements the real CryptoQuant integration.
pending_impl = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="Phase 2 Task 3: src.sensory.on_chain.fetch_on_chain not yet implemented",
)


@pending_impl
@responses.activate
def test_fetch_on_chain_returns_structured_signals_on_success() -> None:
    """Happy path: funding rate + exchange flow → OnChainSignal list."""
    # Funding rate endpoint
    responses.add(
        responses.GET,
        f"{CRYPTOQUANT_BASE}/btc/market-data/funding-rates",
        json={
            "result": {
                "data": [
                    {"datetime": "2026-04-06T00:00:00Z", "funding_rate": 0.0001},
                ]
            }
        },
        status=200,
    )
    # Exchange flow endpoint
    responses.add(
        responses.GET,
        f"{CRYPTOQUANT_BASE}/btc/exchange-flows/netflow",
        json={
            "result": {
                "data": [
                    {"datetime": "2026-04-06T00:00:00Z", "netflow": -1500.0},
                ]
            }
        },
        status=200,
    )

    signals = fetch_on_chain(asset="btc")

    assert isinstance(signals, list)
    assert len(signals) >= 1
    for sig in signals:
        assert isinstance(sig, OnChainSignal)
        assert sig.direction in {"bullish", "bearish", "neutral"}
        assert 0.0 <= sig.confidence <= 1.0
        assert isinstance(sig.metric, str) and sig.metric


@pending_impl
@responses.activate
def test_fetch_on_chain_returns_empty_list_and_logs_warning_on_429(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Rate-limit hit → empty list + `logging.WARNING` entry mentioning 429.

    This is the plan's exact test mandate for Task 3. The caplog check
    makes the "logs warning" assertion specific and measurable (CRITICAL-07).

    Implementation note for Task 3: use ``logging.getLogger(__name__)`` so
    the logger name matches ``"src.sensory.on_chain"`` — the caplog filter
    below is scoped to that logger.
    """
    responses.add(
        responses.GET,
        f"{CRYPTOQUANT_BASE}/btc/market-data/funding-rates",
        json={"error": "rate limit exceeded"},
        status=429,
    )

    with caplog.at_level(logging.WARNING, logger="src.sensory.on_chain"):
        signals = fetch_on_chain(asset="btc")

    assert signals == []
    # At least one WARNING record mentions 429 or "rate limit"
    matched = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and ("429" in r.getMessage() or "rate limit" in r.getMessage().lower())
    ]
    observed = [r.getMessage() for r in caplog.records]
    assert matched, f"Expected a rate-limit warning, got: {observed}"


@pending_impl
@responses.activate
def test_fetch_on_chain_returns_empty_list_on_500_error() -> None:
    """Server error → empty list, no exception, no crash."""
    responses.add(
        responses.GET,
        f"{CRYPTOQUANT_BASE}/btc/market-data/funding-rates",
        json={"error": "internal server error"},
        status=500,
    )

    signals = fetch_on_chain(asset="btc")

    assert signals == []


@pending_impl
@responses.activate
def test_fetch_on_chain_returns_empty_list_on_malformed_payload() -> None:
    """Defensive parse: wrong JSON shape → empty list."""
    responses.add(
        responses.GET,
        f"{CRYPTOQUANT_BASE}/btc/market-data/funding-rates",
        json={"no_result_key": True},
        status=200,
    )

    signals = fetch_on_chain(asset="btc")

    assert signals == []


def test_on_chain_signal_is_frozen_dataclass() -> None:
    """OnChainSignal must be immutable — signals are values, not state."""
    sig = OnChainSignal(
        metric="funding_rate",
        value=0.0001,
        direction="bullish",
        confidence=0.6,
    )
    with pytest.raises(AttributeError):
        sig.confidence = 0.99  # type: ignore[misc]
