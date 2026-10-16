"""Read-only observation and atomic publications for the live research cockpit.

No trading or model calls. A writer lock indicates an observed local replay process,
not a healthy exchange connection. Only completed journals become performance reports.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import signal
import sqlite3
import subprocess
import time
import zipfile
import zlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.cockpit.report import Run, load_archive, load_journal, render
from src.evaluation.screen import load_candles, references
from src.replay.engine import Settings

MAX_JOURNALS = 200
MAX_REPORT = 4 * 1024 * 1024


def writer_present(path: Path) -> bool:
    """Probe only an existing lock inode; never create a sidecar while observing."""
    lock = path.with_name(path.name + ".lock")
    if not lock.exists():
        return False
    with lock.open("rb") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(stream, fcntl.LOCK_UN)
    return False


def journal_status(path: Path) -> dict[str, Any]:
    """Read a bounded checkpoint and its event boundary in one SQLite snapshot."""
    if not path.is_file():
        raise FileNotFoundError(path.name)
    running = writer_present(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
    try:
        connection.execute("BEGIN")
        row = connection.execute(
            "SELECT substr(state,1,4194305),checksum,sequence FROM checkpoint WHERE id=1"
        ).fetchone()
        if row is None:
            if running:
                return {"run": path.parent.name + "/" + path.name, "state": "starting"}
            raise ValueError("Missing checkpoint")
        payload, checksum, sequence = row
        maximum = connection.execute("SELECT MAX(sequence) FROM events").fetchone()[0]
        if (not isinstance(payload, str) or len(payload.encode()) > MAX_REPORT
                or hashlib.sha256(payload.encode()).hexdigest() != checksum or sequence != maximum):
            raise ValueError("Invalid checkpoint integrity")
        state = json.loads(payload)
        if (type(state["completed"]) is not bool or type(state["next_index"]) is not int
                or state["next_index"] < 0 or not isinstance(state["positions"], dict)
                or type(state["equity"]) not in (int, float)
                or not math.isfinite(state["equity"]) or state["equity"] < 0):
            raise ValueError("Invalid checkpoint metrics")
        errors = connection.execute(
            "SELECT COUNT(*) FROM events WHERE json_extract(payload,'$.kind')='POLICY_ERROR'"
        ).fetchone()[0]
        status = ("attention" if errors else "complete") if state["completed"] else (
            "running" if running else "paused"
        )
        return {"run": path.parent.name + "/" + path.name, "state": status,
                "steps": state["next_index"], "equity": state["equity"],
                "market_time": state["performance"]["last_time"], "policy_errors": errors,
                "open_positions": len(state["positions"]), "completed": state["completed"]}
    finally:
        connection.close()


def fingerprint(path: Path) -> tuple[tuple[int, int, int], ...]:
    values = []
    for source in (path, path.with_name(path.name + "-wal")):
        if source.exists():
            stat = source.stat()
            values.append((stat.st_ino, stat.st_size, stat.st_mtime_ns))
        else:
            values.append((0, 0, 0))
    return tuple(values)


class LiveFeed:
    """Observe an explicit local source configuration; retain the last good report on errors."""

    def __init__(self, config: Path, *, output: Path | None = None) -> None:
        raw = config.read_bytes()
        self.config_hash = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if set(data) != {"roots", "archives", "references"}:
            raise ValueError("Expected roots, archives and references")
        self.roots = [Path(p).resolve() for p in data["roots"]]
        self.archives = [Path(p).resolve() for p in data["archives"]]
        self.references = data["references"]
        if not 1 <= len(self.roots) <= 10 or len(self.archives) > 10:
            raise ValueError("Source configuration exceeds bounds")
        self.cache: dict[Path, tuple[object, dict[str, Any], Run | None]] = {}
        self.seen: set[Path] = set()
        self.report_key: str | None = None
        self.report_revision: str | None = None
        self.report_updated_at: float | None = None
        self.completed_runs = 0
        if output is not None and (output / "observer-state.json").exists():
            self.restore(output)

    def restore(self, output: Path) -> None:
        """Restore only verified report metadata; never freshen its historical timestamp."""
        saved = output / "observer-state.json"
        if saved.stat().st_size > 256 * 1024:
            raise ValueError("Saved report state exceeds bounds")
        data = json.loads(saved.read_text())
        if (not isinstance(data, dict) or data.get("config_hash") != self.config_hash
                or not isinstance(data.get("seen"), list) or len(data["seen"]) > MAX_JOURNALS
                or not all(isinstance(p, str) for p in data["seen"])):
            raise ValueError("Saved report state does not match source configuration")
        revision, timestamp = data.get("revision"), data.get("updated_at")
        key = data.get("source_key")
        count = data.get("completed_runs")
        if type(count) is not int or not 0 <= count <= 1000:
            raise ValueError("Saved report count is invalid")
        if revision is not None:
            path = output / "report.html"
            if (not isinstance(revision, str) or len(revision) != 64
                    or not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool)
                    or not math.isfinite(timestamp) or timestamp < 0
                    or path.stat().st_size > MAX_REPORT
                    or hashlib.sha256(path.read_bytes()).hexdigest() != revision):
                raise ValueError("Saved report failed integrity verification")
            if (not isinstance(key, str) or len(key) != 64
                    or any(c not in "0123456789abcdef" for c in key)):
                raise ValueError("Saved report source fingerprint is invalid")
        elif timestamp is not None or count != 0:
            raise ValueError("Saved report metadata has no report")
        self.seen = {Path(p) for p in data["seen"]}
        self.report_revision = revision
        self.report_updated_at = timestamp
        self.completed_runs = count
        self.report_key = key

    def persist(self, output: Path) -> None:
        """Save private source inventory separately from sanitized public metadata."""
        atomic_write(output / "observer-state.json", json.dumps({
            "config_hash": self.config_hash, "seen": sorted(str(p) for p in self.seen),
            "revision": self.report_revision, "updated_at": self.report_updated_at,
            "completed_runs": self.completed_runs,
            "source_key": self.report_key,
        }, allow_nan=False))

    def sample(self, *, now: float | None = None) -> tuple[dict[str, Any], str | None]:
        now = time.time() if now is None else now
        if not math.isfinite(now) or now < 0:
            raise ValueError("Invalid observation time")
        errors: list[str] = []
        paths: set[Path] = set()
        for root in self.roots:
            if not root.is_dir():
                errors.append("A configured research directory is unavailable")
                continue
            for path in root.rglob("*.sqlite"):
                if not path.name.endswith(".responses.sqlite"):
                    paths.add(path.resolve())
                    if len(paths) > MAX_JOURNALS:
                        raise ValueError("Research journal limit exceeded")
        if len(self.seen | paths) > MAX_JOURNALS:
            raise ValueError("Observed journal limit exceeded")
        if self.seen - paths:
            errors.append("A previously observed journal is missing; previous report retained")
        self.seen.update(paths)
        ordered = []
        for path in paths:
            try:
                ordered.append((path.stat().st_mtime_ns, str(path), path))
            except OSError:
                errors.append("A research journal became unavailable during observation")
        paths_ordered = [item[2] for item in sorted(ordered)]
        statuses = []
        runs: list[Run] = []
        for path in paths_ordered:
            try:
                key = fingerprint(path), writer_present(path)
                cached = self.cache.get(path)
                if cached is None or cached[0] != key:
                    state = journal_status(path)
                    run = load_journal(path) if state.get("completed") else None
                    cached = key, state, run
                    self.cache[path] = cached
                statuses.append(cached[1])
                if cached[2] is not None:
                    runs.append(cached[2])
            except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error):
                errors.append(f"Cannot verify {path.parent.name}/{path.name}")
        self.cache = {p: value for p, value in self.cache.items() if p in paths}
        page = None
        report_key: list[object] = []
        try:
            report_key = [(str(p), fingerprint(p)) for p in paths_ordered
                          if p in self.cache and self.cache[p][2] is not None]
            report_key += [(str(p), fingerprint(p)) for p in self.archives]
            for item in self.references:
                report_key.append((item["candles"], fingerprint(Path(item["candles"]))))
        except OSError:
            errors.append("A result source became unavailable during observation")
        source_key = hashlib.sha256(json.dumps(report_key).encode()).hexdigest()
        if not errors and source_key != self.report_key:
            try:
                records = [r for path in self.archives for r in load_archive(path)]
                for item in self.references:
                    baseline_path = Path(item["baseline"]).resolve()
                    if baseline_path not in self.cache or self.cache[baseline_path][2] is None:
                        raise ValueError("Reference baseline unavailable")
                    base = self.cache[baseline_path][2]
                    assert base is not None
                    settings = Settings(**item["settings"])
                    source = Path(item["candles"])
                    identity = json.loads(base.comparison_key or "null")
                    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                    if (not identity or identity[0] != source_hash
                            or identity[1] != asdict(settings) or settings.lookback < 21):
                        raise ValueError("Reference data/settings differ from baseline")
                    records.extend(references(load_candles(source), base, settings))
                records.extend(runs)
                candidate = render(records)
                if len(candidate.encode()) > MAX_REPORT:
                    raise ValueError("Report exceeds publication limit")
                page = candidate
                self.report_key = source_key
                self.report_revision = hashlib.sha256(page.encode()).hexdigest()
                self.report_updated_at = now
                self.completed_runs = len(records)
            except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error,
                    zipfile.BadZipFile, zlib.error, RuntimeError):
                errors.append("Results could not be refreshed; previous report retained")
        active = [s for s in statuses if s["state"] in {"running", "starting"}]
        paused = [s for s in statuses if s["state"] == "paused"]
        agent_state = "unavailable" if errors else "running" if active else (
            "paused" if paused else "idle"
        )
        return {"version": 1, "updated_at": now, "agent_state": agent_state,
                "activity": (active + paused)[-10:], "source_errors": errors[:10],
                "completed_runs": self.completed_runs, "report_revision": self.report_revision,
                "report_updated_at": self.report_updated_at, "mode": "paper_research"}, page


def atomic_write(path: Path, payload: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class CloudPublisher:
    """Publish under the observer's advisory lock; retry transient failures with backoff."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()
        self.revision: str | None = None
        self.next_attempt = 0.0
        self.failures = 0

    def send(self, revision: str | None, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if now < self.next_attempt:
            return False
        script = Path(__file__).resolve().parents[2] / "web/cockpit/publish.mjs"
        try:
            subprocess.run(
                ["node", str(script), str(self.directory), self.revision or ""],
                check=True, capture_output=True, text=True, timeout=25,
            )
        except (OSError, subprocess.SubprocessError):
            self.failures += 1
            delay = min(300, 60 * 2 ** min(self.failures - 1, 3))
            self.next_attempt = now + delay
            print(json.dumps({"cloud": "unavailable", "retry_after_seconds": delay,
                              "message": "Last successful cloud timestamp retained"}), flush=True)
            return False
        self.revision = revision
        self.failures = 0
        self.next_attempt = now + 60
        print(json.dumps({"cloud": "published"}), flush=True)
        return True


def stop_observer(signum: int, frame: object) -> None:
    """Unwind subprocess.run and release the advisory lock on normal service shutdown."""
    raise SystemExit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--publish", action="store_true",
                        help="Upload to the configured private store; retry failures in watch mode")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lock = (args.output / "publisher.lock").open("a+b")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, stop_observer)
        feed = LiveFeed(args.config, output=args.output)
        publisher = CloudPublisher(args.output) if args.publish else None
        while True:
            snapshot, page = feed.sample()
            if page is not None:
                atomic_write(args.output / "report.html", page)
            feed.persist(args.output)
            atomic_write(args.output / "status.json", json.dumps(snapshot, allow_nan=False))
            print(json.dumps({"agent_state": snapshot["agent_state"],
                              "completed_runs": snapshot["completed_runs"],
                              "source_errors": snapshot["source_errors"]}), flush=True)
            if publisher is not None:
                sent = publisher.send(snapshot["report_revision"])
                if not sent and not args.watch:
                    raise SystemExit(1)
            if not args.watch:
                break
            time.sleep(60)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
