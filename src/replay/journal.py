"""Single-writer SQLite journal with atomic candle events and recovery checkpoints."""

from __future__ import annotations

import fcntl
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class Journal:
    def __init__(self, path: Path, *, resume: bool = False) -> None:
        self.resuming = resume
        if resume:
            with path.open("rb"):
                pass
        # A separate persistent inode avoids interfering with SQLite's own file locks.
        self._file = path.with_name(path.name + ".lock").open("a+b")
        self._in_batch = False
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._file.close()
            raise RuntimeError("Another replay writer already owns this journal") from None
        try:
            if not resume:
                with path.open("xb"):
                    pass
            self.connection = sqlite3.connect(path)
            self.connection.execute("PRAGMA synchronous=FULL")
            if not resume:
                self.connection.execute(
                    "CREATE TABLE events (sequence INTEGER PRIMARY KEY, payload TEXT)"
                )
                self.connection.execute("""
                    CREATE TABLE checkpoint (
                        id INTEGER PRIMARY KEY CHECK(id=1),
                        state TEXT NOT NULL, checksum TEXT NOT NULL, sequence INTEGER NOT NULL
                    )
                """)
                self.connection.commit()
            elif self.connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Journal integrity check failed")
        except BaseException:
            if hasattr(self, "connection"):
                self.connection.close()
            self._file.close()
            raise

    @contextmanager
    def batch(self) -> Iterator[None]:
        if self._in_batch:
            raise RuntimeError("Nested journal batches are not supported")
        self.connection.execute("BEGIN IMMEDIATE")
        self._in_batch = True
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise
        finally:
            self._in_batch = False

    def record(self, event: dict[str, object]) -> None:
        payload = json.dumps(event, sort_keys=True, allow_nan=False)
        if self._in_batch:
            self.connection.execute("INSERT INTO events(payload) VALUES (?)", (payload,))
        else:
            with self.connection:
                self.connection.execute("INSERT INTO events(payload) VALUES (?)", (payload,))

    def save_checkpoint(self, state: dict[str, Any]) -> None:
        if not self._in_batch:
            raise RuntimeError("Checkpoint must commit with its candle events")
        payload = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        sequence = self.connection.execute(
            "SELECT COALESCE(MAX(sequence),0) FROM events"
        ).fetchone()[0]
        self.connection.execute(
            "INSERT INTO checkpoint VALUES (1, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "state=excluded.state, checksum=excluded.checksum, sequence=excluded.sequence",
            (payload, digest, sequence),
        )

    def load_checkpoint(self) -> dict[str, Any]:
        try:
            row = self.connection.execute(
                "SELECT state, checksum, sequence FROM checkpoint WHERE id=1"
            ).fetchone()
        except sqlite3.Error:
            raise ValueError("Journal has no supported recovery checkpoint") from None
        if row is None or hashlib.sha256(row[0].encode()).hexdigest() != row[1]:
            raise ValueError("Missing or corrupted checkpoint checksum")
        sequence = self.connection.execute(
            "SELECT COALESCE(MAX(sequence),0) FROM events"
        ).fetchone()[0]
        if row[2] != sequence:
            raise ValueError("Journal events are inconsistent with the checkpoint")
        result = json.loads(row[0])
        if not isinstance(result, dict):
            raise ValueError("Checkpoint must be an object")
        return result

    def close(self) -> None:
        try:
            self.connection.close()
        finally:
            self._file.close()
