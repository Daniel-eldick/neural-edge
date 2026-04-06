"""Macro signals (stablecoin flows + funding rate aggregates) — STUB.

Phase 2 Task 5 implements. TDD scaffold: the dataclass contract is
pinned for test imports, but ``fetch_macro`` raises
:class:`NotImplementedError` until Task 5 lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MacroDirection = Literal["bullish", "bearish", "neutral"]


@dataclass(frozen=True)
class MacroSignal:
    """A single macro-level reading (stablecoin supply, aggregate funding, etc.).

    Attributes:
        metric: Name of the metric (e.g. ``"stablecoin_supply"``,
            ``"avg_funding_rate"``).
        value: The raw metric value.
        direction: One of ``"bullish"``, ``"bearish"``, ``"neutral"``.
    """

    metric: str
    value: float
    direction: MacroDirection


def fetch_macro() -> list[MacroSignal]:
    """Fetch macro signals from upstream providers.

    Returns:
        List of :class:`MacroSignal`. Empty list when ALL underlying
        endpoints fail. Partial failures return only the successful
        signals — never raises.

    Note:
        This is a scaffold. Phase 2 Task 5 implements the real provider
        integration via :mod:`src.core.api_client`.
    """
    msg = "src.sensory.macro.fetch_macro is not yet implemented (Phase 2 Task 5)"
    raise NotImplementedError(msg)
