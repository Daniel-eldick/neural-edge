"""The teacher must earn memory from this run's matured evidence only."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from src.agents.jev import MODEL, Choice
from src.agents.learning import LearningPolicy
from src.agents.responses import ResponseStore
from src.cockpit.report import load_journal, render
from src.memory.teacher import ClosedTradeTeacher, curriculum
from src.replay.engine import Candle, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


class Provider:
    def __init__(self) -> None:
        self.states: list[dict[str, object]] = []

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        self.states.append(json.loads(state))
        return Choice("enter", 0.8, {"enter": 0.8, "wait": 0.2}, MODEL, 100, 4200)


def data() -> list[Candle]:
    prices = [100] * 20 + [101, 102, 90] + [90] * 20 + [91, 92, 80]
    return [Candle("BTC", i * 300, p, p, p, p, 1) for i, p in enumerate(prices)]


def closed_case(
    teacher: ClosedTradeTeacher, *, start: int = 0, profit: float = -1, sequence: int = 1
) -> None:
    teacher.consume(
        sequence,
        {"kind": "ENTER", "time": start, "symbol": "BTC", "price": 100, "quantity": 1},
        now=start + 300,
    )
    teacher.consume(
        sequence + 1,
        {
            "kind": "EXIT",
            "time": start + 300,
            "symbol": "BTC",
            "price": 101,
            "quantity": 1,
            "net_profit": profit,
            "reason": "target",
        },
        now=start + 300,
    )


def test_cases_need_closed_outcomes_and_a_later_review() -> None:
    teacher = ClosedTradeTeacher(300)
    closed_case(teacher)
    assert teacher.review(300) is None
    assert teacher.context("BTC", 300)["cases"] == []
    review = teacher.review(600)
    assert review is not None and review["case_ids"] == ["trade:1:2"]
    context = teacher.context("BTC", 600)
    assert context["cases"][0]["net_profit"] == -1
    assert context["lesson"]["counterexample_case_ids"] == ["trade:1:2"]
    assert context["lesson"]["status"] == "candidate"
    assert teacher.context("BTC", 599)["cases"] == []
    assert teacher.review(600) is None
    assert teacher.context("ETH", 600)["cases"] == []


def test_support_and_counterexamples_are_both_retained() -> None:
    teacher = ClosedTradeTeacher(300)
    closed_case(teacher)
    teacher.review(600)
    closed_case(teacher, start=900, profit=2, sequence=3)
    teacher.review(1500)
    lesson = teacher.context("BTC", 1500)["lesson"]
    assert lesson["supporting_case_ids"] == ["trade:3:4"]
    assert lesson["counterexample_case_ids"] == ["trade:1:2"]
    assert ClosedTradeTeacher(300).context("BTC", 0)["cases"] == []


def test_future_and_unmatched_outcomes_are_rejected_before_memory_changes() -> None:
    teacher = ClosedTradeTeacher(300)
    with pytest.raises(ValueError, match="future"):
        teacher.consume(
            1, {"kind": "ENTER", "time": 900, "symbol": "BTC", "price": 100, "quantity": 1}, now=600
        )
    with pytest.raises(ValueError, match="entry"):
        teacher.consume(
            2,
            {
                "kind": "EXIT",
                "time": 300,
                "symbol": "BTC",
                "price": 100,
                "quantity": 1,
                "net_profit": 0,
                "reason": "stop",
            },
            now=600,
        )
    assert teacher.context("BTC", 0)["cases"] == []


def test_curriculum_cannot_be_backdated_or_contain_quiz_answers() -> None:
    assert curriculum(1717200000) == []  # 2024 pilot
    cards = curriculum(1790726400)  # 2026-09-30 UTC
    assert len(cards) == 6
    assert all(card["available_at"] == 1790726400 for card in cards)
    assert all("answer" not in key and "quiz" not in key for card in cards for key in card)
    assert "100.0995003" not in json.dumps(cards)


def run(
    path: Path,
    *,
    provider: Provider,
    stop_after: int | None = None,
    resume: bool = False,
    journal_type: type[Journal] = Journal,
) -> list[dict[str, object]]:
    journal = journal_type(path, resume=resume)
    store = ResponseStore(path.with_suffix(".responses.sqlite"), resume=resume)
    try:
        if not resume:
            journal.record({"kind": "MANIFEST", "policy": "jev-memory-filter-v1"})
        policy = LearningPolicy(provider, store, journal, interval=300)
        Replay(Settings(), journal).run(data(), policy, stop_after=stop_after, resume=resume)
        return [
            json.loads(row[0])
            for row in journal.connection.execute("SELECT payload FROM events ORDER BY sequence")
        ]
    finally:
        journal.close()
        store.close()


def test_memory_enters_only_later_candidates_and_survives_restart(tmp_path: Path) -> None:
    full_provider = Provider()
    full = run(tmp_path / "full.sqlite", provider=full_provider)
    split_provider = Provider()
    run(tmp_path / "split.sqlite", provider=split_provider, stop_after=23)
    split = run(tmp_path / "split.sqlite", provider=split_provider, resume=True)
    assert full == split
    assert full_provider.states == split_provider.states
    first, second = full_provider.states
    assert isinstance(first["memory"], dict) and isinstance(second["memory"], dict)
    assert isinstance(second["now"], int)
    assert first["memory"]["cases"] == []
    assert len(second["memory"]["cases"]) == 1
    assert second["memory"]["cases"][0]["closed_at"] <= second["now"] - 300
    assert second["memory"]["curriculum"] == []
    assert any(e["kind"] == "TEACHER_REVIEW" for e in full)
    assert any(e["kind"] == "MEMORY_READ" for e in full)
    loaded = load_journal(tmp_path / "full.sqlite")
    assert loaded.reviewed_cases == 2 and loaded.memory_reads == 2
    assert loaded.last_review_at is not None
    page = render([loaded])
    assert "Jev with memory" in page and "On · improvement unproven" in page
    assert "Reviewed trades" in page and "Last review" in page


def test_review_crash_rolls_back_then_replays_once(tmp_path: Path) -> None:
    class CrashJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            super().record(event)
            if event["kind"] == "TEACHER_REVIEW":
                raise SystemExit("simulated process death")

    provider = Provider()
    path = tmp_path / "crash.sqlite"
    with pytest.raises(SystemExit):
        run(path, provider=provider, journal_type=CrashJournal)
    recovered = run(path, provider=provider, resume=True)
    clean = run(tmp_path / "clean.sqlite", provider=Provider())
    assert recovered == clean
    assert len(provider.states) == 2


def test_future_suffix_cannot_change_earlier_memory_or_model_inputs(tmp_path: Path) -> None:
    left = Provider()
    run(tmp_path / "left.sqlite", provider=left)
    right = Provider()
    changed = data()[:-1] + [Candle("BTC", data()[-1].opened_at, 200, 200, 200, 200, 1)]
    journal = Journal(tmp_path / "right.sqlite")
    store = ResponseStore(tmp_path / "right.responses.sqlite")
    try:
        journal.record({"kind": "MANIFEST", "policy": "jev-memory-filter-v1"})
        Replay(Settings(), journal).run(
            changed, LearningPolicy(right, store, journal, interval=300)
        )
    finally:
        journal.close()
        store.close()
    assert right.states[:2] == left.states[:2]


def test_memory_is_bounded_without_selecting_only_winners() -> None:
    teacher = ClosedTradeTeacher(300)
    for index in range(70):
        closed_case(
            teacher, start=index * 900, sequence=index * 2 + 1, profit=1 if index % 2 else -1
        )
        teacher.review(index * 900 + 600)
    assert len(teacher.cases) == 64 and teacher.reviewed_total == 70
    context = teacher.context("BTC", 69 * 900 + 600)
    assert len(context["cases"]) == 6
    assert len(context["lesson"]["supporting_case_ids"]) == 3
    assert len(context["lesson"]["counterexample_case_ids"]) == 3


@pytest.mark.parametrize(
    "field,value",
    [
        ("memory_sha256", "0" * 64),
        ("cursor", 0),
        ("now", 999999),
        ("response_store", "replacement"),
    ],
)
def test_changed_memory_checkpoint_fails_before_any_new_call(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    path = tmp_path / "changed.sqlite"
    provider = Provider()
    run(path, provider=provider, stop_after=25)
    before = list(provider.states)
    journal = Journal(path, resume=True)
    try:
        state = journal.load_checkpoint()
        state["policy_state"][field] = value
        # Recompute the outer checksum: inner evidence reconstruction must still reject.
        with journal.batch():
            journal.save_checkpoint(state)
    finally:
        journal.close()
    with pytest.raises(ValueError):
        run(path, provider=provider, resume=True)
    assert provider.states == before


def test_saved_response_with_memory_is_not_paid_for_twice_after_crash(tmp_path: Path) -> None:
    class CrashJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            super().record(event)
            if event["kind"] == "MODEL_CHOICE" and event["time"] == 13200:
                raise SystemExit("crash after the second durable response")

    provider = Provider()
    path = tmp_path / "crash.sqlite"
    with pytest.raises(SystemExit):
        run(path, provider=provider, journal_type=CrashJournal)
    assert len(provider.states) == 2
    recovered = run(path, provider=provider, resume=True)
    assert recovered == run(tmp_path / "clean.sqlite", provider=Provider())
    assert len(provider.states) == 2


def test_teacher_integrity_error_rolls_back_candle_instead_of_bad_checkpoint(
    tmp_path: Path,
) -> None:
    class CorruptJournal(Journal):
        def record(self, event: dict[str, object]) -> None:
            if event["kind"] == "ENTER":
                event = {**event, "time": 999999}
            super().record(event)

    path = tmp_path / "invalid.sqlite"
    provider = Provider()
    with pytest.raises(ValueError, match="Memory integrity"):
        run(path, provider=provider, journal_type=CorruptJournal)
    assert run(path, provider=provider, resume=True) == run(
        tmp_path / "clean.sqlite",
        provider=Provider(),
    )
    assert len(provider.states) == 2
