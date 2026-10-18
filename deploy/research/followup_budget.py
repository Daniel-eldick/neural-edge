"""One fresh replay comparison funded by a separate hold in the original monthly guard."""

from __future__ import annotations

import fcntl
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from deploy.research.guard import digest, rows
from src.agents.budget import Budget, BudgetError

if TYPE_CHECKING:
    from pathlib import Path

CAP = 432_000_000
PER_CALL = 3_000_000
ATTEMPTS = 144
MONTH = "2026-10"
PROVIDER = "lesson-fresh-v1-escrow"


def export(budget: Budget, target: Path, known_holds: set[str], *, now: datetime) -> dict[str, Any]:
    if now.tzinfo is None or now.astimezone(UTC).strftime("%Y-%m") != MONTH:
        raise BudgetError("Fresh funding is restricted to October")
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents]):
        raise BudgetError("Fresh copy must be a new regular path")
    with budget.path.with_suffix(".fresh-export.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        history = rows(budget.path)
        pending = [r for r in history if r[1] == MONTH and not r[5]]
        if any(r[2] == PROVIDER for r in history) or any(
            r[0] not in known_holds
            or r[2:6]
            not in [
                ["lesson-week-v2-cloud-escrow", 504_000_000, 504_000_000, 0],
                ["lesson-week-v2-learning-escrow", 3_000_000, 3_000_000, 0],
            ]
            for r in pending
        ):
            raise BudgetError("Duplicate fresh funding or unknown pending usage")
        hold = budget.reserve(PROVIDER, CAP, now=now)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open("xb"):
            target.chmod(0o600)
        with (
            closing(sqlite3.connect(budget.path.as_uri() + "?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(target)) as copy,
            copy,
        ):
            source.backup(copy)
            current = [list(r) for r in copy.execute("SELECT * FROM charges ORDER BY id")]
            own = [r for r in current if r[0] == hold]
            uncertain = [r[0] for r in current if r[1] == MONTH and not r[5]]
            if own != [[hold, MONTH, PROVIDER, CAP, CAP, 0, None, None]] or set(uncertain) - (
                known_holds | {hold}
            ):
                raise BudgetError("Concurrent uncertain usage; fresh hold retained")
            copy.execute("DELETE FROM charges WHERE id=?", (hold,))
        seed = rows(target)
        return {
            "schema": 1,
            "kind": "lesson-fresh-v1",
            "month": MONTH,
            "escrow_id": hold,
            "cap_nano_usd": CAP,
            "seed_ids": [r[0] for r in seed],
            "seed_sha256": digest(seed),
            "host_budget_before": {
                "used_nano_usd": sum(r[4] for r in seed if r[1] == MONTH),
                "pending_calls": sum(1 - r[5] for r in seed if r[1] == MONTH),
            },
        }


class FollowupBudget(Budget):
    def __init__(self, path: Path, metadata: dict[str, Any]) -> None:
        super().__init__(path)
        if (
            metadata["schema"] != 1
            or metadata["kind"] != "lesson-fresh-v1"
            or metadata["month"] != MONTH
            or metadata["cap_nano_usd"] != CAP
        ):
            raise BudgetError("Invalid fresh allocation")
        self.metadata = metadata
        self.validate()

    def validate(self) -> list[list[Any]]:
        history = rows(self.path)
        seed = [r for r in history if r[0] in self.metadata["seed_ids"]]
        new = [r for r in history if r[0] not in self.metadata["seed_ids"]]
        if (
            digest(seed) != self.metadata["seed_sha256"]
            or len(new) > ATTEMPTS
            or any(r[1] != MONTH or r[2] != "typesafe" or r[3] != PER_CALL for r in new)
        ):
            raise BudgetError("Fresh history or 144-call cap differs")
        return new

    def reserve(self, provider: str, amount: int, *, now: datetime | None = None) -> str:
        moment = now or datetime.now(UTC)
        if (
            moment.tzinfo is None
            or moment.astimezone(UTC).strftime("%Y-%m") != MONTH
            or provider != "typesafe"
            or amount != PER_CALL
        ):
            raise BudgetError("Fresh request outside its frozen allowance")
        with self.path.with_suffix(".fresh.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if len(self.validate()) >= ATTEMPTS or any(not r[5] for r in self.validate()):
                raise BudgetError("Fresh attempt cap exhausted or usage uncertain")
            return super().reserve(provider, amount, now=moment)

    def usage(self) -> dict[str, int]:
        new = self.validate()
        return {
            "attempts": len(new),
            "accounted_nano_usd": sum(r[4] for r in new),
            "pending_calls": sum(1 - r[5] for r in new),
            "settled_nano_usd": sum(r[4] for r in new if r[5]),
            "input_tokens": sum(r[7] or 0 for r in new),
        }


def reconcile(budget: Budget, metadata: dict[str, Any], usage: dict[str, int]) -> str:
    if (
        usage["pending_calls"]
        or not 0 <= usage["accounted_nano_usd"] <= CAP
        or usage["settled_nano_usd"] != usage["accounted_nano_usd"]
        or not 0 <= usage["attempts"] <= ATTEMPTS
    ):
        raise BudgetError("Uncertain fresh usage retains its full original hold")
    found = [r for r in rows(budget.path) if r[0] == metadata["escrow_id"]]
    if len(found) != 1 or found[0][1:4] != [MONTH, PROVIDER, CAP]:
        raise BudgetError("Original fresh hold differs")
    row = found[0]
    if row[5]:
        if row[4] != usage["accounted_nano_usd"] or row[7] != usage["input_tokens"]:
            raise BudgetError("Previously reconciled fresh usage differs")
        return "already_reconciled"
    budget.settle(
        metadata["escrow_id"],
        usage["accounted_nano_usd"],
        model="delegated-jev-fresh-1.13.0",
        input_tokens=usage["input_tokens"],
    )
    return "reconciled"
