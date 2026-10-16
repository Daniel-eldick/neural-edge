"""A bounded evidence teacher: facts first, candidate lessons, no risk authority."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

VERSION = "closed-trade-teacher-v1"
CURRICULUM = Path(__file__).with_name("curriculum.json")
MAX_CASES = 64
RETRIEVAL_LIMIT = 6


def integer(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Memory requires nonnegative integer times/sequences")
    return value


def finite(value: Any, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Memory requires numeric trade evidence")
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError("Memory requires finite valid trade evidence")
    return float(value)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def curriculum(now: int) -> list[dict[str, Any]]:
    now = integer(now)
    pack = json.loads(CURRICULUM.read_text())
    if (
        set(pack) != {"version", "available_at", "cards"}
        or pack["version"] != "foundations-v0.1"
        or integer(pack["available_at"]) != 1790726400
        or not isinstance(pack["cards"], list)
        or len(pack["cards"]) != 6
    ):
        raise ValueError("Unsupported curriculum contract")
    for card in pack["cards"]:
        if (
            set(card) != {"lesson_id", "source_ids", "claim"}
            or not isinstance(card["claim"], str)
            or not 1 <= len(card["claim"]) <= 500
        ):
            raise ValueError("Curriculum must contain original claims, not quiz answers")
    if now < pack["available_at"]:
        return []
    return [
        {**card, "version": pack["version"], "available_at": pack["available_at"]}
        for card in pack["cards"]
    ]


@dataclass(frozen=True)
class Entry:
    sequence: int
    time: int
    price: float
    quantity: float


@dataclass(frozen=True)
class Case:
    case_id: str
    symbol: str
    opened_at: int
    closed_at: int
    available_at: int
    entry_price: float
    exit_price: float
    quantity: float
    net_profit: float
    reviewed_at: int | None = None


class ClosedTradeTeacher:
    """Review only completed trades from the caller's own causal event prefix."""

    def __init__(self, interval: int) -> None:
        if interval not in (60, 300):
            raise ValueError("Teacher requires the replay's 60s/300s interval")
        self.interval = interval
        self.entries: dict[str, Entry] = {}
        self.cases: list[Case] = []
        self.clock = self.last_sequence = self.reviewed_total = 0

    def consume(self, sequence: int, event: dict[str, Any], *, now: int) -> None:
        if event.get("kind") not in {"ENTER", "EXIT"}:
            return
        sequence, now, occurred = integer(sequence), integer(now), integer(event["time"])
        if occurred > now:
            raise ValueError("Teacher rejected a future event")
        if sequence <= self.last_sequence:
            raise ValueError("Teacher trade events must advance once in sequence")
        symbol = event["symbol"]
        if not isinstance(symbol, str) or not 1 <= len(symbol) <= 40:
            raise ValueError("Invalid memory symbol")
        price, quantity = (
            finite(event["price"], positive=True),
            finite(event["quantity"], positive=True),
        )
        if event["kind"] == "ENTER":
            if symbol in self.entries or len(self.entries) >= 5:
                raise ValueError("Duplicate entry or excessive pending teacher positions")
            self.entries[symbol] = Entry(sequence, occurred, price, quantity)
        else:
            entry = self.entries.get(symbol)
            if entry is None:
                raise ValueError("Teacher outcome has no matching entry")
            if occurred < entry.time or not math.isclose(quantity, entry.quantity, rel_tol=1e-12):
                raise ValueError("Teacher exit does not match its entry")
            case = Case(
                f"trade:{entry.sequence}:{sequence}",
                symbol,
                entry.time,
                occurred,
                occurred + self.interval,
                entry.price,
                price,
                quantity,
                finite(event["net_profit"]),
            )
            if len(self.cases) >= MAX_CASES and self.cases[0].reviewed_at is None:
                raise ValueError("Too many unreviewed cases; cannot silently discard evidence")
            self.cases = [*self.cases, case][-MAX_CASES:]
            del self.entries[symbol]
        self.last_sequence = sequence

    def review(self, now: int) -> dict[str, Any] | None:
        now = integer(now)
        if now < self.clock:
            raise ValueError("Teacher review clock cannot move backwards")
        self.clock = now
        ready = [
            case for case in self.cases if case.reviewed_at is None and case.available_at <= now
        ]
        if not ready:
            return None
        ids = {case.case_id for case in ready}
        self.cases = [
            replace(case, reviewed_at=now) if case.case_id in ids else case for case in self.cases
        ]
        self.reviewed_total += len(ready)
        visible = [case for case in self.cases if case.reviewed_at is not None]
        return {
            "kind": "TEACHER_REVIEW",
            "time": now,
            "teacher_version": VERSION,
            "case_ids": [case.case_id for case in ready],
            "reviewed_total": self.reviewed_total,
            "supporting_case_ids": [c.case_id for c in visible if c.net_profit > 0],
            "counterexample_case_ids": [c.case_id for c in visible if c.net_profit <= 0],
            "status": "candidate",
            "available_at": now,
        }

    def context(self, symbol: str, now: int) -> dict[str, Any]:
        now = integer(now)
        if now > self.clock:
            raise ValueError("Memory retrieval cannot advance the reviewed clock")
        cases = [
            case
            for case in self.cases
            if case.symbol == symbol
            and case.reviewed_at is not None
            and case.available_at <= now
            and case.reviewed_at <= now
        ][-RETRIEVAL_LIMIT:]
        lesson = None
        if cases:
            lesson = {
                "lesson_id": f"{VERSION}:{symbol}:{max(c.reviewed_at or 0 for c in cases)}",
                "status": "candidate",
                "available_at": max(c.reviewed_at or 0 for c in cases),
                "hypothesis": "This fixed breakout setup may produce positive returns after costs.",
                "claim": "These observations do not establish a reliable trading rule.",
                "supporting_case_ids": [c.case_id for c in cases if c.net_profit > 0],
                "counterexample_case_ids": [c.case_id for c in cases if c.net_profit <= 0],
                "uncertainty": "Small, policy-selected rolling sample; no causal explanation or "
                "calibrated probability can be inferred.",
                "test_protocol": "Freeze the candidate and compare memory-on with memory-off and "
                "a simple baseline on untouched periods after costs.",
            }
        return {
            "teacher_version": VERSION,
            "cases": [asdict(case) for case in cases],
            "lesson": lesson,
            "curriculum": curriculum(now),
            "scope": "Most recent same-symbol reviewed cases in this run only; no rule promotion",
        }

    def fingerprint(self) -> str:
        return digest(
            {
                "entries": {s: asdict(e) for s, e in sorted(self.entries.items())},
                "cases": [asdict(case) for case in self.cases],
                "clock": self.clock,
                "last_sequence": self.last_sequence,
                "reviewed_total": self.reviewed_total,
            }
        )
