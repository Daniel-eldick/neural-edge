"""Deterministic, synchronized candle replay for testing decision policies.

Candles are coarse execution approximations: next-open fills, adverse slippage,
stop-first ambiguity and gap-aware exits. This is not a scalping fill simulator.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Literal, Protocol

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

    def emit(self, kind: str, now: int, **details: object) -> None:
        self.recorder.record({"kind": kind, "time": now, **details})

    def mark(self, prices: dict[str, float], now: int) -> None:
        self.equity = self.cash + sum(p.quantity * prices[s] for s, p in self.positions.items())
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
            for s, p in self.positions.items()
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

    def run(self, candles: Sequence[Candle], policy: Policy) -> Result:
        if self._used:
            raise ValueError("Replay instances cannot be reused")
        self._used = True
        groups: dict[int, dict[str, Candle]] = defaultdict(dict)
        for c in candles:
            if c.symbol in groups[c.opened_at]:
                raise ValueError("Duplicate symbol/timestamp")
            groups[c.opened_at][c.symbol] = c
        times = sorted(groups)
        if not times:
            raise ValueError("Empty dataset")
        symbols = sorted(groups[times[0]])
        for i, t in enumerate(times):
            if sorted(groups[t]) != symbols:
                raise ValueError("Every timestamp must contain the same symbols")
            if i and t - times[i - 1] != self.settings.interval:
                raise ValueError("Missing or misaligned candle interval")
        histories: dict[str, list[Candle]] = {s: [] for s in symbols}
        self.emit("START", times[0], settings=asdict(self.settings), symbols=symbols)
        for t in times:
            batch = groups[t]
            opens = {s: c.open for s, c in batch.items()}
            self.mark(opens, t)
            # Protective gap and age exits happen even when the policy fails or halts.
            for s, p in list(self.positions.items()):
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
            for s, p in list(self.positions.items()):
                c = batch[s]
                if c.low <= p.stop:
                    self.close(s, p.stop, t + self.settings.interval, "stop")
                elif c.high >= p.target:
                    self.close(s, p.target, t + self.settings.interval, "target")
            now = t + self.settings.interval
            self.mark({s: c.close for s, c in batch.items()}, now)
            self.emit("EQUITY", now, equity=self.equity, cash=self.cash,
                      open_positions=len(self.positions), halted=self.halted)
            for s in symbols:
                histories[s].append(batch[s])
                histories[s] = histories[s][-self.settings.lookback:]
                obs = Observation(now, tuple(histories[s]), tuple(self.positions.values()),
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
        if self.pending:
            self.emit("EXPIRED", times[-1] + self.settings.interval,
                      symbols=sorted(self.pending), reason="No next candle")
        self.pending.clear()
        result = Result(self.settings.balance, self.equity, self.equity - self.settings.balance,
                        self.max_drawdown, self.closed_trades, len(self.positions),
                        self.halted, None)
        self.emit("RESULT", times[-1] + self.settings.interval, **asdict(result))
        return result
