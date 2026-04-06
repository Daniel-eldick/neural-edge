"""CryptoQuant on-chain signals — STUB (Phase 2 Task 3 implements).

TDD scaffold: the dataclass contract is pinned for test imports,
but ``fetch_on_chain`` raises :class:`NotImplementedError` until
Task 3 lands the real integration through
:mod:`src.core.api_client`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OnChainDirection = Literal["bullish", "bearish", "neutral"]


@dataclass(frozen=True)
class OnChainSignal:
    """A single on-chain metric reading.

    Attributes:
        metric: Name of the metric (e.g. ``"funding_rate"``, ``"exchange_netflow"``).
        value: The raw metric value (unit depends on ``metric``).
        direction: One of ``"bullish"``, ``"bearish"``, ``"neutral"``.
        confidence: Confidence in the reading, in ``[0.0, 1.0]``.
    """

    metric: str
    value: float
    direction: OnChainDirection
    confidence: float


def fetch_on_chain(asset: str = "btc") -> list[OnChainSignal]:
    """Fetch on-chain signals (funding rates, exchange flows, etc.).

    Args:
        asset: Asset symbol in CryptoQuant's notation (e.g. ``"btc"``).

    Returns:
        List of :class:`OnChainSignal`. Empty list on any failure
        (rate-limit 429, 500s, malformed payload). On 429 specifically,
        a ``logging.WARNING`` is emitted before returning — never raises.

    Note:
        This is a scaffold. Phase 2 Task 3 implements the real CryptoQuant
        REST integration.
    """
    msg = "src.sensory.on_chain.fetch_on_chain is not yet implemented (Phase 2 Task 3)"
    raise NotImplementedError(msg)
