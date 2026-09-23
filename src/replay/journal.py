"""Exclusive per-run SQLite journal: failures never silently overwrite an experiment."""

from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Journal:
    def __init__(self, path: Path) -> None:
        # Atomic exclusive creation avoids accidentally mixing runs or overwriting evidence.
        with path.open("x"):
            pass
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE events (sequence INTEGER PRIMARY KEY, payload TEXT)")
        self.connection.commit()

    def record(self, event: dict[str, object]) -> None:
        payload = json.dumps(event, sort_keys=True, allow_nan=False)
        with self.connection:
            self.connection.execute("INSERT INTO events(payload) VALUES (?)", (payload,))

    def close(self) -> None:
        self.connection.close()
