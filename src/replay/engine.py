"""Deterministic, synchronized candle replay for testing decision policies.

Candles are coarse execution approximations: next-open fills, adverse slippage,
stop-first ambiguity and gap-aware exits. This is not a scalping fill simulator.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
from collections import defaultdict
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from src.replay.journal import Journal
from src.replay.performance import DailyPerformance, finite, integer

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class Candle:
    symbol: str
    opened_at: int  # UTC Unix seconds
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        prices = (self.open, self.high, self.low, self.close)
        if not self.symbol or type(self.opened_at) is not int or self.opened_at < 0:
            raise ValueError("Invalid symbol or timestamp")
        if not all(math.isfinite(x) and x > 0 for x in prices):
            raise ValueError("Prices must be positive and finite")
        if self.low > min(prices) or self.high < max(prices):
            raise ValueError("Invalid OHLC range")
        if not math.isfinite(self.volume) or self.volume < 0:
            raise ValueError("Invalid volume")


@dataclass(frozen=True)
class Decision:
    action: Literal["WAIT", "ENTER_LONG", "EXIT"] = "WAIT"
    stop: float | None = None
    target: float | None = None
    reason: str = "No setup"


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    entry: float
    stop: float
    target: float
    opened_at: int


@dataclass(frozen=True)
class Observation:
    now: int
    candles: tuple[Candle, ...]
    positions: tuple[Position, ...]
    equity: float
    halted: bool


class Policy(Protocol):
    def decide(self, observation: Observation) -> Decision: ...


@runtime_checkable
class CheckpointPolicy(Policy, Protocol):
    checkpoint_id: str

    def save_state(self) -> dict[str, object]: ...

    def restore_state(self, state: dict[str, object]) -> None: ...


@dataclass(frozen=True)
class Settings:
    balance: float = 1000.0
    interval: int = 300
    fee: float = 0.001
    slippage: float = 0.001
    lookback: int = 200

    def __post_init__(self) -> None:
        if not math.isfinite(self.balance) or self.balance <= 0:
            raise ValueError("Balance must be positive and finite")
        if self.interval not in (60, 300) or self.lookback < 2:
            raise ValueError("Use 60s/300s candles and lookback >= 2")
        if not all(math.isfinite(x) and 0 <= x < 0.1 for x in (self.fee, self.slippage)):
            raise ValueError("Invalid execution costs")


@dataclass(frozen=True)
class Result:
    starting_equity: float
    ending_equity: float
    net_profit: float
    max_drawdown: float
    closed_trades: int
    open_positions: int
    halted: bool
    daily_sharpe: float | None
    complete_days: int = 0
    sharpe_unavailable_reason: str | None = None
    completed: bool = True


class Recorder(Protocol):
    def record(self, event: dict[str, object]) -> None: ...


class Replay:
    """One fresh account per instance. Policies receive immutable observations only.

    The policy is trusted local code, not a sandbox. External model adapters must
    serialize Observation only; they must never get the engine or dataset.
    """

    def __init__(self, settings: Settings, recorder: Recorder) -> None:
        self.settings = settings
        self.recorder = recorder
        self.cash = settings.balance
        self.peak = settings.balance
        self.equity = settings.balance
        self.max_drawdown = 0.0
        self.halted = False
        self.positions: dict[str, Position] = {}
        self.pending: dict[str, Decision] = {}
        self.closed_trades = 0
        self._used = False
        self.performance = DailyPerformance(0, settings.balance, settings.interval)

    def emit(self, kind: str, now: int, **details: object) -> None:
        self.recorder.record({"kind": kind, "time": now, **details})

    def mark(self, prices: dict[str, float], now: int) -> None:
        self.equity = self.cash + sum(
            p.quantity * prices[s] for s, p in sorted(self.positions.items())
        )
        self.peak = max(self.peak, self.equity)
        drawdown = (self.peak - self.equity) / self.peak
        self.max_drawdown = max(self.max_drawdown, drawdown)
        if drawdown >= 0.10 - 1e-12 and not self.halted:
            self.halted = True
            self.pending = {s: d for s, d in self.pending.items() if d.action == "EXIT"}
            self.emit("HALT", now, equity=self.equity, drawdown=drawdown)

    def close(self, symbol: str, price: float, now: int, reason: str) -> None:
        p = self.positions.pop(symbol)
        fill = price * (1 - self.settings.slippage)
        self.cash += p.quantity * fill * (1 - self.settings.fee)
        pnl = p.quantity * (fill * (1 - self.settings.fee)
                            - p.entry * (1 + self.settings.fee))
        self.closed_trades += 1
        self.emit("EXIT", now, symbol=symbol, price=fill, quantity=p.quantity,
                  net_profit=pnl, reason=reason)

    def enter(self, c: Candle, d: Decision, prices: dict[str, float]) -> None:
        now = c.opened_at
        entry = c.open * (1 + self.settings.slippage)
        stop, target = d.stop, d.target
        if self.halted or c.symbol in self.positions or len(self.positions) >= 5:
            self.emit("VETO", now, symbol=c.symbol, reason="Halt, duplicate or position limit")
            return
        if stop is None or target is None or not 0 < stop < entry < target:
            self.emit("VETO", now, symbol=c.symbol, reason="Gap invalidated protective prices")
            return
        fee = self.settings.fee
        stop_proceeds = stop * (1 - self.settings.slippage) * (1 - fee)
        unit_loss = entry * (1 + fee) - stop_proceeds
        open_risk = sum(
            p.quantity * max(0.0, prices[s] - p.stop * (1 - self.settings.slippage) * (1 - fee))
            for s, p in sorted(self.positions.items())
        )
        # Account for entry friction reducing equity immediately after admission.
        friction = entry * (1 + fee) - c.open
        quantity = min(
            self.equity * 0.005 / (unit_loss + 0.005 * friction),
            max(0.0, self.equity * 0.025 - open_risk) / (unit_loss + 0.025 * friction),
            self.cash / (entry * (1 + fee)),
        )
        if quantity <= 1e-12:
            self.emit("VETO", now, symbol=c.symbol, reason="Cash or risk capacity exhausted")
            return
        self.cash -= quantity * entry * (1 + fee)
        self.positions[c.symbol] = Position(c.symbol, quantity, entry, stop, target, now)
        self.emit("ENTER", now, symbol=c.symbol, price=entry, quantity=quantity,
                  planned_risk=quantity * unit_loss, reason=d.reason)

    def _step(self, t: int, batch: dict[str, Candle],
              histories: dict[str, list[Candle]], policy: Policy) -> None:
        opens = {s: c.open for s, c in batch.items()}
        self.mark(opens, t)
        # Protective gap and age exits happen even when the policy fails or halts.
        for s, p in sorted(self.positions.items()):
            c = batch[s]
            if c.open <= p.stop or c.open >= p.target or t - p.opened_at >= 86400:
                self.close(s, c.open, t, "gap_or_max_age")
        for s, d in sorted(self.pending.items()):
            if d.action == "EXIT" and s in self.positions:
                self.close(s, opens[s], t, d.reason)
        self.mark(opens, t)
        for s, d in sorted(self.pending.items()):
            if d.action == "ENTER_LONG":
                self.enter(batch[s], d, opens)
                self.mark(opens, t)
        self.pending.clear()
        # Unknown within-candle path: stop wins if both stop and target touch.
        for s, p in sorted(self.positions.items()):
            c = batch[s]
            if c.low <= p.stop:
                self.close(s, p.stop, t + self.settings.interval, "stop")
            elif c.high >= p.target:
                self.close(s, p.target, t + self.settings.interval, "target")
        now = t + self.settings.interval
        self.mark({s: c.close for s, c in batch.items()}, now)
        self.emit("EQUITY", now, equity=self.equity, cash=self.cash,
                  open_positions=len(self.positions), halted=self.halted)
        daily_return = self.performance.observe(now, self.equity)
        if daily_return is not None:
            self.emit("DAILY_RETURN", now, net_return=daily_return)
        for s in sorted(batch):
            histories[s].append(batch[s])
            histories[s] = histories[s][-self.settings.lookback:]
            obs = Observation(now, tuple(histories[s]),
                              tuple(p for _, p in sorted(self.positions.items())),
                              self.equity, self.halted)
            try:
                d = policy.decide(obs)
                if not isinstance(d, Decision) or d.action not in (
                    "WAIT", "ENTER_LONG", "EXIT"
                ):
                    raise ValueError("Invalid decision action")
                if not isinstance(d.reason, str) or not d.reason.strip():
                    raise ValueError("Decision needs a reason")
                if d.action == "ENTER_LONG" and (
                    d.stop is None or d.target is None
                    or not math.isfinite(d.stop) or not math.isfinite(d.target)
                    or not 0 < d.stop < batch[s].close < d.target
                ):
                    raise ValueError("Invalid protective prices")
                self.emit("DECISION", now, symbol=s, **asdict(d))
                if d.action != "WAIT":
                    self.pending[s] = d
            except Exception as exc:
                # Policy errors veto new proposals; execution protection remains active.
                self.emit("POLICY_ERROR", now, symbol=s, error=str(exc))

    def _result(self, *, completed: bool) -> Result:
        sharpe, days, reason = self.performance.summary()
        return Result(self.settings.balance, self.equity, self.equity - self.settings.balance,
                      self.max_drawdown, self.closed_trades, len(self.positions), self.halted,
                      sharpe, days, reason, completed)

    def _checkpoint(self, contract: dict[str, object], index: int,
                    policy: CheckpointPolicy, *, completed: bool = False) -> dict[str, Any]:
        policy_state = policy.save_state()
        if not isinstance(policy_state, dict):
            raise ValueError("Policy checkpoint state must be an object")
        return {"contract": contract, "next_index": index, "completed": completed,
                "cash": self.cash, "equity": self.equity, "peak": self.peak,
                "max_drawdown": self.max_drawdown, "halted": self.halted,
                "closed_trades": self.closed_trades,
                "positions": {s: asdict(p) for s, p in self.positions.items()},
                "pending": {s: asdict(d) for s, d in self.pending.items()},
                "performance": self.performance.snapshot(), "policy_state": policy_state}

    def _restore(self, state: dict[str, Any], contract: dict[str, object],
                 times: list[int], groups: dict[int, dict[str, Candle]],
                 policy: CheckpointPolicy) -> int:
        try:
            if state["contract"] != contract:
                raise ValueError("Checkpoint data, settings or policy differs from this run")
            if type(state["completed"]) is not bool or state["completed"]:
                raise ValueError("A completed replay cannot resume")
            index = integer(state["next_index"])
            if index > len(times):
                raise ValueError("Invalid replay checkpoint cursor")
            symbols = set(groups[times[0]])
            cash, equity, peak = (finite(state[k]) for k in ("cash", "equity", "peak"))
            drawdown = finite(state["max_drawdown"])
            halted = state["halted"]
            closed = integer(state["closed_trades"])
            positions = {s: Position(**p) for s, p in state["positions"].items()}
            pending = {s: Decision(**d) for s, d in state["pending"].items()}
            if (cash < -1e-8 or equity <= 0 or peak < max(equity, self.settings.balance)
                    or not 0 <= drawdown <= 1 or type(halted) is not bool
                    or drawdown + 1e-12 < (peak - equity) / peak
                    or (drawdown >= 0.1 - 1e-12 and not halted)
                    or len(positions) > 5 or not set(positions) <= symbols
                    or not set(pending) <= symbols):
                raise ValueError("Invalid checkpoint account/risk state")
            for symbol, position in positions.items():
                if (position.symbol != symbol or not index
                        or integer(position.opened_at) not in times[:index]
                        or finite(position.quantity, positive=True) <= 0
                        or not 0 < finite(position.stop) < finite(position.entry)
                        < finite(position.target)):
                    raise ValueError("Invalid checkpoint position")
            last = groups[times[index - 1]] if index else groups[times[0]]
            marked = cash + sum(p.quantity * last[s].close for s, p in sorted(positions.items()))
            if not math.isclose(marked, equity, rel_tol=1e-12, abs_tol=1e-8):
                raise ValueError("Checkpoint equity does not match its positions and cash")
            for symbol, decision in pending.items():
                if (decision.action not in ("ENTER_LONG", "EXIT")
                        or not isinstance(decision.reason, str) or not decision.reason.strip()):
                    raise ValueError("Invalid pending checkpoint decision")
                if decision.action == "ENTER_LONG" and not (
                    0 < finite(decision.stop) < last[symbol].close < finite(decision.target)
                ):
                    raise ValueError("Invalid pending checkpoint protection")
            performance = DailyPerformance.restore(state["performance"])
            expected_time = times[index - 1] + self.settings.interval if index else times[0]
            if (performance.start != times[0] or performance.last_time != expected_time
                    or performance.initial_equity != self.settings.balance
                    or performance.interval != self.settings.interval
                    or not isinstance(state["policy_state"], dict)):
                raise ValueError("Inconsistent checkpoint performance or policy state")
            if not index and (positions or pending or closed or equity != self.settings.balance):
                raise ValueError("Invalid initial checkpoint")
            policy.restore_state(state["policy_state"])
            self.cash, self.equity, self.peak = cash, equity, peak
            self.max_drawdown, self.halted, self.closed_trades = drawdown, halted, closed
            self.positions, self.pending, self.performance = positions, pending, performance
            return index
        except (TypeError, KeyError, AttributeError):
            raise ValueError("Malformed replay checkpoint") from None

    def run(self, candles: Sequence[Candle], policy: Policy, *,
            resume: bool = False, stop_after: int | None = None) -> Result:
        if self._used:
            raise ValueError("Replay instances cannot be reused")
        self._used = True
        journal = self.recorder if isinstance(self.recorder, Journal) else None
        checkpoint_policy = policy if isinstance(policy, CheckpointPolicy) else None
        if journal is not None and journal.resuming != resume:
            raise ValueError("Journal and replay resume modes must match")
        if (resume or stop_after is not None) and (journal is None or checkpoint_policy is None):
            raise ValueError("Pause/resume requires a journal and checkpoint-capable policy")
        if stop_after is not None and (type(stop_after) is not int or stop_after <= 0):
            raise ValueError("stop_after must be a positive candle-batch count")
        groups: dict[int, dict[str, Candle]] = defaultdict(dict)
        for candle in candles:
            if candle.symbol in groups[candle.opened_at]:
                raise ValueError("Duplicate symbol/timestamp")
            groups[candle.opened_at][candle.symbol] = candle
        times = sorted(groups)
        if not times:
            raise ValueError("Empty dataset")
        symbols = sorted(groups[times[0]])
        digest = hashlib.sha256()
        for i, t in enumerate(times):
            if sorted(groups[t]) != symbols:
                raise ValueError("Every timestamp must contain the same symbols")
            if t % self.settings.interval or (i and t - times[i - 1] != self.settings.interval):
                raise ValueError("Missing or misaligned candle interval")
            for symbol in symbols:
                digest.update(json.dumps(asdict(groups[t][symbol]), sort_keys=True,
                                         allow_nan=False).encode())
        contract: dict[str, object] = {}
        if checkpoint_policy is not None and journal is not None:
            if (not isinstance(checkpoint_policy.checkpoint_id, str)
                    or not checkpoint_policy.checkpoint_id):
                raise ValueError("Checkpoint policy needs a version identity")
            engine_digest = hashlib.sha256()
            for source in sorted(Path(__file__).parent.glob("*.py")):
                engine_digest.update(source.name.encode())
                engine_digest.update(source.read_bytes())
            contract = {"version": 1, "dataset": digest.hexdigest(),
                        "settings": asdict(self.settings),
                        "policy": checkpoint_policy.checkpoint_id,
                        "policy_source": hashlib.sha256(
                            inspect.getsource(type(policy)).encode()).hexdigest(),
                        "engine_source": engine_digest.hexdigest()}
        self.performance = DailyPerformance(times[0], self.settings.balance, self.settings.interval)
        index = 0
        if resume and journal is not None and checkpoint_policy is not None:
            index = self._restore(journal.load_checkpoint(), contract, times, groups,
                                  checkpoint_policy)
        else:
            with journal.batch() if journal else nullcontext():
                self.emit("START", times[0], settings=asdict(self.settings), symbols=symbols)
                if journal is not None and checkpoint_policy is not None:
                    journal.save_checkpoint(self._checkpoint(contract, 0, checkpoint_policy))
        histories = {s: [groups[t][s] for t in times[max(0, index-self.settings.lookback):index]]
                     for s in symbols}
        end = min(len(times), index + stop_after) if stop_after is not None else len(times)
        for i in range(index, end):
            with journal.batch() if journal else nullcontext():
                self._step(times[i], groups[times[i]], histories, policy)
                if journal is not None and checkpoint_policy is not None:
                    journal.save_checkpoint(self._checkpoint(contract, i + 1, checkpoint_policy))
        if end < len(times):
            return self._result(completed=False)
        with journal.batch() if journal else nullcontext():
            if self.pending:
                self.emit("EXPIRED", times[-1] + self.settings.interval,
                          symbols=sorted(self.pending), reason="No next candle")
            self.pending.clear()
            result = self._result(completed=True)
            self.emit("RESULT", times[-1] + self.settings.interval, **asdict(result))
            if journal is not None and checkpoint_policy is not None:
                journal.save_checkpoint(self._checkpoint(contract, len(times), checkpoint_policy,
                                                         completed=True))
        return result
