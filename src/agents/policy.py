"""Experimental Jev breakout filter; deterministic code retains all risk authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from src.agents.jev import MODEL
from src.replay.engine import Decision, Observation

if TYPE_CHECKING:
    from src.agents.responses import Chooser, ResponseStore
    from src.replay.engine import Recorder

INSTRUCTIONS = (
    "Evaluate this hypothetical long-only spot breakout using only the supplied closed OHLCV "
    "candles and current portfolio. Choose enter only if trend and volume support continuation; "
    "otherwise choose wait. Do not infer future prices or use outside historical knowledge. "
    "This is research, not a claim of profitability. Stops, targets and position size are "
    "controlled by independent code. Your choice cannot change risk limits."
)
OPTIONS = {"enter": "Accept the breakout candidate with its fixed protective stop and target",
           "wait": "Abstain because the supplied evidence does not justify this candidate"}


class JevPolicy:
    def __init__(self, client: Chooser, store: ResponseStore, recorder: Recorder, *,
                 max_attempts: int = 20) -> None:
        if type(max_attempts) is not int or not 1 <= max_attempts <= 100:
            raise ValueError("Model attempt limit must be between 1 and 100")
        self.client, self.store, self.recorder = client, store, recorder
        self.max_attempts = max_attempts
        source = hashlib.sha256()
        for name in ("policy.py", "responses.py", "jev.py", "budget.py"):
            source.update(Path(__file__).with_name(name).read_bytes())
        self.checkpoint_id = f"jev-breakout-filter-v1:{MODEL}:{max_attempts}:{source.hexdigest()}"

    def save_state(self) -> dict[str, object]:
        return {"response_store": self.store.identity}

    def restore_state(self, state: dict[str, object]) -> None:
        if state != self.save_state():
            raise ValueError("Jev response store differs from checkpoint; recovery refused")

    def decide(self, observation: Observation) -> Decision:
        bars = observation.candles
        if observation.halted:
            return Decision(reason="Portfolio risk halt; no new candidates")
        if len(bars) < 21:
            return Decision(reason="Waiting for 21 closed candles")
        latest = bars[-1]
        if any(p.symbol == latest.symbol for p in observation.positions):
            return Decision(reason="Existing position managed by protective orders")
        if len(observation.positions) >= 5:
            return Decision(reason="Shared five-position limit reached")
        if latest.close <= max(c.high for c in bars[-21:-1]):
            return Decision(reason="No close above the previous 20-bar high")
        stop, target = latest.close * 0.98, latest.close * 1.04
        state = json.dumps({
            "now": observation.now, "candles": [asdict(c) for c in bars[-21:]],
            "positions": [asdict(p) for p in observation.positions],
            "equity": observation.equity, "halted": observation.halted,
            "candidate": {"symbol": latest.symbol, "stop": stop, "target": target},
        }, sort_keys=True, allow_nan=False)
        key = json.dumps([latest.symbol, observation.now], separators=(",", ":"))
        answer = self.store.choose(key, state, INSTRUCTIONS, OPTIONS,
                                   self.client, self.max_attempts)
        self.recorder.record({"kind": "MODEL_CHOICE", "time": observation.now,
                              "symbol": latest.symbol, "receipt": key, **asdict(answer)})
        if answer.choice == "enter":
            return Decision("ENTER_LONG", stop, target,
                            "Close exceeded the prior 20-bar high and Jev accepted the candidate")
        return Decision(reason="Jev declined the breakout candidate; no entry proposed")
