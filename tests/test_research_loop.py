"""Recurring research: one authority, untouched windows, no duplicated spend."""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import pytest

# Public checkout keeps scientific runtime in the approved encrypted input.
# Operators may point this test at a privately restored, hash-verified runtime.
if frozen_runtime := os.environ.get("JEV_FROZEN_TEST_RUNTIME"):
    sys.path.insert(0, frozen_runtime)

from src.agents.budget import Budget, BudgetError  # noqa: E402

if TYPE_CHECKING:
    from pathlib import Path

NOV = datetime(2026, 11, 2, 7, tzinfo=UTC)


def test_calendar_freezes_before_untouched_week_and_never_catches_up() -> None:
    from deploy.research.loop import window

    p = window(NOV)
    assert p["id"] == "2026-11-02"
    assert p["start"] == int(datetime(2026, 11, 3, tzinfo=UTC).timestamp())
    assert p["end"] - p["start"] == 4 * 86400
    assert p["ready"] - p["end"] == 86400
    assert window(datetime(2026, 11, 9, tzinfo=UTC))["start"] > p["ready"]
    with pytest.raises(ValueError):
        window(datetime(2026, 11, 1, tzinfo=UTC))


def test_migration_blocks_local_reservations_in_all_months_preserves_reconciliation(
    tmp_path: Path,
) -> None:
    from deploy.research.loop_budget import migrate

    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    b = Budget(path)
    hold = b.reserve("lesson-fresh-v1-escrow", 432_000_000, now=NOV)
    seed = migrate(path, "authority", {hold})
    assert seed["history"][0][0] == hold
    for date in [NOV, datetime(2027, 1, 1, tzinfo=UTC)]:
        with pytest.raises(BudgetError):
            b.reserve("typesafe", 3_000_000, now=date)
    b.settle(hold, 42, model="jev-1.13.0", input_tokens=1)
    assert b.snapshot(now=NOV)["used_nano_usd"] == 42
    with pytest.raises(BudgetError):
        migrate(path, "another", set())


def test_unknown_local_usage_prevents_migration(tmp_path: Path) -> None:
    from deploy.research.loop_budget import migrate

    p = tmp_path / "budget.sqlite"
    Budget.initialize(p)
    Budget(p).reserve("typesafe", 3_000_000, now=NOV)
    with pytest.raises(BudgetError):
        migrate(p, "authority", set())
    assert Budget(p).reserve("typesafe", 3_000_000, now=NOV)


def test_global_monthly_cap_duplicates_and_unknown_holds() -> None:
    from deploy.research.loop_budget import allocate, settle

    state: dict[str, Any] = {"seed": [], "charges": {}}
    for i in range(6):
        allocate(state, str(i), "test", NOV)
    with pytest.raises(BudgetError):
        allocate(state, "7", "test", NOV)
    with pytest.raises(BudgetError):
        allocate(state, "0", "test", NOV)
    assert sum(r["cost"] for r in state["charges"].values()) == 2_592_000_000
    with pytest.raises(BudgetError):
        settle(
            state,
            "0/test",
            {
                "attempts": 1,
                "pending_calls": 1,
                "settled_nano_usd": 0,
                "accounted_nano_usd": 3_000_000,
                "input_tokens": 0,
            },
        )
    allocate(state, "dec", "test", datetime(2026, 12, 1, tzinfo=UTC))
    assert state["charges"]["dec/test"]["month"] == "2026-12"
    assert state["charges"]["0/test"]["cost"] == 432_000_000


def test_real_clock_month_pending_and_attempt_cap_before_post(tmp_path: Path) -> None:
    from deploy.research.loop_budget import PhaseBudget

    p = tmp_path / "budget.sqlite"
    Budget.initialize(p)
    clock = [NOV]
    b = PhaseBudget(p, "review", "2026-11", int(NOV.timestamp()) + 1000, clock=lambda: clock[0])
    with pytest.raises(BudgetError):
        b.reserve("typesafe", 3_000_000, now=datetime(2026, 10, 1, tzinfo=UTC))
    ident = b.reserve("typesafe", 3_000_000, now=NOV)
    with pytest.raises(BudgetError):
        b.reserve("typesafe", 3_000_000, now=NOV)
    b.settle(ident, 42, model="jev-1.13.0", input_tokens=1)
    with pytest.raises(BudgetError):
        b.reserve("typesafe", 3_000_000, now=NOV)
    clock[0] = datetime(2026, 12, 1, tzinfo=UTC)
    with pytest.raises(BudgetError):
        b.reserve("typesafe", 3_000_000, now=NOV)


def test_price_document_exact_pinned_model_column_not_other_model() -> None:
    from deploy.research.loop_client import validate_price

    doc = (
        "| Model ID | `jev-1.14.0` | `jev-1.13.0` |\n"
        "| Price (per Btok / per Mtok) | \\$42 / \\$0.042 | \\$42 / \\$0.042 |\n"
        "| Context length | 64k per-request / 32k per-question | "
        "64k per-request / 32k per-question |\n"
        "You pay per input token. Output tokens are free."
    )
    validate_price(doc)
    for bad in [
        doc.replace("`jev-1.13.0`", "`jev-1.15.0`"),
        doc.replace("\\$42 / \\$0.042 |\n", "\\$420 / \\$0.42 |\n"),
        doc.replace("Output tokens are free.", "Output charged."),
    ]:
        with pytest.raises(ValueError):
            validate_price(bad)


def test_store_cas_and_immutable_artifacts_with_real_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    from deploy.research import loop_store

    repo = tmp_path / "git"
    repo.mkdir()

    def git(*args: str, data: str | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, input=data, text=True, capture_output=True, check=True
        ).stdout

    git("init", "-b", "reports")
    git("config", "user.name", "test")
    git("config", "user.email", "test@example.com")
    git("commit", "--allow-empty", "-m", "init")
    monkeypatch.setattr(loop_store, "session", lambda op: op(git, git("rev-parse", "HEAD").strip()))
    monkeypatch.setattr(loop_store, "assert_private", lambda: None)
    # Substitute local CAS for remote ref update, preserving Git's actual lock semantics.
    original = git

    def local_git(*args: str, data: str | None = None) -> str:
        if args[0] == "push":
            commit = args[-1].split(":")[0]
            return original("update-ref", "refs/heads/reports", commit, args[1].split(":")[-1])
        return original(*args, data=data)

    monkeypatch.setattr(
        loop_store, "session", lambda op: op(local_git, git("rev-parse", "HEAD").strip())
    )
    parent = git("rev-parse", "HEAD").strip()
    name = "loop-v1/cycles/2026-11-02/frozen.enc.base64"
    new = loop_store.write(parent, {loop_store.STATE: "state1", name: "frozen"})
    assert new != parent
    with pytest.raises(ValueError):
        loop_store.write(parent, {loop_store.STATE: "stale"})
    with pytest.raises(ValueError):
        loop_store.write(new, {name: "overwrite"})
    assert git("show", f"HEAD:{loop_store.STATE}") == "state1"


def test_bounded_candidate_consumes_last_findings_without_recursive_growth() -> None:
    from deploy.research.loop import lesson

    parent = {
        "sha256": "a" * 64,
        "available_at": 1,
        "training_cutoff": 1,
        "payload": {"original": True},
    }
    findings = {"runs": [], "status": "skipped"}
    c = lesson(parent, findings, None, "2026-11-02", 10, 5)
    assert c["training_cutoff"] == 5 and c["available_at"] == 10
    assert "findings" in c["payload"]["post_test_review"]
    c2 = lesson(parent, findings, None, "2026-11-09", 20, 15)
    assert len(json.dumps(c2)) < 3000
    assert c["sha256"] != c2["sha256"]


def initial(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    from dataclasses import asdict

    from deploy.research import loop
    from deploy.research.guard import digest

    p = {"schema": 1, "authority": "test", "source_sha256": loop.source_hash()}
    monkeypatch.setattr(loop, "config", lambda: p)
    parent = asdict(make_pack())
    state = {
        "schema": 1,
        "authority": "test",
        "config": p,
        "seed": [],
        "migration_sha256": digest([]),
        "charges": {},
        "cycles": {},
        "original": parent,
        "active": parent,
        "evidence": {"report": {"status": "skipped"}, "cutoff": 1000, "sha256": "bootstrap"},
    }
    return loop, state, p


@pytest.mark.parametrize("scenario", ["ack-lost", "review-post-failure", "late-freeze"])
def test_claimed_phase_never_retries_after_uncertainty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scenario: str
) -> None:
    import responses

    from deploy.research import loop_client

    loop, state, _ = initial(monkeypatch)
    p = loop.window(NOV)
    monkeypatch.setattr(
        loop_client,
        "price_proof",
        lambda **kw: {"model": "jev-1.13.0", "checked_at": NOV.timestamp()},
    )
    published: list[dict[str, Any]] = []

    def save(s: dict[str, Any], *args: Any, **kw: Any) -> str:
        published.append(copy.deepcopy(s))
        if scenario == "ack-lost":
            raise RuntimeError("push acknowledgement lost")
        return "claimed"

    monkeypatch.setattr(loop, "save", save)
    monkeypatch.setenv("TYPESAFE_API_KEY", "mock-only")
    if scenario == "review-post-failure":
        state["evidence"]["report"] = {
            "status": "complete",
            "runs": [
                {
                    "variant": v,
                    "closed_trades": 12,
                    "net_profit_usdt": 1,
                    "net_return": 0.001,
                    "max_drawdown": 0.01,
                    "model_choices": 1,
                    "selected_seen": 1,
                    "mean_close_exposure_fraction": 0.1,
                }
                for v in ["baseline", "frozen", "original", "candidate"]
            ],
        }
    when = datetime.fromtimestamp(p["start"] + 1, UTC) if scenario == "late-freeze" else NOV
    with responses.RequestsMock(assert_all_requests_are_fired=False) as network:
        network.post("https://api.typesafe.ai/v1/systemone", status=503)
        if scenario == "late-freeze":
            assert loop.tick(
                state, "rev", b"x" * 32, tmp_path, {}, now=when, clock=lambda: when
            ).startswith("missed")
            assert not published and not network.calls
        else:
            with pytest.raises(RuntimeError):
                loop.tick(state, "rev", b"x" * 32, tmp_path, {}, now=NOV, clock=lambda: NOV)
            durable = published[-1]
            assert durable["cycles"][p["id"]]["stage"] == "review_claimed"
            assert durable["charges"][p["id"] + "/review"]["cost"] == 3_000_000
            assert loop.tick(
                durable, "rev2", b"x" * 32, tmp_path, {}, now=NOV, clock=lambda: NOV
            ).endswith("no_retry")
            assert len(network.calls) == (1 if scenario == "review-post-failure" else 0)


def test_two_real_fresh_cycles_reconstruct_and_use_saved_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import responses

    from deploy.research import loop_client, loop_replay
    from src.replay.engine import Candle

    loop, state, _ = initial(monkeypatch)
    key = b"x" * 32
    files: dict[str, str] = {}
    times: dict[str, int] = {}
    revision = ["initial"]
    clock = [NOV]
    p = [loop.window(NOV)]

    def write(expected: str, updates: dict[str, str], **kw: Any) -> str:
        assert expected == revision[0]
        files.update(updates)
        times.update({name: int(clock[0].timestamp()) for name in updates})
        revision[0] += "x"
        return revision[0]

    def read(paths: list[str]) -> Any:
        return {name: files[name] for name in paths if name in files}, revision[0], times.copy()

    monkeypatch.setattr(loop, "write", write)
    monkeypatch.setattr(loop, "read", read)
    monkeypatch.setattr(
        loop_client,
        "price_proof",
        lambda **kw: {"model": "jev-1.13.0", "checked_at": int(clock[0].timestamp())},
    )
    monkeypatch.setenv("TYPESAFE_API_KEY", "mock-only")

    def market(endpoint: str, params: dict[str, str]) -> tuple[bytes, int]:
        if endpoint.endswith("time"):
            return json.dumps({"serverTime": p[0]["ready"] * 1000}).encode(), p[0]["ready"]
        start = int(params["startTime"]) // 1000
        end = (int(params["endTime"]) + 1) // 1000
        candles = [
            kline(Candle(params["symbol"], t, price, price, price, price, 1))
            for t in range(start, end, 300)
            for price in [100 + (t - p[0]["start"]) * 0.00001]
        ]
        return json.dumps(candles).encode(), p[0]["ready"]

    monkeypatch.setattr(loop_replay, "public_get", market)
    seen: list[dict[str, Any]] = []

    def post(request: Any) -> tuple[int, dict[str, str], str]:
        req = json.loads(request.body)
        options = list(req["questions"]["decision"]["criteria"])
        if "enter" in options:
            seen.append(json.loads(req["state"]))
        return (
            200,
            {},
            json.dumps(answer(options, "enter" if "enter" in options else "revise_caution")),
        )

    with responses.RequestsMock() as network:
        network.add_callback(responses.POST, "https://api.typesafe.ai/v1/systemone", callback=post)
        for week in range(2):
            clock[0] = NOV + timedelta(days=7 * week)
            p[0] = loop.window(clock[0])
            root = tmp_path / f"review-{week}"
            root.mkdir()
            assert (
                loop.tick(state, revision[0], key, root, {}, now=clock[0], clock=lambda: clock[0])
                == "candidate_frozen_before_fresh_data"
            )
            frozen = state["cycles"][p[0]["id"]]
            assert frozen["candidate"]["payload"]["post_test_review"]["findings"]["status"] == (
                "skipped" if week == 0 else "complete"
            )
            clock[0] = datetime.fromtimestamp(p[0]["ready"] + 7 * 3600, UTC)
            root = tmp_path / f"test-{week}"
            root.mkdir()
            status = loop.tick(
                state, revision[0], key, root, {}, now=clock[0], clock=lambda: clock[0]
            )
            assert status == "fresh_test_complete_original"
            cycle = state["cycles"][p[0]["id"]]
            assert cycle["stage"] == "complete"
            assert all(
                r["open_positions"] == 0 and r["closed_trades"] > 0 for r in cycle["report"]["runs"]
            )
            assert cycle["usage"]["attempts"] <= 144 and cycle["usage"]["pending_calls"] == 0
            assert cycle["candidate"]["sha256"] in {
                s.get("research_lesson", {}).get("lesson_sha256") for s in seen
            }
            assert loop.artifact(p[0], "result") in files
        assert len(state["cycles"]) == 2
        assert all(c["settled"] for c in state["charges"].values())
        assert state["evidence"]["cycle"] == "2026-11-09"
        assert state["active"] == state["original"]


def test_verify_only_has_no_paid_secret_or_state_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy.research import followup, loop

    monkeypatch.setattr(loop, "config", lambda: {})
    monkeypatch.setattr(followup, "restore_inputs", lambda *a: ({}, {}))
    monkeypatch.setattr(loop, "read", lambda paths: ({}, "revision", {}))
    writes = []
    monkeypatch.setattr(loop, "write", lambda rev, files: writes.append(files))
    monkeypatch.setattr(loop, "tick", lambda *a, **kw: pytest.fail("verify cannot tick"))
    assert loop.hosted("verify", tmp_path, tmp_path, b"x" * 32) == "recurring_transport_verified"
    assert list(writes[0]) == ["loop-v1/connection-check.md"]


def test_runtime_and_old_frozen_sources_remain_exact() -> None:
    from deploy.research import followup, learning, promotion
    from deploy.research.cloud import CODE_SHA
    from src.evaluation.lesson_week import implementation_hash

    assert implementation_hash() == CODE_SHA
    assert (
        learning.source_hash() == "80adfeaab423a0af6ed8ed425607fd764f7aad325555b0ef7932a0986b20a145"
    )
    assert (
        followup.source_hash() == "a284e99b26c4a2f5f1e6d7890738a447c4d219af0924b8aadf5b13f51f15d8fe"
    )
    assert (
        promotion.source_hash()
        == "278e87604e4153b65d610156385d1458b2f76ea7e4d141dcc191775b9eb514cf"
    )


def test_positive_adoption_is_next_cycles_actual_incumbent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unit test of publication/consumer wiring; real reconstruction tested separately."""
    from deploy.research import loop_client, loop_replay

    loop, state, _ = initial(monkeypatch)
    key = b"x" * 32
    p = loop.window(NOV)
    candidate = loop.lesson(
        state["original"], {"status": "complete"}, None, p["id"], int(NOV.timestamp()), 1000
    )
    frozen = {
        "protocol": p,
        "stage": "frozen",
        "incumbent": copy.deepcopy(state["active"]),
        "candidate": candidate,
        "review_choice": {"choice": "revise_caution"},
    }
    state["cycles"][p["id"]] = copy.deepcopy(frozen)
    files = {loop.artifact(p, "frozen"): loop.seal(frozen, key, "research-loop-freeze")}
    monkeypatch.setattr(
        loop,
        "read",
        lambda paths: (files, "rev", {loop.artifact(p, "frozen"): int(NOV.timestamp())}),
    )
    monkeypatch.setattr(loop, "save", lambda *a, **kw: "rev")
    monkeypatch.setattr(loop_client, "price_proof", lambda **kw: {})
    monkeypatch.setattr(loop_client, "LoopClient", lambda *a, **kw: None)
    monkeypatch.setattr(loop_replay, "acquire", lambda *a: [])
    r = report()
    for row in r["runs"]:
        row.update(model_choices=0, inference_cost_usd=0)
    monkeypatch.setattr(loop_replay, "run_variants", lambda *a, **kw: r)
    monkeypatch.setattr(loop, "verify_cycle", lambda *a: None)
    monkeypatch.setenv("TYPESAFE_API_KEY", "mock-only")
    when = datetime.fromtimestamp(p["ready"] + 7 * 3600, UTC)
    assert (
        loop.evaluate(state, "rev", key, tmp_path, p, when, lambda: when)
        == "fresh_test_complete_candidate"
    )
    assert state["active"]["sha256"] == candidate["sha256"]
    assert state["active"]["payload"] == candidate["payload"]
    assert state["active"]["training_cutoff"] == p["ready"]
    assert state["active"]["available_at"] >= when.timestamp()
    # Next review binds this adopted payload, rather than starting over at the original.
    future = tmp_path / "next"
    future.mkdir()
    next_when = NOV + timedelta(days=7)
    import responses

    # Insufficient evidence abstains; inspect the next frozen incumbent.
    state["evidence"]["report"] = {"status": "skipped"}
    monkeypatch.setattr(
        loop_client, "LoopClient", lambda *a, **kw: pytest.fail("abstention cannot call")
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False):
        assert (
            loop.review(
                state, "rev", key, future, loop.window(next_when), next_when, lambda: next_when
            )
            == "candidate_frozen_before_fresh_data"
        )
    incumbent = state["cycles"]["2026-11-09"]["incumbent"]
    assert incumbent == state["active"] and incumbent["payload"] == candidate["payload"]


def test_shallow_history_deepens_to_actual_freeze_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os
    import subprocess

    from deploy.research import loop_store

    source = tmp_path / "source"
    source.mkdir()

    def run(root: Path, *args: str, date: str = "2026-11-02T07:00:00Z") -> str:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
            env={**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
        ).stdout

    run(source, "init", "-b", "reports")
    run(source, "config", "user.name", "test")
    run(source, "config", "user.email", "test@example.com")
    name = "loop-v1/cycles/2026-11-02/frozen.enc.base64"
    target = source / name
    target.parent.mkdir(parents=True)
    target.write_text("frozen")
    run(source, "add", ".")
    run(source, "commit", "-m", "freeze")
    for i in range(4):
        (source / "later").write_text(str(i))
        run(source, "add", "later")
        run(source, "commit", "-m", "later", date="2027-04-01T00:00:00Z")
    run(tmp_path, "clone", "--depth=2", source.as_uri(), str(tmp_path / "copy"))
    clone = tmp_path / "copy"
    monkeypatch.setattr(
        loop_store,
        "session",
        lambda op: op(lambda *a: run(clone, *a), run(clone, "rev-parse", "HEAD").strip()),
    )
    _, _, times = loop_store.read([name])
    assert times[name] == int(NOV.timestamp())


def make_pack() -> Any:
    from src.agents.lessons import LessonPack

    return LessonPack(
        "a" * 64,
        1200,
        900,
        {
            "status": "candidate_only",
            "assessment": "inconclusive",
            "evidence": {},
        },
    )


def answer(options: list[str], choice: str) -> dict[str, Any]:
    return {
        "model": "jev-1.13.0",
        "usage": {"input_tokens": 100},
        "answers": {
            "decision": {
                "type": "choice",
                "choice": choice,
                "confidence": 0.8,
                "probabilities": {key: int(key == choice) for key in options},
            }
        },
    }


def kline(candle: Any) -> list[Any]:
    return [
        candle.opened_at * 1000,
        *[
            str(v)
            for v in (
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            )
        ],
        (candle.opened_at + 300) * 1000 - 1,
        "0",
        1,
        "0",
        "0",
        "0",
    ]


def report() -> dict[str, Any]:
    return {
        "status": "complete",
        "promotion_allowed": False,
        "runs": [
            {
                "variant": variant,
                "closed_trades": 12,
                "open_positions": 0,
                "policy_errors": 0,
                "net_return": net,
                "net_profit_usdt": net * 1000,
                "max_drawdown": dd,
                "model_choices": 0 if variant == "baseline" else 20,
                "inference_cost_usd": 0 if variant == "baseline" else 0.000084,
            }
            for variant, net, dd in [
                ("baseline", 0.002, 0.02),
                ("frozen", 0.003, 0.02),
                ("original", 0.004, 0.02),
                ("candidate", 0.006, 0.015),
            ]
        ],
    }


def test_phase_budget_concurrent_callers_cannot_exceed_one_review(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from deploy.research.loop_budget import PhaseBudget

    path = tmp_path / "phase.sqlite"
    Budget.initialize(path)
    b = PhaseBudget(path, "review", "2026-11", int(NOV.timestamp()) + 1000, clock=lambda: NOV)

    def reserve(_: int) -> str | None:
        try:
            return b.reserve("typesafe", 3_000_000, now=NOV)
        except BudgetError:
            return None

    with ThreadPoolExecutor(max_workers=20) as workers:
        calls = list(workers.map(reserve, range(20)))
    assert sum(c is not None for c in calls) == 1
    assert b.usage()["attempts"] == 1


def test_workflow_keeps_secrets_out_of_upkeep_and_verification() -> None:
    from pathlib import Path

    import yaml  # type: ignore[import-untyped]

    w = yaml.safe_load(Path(".github/workflows/jev-recurring-research.yml").read_text())
    assert w["on"]["schedule"] == [{"cron": "17 7 * * *"}]
    assert w["jobs"]["research"]["permissions"] == {"contents": "read"}
    assert w["jobs"]["keep_schedule"]["permissions"] == {"contents": "write"}
    assert "always()" in w["jobs"]["keep_schedule"]["if"]
    assert w["jobs"]["research"]["environment"] == "jev-lesson-week"
    assert w["concurrency"]["cancel-in-progress"] is False
    for step in w["jobs"]["research"]["steps"]:
        if step["name"] == "Verify recurring research":
            assert "TYPESAFE_API_KEY" not in step["env"]
    assert "secrets." not in json.dumps(w["jobs"]["keep_schedule"])
    assert "'force':False" in w["jobs"]["keep_schedule"]["steps"][0]["run"]


def test_missing_authority_never_initializes_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy.research import followup, loop

    monkeypatch.setattr(loop, "config", lambda: {})
    monkeypatch.setattr(followup, "restore_inputs", lambda *a: ({}, {}))
    monkeypatch.setattr(loop, "read", lambda paths: ({}, "rev", {}))
    monkeypatch.setattr(loop, "write", lambda *a, **kw: pytest.fail("no reset"))
    with pytest.raises(ValueError, match="not initialized"):
        loop.hosted("tick", tmp_path, tmp_path, b"x" * 32)
