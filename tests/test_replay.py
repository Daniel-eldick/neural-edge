"""Contract tests for causal replay and loss controls, independent of strategy returns."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import FrozenInstanceError
from typing import TYPE_CHECKING

import pytest

from src.replay.__main__ import main
from src.replay.engine import Candle, Decision, Observation, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


class Events:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def record(self, event: dict[str, object]) -> None:
        self.rows.append(event)

    def of(self, kind: str) -> list[dict[str, object]]:
        return [r for r in self.rows if r["kind"] == kind]


class EnterOnce:
    def __init__(self, stop: float = 90, target: float = 120) -> None:
        self.stop = stop
        self.target = target
        self.seen: list[Observation] = []

    def decide(self, observation: Observation) -> Decision:
        self.seen.append(observation)
        if len(observation.candles) == 1:
            return Decision("ENTER_LONG", self.stop, self.target, "Test setup")
        return Decision()


def bar(t: int, symbol: str = "BTC", price: float = 100) -> Candle:
    return Candle(symbol, t, price, price, price, price, 10)


def test_prefix_only_immutable_observations_and_next_open() -> None:
    events, policy = Events(), EnterOnce()
    engine = Replay(Settings(fee=0, slippage=0), events)
    result = engine.run([bar(0), bar(300, price=105), bar(600)], policy)
    assert [o.now for o in policy.seen] == [300, 600, 900]
    assert [len(o.candles) for o in policy.seen] == [1, 2, 3]
    assert all(c.opened_at + 300 <= o.now for o in policy.seen for c in o.candles)
    assert policy.seen[0].positions == ()
    with pytest.raises(FrozenInstanceError):
        policy.seen[0].candles[0].close = 1  # type: ignore[misc]
    assert events.of("ENTER")[0]["time"] == 300
    assert events.of("ENTER")[0]["price"] == 105
    assert result.open_positions == 1
    with pytest.raises(ValueError, match="reused"):
        engine.run([bar(0)], policy)


def test_costs_and_stop_first_ambiguous_candle() -> None:
    events = Events()
    result = Replay(Settings(), events).run(
        [bar(0), Candle("BTC", 300, 100, 130, 80, 100, 10)], EnterOnce()
    )
    # Entry=100.1, exit=89.91, both charged 0.1%; risk includes both legs.
    loss_per_unit = 100.1 * 1.001 - 89.91 * 0.999
    quantity = 5 / (loss_per_unit + 0.005 * (100.1 * 1.001 - 100))
    assert result.net_profit == pytest.approx(-quantity * loss_per_unit)
    assert events.of("EXIT")[0]["reason"] == "stop"
    assert events.of("ENTER")[0]["planned_risk"] == pytest.approx(quantity * loss_per_unit)


def test_gap_loss_can_exceed_planned_risk() -> None:
    events = Events()
    result = Replay(Settings(fee=0, slippage=0), events).run(
        [bar(0), bar(300), bar(600, price=50)], EnterOnce()
    )
    assert result.net_profit == -25
    assert events.of("EXIT")[0]["price"] == 50


def test_invalid_entry_gap_veto_and_last_decision_expires() -> None:
    events = Events()
    Replay(Settings(), events).run([bar(0), bar(300, price=80)], EnterOnce())
    assert not events.of("ENTER")
    assert len(events.of("VETO")) == 1
    events = Events()
    Replay(Settings(), events).run([bar(0)], EnterOnce())
    assert not events.of("ENTER")
    assert len(events.of("EXPIRED")) == 1


def test_shared_five_position_and_total_risk_limits() -> None:
    events = Events()
    candles = [bar(t, str(s)) for t in (0, 300) for s in range(6)]
    engine = Replay(Settings(fee=0, slippage=0), events)
    engine.run(candles, EnterOnce())
    assert len(engine.positions) == 5
    assert sum(p.quantity * (p.entry - p.stop) for p in engine.positions.values()) == 25
    assert engine.cash == 750
    assert len(events.of("VETO")) == 1


def test_halt_is_latched_after_gap_and_policy_cannot_override() -> None:
    events = Events()
    # Five correlated gaps lose 12.5%, despite only 2.5% planned stop risk.
    candles = [bar(t, str(s), price) for t, price in ((0, 100), (300, 100),
               (600, 50), (900, 100)) for s in range(5)]
    result = Replay(Settings(fee=0, slippage=0), events).run(candles, EnterOnce())
    assert result.halted
    assert result.max_drawdown == pytest.approx(0.125)
    assert len(events.of("HALT")) == 1
    assert result.closed_trades == 5
    assert result.ending_equity == 875


def test_maximum_holding_time() -> None:
    events = Events()
    result = Replay(Settings(fee=0, slippage=0), events).run(
        [bar(t) for t in range(0, 87000, 300)], EnterOnce()
    )
    assert result.closed_trades == 1
    assert events.of("EXIT")[0]["time"] == 86700


def test_policy_failure_does_not_disable_stops() -> None:
    class Broken(EnterOnce):
        def decide(self, observation: Observation) -> Decision:
            if len(observation.candles) > 1:
                raise RuntimeError("Unavailable model")
            return super().decide(observation)

    events = Events()
    result = Replay(Settings(fee=0, slippage=0), events).run(
        [bar(0), bar(300), Candle("BTC", 600, 100, 100, 85, 95, 10)], Broken()
    )
    assert result.net_profit == -5
    assert len(events.of("POLICY_ERROR")) == 2


@pytest.mark.parametrize("candles", [[], [bar(0), bar(0)], [bar(0), bar(600)],
                                      [bar(0), bar(300, "ETH")]])
def test_rejects_incomplete_or_duplicate_data(candles: list[Candle]) -> None:
    with pytest.raises(ValueError):
        Replay(Settings(), Events()).run(candles, EnterOnce())


def test_journal_persists_and_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    result = Replay(Settings(), journal).run([bar(0)], EnterOnce())
    journal.close()
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT payload FROM events ORDER BY sequence").fetchall()
    assert json.loads(rows[-1][0])["ending_equity"] == result.ending_equity
    with pytest.raises(FileExistsError):
        Journal(path)


def test_cli_breakout_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                          capsys: pytest.CaptureFixture[str]) -> None:
    source, journal = tmp_path / "candles.csv", tmp_path / "run.sqlite"
    lines = ["symbol,opened_at,open,high,low,close,volume"]
    lines += [f"BTC,{i * 300},100,100,100,100,10" for i in range(20)]
    lines += ["BTC,6000,100,102,100,102,10", "BTC,6300,102,110,102,109,10"]
    source.write_text("\n".join(lines) + "\n")
    monkeypatch.setattr(sys, "argv", ["replay", "--csv", str(source), "--journal", str(journal)])
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["closed_trades"] == 1
    assert result["net_profit"] > 0
    with sqlite3.connect(journal) as connection:
        rows = connection.execute("SELECT payload FROM events ORDER BY sequence").fetchall()
    assert json.loads(rows[0][0])["policy"] == "breakout-baseline-v1"


def test_tiny_stop_cannot_borrow_cash() -> None:
    engine = Replay(Settings(fee=0, slippage=0), Events())
    engine.run([bar(0), bar(300)], EnterOnce(stop=99.999))
    assert engine.cash == pytest.approx(0)
    assert engine.positions["BTC"].quantity == 10


def test_halted_engine_rejects_new_proposals() -> None:
    class Persistent:
        def decide(self, observation: Observation) -> Decision:
            price = observation.candles[-1].close
            return Decision("ENTER_LONG", price * 0.9, price * 1.2, "Persistent proposal")

    events = Events()
    candles = [bar(t, str(s), price) for t, price in ((0, 100), (300, 100),
               (600, 50), (900, 50)) for s in range(5)]
    result = Replay(Settings(fee=0, slippage=0), events).run(candles, Persistent())
    assert result.halted
    assert len(events.of("ENTER")) == 5
    assert result.open_positions == 0
    assert len(events.of("VETO")) == 5


def test_malformed_decision_fails_closed() -> None:
    events = Events()
    Replay(Settings(), events).run([bar(0), bar(300)], EnterOnce(stop=float("nan")))
    assert len(events.of("POLICY_ERROR")) == 1
    assert not events.of("ENTER")
