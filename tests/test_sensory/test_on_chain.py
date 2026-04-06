"""Failing tests for src.sensory.on_chain — CryptoQuant funding rates + flows.

These tests define the contract for Task 3 of Phase 2. They are expected
to fail with ImportError until `src/sensory/on_chain.py` is implemented.

Plan mandate: on 429 rate-limit response → return empty list + log a
warning. Verify the warning with `caplog`.
"""

from __future__ import annotations

import logging

import pytest
import responses
from src.sensory.on_chain import OnChainSignal, fetch_on_chain  # noqa: E402

# CryptoQuant REST base — the real endpoint shape varies by plan,
# so we treat the URL as opaque and mock whatever the module calls.
CRYPTOQUANT_BASE = "https://api.cryptoquant.com/v1"


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


@responses.activate
def test_fetch_on_chain_returns_empty_list_and_logs_warning_on_429(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Rate-limit hit → empty list + `logging.WARNING` entry mentioning 429.

    This is the plan's exact test mandate for Task 3. The caplog check
    makes the "logs warning" assertion specific and measurable (CRITICAL-07).
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
