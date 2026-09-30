"""A recorded model preference cannot bypass causal observations or risk enforcement."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import responses

from src.agents.budget import Budget
from src.agents.jev import ENDPOINT, MODEL, Choice, JevError
from src.agents.learning import LearningPolicy
from src.agents.policy import JevPolicy
from src.agents.responses import ResponseStore
from src.cockpit.report import load_journal, render
from src.replay import __main__ as cli
from src.replay.engine import Candle, Observation, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


class Provider:
    def __init__(self, choice: str = "enter") -> None:
        self.states: list[dict[str, object]] = []
        self.choice = choice

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        self.states.append(json.loads(state))
        return Choice(self.choice, 0.8, {"enter": 0.8, "wait": 0.2}, MODEL, 100, 4200)


def candles() -> list[Candle]:
    return [Candle("BTC", i * 300, p, p, p, p, 1)
            for i, p in enumerate([100] * 20 + [101, 102, 90])]


def events(path: Path) -> list[dict[str, object]]:
    with sqlite3.connect(path) as connection:
        return [json.loads(row[0]) for row in connection.execute(
            "SELECT payload FROM events ORDER BY sequence"
        )]


@pytest.mark.parametrize("choice,entries", [("enter", 1), ("wait", 0)])
def test_model_mapping_causal_state_and_protective_exit(
    tmp_path: Path, choice: str, entries: int,
) -> None:
    journal = Journal(tmp_path / "run.sqlite")
    store = ResponseStore(tmp_path / "responses.sqlite")
    provider = Provider(choice)
    try:
        result = Replay(Settings(), journal).run(candles(), JevPolicy(provider, store, journal))
        assert result.closed_trades == entries
        state = provider.states[0]
        assert "memory" not in state
        assert state["now"] == 6300
        bars = state["candles"]
        assert isinstance(bars, list)
        assert len(bars) == 21
        assert bars[-1]["close"] == 101 and bars[-1]["opened_at"] == 6000
        assert all(bar["close"] >= 100 and bar["opened_at"] <= 6000 for bar in bars)
    finally:
        journal.close()
        store.close()
    rows = events(tmp_path / "run.sqlite")
    fills = [e for e in rows if e["kind"] == "ENTER"]
    assert len(fills) == entries
    if entries:
        assert fills[0]["time"] == 6300
        assert float(str(fills[0]["planned_risk"])) <= 5
        assert any(e["kind"] == "EXIT" and e["reason"] == "gap_or_max_age" for e in rows)
    loaded = load_journal(tmp_path / "run.sqlite")
    assert loaded.inference_cost_usd == 0.0000042 * len(provider.states)
    assert loaded.model_choices == len(provider.states)
    page = render([loaded])
    assert MODEL in page and "0.000004200" in page


def test_no_candidate_or_halt_never_calls_provider(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "run.sqlite")
    store = ResponseStore(tmp_path / "responses.sqlite")
    provider = Provider()
    policy = JevPolicy(provider, store, journal)
    try:
        for bars, halted in [(candles()[:10], False), (candles()[:20], False),
                             (candles()[:21], True)]:
            assert policy.decide(Observation(bars[-1].opened_at + 300, tuple(bars), (),
                                             1000, halted)).action == "WAIT"
        assert not provider.states
    finally:
        journal.close()
        store.close()


def test_saved_model_call_survives_candle_rollback(tmp_path: Path) -> None:
    class CrashJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            super().record(event)
            if event["kind"] == "MODEL_CHOICE":
                raise SystemExit("crash after saved response")

    path, responses = tmp_path / "run.sqlite", tmp_path / "responses.sqlite"
    provider = Provider()
    journal: Journal = CrashJournal(path)
    store = ResponseStore(responses)
    try:
        with pytest.raises(SystemExit):
            Replay(Settings(), journal).run(candles(), JevPolicy(provider, store, journal))
    finally:
        journal.close()
        store.close()
    assert len(provider.states) == 1
    assert not any(e["kind"] == "MODEL_CHOICE" for e in events(path))
    journal = Journal(path, resume=True)
    store = ResponseStore(responses, resume=True)
    try:
        result = Replay(Settings(), journal).run(candles(), JevPolicy(provider, store, journal),
                                                resume=True)
    finally:
        journal.close()
        store.close()
    assert len(provider.states) == 1
    assert result.closed_trades == 1
    assert sum(e["kind"] == "MODEL_CHOICE" for e in events(path)) == 1


def test_replaced_store_rejected_before_model_calls(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    store = ResponseStore(tmp_path / "original.sqlite")
    provider = Provider()
    Replay(Settings(), journal).run(candles(), JevPolicy(provider, store, journal), stop_after=20)
    journal.close()
    store.close()
    store = ResponseStore(tmp_path / "replacement.sqlite")
    journal = Journal(path, resume=True)
    try:
        with pytest.raises(ValueError, match="response store"):
            Replay(Settings(), journal).run(candles(), JevPolicy(provider, store, journal),
                                            resume=True)
        assert not provider.states
    finally:
        journal.close()
        store.close()


@pytest.mark.parametrize("mode", ["jev", "jev-memory"])
@responses.activate
def test_cli_paid_filter_pause_resume_reuses_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    mode: str,
) -> None:
    budget_path = tmp_path / "budget.sqlite"
    Budget.initialize(budget_path)
    monkeypatch.setattr(cli, "LEDGER", budget_path)
    monkeypatch.setenv("TYPESAFE_API_KEY", "PRIVATE-TEST-KEY")
    # Pin the test clock without changing production's expiry guard.
    from src.agents.jev import JevClient
    monkeypatch.setattr(cli, "JevClient", lambda key, budget: JevClient(
        key, budget, clock=lambda: datetime(2026, 9, 30, tzinfo=UTC),
    ))
    source = tmp_path / "candles.csv"
    source.write_text("symbol,opened_at,open,high,low,close,volume\n" + "\n".join(
        f"{c.symbol},{c.opened_at},{c.open},{c.high},{c.low},{c.close},{c.volume}"
        for c in candles()
    ))
    path = tmp_path / "run.sqlite"
    command = ["replay", "--csv", str(source), "--journal", str(path), "--policy", mode,
               "--max-model-calls", "1"]
    responses.post(ENDPOINT, json={
        "model": MODEL, "usage": {"input_tokens": 100},
        "answers": {"decision": {"type": "choice", "choice": "enter", "confidence": 0.8,
                                  "probabilities": {"enter": 0.8, "wait": 0.2}}},
    })
    monkeypatch.setattr(sys, "argv", command + ["--stop-after", "21"])
    cli.main()
    assert not json.loads(capsys.readouterr().out)["completed"]
    monkeypatch.setattr(sys, "argv", command + ["--resume"])
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["completed"] and result["closed_trades"] == 1
    assert len(responses.calls) == 1
    assert "PRIVATE-TEST-KEY" not in path.read_bytes().decode(errors="ignore")
    assert "PRIVATE-TEST-KEY" not in path.with_name(path.name + ".responses.sqlite").read_bytes(
    ).decode(errors="ignore")


@pytest.mark.parametrize("learning", [False, True])
def test_provider_failure_vetoes_candidate_but_does_not_disable_stops(
    tmp_path: Path, learning: bool,
) -> None:
    class FailingProvider(Provider):
        def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
            if self.states:
                raise JevError("Provider unavailable; reservation retained")
            return super().choose(state, instructions, options)

    data = candles() + [Candle("ETH", c.opened_at, 100, 100, 100, 100, 1)
                        for c in candles()[:21]] + [
                            Candle("ETH", 6300, 101, 101, 101, 101, 1),
                            Candle("ETH", 6600, 101, 101, 101, 101, 1),
                        ]
    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    store = ResponseStore(tmp_path / "responses.sqlite")
    try:
        policy = (LearningPolicy(FailingProvider(), store, journal, interval=300) if learning
                  else JevPolicy(FailingProvider(), store, journal))
        result = Replay(Settings(), journal).run(data, policy)
    finally:
        journal.close()
        store.close()
    assert result.closed_trades == 1 and result.open_positions == 0
    assert any(e["kind"] == "POLICY_ERROR" and e["symbol"] == "ETH" for e in events(path))
    assert not any(e["kind"] == "ENTER" and e["symbol"] == "ETH" for e in events(path))
