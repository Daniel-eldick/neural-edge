"""A bounded execution copy funded by a hold in the original shared AI ledger."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.agents.budget import Budget, BudgetError

if TYPE_CHECKING:
    from pathlib import Path

ALLOCATION = 504_000_000
ATTEMPTS = 168
PER_CALL = 3_000_000
MONTH = "2026-10"


def rows(path: Path) -> list[list[Any]]:
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        return [list(r) for r in connection.execute("SELECT * FROM charges ORDER BY id")]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def export_escrow(budget: Budget, destination: Path, *, now: datetime) -> dict[str, Any]:
    """Hold the complete maximum globally; never automatically refund an export failure."""
    if now.tzinfo is None or now.astimezone(UTC).strftime("%Y-%m") != MONTH:
        raise BudgetError("Only the frozen October allocation is authorized")
    if destination.exists():
        raise FileExistsError("Execution ledger already exists")
    before = budget.snapshot(now=now)
    if before["pending_calls"]:
        raise BudgetError("Existing uncertain usage prevents budget delegation")
    hold = budget.reserve("lesson-week-v2-cloud-escrow", ALLOCATION, now=now)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    with (
        closing(sqlite3.connect(budget.path.as_uri() + "?mode=ro", uri=True)) as source,
        closing(sqlite3.connect(destination)) as target,
        target,
    ):
        source.backup(target)
        stored = target.execute("SELECT * FROM charges WHERE id=?", (hold,)).fetchone()
        if (
            stored is None
            or stored[1:6] != (MONTH, "lesson-week-v2-cloud-escrow", ALLOCATION, ALLOCATION, 0)
            or target.execute(
                "SELECT COUNT(*) FROM charges WHERE month=? AND settled=0", (MONTH,)
            ).fetchone()[0]
            != 1
        ):
            raise BudgetError("Concurrent uncertain usage; full host hold retained")
        target.execute("DELETE FROM charges WHERE id=?", (hold,))
    return allocation_metadata(destination, hold, before)


def allocation_metadata(destination: Path, hold: str, before: dict[str, int]) -> dict[str, Any]:
    seed = rows(destination)
    return {
        "schema": 1,
        "escrow_id": hold,
        "allocation_nano_usd": ALLOCATION,
        "month": MONTH,
        "seed_ids": [r[0] for r in seed],
        "seed_sha256": digest(seed),
        "host_budget_before": before,
        "host_hold_nano_usd": ALLOCATION,
        "scope": "Execution copy funded by host escrow; not the live global ledger",
    }


def resume_export(budget: Budget, destination: Path, *, now: datetime) -> dict[str, Any]:
    """Recover an unsealed preparation only; retain the existing hold without a new allocation."""
    if now.tzinfo is None or now.astimezone(UTC).strftime("%Y-%m") != MONTH:
        raise BudgetError("Only the original October preparation may recover")
    if (
        not destination.is_file()
        or any(p.is_symlink() for p in [destination, *destination.parents])
        or destination.samefile(budget.path)
    ):
        raise BudgetError("Execution copy must be a separate regular file, without aliases")
    copied = rows(destination)
    candidates = [
        r
        for r in copied
        if r[1:6] == [MONTH, "lesson-week-v2-cloud-escrow", ALLOCATION, ALLOCATION, 0]
    ]
    current = budget.snapshot(now=now)
    if len(candidates) != 1 or copied != rows(budget.path) or current["pending_calls"] != 1:
        raise BudgetError("Preparation copy or original hold differs; no recovery")
    hold = candidates[0][0]
    with closing(sqlite3.connect(destination)) as connection, connection:
        connection.execute("DELETE FROM charges WHERE id=?", (hold,))
    before = {"used_nano_usd": current["used_nano_usd"] - ALLOCATION, "pending_calls": 0}
    return allocation_metadata(destination, hold, before)


class FundedBudget(Budget):
    """Original guard plus an independent lifetime reservation ceiling for this one job."""

    def __init__(self, path: Path, metadata: dict[str, Any]) -> None:
        super().__init__(path)
        if (
            metadata["schema"] != 1
            or metadata["allocation_nano_usd"] != ALLOCATION
            or metadata["month"] != MONTH
        ):
            raise BudgetError("Invalid delegated allowance")
        self.metadata = metadata
        self.validate()

    def validate(self) -> list[list[Any]]:
        all_rows = rows(self.path)
        ids = self.metadata["seed_ids"]
        seed = [r for r in all_rows if r[0] in ids]
        new = [r for r in all_rows if r[0] not in ids]
        if (
            digest(seed) != self.metadata["seed_sha256"]
            or len(new) > ATTEMPTS
            or sum(r[3] for r in new) > ALLOCATION
            or any(r[1] != MONTH or r[2] != "typesafe" or r[3] != PER_CALL for r in new)
        ):
            raise BudgetError("Execution ledger seed or allocation differs")
        return new

    def reserve(self, provider: str, amount: int, *, now: datetime | None = None) -> str:
        moment = now or datetime.now(UTC)
        if (
            moment.tzinfo is None
            or moment.astimezone(UTC).strftime("%Y-%m") != MONTH
            or provider != "typesafe"
            or amount != PER_CALL
        ):
            raise BudgetError("Delegated requests must use the frozen October provider/cap")
        with self.path.with_suffix(".fund.lock").open("a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            new = self.validate()
            if (
                len(new) >= ATTEMPTS
                or sum(r[3] for r in new) + amount > ALLOCATION
                or any(r[5] == 0 for r in new)
            ):
                raise BudgetError("Delegated reservations exhausted or uncertain")
            return super().reserve(provider, amount, now=moment)

    def snapshot(self, *, now: datetime | None = None) -> dict[str, int]:
        self.validate()
        return super().snapshot(now=now)

    def usage(self) -> dict[str, int]:
        new = self.validate()
        return {
            "attempts": len(new),
            "accounted_nano_usd": sum(r[4] for r in new),
            "pending_calls": sum(1 - r[5] for r in new),
            "input_tokens": sum(r[7] or 0 for r in new),
        }


def reconcile(budget: Budget, metadata: dict[str, Any], usage: dict[str, int]) -> str:
    """Called only after authenticating a terminal result and its execution ledger."""
    if usage["pending_calls"]:
        raise BudgetError("Uncertain provider usage retains the complete original escrow")
    if not 0 <= usage["accounted_nano_usd"] <= ALLOCATION or not 0 <= usage["attempts"] <= ATTEMPTS:
        raise BudgetError("Result exceeds the allocated envelope")
    found = [r for r in rows(budget.path) if r[0] == metadata["escrow_id"]]
    if len(found) != 1 or found[0][1:4] != [MONTH, "lesson-week-v2-cloud-escrow", ALLOCATION]:
        raise BudgetError("Original host escrow is unavailable")
    row = found[0]
    if row[5] == 1:
        if row[4] != usage["accounted_nano_usd"] or row[7] != usage["input_tokens"]:
            raise BudgetError("Already reconciled escrow differs")
        return "already_reconciled"
    budget.settle(
        metadata["escrow_id"],
        usage["accounted_nano_usd"],
        model="delegated-jev-1.13.0",
        input_tokens=usage["input_tokens"],
    )
    return "reconciled"
