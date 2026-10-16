"""Budget enforcement must survive failures, concurrency and process restarts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from src.agents.budget import CAP_NANO_USD, Budget, BudgetError

if TYPE_CHECKING:
    from pathlib import Path


NOW = datetime(2026, 9, 30, tzinfo=UTC)


def test_explicit_initialization_and_missing_ledger_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "budget.sqlite"
    budget = Budget(path)
    with pytest.raises(BudgetError):
        budget.reserve("typesafe", 1, now=NOW)
    assert not path.exists()
    Budget.initialize(path)
    with pytest.raises(FileExistsError):
        Budget.initialize(path)


def test_settlement_retains_exact_cost_and_cannot_refund_twice(tmp_path: Path) -> None:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    budget = Budget(path)
    call = budget.reserve("typesafe", 3_000_000, now=NOW)
    budget.settle(call, 4200, model="jev-1.13.0", input_tokens=100)
    assert Budget(path).snapshot(now=NOW) == {"used_nano_usd": 4200, "pending_calls": 0}
    with pytest.raises(BudgetError):
        budget.settle(call, 0, model="jev-1.13.0", input_tokens=0)
    assert budget.snapshot(now=NOW)["used_nano_usd"] == 4200


def test_last_reservation_is_atomic_across_connections(tmp_path: Path) -> None:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    Budget(path).reserve("another-provider", CAP_NANO_USD - 3_000_000, now=NOW)

    def reserve(_: int) -> bool:
        try:
            Budget(path).reserve("typesafe", 3_000_000, now=NOW)
        except BudgetError:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, range(2))) == [False, True]
    assert Budget(path).snapshot(now=NOW)["used_nano_usd"] == CAP_NANO_USD


def test_utc_rollover_does_not_erase_previous_spending(tmp_path: Path) -> None:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    budget = Budget(path)
    budget.reserve("typesafe", CAP_NANO_USD, now=NOW)
    with pytest.raises(BudgetError):
        budget.reserve("typesafe", 1, now=NOW)
    october = datetime(2026, 10, 1, tzinfo=UTC)
    budget.reserve("typesafe", 10, now=october)
    assert budget.snapshot(now=october)["used_nano_usd"] == 10
    assert budget.snapshot(now=NOW)["used_nano_usd"] == CAP_NANO_USD


def test_invalid_or_excess_settlement_keeps_reservation(tmp_path: Path) -> None:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    budget = Budget(path)
    call = budget.reserve("typesafe", 100, now=NOW)
    for cost in (-1, 101):
        with pytest.raises(BudgetError):
            budget.settle(call, cost, model="jev-1.13.0", input_tokens=1)
    assert budget.snapshot(now=NOW)["used_nano_usd"] == 100
