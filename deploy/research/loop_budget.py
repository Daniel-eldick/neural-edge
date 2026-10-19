"""Single remote monthly authority; whole-phase reservations survive runner loss."""

from __future__ import annotations

import fcntl
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from deploy.research.guard import digest, rows
from src.agents.budget import CAP_NANO_USD, Budget, BudgetError, month

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

PER_CALL = 3_000_000
LIMITS = {"review": 1, "test": 144}


def migrate(path: Path, authority: str, known_holds: set[str]) -> dict[str, Any]:
    """Seal the existing authority before remotely allocating any future allowance."""
    with closing(sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        history = [list(r) for r in db.execute("SELECT * FROM charges ORDER BY id")]
        if db.execute("SELECT name FROM sqlite_master WHERE name='remote_authority'").fetchone():
            raise BudgetError("Budget already migrated; do not create another authority")
        if any(not r[5] and r[0] not in known_holds for r in history):
            raise BudgetError("Unknown outstanding usage prevents migration")
        seed = {"authority": authority, "history": history, "sha256": digest(history)}
        db.execute(
            "CREATE TABLE remote_authority "
            "(identity TEXT PRIMARY KEY, seed_sha256 TEXT, seed_json TEXT NOT NULL)"
        )
        db.execute(
            "INSERT INTO remote_authority VALUES (?, ?, ?)",
            (authority, seed["sha256"], json.dumps(seed, sort_keys=True)),
        )
        db.execute("""CREATE TRIGGER seal_local_reservations BEFORE INSERT ON charges
                    BEGIN SELECT RAISE(ABORT, 'Use private cloud budget authority'); END""")
        return seed


def validate(state: dict[str, Any]) -> None:
    if not isinstance(state["seed"], list) or not isinstance(state["charges"], dict):
        raise BudgetError("Remote budget history unavailable")
    totals: dict[str, int] = {}
    for row in state["seed"]:
        if len(row) != 8 or type(row[4]) is not int or not 0 <= row[4] <= row[3]:
            raise BudgetError("Invalid migrated history")
        totals[row[1]] = totals.get(row[1], 0) + row[4]
    for ident, row in state["charges"].items():
        if (
            ident != row["id"]
            or row["phase"] not in LIMITS
            or row["reserved"] != LIMITS[row["phase"]] * PER_CALL
            or type(row["cost"]) is not int
            or not 0 <= row["cost"] <= row["reserved"]
            or type(row["settled"]) is not bool
            or (not row["settled"] and row["cost"] != row["reserved"])
        ):
            raise BudgetError("Invalid durable phase reservation")
        totals[row["month"]] = totals.get(row["month"], 0) + row["cost"]
    if any(total > CAP_NANO_USD for total in totals.values()):
        raise BudgetError("Remote monthly allowance exceeded")


def allocate(state: dict[str, Any], cycle: str, phase: str, now: datetime) -> str:
    validate(state)
    ident = cycle + "/" + phase
    if ident in state["charges"] or phase not in LIMITS:
        raise BudgetError("This phase was already claimed")
    period = month(now)
    amount = LIMITS[phase] * PER_CALL
    used = sum(r[4] for r in state["seed"] if r[1] == period) + sum(
        r["cost"] for r in state["charges"].values() if r["month"] == period
    )
    if used + amount > CAP_NANO_USD:
        raise BudgetError("USD3 monthly allowance exhausted; wait for a later cycle")
    state["charges"][ident] = {
        "id": ident,
        "phase": phase,
        "month": period,
        "reserved": amount,
        "cost": amount,
        "settled": False,
    }
    return ident


def settle(state: dict[str, Any], ident: str, usage: dict[str, int]) -> None:
    row = state["charges"][ident]
    for key in [
        "attempts",
        "pending_calls",
        "settled_nano_usd",
        "accounted_nano_usd",
        "input_tokens",
    ]:
        if type(usage[key]) is not int or usage[key] < 0:
            raise BudgetError("Invalid phase usage")
    if (
        row["settled"]
        or usage["pending_calls"]
        or usage["attempts"] > LIMITS[row["phase"]]
        or usage["settled_nano_usd"] != usage["accounted_nano_usd"]
        or usage["settled_nano_usd"] != usage["input_tokens"] * 42
        or usage["settled_nano_usd"] > row["reserved"]
    ):
        raise BudgetError("Unknown or inconsistent usage; retain full phase allocation")
    row.update(cost=usage["settled_nano_usd"], settled=True, usage=dict(usage))
    validate(state)


class PhaseBudget(Budget):
    """Runner copy spends only an already committed phase, in its real UTC month."""

    def __init__(
        self,
        path: Path,
        phase: str,
        period: str,
        deadline: int,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(path)
        self.phase, self.period, self.deadline = phase, period, deadline
        self.clock = clock or (lambda: datetime.now(UTC))
        self.usage()

    def usage(self) -> dict[str, int]:
        history = rows(self.path)
        if len(history) > LIMITS[self.phase] or any(
            r[1] != self.period
            or r[2] != "typesafe"
            or r[3] != PER_CALL
            or (
                r[5]
                and (
                    r[6] != "jev-1.13.0"
                    or type(r[7]) is not int
                    or not 0 <= r[7] <= 65536
                    or r[4] != r[7] * 42
                )
            )
            for r in history
        ):
            raise BudgetError("Phase budget differs from authorized allocation")
        return {
            "attempts": len(history),
            "pending_calls": sum(1 - r[5] for r in history),
            "settled_nano_usd": sum(r[4] for r in history if r[5]),
            "accounted_nano_usd": sum(r[4] for r in history),
            "input_tokens": sum(r[7] or 0 for r in history),
        }

    def reserve(self, provider: str, amount: int, *, now: datetime | None = None) -> str:
        # Serialize the attempt/pending check with insertion across all local clients.
        with self.path.with_suffix(".phase-reserve.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._reserve_phase(provider, amount, now=now)

    def _reserve_phase(self, provider: str, amount: int, *, now: datetime | None) -> str:
        actual = self.clock()
        usage = self.usage()
        # A passed timestamp never overrides the real clock. Avoid requests near midnight.
        if (
            now is None
            or month(now) != self.period
            or month(actual) != self.period
            or abs((actual - now).total_seconds()) > 5
            or actual.timestamp() >= self.deadline - 120
            or actual.day != datetime.fromtimestamp(actual.timestamp() + 120, UTC).day
            or usage["pending_calls"]
            or usage["attempts"] >= LIMITS[self.phase]
            or provider != "typesafe"
            or amount != PER_CALL
        ):
            raise BudgetError("Phase expired, uncertain, exhausted or outside its funded month")
        return super().reserve(provider, amount, now=actual)
