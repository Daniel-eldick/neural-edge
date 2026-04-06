"""Failing tests for src.core.api_client — shared HTTP wrapper.

Contract for Phase 2 Task 1:

- Single entry point: ``APIClient.get(provider, url, params, ttl_seconds)``.
- Per-provider rate-limit token bucket (CoinGecko 30/min, Alpaca 200/min,
  CryptoQuant 10/min — conservative free-tier default).
- TTL cache keyed by ``(provider, url, sorted_params)``.
- Raises :class:`RateLimitError` when the bucket is empty (caller
  decides whether to retry, degrade, or bubble up — the client itself
  never silently sleeps and stalls the trading loop).
- Clock and HTTP session are injectable for deterministic tests.

Mocking convention: ``responses`` library — no ``unittest.mock.patch``
on ``requests``.
"""

from __future__ import annotations

import pytest
import requests
import responses

from src.core.api_client import APIClient, APIClientError, RateLimitError

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


class FakeClock:
    """Monotonic clock replacement for deterministic TTL / rate-limit tests."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@responses.activate
def test_cache_hit_returns_without_http_call() -> None:
    """Identical request within TTL must not touch the wire a second time."""
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"bitcoin": {"usd": 65000}},
        status=200,
    )

    clock = FakeClock()
    client = APIClient(clock=clock)

    payload_1 = client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        ttl_seconds=60,
    )
    payload_2 = client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        ttl_seconds=60,
    )

    assert payload_1 == payload_2 == {"bitcoin": {"usd": 65000}}
    # Second call served from cache — wire should only have fired once.
    assert len(responses.calls) == 1


@responses.activate
def test_ttl_expiry_forces_refetch() -> None:
    """Once TTL elapses, the next request must refetch from the wire."""
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"bitcoin": {"usd": 65000}},
        status=200,
    )
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"bitcoin": {"usd": 66000}},
        status=200,
    )

    clock = FakeClock()
    client = APIClient(clock=clock)

    first = client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "bitcoin"},
        ttl_seconds=60,
    )

    # Advance past the cache TTL — next call must go to the wire.
    clock.advance(61.0)

    second = client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "bitcoin"},
        ttl_seconds=60,
    )

    assert first == {"bitcoin": {"usd": 65000}}
    assert second == {"bitcoin": {"usd": 66000}}
    assert len(responses.calls) == 2


@responses.activate
def test_rate_limiter_blocks_31st_coingecko_request_in_60s_window() -> None:
    """CoinGecko bucket is 30/min — the 31st call must raise before the HTTP layer."""
    # Register 30 mock responses (FIFO-served by `responses`).
    for _ in range(30):
        responses.add(
            responses.GET,
            COINGECKO_URL,
            json={"ok": True},
            status=200,
        )

    clock = FakeClock()
    client = APIClient(clock=clock)

    # 30 unique params -> bypass the cache, consume 30 tokens.
    for i in range(30):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params={"ids": f"coin_{i}"},
            ttl_seconds=0,  # disable caching to isolate the rate-limiter
        )

    assert len(responses.calls) == 30

    # 31st call in the same 60s window — must raise *before* hitting the wire.
    with pytest.raises(RateLimitError) as excinfo:
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params={"ids": "coin_31"},
            ttl_seconds=0,
        )

    assert excinfo.value.provider == "coingecko"
    assert excinfo.value.retry_after > 0
    # The HTTP layer was never touched by the 31st call.
    assert len(responses.calls) == 30


@responses.activate
def test_rate_limit_window_rolls_and_bucket_refills() -> None:
    """Once the 60s window passes, the token bucket refills and calls succeed again."""
    for _ in range(31):
        responses.add(
            responses.GET,
            COINGECKO_URL,
            json={"ok": True},
            status=200,
        )

    clock = FakeClock()
    client = APIClient(clock=clock)

    for i in range(30):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params={"ids": f"coin_{i}"},
            ttl_seconds=0,
        )

    # Advance past the 60s window — all 30 old timestamps should be evicted.
    clock.advance(61.0)

    # This call must succeed (not raise).
    client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "coin_30"},
        ttl_seconds=0,
    )

    assert len(responses.calls) == 31


def test_unknown_provider_raises_api_client_error() -> None:
    """Guard against typos — unknown providers are a programming error, not a runtime condition."""
    client = APIClient(clock=FakeClock())

    with pytest.raises(APIClientError) as excinfo:
        client.get(
            provider="bogus_provider",
            url="https://example.com",
            params=None,
            ttl_seconds=60,
        )

    assert "bogus_provider" in str(excinfo.value)


@responses.activate
def test_http_500_propagates_as_http_error() -> None:
    """5xx responses must propagate via ``raise_for_status`` — the
    sensory-layer catches and returns an empty signal list. The
    transport layer is deliberately a thin wrapper; it does not
    swallow failures.
    """
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"error": "internal server error"},
        status=500,
    )

    client = APIClient(clock=FakeClock())

    with pytest.raises(requests.HTTPError):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params=None,
            ttl_seconds=0,
        )


@responses.activate
def test_connection_error_propagates() -> None:
    """ConnectionError (network down, DNS failure, etc.) propagates unchanged.

    Note: at the ``responses`` mock layer, ConnectionError and Timeout
    are indistinguishable — both are simulated via ``body=<exception>``.
    This test pins the contract for the *ConnectionError branch*; the
    sibling ``test_timeout_propagates`` pins the *Timeout branch*.
    """
    responses.add(
        responses.GET,
        COINGECKO_URL,
        body=requests.ConnectionError("network unreachable"),
    )

    client = APIClient(clock=FakeClock())

    with pytest.raises(requests.ConnectionError):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params=None,
            ttl_seconds=0,
        )


@responses.activate
def test_timeout_propagates() -> None:
    """requests.Timeout propagates unchanged — the api_client does not retry."""
    responses.add(
        responses.GET,
        COINGECKO_URL,
        body=requests.Timeout("timed out after 10s"),
    )

    client = APIClient(clock=FakeClock())

    with pytest.raises(requests.Timeout):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params=None,
            ttl_seconds=0,
        )


@responses.activate
def test_failed_request_does_not_populate_cache() -> None:
    """A 5xx failure must not poison the cache — the next call must
    try the wire again. Caching error payloads would mask transient
    outages from the sensory-layer retry loop.
    """
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"error": "boom"},
        status=500,
    )
    responses.add(
        responses.GET,
        COINGECKO_URL,
        json={"bitcoin": {"usd": 65000}},
        status=200,
    )

    client = APIClient(clock=FakeClock())

    with pytest.raises(requests.HTTPError):
        client.get(
            provider="coingecko",
            url=COINGECKO_URL,
            params={"ids": "bitcoin"},
            ttl_seconds=60,
        )

    # Second call — same params, same TTL. Must refetch (cache was not
    # populated by the failed request).
    payload = client.get(
        provider="coingecko",
        url=COINGECKO_URL,
        params={"ids": "bitcoin"},
        ttl_seconds=60,
    )

    assert payload == {"bitcoin": {"usd": 65000}}
    assert len(responses.calls) == 2
