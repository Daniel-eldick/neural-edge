"""Run an offline baseline replay: python -m src.replay --help."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from dotenv import dotenv_values

from src.agents.budget import Budget
from src.agents.contextual import ContextPolicy
from src.agents.jev import LEDGER, ROOT, JevClient
from src.agents.learning import LearningPolicy
from src.agents.market_context import MarketContext
from src.agents.policy import JevPolicy
from src.agents.responses import ResponseStore
from src.replay.engine import Candle, Decision, Observation, Policy, Replay, Settings
from src.replay.journal import Journal


class BreakoutBaseline:
    """Fixed comparison policy, NOT an AI apprentice or a recommended strategy."""

    checkpoint_id = "breakout-baseline-v1"

    def save_state(self) -> dict[str, object]:
        return {}

    def restore_state(self, state: dict[str, object]) -> None:
        if state:
            raise ValueError("The fixed baseline has no mutable policy state")

    def decide(self, observation: Observation) -> Decision:
        bars = observation.candles
        if observation.halted or len(bars) < 21:
            return Decision()
        if any(p.symbol == bars[-1].symbol for p in observation.positions):
            return Decision(reason="Existing position managed by protective orders")
        latest = bars[-1]
        if latest.close > max(c.high for c in bars[-21:-1]):
            return Decision("ENTER_LONG", latest.close * 0.98, latest.close * 1.04,
                            "Close exceeds prior 20-bar high")
        return Decision()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--interval", type=int, choices=(60, 300), default=300)
    parser.add_argument("--balance", type=float, default=1000)
    parser.add_argument("--fee", type=float, default=0.001)
    parser.add_argument("--slippage", type=float, default=0.001)
    parser.add_argument("--policy", choices=("baseline", "jev", "jev-memory", "jev-context"),
                        default="baseline",
                        help="Jev opts into paid candidate filtering under the shared AI budget")
    parser.add_argument("--context-csv", type=Path,
                        help="UTC daily OHLCV history, required only for jev-context")
    parser.add_argument("--max-model-calls", type=int, default=20,
                        help="Jev attempt limit per run, 1–100 (default: 20)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume this journal with the same data, settings and policy")
    parser.add_argument("--stop-after", type=int,
                        help="Pause after this many additional candle batches")
    args = parser.parse_args()
    if args.stop_after is not None and args.stop_after <= 0:
        parser.error("--stop-after must be positive")
    if not 1 <= args.max_model_calls <= 100:
        parser.error("--max-model-calls must be between 1 and 100")
    if (args.policy == "jev-context") != (args.context_csv is not None):
        parser.error("--context-csv is required exactly when --policy is jev-context")
    settings = Settings(args.balance, args.interval, args.fee, args.slippage)
    with args.csv.open(newline="") as source:
        candles = [Candle(row["symbol"], int(row["opened_at"]),
                          *[float(row[k]) for k in ("open", "high", "low", "close", "volume")])
                   for row in csv.DictReader(source)]
    market = MarketContext.from_csv(args.context_csv) if args.context_csv is not None else None
    if market is not None and {c.symbol for c in candles} != {market.symbol}:
        raise ValueError("Context and intraday data must have the same single symbol")
    journal = Journal(args.journal, resume=args.resume)
    store: ResponseStore | None = None
    try:
        policy: Policy = BreakoutBaseline()
        if args.policy in {"jev", "jev-memory", "jev-context"}:
            budget = Budget(LEDGER)
            budget.snapshot()  # Refuse missing/corrupt accounting before creating model state.
            key = os.environ.get("TYPESAFE_API_KEY") or dotenv_values(ROOT / ".env.local").get(
                "TYPESAFE_API_KEY"
            ) or ""
            client = JevClient(key, budget)
            store = ResponseStore(args.journal.with_name(args.journal.name + ".responses.sqlite"),
                                  resume=args.resume)
            if market is not None:
                policy = ContextPolicy(client, store, journal, interval=args.interval,
                                       market=market, max_attempts=args.max_model_calls)
            elif args.policy == "jev-memory":
                policy = LearningPolicy(client, store, journal, interval=args.interval,
                                        max_attempts=args.max_model_calls)
            else:
                policy = JevPolicy(client, store, journal, max_attempts=args.max_model_calls)
        if not args.resume:
            digest = hashlib.sha256(args.csv.read_bytes()).hexdigest()
            names = {"baseline": "breakout-baseline-v1", "jev": "jev-breakout-filter-v1",
                     "jev-memory": "jev-memory-filter-v1", "jev-context": "jev-context-filter-v1"}
            manifest: dict[str, object] = {"kind": "MANIFEST", "sha256": digest,
                                           "policy": names[args.policy],
                                           "simulation": "coarse-candles-v1"}
            if market is not None:
                manifest["context_sha256"] = market.source_sha256
                manifest["context_interval"] = 86400
            journal.record(manifest)
        result = Replay(settings, journal).run(candles, policy,
                                              resume=args.resume, stop_after=args.stop_after)
        print(json.dumps(asdict(result), indent=2, allow_nan=False))
    except Exception as exc:
        # Never append past the last checkpoint after a failed/rejected resume.
        print(f"Replay stopped: {exc}. Last committed checkpoint preserved.", file=sys.stderr)
        raise
    finally:
        journal.close()
        if store is not None:
            store.close()


if __name__ == "__main__":
    main()
