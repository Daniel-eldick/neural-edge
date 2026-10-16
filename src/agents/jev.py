"""Pinned Jev Choice connector and bounded connection check; no trading execution."""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from dotenv import dotenv_values

from src.agents.budget import CAP_NANO_USD, Budget, BudgetError

if TYPE_CHECKING:
    from collections.abc import Callable

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
# https://docs.typesafe.ai/models, verified 2026-09-30:
# $0.042 / million input tokens, output free, 64k total context.
PRICE_NANO_USD_PER_TOKEN = 42
MAX_INPUT_TOKENS = 65_536
RESERVE_NANO_USD = 3_000_000  # $0.003, above the documented maximum per-request price.
PRICING_EXPIRES = datetime(2026, 11, 1, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "user_data/ai/budget.sqlite"


class JevError(RuntimeError):
    """Safe-to-display provider failure; contains no credentials or raw response body."""


@dataclass(frozen=True)
class Choice:
    choice: str
    confidence: float
    probabilities: dict[str, float]
    model: str
    input_tokens: int
    cost_nano_usd: int


def probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Invalid probability")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability")
    return float(value)


def parse_response(data: Any, options: dict[str, str]) -> Choice:
    try:
        if data["model"] != MODEL:
            raise ValueError("Unreviewed model")
        tokens = data["usage"]["input_tokens"]
        if type(tokens) is not int or not 0 <= tokens <= MAX_INPUT_TOKENS:
            raise ValueError("Invalid token usage")
        answer = data["answers"]["decision"]
        if answer["type"] != "choice" or answer["choice"] not in options:
            raise ValueError("Unexpected answer")
        values = answer["probabilities"]
        if not isinstance(values, dict) or set(values) != set(options):
            raise ValueError("Mismatched probabilities")
        probabilities = {key: probability(value) for key, value in values.items()}
        if not math.isclose(sum(probabilities.values()), 1, abs_tol=1e-5):
            raise ValueError("Probabilities do not sum to one")
        return Choice(answer["choice"], probability(answer["confidence"]), probabilities,
                      MODEL, tokens, tokens * PRICE_NANO_USD_PER_TOKEN)
    except (TypeError, KeyError, ValueError):
        raise JevError("Invalid Jev response; full cost reservation retained") from None


class JevClient:
    def __init__(self, api_key: str, budget: Budget, *,
                 clock: Callable[[], datetime] | None = None) -> None:
        if not api_key.strip():
            raise JevError("TypeSafe token is missing from the environment or .env.local")
        self._api_key = api_key.strip()
        self.budget = budget
        self.clock = clock or (lambda: datetime.now(UTC))

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        now = self.clock()
        if now.tzinfo is None or now >= PRICING_EXPIRES:
            raise JevError("Jev pricing review required before new paid calls")
        if (not state.strip() or not instructions.strip() or not 2 <= len(options) <= 32
                or any(not k.strip() or not v.strip() for k, v in options.items())):
            raise JevError("Provide state, instructions and 2–32 nonempty choices")
        payload = {"model": MODEL, "state": state, "questions": {"decision": {
            "type": "choice", "instructions": instructions, "criteria": options,
        }}}
        wire = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode("utf-8")
        if len(wire) > 24_000:
            raise JevError("Jev request exceeds the 24,000-byte local bound")
        call_id = self.budget.reserve("typesafe", RESERVE_NANO_USD, now=now)
        try:
            # requests does not retry POST by default. Never follow redirects with the key.
            with requests.post(
                ENDPOINT, data=wire, headers={"Authorization": f"Bearer {self._api_key}",
                                             "Content-Type": "application/json"},
                timeout=(5, 20), allow_redirects=False, stream=True,
            ) as response:
                if response.status_code != 200:
                    raise JevError(f"TypeSafe HTTP {response.status_code}; reservation retained")
                chunks = bytearray()
                for chunk in response.iter_content(8192):
                    chunks.extend(chunk)
                    if len(chunks) > 256_000:
                        raise JevError("Oversized Jev response; reservation retained")
                data = json.loads(chunks)
        except requests.RequestException:
            raise JevError("TypeSafe connection failed; full reservation retained") from None
        except (ValueError, UnicodeError):
            raise JevError("Invalid Jev response encoding; full reservation retained") from None
        result = parse_response(data, options)
        self.budget.settle(call_id, result.cost_nano_usd,
                           model=result.model, input_tokens=result.input_tokens)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init-budget", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.init_budget:
            Budget.initialize(LEDGER)
            print("Created shared USD 3/month AI budget ledger (UTC calendar months).")
            return
        budget = Budget(LEDGER)
        if args.check:
            key = os.environ.get("TYPESAFE_API_KEY") or dotenv_values(ROOT / ".env.local").get(
                "TYPESAFE_API_KEY"
            ) or ""
            result = JevClient(key, budget).choose(
                "Connection check only. NeuralEdge is configured for paper-only simulation. "
                "No real orders or trading action is being requested.",
                "Which operating mode is explicitly stated?",
                {"paper": "Simulation without real money", "live": "Real-money trading"},
            )
            print(json.dumps(asdict(result), sort_keys=True))
            if result.choice != "paper":
                raise JevError("Jev responded but failed the paper-mode connection check")
        snapshot = budget.snapshot()
        print(json.dumps({
            "monthly_limit_usd": CAP_NANO_USD / 1e9,
            "accounted_usd": snapshot["used_nano_usd"] / 1e9,
            "remaining_usd": (CAP_NANO_USD - snapshot["used_nano_usd"]) / 1e9,
            "unresolved_reservations": snapshot["pending_calls"],
        }, sort_keys=True))
    except (BudgetError, JevError) as exc:
        parser.exit(1, f"{exc}\n")
    except (OSError, sqlite3.Error):
        parser.exit(1, "Local AI state could not be initialized/read; existing data preserved.\n")


if __name__ == "__main__":
    main()
