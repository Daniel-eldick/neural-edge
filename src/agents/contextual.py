"""Separate opt-in Jev variant with completed daily/weekly data and causal trade memory."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from src.agents.learning import MEMORY_INSTRUCTIONS, LearningPolicy
from src.memory.teacher import digest

if TYPE_CHECKING:
    from src.agents.market_context import MarketContext
    from src.agents.responses import Chooser, ResponseStore
    from src.replay.engine import Observation
    from src.replay.journal import Journal

CONTEXT_INSTRUCTIONS = (
    MEMORY_INSTRUCTIONS + " Market context contains only completed UTC daily and Monday-based "
    "weekly OHLCV bars available at the decision cutoff. Daily descriptors use 20 bars; weekly "
    "descriptors use 8 bars. Return and mean high-low/open range are descriptive, not forecasts. "
    "Unknown means insufficient or stale history: do not invent a direction from it. "
    "A positive trailing return does not establish a bull market or a repeating cycle. "
    "Consider conflicting timeframes and the possibility of a failed breakout. "
    "This context supplies no historical analogue outcomes or calibrated confidence."
)


class ContextPolicy(LearningPolicy):
    def __init__(
        self,
        client: Chooser,
        store: ResponseStore,
        recorder: Journal,
        *,
        interval: int,
        market: MarketContext,
        max_attempts: int = 20,
    ) -> None:
        super().__init__(client, store, recorder, interval=interval, max_attempts=max_attempts)
        self.market = market
        self.instructions = CONTEXT_INSTRUCTIONS
        source = hashlib.sha256()
        for path in (Path(__file__), Path(__file__).with_name("market_context.py")):
            source.update(path.read_bytes())
        self.checkpoint_id += f":context-v1:{market.source_sha256}:{source.hexdigest()}"

    def context(self, observation: Observation) -> dict[str, object]:
        market = self.market.snapshot(observation.candles[-1].symbol, observation.now)
        self.journal.record(
            {
                "kind": "CONTEXT_READ",
                "time": observation.now,
                "as_of": market["as_of"],
                "symbol": market["symbol"],
                "context_sha256": digest(market),
                "daily_status": market["daily"]["status"],
                "daily_reason": market["daily"]["reason"],
                "daily_last_closed_at": market["daily"]["last_closed_at"],
                "weekly_status": market["weekly"]["status"],
                "weekly_reason": market["weekly"]["reason"],
                "weekly_last_closed_at": market["weekly"]["last_closed_at"],
            }
        )
        return {**super().context(observation), "market_context": market}
