"""Failing tests for src.sensory.sentiment — keyword-based sentiment scoring.

Task 4 of Phase 2. Keyword sentiment is intentionally basic — FinGPT
fine-tuning is deferred to BACKLOG. The contract: score in [-1, 1],
no crashes on empty input, no HTTP calls at all (pure function).

The behaviour tests are marked ``xfail(strict=True,
raises=NotImplementedError)`` while the module is a skeleton — when
Task 4 lands, xfail becomes XPASS and strict mode forces marker
removal. Self-healing TDD red state that keeps the quality gate green.

The frozen-dataclass immutability test is NOT xfailed — the dataclass
contract is already locked in the skeleton.
"""

from __future__ import annotations

import pytest

from src.sensory.sentiment import SentimentSignal, score_sentiment

# Marker applied to every behaviour test below. Removed (and the test
# turned green) as Task 4 implements the real keyword scoring logic.
pending_impl = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="Phase 2 Task 4: src.sensory.sentiment.score_sentiment not yet implemented",
)


@pending_impl
def test_score_sentiment_returns_signal_in_valid_range_for_bullish_headlines() -> None:
    """Bullish keywords → positive score in (0, 1]."""
    headlines = [
        "Bitcoin surges to new all-time high on strong inflows",
        "Ethereum rallies as bullish sentiment grows",
        "Crypto market soars after positive ETF news",
    ]

    signal = score_sentiment(headlines)

    assert isinstance(signal, SentimentSignal)
    assert -1.0 <= signal.score <= 1.0
    assert signal.score > 0.0, "bullish headlines should produce a positive score"


@pending_impl
def test_score_sentiment_returns_signal_in_valid_range_for_bearish_headlines() -> None:
    """Bearish keywords → negative score in [-1, 0)."""
    headlines = [
        "Bitcoin crashes 20% on exchange hack",
        "Crypto market plunges after regulatory crackdown",
        "Ethereum drops sharply on bearish signals",
    ]

    signal = score_sentiment(headlines)

    assert isinstance(signal, SentimentSignal)
    assert -1.0 <= signal.score <= 1.0
    assert signal.score < 0.0, "bearish headlines should produce a negative score"


@pending_impl
def test_score_sentiment_returns_zero_for_empty_input() -> None:
    """Empty list → SentimentSignal(score=0.0), not an exception."""
    signal = score_sentiment([])

    assert isinstance(signal, SentimentSignal)
    assert signal.score == 0.0


@pending_impl
def test_score_sentiment_returns_neutral_for_non_sentiment_headlines() -> None:
    """Headlines with no sentiment keywords → score close to 0."""
    headlines = [
        "Conference scheduled for next month",
        "New exchange opens in Singapore",
    ]

    signal = score_sentiment(headlines)

    assert isinstance(signal, SentimentSignal)
    assert -1.0 <= signal.score <= 1.0
    assert abs(signal.score) < 0.3, f"neutral headlines should be near 0, got {signal.score}"


@pending_impl
def test_score_sentiment_clamps_extreme_scores_to_unit_interval() -> None:
    """Even with dozens of strong-sentiment keywords, score must stay in [-1, 1]."""
    headlines = ["Bitcoin surges rallies soars moons pumps explodes"] * 50

    signal = score_sentiment(headlines)

    assert -1.0 <= signal.score <= 1.0


def test_sentiment_signal_is_frozen_dataclass() -> None:
    """SentimentSignal must be immutable — score is a value, not state."""
    sig = SentimentSignal(score=0.5, sample_size=10)
    with pytest.raises(AttributeError):
        sig.score = 0.9  # type: ignore[misc]
