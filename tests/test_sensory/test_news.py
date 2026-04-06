"""Failing tests for src.sensory.news — Alpaca News API integration.

These tests define the contract for Task 2 of Phase 2. They are expected
to fail with ImportError until `src/sensory/news.py` is implemented.

Mocking convention: `responses` library (see plan §Phase 2 note). No
`unittest.mock.patch` on `requests` — too fragile.
"""

from __future__ import annotations

import pytest
import responses

# The module under test does not yet exist. These imports will raise
# ImportError until Task 2 implements `src/sensory/news.py`. That is the
# intended red state of the TDD cycle.
from src.sensory.news import NewsSignal, fetch_news  # noqa: E402

# Alpaca News API base (real shape — see https://docs.alpaca.markets/reference/news-3).
ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"


@responses.activate
def test_fetch_news_returns_structured_signals_on_success() -> None:
    """Happy path: API returns headlines → function returns NewsSignal list."""
    responses.add(
        responses.GET,
        ALPACA_NEWS_URL,
        json={
            "news": [
                {
                    "id": 1,
                    "headline": "Bitcoin surges past $70k on ETF inflows",
                    "summary": "Strong institutional demand drives price up.",
                    "created_at": "2026-04-06T10:00:00Z",
                    "symbols": ["BTCUSD"],
                },
                {
                    "id": 2,
                    "headline": "Ethereum upgrade delayed by two months",
                    "summary": "Core devs cite testnet issues.",
                    "created_at": "2026-04-06T11:00:00Z",
                    "symbols": ["ETHUSD"],
                },
            ],
            "next_page_token": None,
        },
        status=200,
    )

    signals = fetch_news(symbols=["BTCUSD", "ETHUSD"], limit=10)

    assert isinstance(signals, list)
    assert len(signals) == 2
    for sig in signals:
        assert isinstance(sig, NewsSignal)
        assert isinstance(sig.headline, str) and sig.headline
        assert isinstance(sig.sentiment, float)
        assert -1.0 <= sig.sentiment <= 1.0
        assert isinstance(sig.published_at, str)
        assert isinstance(sig.symbols, tuple)


@responses.activate
def test_fetch_news_returns_empty_list_on_api_500_error() -> None:
    """Fail-loudly-but-safely: 500 → empty list, no crash, no exception bubbles up."""
    responses.add(
        responses.GET,
        ALPACA_NEWS_URL,
        json={"error": "internal server error"},
        status=500,
    )

    signals = fetch_news(symbols=["BTCUSD"], limit=10)

    assert signals == []


@responses.activate
def test_fetch_news_returns_empty_list_on_timeout() -> None:
    """Timeouts are treated as transient errors → empty list, no exception."""
    responses.add(
        responses.GET,
        ALPACA_NEWS_URL,
        body=ConnectionError("connection timeout"),
    )

    signals = fetch_news(symbols=["BTCUSD"], limit=10)

    assert signals == []


@responses.activate
def test_fetch_news_returns_empty_list_on_malformed_payload() -> None:
    """Defensive parse: if the response is valid JSON but the wrong shape,
    return empty list instead of raising KeyError."""
    responses.add(
        responses.GET,
        ALPACA_NEWS_URL,
        json={"unexpected_key": "nope"},  # missing "news" key
        status=200,
    )

    signals = fetch_news(symbols=["BTCUSD"], limit=10)

    assert signals == []


@responses.activate
def test_fetch_news_returns_empty_list_when_no_news_available() -> None:
    """Empty but valid response → empty list, no NewsSignal objects."""
    responses.add(
        responses.GET,
        ALPACA_NEWS_URL,
        json={"news": [], "next_page_token": None},
        status=200,
    )

    signals = fetch_news(symbols=["BTCUSD"], limit=10)

    assert signals == []


def test_news_signal_is_frozen_dataclass() -> None:
    """NewsSignal must be immutable (frozen=True) — signals are values, not state."""
    sig = NewsSignal(
        headline="Test",
        sentiment=0.5,
        published_at="2026-04-06T10:00:00Z",
        symbols=("BTCUSD",),
    )
    with pytest.raises(AttributeError):
        sig.sentiment = 0.9  # type: ignore[misc]
