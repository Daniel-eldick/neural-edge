"""Durable at-most-once model attempts, independent of replay candle transactions."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from src.agents.budget import BudgetError
from src.agents.jev import MODEL, Choice, JevError, parse_response

if TYPE_CHECKING:
    from pathlib import Path


class Chooser(Protocol):
    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice: ...


class ResponseError(RuntimeError):
    """Safe-to-display failure; the corresponding model decision must be vetoed."""


class ResponseStore:
    def __init__(self, path: Path, *, resume: bool = False) -> None:
        try:
            if not resume:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            self.connection = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True)
            self.connection.execute("PRAGMA synchronous=FULL")
            if not resume:
                with self.connection:
                    self.connection.execute("CREATE TABLE identity (id TEXT PRIMARY KEY)")
                    self.connection.execute("INSERT INTO identity VALUES (?)", (uuid4().hex,))
                    self.connection.execute("""
                        CREATE TABLE attempts (
                            key TEXT PRIMARY KEY, request TEXT NOT NULL,
                            status TEXT NOT NULL CHECK(status IN ('pending','done','failed')),
                            response TEXT, checksum TEXT, error TEXT
                        )
                    """)
            if self.connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ResponseError("Model response store is corrupt")
            rows = self.connection.execute("SELECT id FROM identity").fetchall()
            if len(rows) != 1 or not isinstance(rows[0][0], str) or len(rows[0][0]) != 32:
                raise ResponseError("Model response store identity is invalid")
            self.identity = rows[0][0]
        except (OSError, sqlite3.Error, ResponseError):
            if hasattr(self, "connection"):
                self.connection.close()
            raise ResponseError("Model response store unavailable; no request sent") from None

    def choose(self, key: str, state: str, instructions: str, options: dict[str, str],
               client: Chooser, max_attempts: int) -> Choice:
        if type(max_attempts) is not int or not 1 <= max_attempts <= 100:
            raise ResponseError("Model attempt limit must be between 1 and 100")
        request = json.dumps({"model": MODEL, "state": state, "instructions": instructions,
                              "options": options}, sort_keys=True, allow_nan=False)
        try:
            with self.connection:
                self.connection.execute("BEGIN IMMEDIATE")
                row = self.connection.execute(
                    "SELECT request,status,response,checksum,error FROM attempts WHERE key=?",
                    (key,),
                ).fetchone()
                if row is not None:
                    if row[0] != request:
                        raise ResponseError("Saved model request differs; no retry permitted")
                    if row[1] == "pending":
                        raise ResponseError("Previous model attempt uncertain; no retry permitted")
                    if row[1] == "failed":
                        raise ResponseError(row[4])
                    if (row[1] != "done" or not isinstance(row[2], str)
                            or hashlib.sha256(row[2].encode()).hexdigest() != row[3]):
                        raise ResponseError("Saved model response is corrupt")
                    try:
                        return parse_response(json.loads(row[2]), options)
                    except (ValueError, JevError):
                        raise ResponseError("Saved model response is corrupt") from None
                # A failed or uncertain request disables new model work for this run.
                # Keep cached successes readable for replay recovery; claim inspection
                # and insertion share the transaction so a second caller cannot race it.
                if self.connection.execute(
                    "SELECT 1 FROM attempts WHERE status != 'done' LIMIT 1"
                ).fetchone() is not None:
                    raise ResponseError(
                        "Previous model attempt failed or uncertain; "
                        "new requests blocked for this run"
                    )
                used = self.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
                if used >= max_attempts:
                    raise ResponseError("Run model-attempt limit reached; new candidates vetoed")
                self.connection.execute(
                    "INSERT INTO attempts(key,request,status) VALUES (?,?,'pending')",
                    (key, request),
                )
            # The pending row is durable before invoking any external side effect.
            try:
                result = client.choose(state, instructions, options)
                data = {"model": result.model, "usage": {"input_tokens": result.input_tokens},
                        "answers": {"decision": {"type": "choice", "choice": result.choice,
                                                 "confidence": result.confidence,
                                                 "probabilities": result.probabilities}}}
                validated = parse_response(data, options)
                if validated.cost_nano_usd != result.cost_nano_usd:
                    raise JevError("Model response cost does not match validated usage")
                payload = json.dumps(data, sort_keys=True, allow_nan=False)
            except Exception as exc:
                message = str(exc) if isinstance(exc, (JevError, BudgetError)) else (
                    "Model request failed unexpectedly; no retry permitted"
                )
                with self.connection:
                    self.connection.execute(
                        "UPDATE attempts SET status='failed',error=? WHERE key=?", (message, key),
                    )
                raise ResponseError(message) from None
            with self.connection:
                self.connection.execute(
                    "UPDATE attempts SET status='done',response=?,checksum=? WHERE key=?",
                    (payload, hashlib.sha256(payload.encode()).hexdigest(), key),
                )
            return validated
        except sqlite3.Error:
            raise ResponseError("Model response persistence failed; no automatic retry") from None

    def close(self) -> None:
        self.connection.close()
