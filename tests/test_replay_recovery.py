"""Crash recovery must match uninterrupted accounting, decisions and risk state."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from src.replay.engine import Candle, Decision, Observation, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


class StatefulPolicy:
    checkpoint_id = "stateful-test-v1"

    def __init__(self) -> None:
        self.calls = 0

    def decide(self, observation: Observation) -> Decision:
        self.calls += 1
        if self.calls == 1:
            return Decision("ENTER_LONG", 90, 120, "First observation only")
        return Decision(reason=f"Observation {self.calls}")

    def save_state(self) -> dict[str, object]:
        return {"calls": self.calls}

    def restore_state(self, state: dict[str, object]) -> None:
        calls = state["calls"]
        if type(calls) is not int or calls < 0:
            raise ValueError("Invalid policy state")
        self.calls = calls


def candles() -> list[Candle]:
    return [Candle("BTC", t, price, price, price, price, 1)
            for t, price in [(0, 100), (300, 101), (600, 95), (900, 89), (1200, 100)]]


def events(path: Path) -> list[dict[str, object]]:
    with sqlite3.connect(path) as connection:
        return [json.loads(row[0]) for row in connection.execute(
            "SELECT payload FROM events ORDER BY sequence"
        )]


@pytest.mark.parametrize("pause_after", [1, 2, 4])
def test_resume_preserves_pending_positions_policy_and_exact_events(
    tmp_path: Path, pause_after: int,
) -> None:
    full, partial = tmp_path / "full.sqlite", tmp_path / "partial.sqlite"
    settings = Settings()
    journal = Journal(full)
    expected = Replay(settings, journal).run(candles(), StatefulPolicy())
    journal.close()
    journal = Journal(partial)
    paused = Replay(settings, journal).run(candles(), StatefulPolicy(), stop_after=pause_after)
    journal.close()
    assert not paused.completed
    assert not any(e["kind"] == "RESULT" for e in events(partial))
    journal = Journal(partial, resume=True)
    resumed_policy = StatefulPolicy()
    actual = Replay(settings, journal).run(candles(), resumed_policy, resume=True)
    journal.close()
    assert actual == expected
    assert resumed_policy.calls == len(candles())
    assert events(full) == events(partial)
    journal = Journal(partial, resume=True)
    try:
        with pytest.raises(ValueError, match="completed"):
            Replay(settings, journal).run(candles(), StatefulPolicy(), resume=True)
    finally:
        journal.close()


def test_atomic_rollback_retains_last_committed_state(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    Replay(Settings(), journal).run(candles(), StatefulPolicy(), stop_after=1)
    state = journal.load_checkpoint()
    before = events(path)
    with pytest.raises(RuntimeError, match="crash"), journal.batch():
        journal.record({"kind": "ENTER", "time": 300})
        journal.save_checkpoint({"bad": True})
        raise RuntimeError("Injected crash before commit")
    assert journal.load_checkpoint() == state
    assert events(path) == before
    journal.close()


@pytest.mark.parametrize("changed", ["data", "settings", "policy", "checksum"])
def test_resume_rejects_mismatch_before_decisions(tmp_path: Path, changed: str) -> None:
    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    Replay(Settings(), journal).run(candles(), StatefulPolicy(), stop_after=1)
    journal.close()
    data, settings, policy = candles(), Settings(), StatefulPolicy()
    if changed == "data":
        data[-1] = Candle("BTC", 1200, 110, 110, 110, 110, 1)
    elif changed == "settings":
        settings = Settings(fee=0)
    elif changed == "policy":
        policy.checkpoint_id = "different-version"
    else:
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE checkpoint SET checksum='corrupted'")
    journal = Journal(path, resume=True)
    try:
        with pytest.raises(ValueError):
            Replay(settings, journal).run(data, policy, resume=True)
        assert policy.calls == 0
    finally:
        journal.close()


def test_journal_has_one_writer_and_missing_resume_never_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    with pytest.raises(FileNotFoundError):
        Journal(path, resume=True)
    assert not path.exists()
    journal = Journal(path)
    try:
        with pytest.raises(RuntimeError, match="writer"):
            Journal(path, resume=True)
    finally:
        journal.close()


def test_crash_during_fill_restarts_without_duplicate_execution(tmp_path: Path) -> None:
    class CrashJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            super().record(event)
            if event["kind"] == "ENTER":
                raise SystemExit("Injected process interruption")

    path = tmp_path / "crash.sqlite"
    journal: Journal = CrashJournal(path)
    try:
        with pytest.raises(SystemExit):
            Replay(Settings(), journal).run(candles(), StatefulPolicy())
    finally:
        journal.close()
    assert not any(e["kind"] == "ENTER" for e in events(path))
    journal = Journal(path, resume=True)
    try:
        result = Replay(Settings(), journal).run(candles(), StatefulPolicy(), resume=True)
    finally:
        journal.close()
    assert result.closed_trades == 1
    assert sum(e["kind"] == "ENTER" for e in events(path)) == 1


class PortfolioPolicy(StatefulPolicy):
    def decide(self, observation: Observation) -> Decision:
        self.calls += 1
        price = observation.candles[-1].close
        return Decision("ENTER_LONG", price * 0.9, price * 1.2, "Risk recovery test")


class ReverseEntryPolicy(StatefulPolicy):
    def decide(self, observation: Observation) -> Decision:
        if observation.now == 300 and observation.candles[-1].symbol == "Z":
            return Decision("ENTER_LONG", 90, 120, "Enter Z first")
        if observation.now == 600 and observation.candles[-1].symbol == "A":
            return Decision("ENTER_LONG", 90, 120, "Enter A later")
        return Decision()


def test_restored_portfolio_order_does_not_change_events(tmp_path: Path) -> None:
    data = [Candle(s, t, price, price, price, price, 1)
            for t, price in ((0, 100), (300, 100), (600, 100), (900, 89))
            for s in ("Z", "A")]
    full, partial = tmp_path / "full.sqlite", tmp_path / "partial.sqlite"
    journal = Journal(full)
    expected = Replay(Settings(), journal).run(data, ReverseEntryPolicy())
    journal.close()
    journal = Journal(partial)
    Replay(Settings(), journal).run(data, ReverseEntryPolicy(), stop_after=3)
    journal.close()
    journal = Journal(partial, resume=True)
    try:
        actual = Replay(Settings(), journal).run(data, ReverseEntryPolicy(), resume=True)
    finally:
        journal.close()
    assert actual == expected
    assert events(full) == events(partial)


def test_restart_preserves_halt_and_peak_after_correlated_gap(tmp_path: Path) -> None:
    data = [Candle(str(s), t, price, price, price, price, 1)
            for t, price in ((0, 100), (300, 100), (600, 50), (900, 100)) for s in range(5)]
    path = tmp_path / "halt.sqlite"
    journal = Journal(path)
    paused = Replay(Settings(fee=0, slippage=0), journal).run(
        data, PortfolioPolicy(), stop_after=3,
    )
    journal.close()
    assert paused.halted
    journal = Journal(path, resume=True)
    engine = Replay(Settings(fee=0, slippage=0), journal)
    try:
        result = engine.run(data, PortfolioPolicy(), resume=True)
    finally:
        journal.close()
    assert result.halted and result.ending_equity == 875
    assert engine.peak == 1000
    assert result.max_drawdown == 0.125
    assert sum(e["kind"] == "ENTER" for e in events(path)) == 5


def test_daily_accumulator_survives_replay_restart(tmp_path: Path) -> None:
    data = [Candle("BTC", t, 100, 100, 100, 100, 1) for t in range(0, 3 * 86400, 300)]
    full_path, paused_path = tmp_path / "full.sqlite", tmp_path / "paused.sqlite"
    journal = Journal(full_path)
    expected = Replay(Settings(), journal).run(data, StatefulPolicy())
    journal.close()
    journal = Journal(paused_path)
    Replay(Settings(), journal).run(data, StatefulPolicy(), stop_after=400)
    journal.close()
    journal = Journal(paused_path, resume=True)
    try:
        actual = Replay(Settings(), journal).run(data, StatefulPolicy(), resume=True)
    finally:
        journal.close()
    assert actual == expected
    assert actual.complete_days == 3
    assert events(full_path) == events(paused_path)


def test_cli_pause_and_fresh_process_resume_match_full_run(tmp_path: Path) -> None:
    source = tmp_path / "candles.csv"
    source.write_text("symbol,opened_at,open,high,low,close,volume\n" + "\n".join(
        f"BTC,{t},100,100,100,100,1" for t in range(0, 7200, 300)
    ))
    full, paused = tmp_path / "full.sqlite", tmp_path / "paused.sqlite"
    command = [sys.executable, "-m", "src.replay", "--csv", str(source), "--journal"]
    first = subprocess.run(command + [str(paused), "--stop-after", "10"],
                           capture_output=True, text=True, check=True)
    assert not json.loads(first.stdout)["completed"]
    resumed = subprocess.run(command + [str(paused), "--resume"],
                             capture_output=True, text=True, check=True)
    expected = subprocess.run(command + [str(full)], capture_output=True, text=True, check=True)
    assert json.loads(resumed.stdout) == json.loads(expected.stdout)
    assert events(paused) == events(full)
    before = events(paused)
    rejected = subprocess.run(command + [str(paused), "--resume"],
                              capture_output=True, text=True, check=False)
    assert rejected.returncode != 0
    assert "completed" in rejected.stderr
    assert events(paused) == before
