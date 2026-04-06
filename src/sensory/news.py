"""Alpaca News API integration — STUB (Phase 2 Task 2 implements).

This file is a TDD scaffold: the dataclass contract is pinned so
`tests/test_sensory/test_news.py` can import it, but ``fetch_news``
raises :class:`NotImplementedError` until Task 2 lands. This keeps
mypy green while the tests stay red (they fail at runtime, not at
collection time).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSignal:
    """A single headline with a sentiment score.

    Attributes:
        headline: The raw headline text.
        sentiment: Score in [-1, 1] — negative = bearish, positive = bullish.
        published_at: ISO-8601 timestamp string from the source.
        symbols: Tuple of ticker symbols this headline is tagged for.
    """

    headline: str
    sentiment: float
    published_at: str
    symbols: tuple[str, ...]


def fetch_news(symbols: list[str], limit: int = 10) -> list[NewsSignal]:
    """Fetch recent headlines for the given symbols.

    Args:
        symbols: List of ticker symbols (e.g. ``["BTCUSD", "ETHUSD"]``).
        limit: Max number of headlines to return per request.

    Returns:
        List of :class:`NewsSignal`. Empty list on any API error, timeout,
        malformed payload, or when no news is available — never raises.

    Note:
        This is a scaffold. Phase 2 Task 2 implements the real Alpaca
        News API integration via the shared :mod:`src.core.api_client`.
    """
    msg = "src.sensory.news.fetch_news is not yet implemented (Phase 2 Task 2)"
    raise NotImplementedError(msg)
