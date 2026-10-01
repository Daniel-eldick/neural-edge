"""Durable reservations for the user-approved USD 3 monthly AI allowance."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from pathlib import Path

CAP_NANO_USD = 3_000_000_000


class BudgetError(RuntimeError):
    """No AI request may proceed when accounting is unavailable or exhausted."""


def month(now: datetime | None) -> str:
    value = now or datetime.now(UTC)
    if value.tzinfo is None:
        raise BudgetError("Budget timestamps must include a timezone")
    return value.astimezone(UTC).strftime("%Y-%m")


class Budget:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    @staticmethod
    def initialize(path: Path) -> None:
        """Explicit one-time creation; never replace or silently reset a ledger."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("""
                CREATE TABLE charges (
                    id TEXT PRIMARY KEY,
                    month TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    reserved INTEGER NOT NULL CHECK(reserved > 0),
                    cost INTEGER NOT NULL CHECK(cost >= 0 AND cost <= reserved),
                    settled INTEGER NOT NULL CHECK(settled IN (0, 1)),
                    model TEXT,
                    input_tokens INTEGER
                )
            """)
            connection.execute("CREATE INDEX charge_month ON charges(month)")

    def _connect(self) -> sqlite3.Connection:
        try:
            return sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=5)
        except sqlite3.Error:
            raise BudgetError("AI budget ledger unavailable; no request sent") from None

    def reserve(self, provider: str, amount: int, *, now: datetime | None = None) -> str:
        if type(amount) is not int or not 0 < amount <= CAP_NANO_USD or not provider:
            raise BudgetError("Invalid budget reservation")
        period = month(now)
        call_id = uuid4().hex
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                used = connection.execute(
                    "SELECT COALESCE(SUM(cost), 0) FROM charges WHERE month = ?", (period,)
                ).fetchone()[0]
                if used + amount > CAP_NANO_USD:
                    raise BudgetError("USD 3 monthly AI allowance exhausted; no request sent")
                connection.execute(
                    "INSERT INTO charges VALUES (?, ?, ?, ?, ?, 0, NULL, NULL)",
                    (call_id, period, provider, amount, amount),
                )
        except sqlite3.Error:
            raise BudgetError("AI budget reservation failed; no request sent") from None
        return call_id

    def settle(self, call_id: str, cost: int, *, model: str, input_tokens: int) -> None:
        if type(cost) is not int or cost < 0 or type(input_tokens) is not int or input_tokens < 0:
            raise BudgetError("Invalid usage; full reservation retained")
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT reserved, settled FROM charges WHERE id = ?", (call_id,)
                ).fetchone()
                if row is None or row[1] != 0 or cost > row[0]:
                    raise BudgetError("Unsettleable usage; reservation unchanged")
                connection.execute(
                    "UPDATE charges SET cost=?, settled=1, model=?, input_tokens=? WHERE id=?",
                    (cost, model, input_tokens, call_id),
                )
        except sqlite3.Error:
            raise BudgetError("AI usage settlement failed; full reservation retained") from None

    def snapshot(self, *, now: datetime | None = None) -> dict[str, int]:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT COALESCE(SUM(cost), 0), COALESCE(SUM(1-settled), 0) "
                    "FROM charges WHERE month = ?", (month(now),),
                ).fetchone()
        except sqlite3.Error:
            raise BudgetError("AI budget ledger cannot be read") from None
        return {"used_nano_usd": int(row[0]), "pending_calls": int(row[1])}
