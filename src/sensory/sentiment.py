"""Keyword-based sentiment scoring — STUB (Phase 2 Task 4 implements).

TDD scaffold: the dataclass contract is pinned for test imports,
but ``score_sentiment`` raises :class:`NotImplementedError` until
Task 4 lands. FinGPT fine-tuning is explicitly out of scope and
deferred to BACKLOG.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentSignal:
    """Aggregate sentiment reading across a batch of headlines.

    Attributes:
        score: Sentiment score in ``[-1.0, 1.0]``. Negative = bearish,
            positive = bullish, zero = neutral / no signal.
        sample_size: Number of headlines that contributed to the score.
    """

    score: float
    sample_size: int


def score_sentiment(headlines: list[str]) -> SentimentSignal:
    """Score a batch of headlines using a basic keyword-based heuristic.

    Args:
        headlines: List of raw headline strings. May be empty.

    Returns:
        A :class:`SentimentSignal` with ``score`` in ``[-1.0, 1.0]``.
        Empty input returns ``SentimentSignal(score=0.0, sample_size=0)``.

    Note:
        This is a scaffold. Phase 2 Task 4 implements the real keyword
        scoring logic. This is a pure function — no HTTP calls.
    """
    msg = "src.sensory.sentiment.score_sentiment is not yet implemented (Phase 2 Task 4)"
    raise NotImplementedError(msg)
