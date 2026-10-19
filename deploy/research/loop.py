"""Weekly hosted research state machine; new phases require durable private claims."""

from __future__ import annotations

import argparse
import base64
import copy
import json
import math
import os
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from deploy.research.cloud import WORKSPACE, archive, decrypt, encrypt, hash_bytes, unpack
from deploy.research.learning import INSTRUCTIONS, LIMITS, OPTIONS, encoded
from deploy.research.loop_store import CHECK, REPORT, STATE, read, write

if TYPE_CHECKING:
    from collections.abc import Callable

FIRST = datetime(2026, 11, 2, tzinfo=UTC)
CONFIG = Path(__file__).with_name("loop-policy") / "runner.json"


def source_hash() -> str:
    from deploy.research.promotion import source_hash as prior_hash

    return hash_bytes(
        encoded(
            {
                "prior": prior_hash(),
                **{
                    p.name: hash_bytes(p.read_bytes())
                    for p in sorted(Path(__file__).parent.glob("loop*.py"))
                },
            }
        )
    )


def config() -> dict[str, Any]:
    p = json.loads(CONFIG.read_bytes())
    if (
        p["schema"] != 1
        or p["source_sha256"] != source_hash()
        or p["first_review"] != int(FIRST.timestamp())
        or p["monthly_cap_nano_usd"] != 3_000_000_000
        or p["rule"] != rule()
        or not p["declared_at"] < FIRST.timestamp()
    ):
        raise ValueError("Recurring source or authorization differs")
    return dict(p)


def rule() -> dict[str, Any]:
    from deploy.research.promotion import RULE

    return dict(RULE)


def window(now: datetime) -> dict[str, Any]:
    if now.tzinfo is None or now < FIRST:
        raise ValueError("Recurring research not due yet")
    date = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    monday = date - timedelta(days=date.weekday())
    start = monday + timedelta(days=1)
    return {
        "id": monday.date().isoformat(),
        "review": int(monday.timestamp()),
        "start": int(start.timestamp()),
        "end": int((start + timedelta(days=4)).timestamp()),
        "ready": int((start + timedelta(days=5)).timestamp()),
        "deadline": int((monday + timedelta(days=7)).timestamp()),
    }


def seal(value: Any, key: bytes, domain: str) -> str:
    return base64.b64encode(encrypt(encoded(value), key, domain)).decode() + "\n"


def open_value(raw: str, key: bytes, domain: str) -> Any:
    return json.loads(decrypt(base64.b64decode(raw, validate=False), key, domain))


def validate_state(state: dict[str, Any], p: dict[str, Any]) -> None:
    from deploy.research.guard import digest
    from deploy.research.loop_budget import validate

    validate(state)
    if (
        state["schema"] != 1
        or state["config"] != p
        or state["authority"] != p["authority"]
        or digest(state["seed"]) != state["migration_sha256"]
        or len(state["cycles"]) > 1000
    ):
        raise ValueError("Recurring authority/source/history differs; no reset allowed")
    for ident, cycle in state["cycles"].items():
        if cycle["protocol"] != window(datetime.fromisoformat(ident).replace(tzinfo=UTC)):
            raise ValueError("Cycle dates differ from fixed calendar")
        if cycle["stage"] not in {"review_claimed", "frozen", "test_claimed", "complete"}:
            raise ValueError("Unknown recurring phase")


def lesson(
    original: dict[str, Any],
    findings: dict[str, Any],
    choice: Any,
    cycle: str,
    available: int,
    cutoff: int,
) -> dict[str, Any]:
    stance = choice.choice if choice else "inconclusive"
    payload = {
        "status": "candidate_only",
        "original_candidate": original["payload"],
        "post_test_review": {"stance": stance, "guidance": OPTIONS[stance], "findings": findings},
        "meaning": "Provisional context from completed development evidence; risk rules fixed.",
    }
    value = {"available_at": available, "training_cutoff": cutoff, "payload": payload}
    return {"sha256": hash_bytes(encoded({"cycle": cycle, **value})), **value}


def findings(report: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "variant",
        "closed_trades",
        "net_profit_usdt",
        "net_return",
        "max_drawdown",
        "model_choices",
        "selected_seen",
        "mean_close_exposure_fraction",
    ]
    return {
        "status": report["status"],
        "runs": [{k: r[k] for k in fields} for r in report.get("runs", [])],
        "decisions": report.get("decisions"),
    }


def summary(state: dict[str, Any], now: datetime) -> str:
    period = now.astimezone(UTC).strftime("%Y-%m")
    used = sum(r[4] for r in state["seed"] if r[1] == period) + sum(
        r["cost"] for r in state["charges"].values() if r["month"] == period
    )
    lines = [
        "# Recurring Jev research",
        "",
        "Weekly context learning, fresh replay and conditional research adoption.",
        "No real trading. Results remain provisional; model weights are unchanged.",
        "",
        f"UTC month: {period}; hard guarded cap USD3; accounted USD{used / 1e9:.9f}.",
        "Uncertain phases retain their full reservation and never retry.",
        "",
        f"Active context: {state.get('active', {}).get('sha256', 'waiting for bootstrap')}.",
        "",
    ]
    for ident, c in sorted(state["cycles"].items(), reverse=True):
        lines += [
            f"## {ident}: {c['stage']}",
            "",
            f"Adoption: {c.get('assessment', {}).get('selected', 'pending')}; "
            f"reasons: {c.get('assessment', {}).get('reasons', [])}.",
        ]
        if c.get("report"):
            for r in c["report"].get("runs", []):
                lines.append(
                    f"{r['variant']}: {r['closed_trades']} completed trades; "
                    f"net {r['net_return'] * 100:.6f}%; "
                    f"drawdown {r['max_drawdown'] * 100:.6f}%."
                )
        for phase in ["review", "test"]:
            row = state["charges"].get(ident + "/" + phase)
            if row:
                lines.append(f"{phase}: USD{row['cost'] / 1e9:.9f}; settled={row['settled']}.")
        lines += [""]
    lines += [
        "USD inference costs are separate from simulated USDT trading profit.",
        "Adoption requires10closed trades per AI arm, positive return, >=0.10pp above",
        "incumbent/frozen/baseline, non-worse drawdown and <10%, and verified receipts.",
        "Missing, tied, incomplete or uncertain evidence preserves the incumbent.",
    ]
    return "\n".join(lines) + "\n"


def save(
    state: dict[str, Any],
    revision: str,
    key: bytes,
    now: datetime,
    *,
    artifacts: dict[str, str] | None = None,
    deadline: int | None = None,
) -> str:
    validate_state(state, config())
    return write(
        revision,
        {
            STATE: seal(state, key, "research-loop-state"),
            REPORT: summary(state, now),
            **(artifacts or {}),
        },
        deadline=deadline,
    )


def bootstrap(root: Path, key: bytes, meta: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Authenticate the one-shot outcome and incumbent without any paid request."""
    from deploy.research.followup_private import RESULT
    from deploy.research.promotion import make_record, validate_record, validate_rule, verify_result
    from deploy.research.promotion_store import ACTIVE, DECISION, read_snapshot
    from src.agents.lessons import LessonPack

    files, _, _ = read_snapshot([RESULT, ACTIVE, DECISION])
    if RESULT not in files or DECISION not in files:
        raise ValueError("Original fresh comparison/selection is not terminal; wait safely")
    receipt = unpack(decrypt(base64.b64decode(files[RESULT]), key, "fresh-result"), root / "peek")
    evidence = verify_result(root, key, meta, run_id=receipt["github_run_id"])
    recorded = open_value(files[DECISION], key, "research-selection")
    expected = make_record(
        evidence, validate_rule(), now=datetime.fromtimestamp(recorded["available_at"], UTC)
    )
    if recorded != expected:
        # Result publication precedes decision publication; retain its original revision.
        expected["private_revision"] = recorded["private_revision"]
        if recorded != expected:
            raise ValueError("Original selection decision does not reproduce")
    parent = asdict(LessonPack.load(root / "runtime" / WORKSPACE, "pilot-jev-1"))
    active = validate_record(recorded, parent, validate_rule(), now=now)
    if recorded["assessment"]["selected"] == "candidate":
        if files.get(ACTIVE) != files[DECISION]:
            raise ValueError("Original approved selection pointer differs")
    elif ACTIVE in files:
        raise ValueError("Unexpected active selection")
    return {
        "original": parent,
        "active": active,
        "evidence": {
            "report": evidence["report"],
            "cutoff": receipt["frozen"]["protocol"]["end"]
            if "protocol" in receipt["frozen"]
            else int(datetime(2026, 10, 31, tzinfo=UTC).timestamp()),
            "sha256": evidence["evidence_sha256"],
        },
    }


def review(
    state: dict[str, Any],
    revision: str,
    key: bytes,
    root: Path,
    p: dict[str, Any],
    now: datetime,
    clock: Callable[[], datetime],
) -> str:
    from deploy.research.loop_budget import PhaseBudget, allocate, settle
    from deploy.research.loop_client import LoopClient, price_proof
    from src.agents.budget import Budget
    from src.agents.responses import ResponseStore

    if clock().timestamp() >= p["start"] - 120:
        return "missed_freeze_wait_next_week"
    proof = price_proof(clock=clock)
    ident = allocate(state, p["id"], "review", now)
    cycle: dict[str, Any] = {
        "protocol": p,
        "stage": "review_claimed",
        "incumbent": copy.deepcopy(state["active"]),
        "source_evidence": state["evidence"]["sha256"],
    }
    state["cycles"][p["id"]] = cycle
    revision = save(state, revision, key, now, deadline=p["start"])
    # No paid work before the durable claim has returned successfully.
    Budget.initialize(root / "phase.sqlite")
    budget = PhaseBudget(
        root / "phase.sqlite", "review", now.strftime("%Y-%m"), p["start"], clock=clock
    )
    evidence = findings(state["evidence"]["report"])
    context = encoded(
        {"incumbent": cycle["incumbent"]["payload"], "findings": evidence, "limitations": LIMITS}
    ).decode()
    if len(context.encode()) > 18_000:
        raise ValueError("Review exceeds context bound; reservation retained")
    choice = None
    store = ResponseStore(root / "review.responses.sqlite")
    try:
        runs = evidence["runs"]
        if (
            evidence["status"] == "complete"
            and len(runs) == 4
            and all(r["closed_trades"] >= 10 for r in runs[1:])
        ):
            client = LoopClient(os.environ["TYPESAFE_API_KEY"], budget, proof=proof, clock=clock)
            choice = store.choose("review", context, INSTRUCTIONS, OPTIONS, client, 1)
    finally:
        store.close()
    completed = clock()
    if completed.timestamp() >= p["start"] - 120:
        raise ValueError("Review finished after freeze deadline; reservation retained")
    candidate = lesson(
        state["original"],
        evidence,
        choice,
        p["id"],
        math.ceil(completed.timestamp()),
        state["evidence"]["cutoff"],
    )
    if (
        max(
            candidate["available_at"],
            candidate["training_cutoff"],
            cycle["incumbent"]["available_at"],
            cycle["incumbent"]["training_cutoff"],
        )
        >= p["start"]
    ):
        raise ValueError("Lesson information is not earlier than validation")
    cycle.update(
        stage="frozen",
        candidate=candidate,
        review_choice=asdict(choice) if choice else None,
        review_price=proof,
        review_usage=budget.usage(),
    )
    frozen = copy.deepcopy(cycle)
    frozen["review_responses"] = base64.b64encode(
        (root / "review.responses.sqlite").read_bytes()
    ).decode()
    frozen["review_budget"] = base64.b64encode((root / "phase.sqlite").read_bytes()).decode()
    settle(state, ident, budget.usage())
    save(
        state,
        revision,
        key,
        completed,
        artifacts={artifact(p, "frozen"): seal(frozen, key, "research-loop-freeze")},
        deadline=p["start"],
    )
    return "candidate_frozen_before_fresh_data"


def artifact(p: dict[str, Any], kind: str) -> str:
    return f"loop-v1/cycles/{p['id']}/{kind}.enc.base64"


class CachedOnly:
    def choose(self, *args: Any) -> Any:
        raise ValueError("Verification cannot make provider calls")


def verify_cycle(
    outcome: Path, frozen: dict[str, Any], p: dict[str, Any], receipt: dict[str, Any]
) -> None:
    from deploy.research.loop_budget import PhaseBudget
    from deploy.research.loop_replay import run_variants, verify_data
    from src.agents.lessons import LessonPack

    if receipt["frozen"] != frozen or receipt["protocol"] != p:
        raise ValueError("Recurring result identity differs")
    usage = PhaseBudget(outcome / "budget.sqlite", "test", receipt["month"], p["deadline"]).usage()
    if usage != receipt["usage"] or usage["pending_calls"]:
        raise ValueError("Unknown recurring result costs")
    rebuilt = run_variants(
        outcome / "study",
        LessonPack(**frozen["incumbent"]),
        LessonPack(**frozen["candidate"]),
        CachedOnly(),
        verify_data(outcome / "study", p),
        verify_only=True,
        protocol=p,
    )
    if rebuilt != receipt["report"]:
        raise ValueError("Recurring result does not reproduce")


def evaluate(
    state: dict[str, Any],
    revision: str,
    key: bytes,
    root: Path,
    p: dict[str, Any],
    now: datetime,
    clock: Callable[[], datetime],
) -> str:
    from deploy.research.loop_budget import PhaseBudget, allocate, settle
    from deploy.research.loop_client import LoopClient, price_proof
    from deploy.research.loop_replay import acquire, run_variants
    from deploy.research.promotion import assess
    from src.agents.budget import Budget
    from src.agents.lessons import LessonPack

    files, fetched_revision, times = read([STATE, artifact(p, "frozen")])
    if fetched_revision != revision or times[artifact(p, "frozen")] >= p["start"]:
        raise ValueError("Private snapshot changed or candidate freeze was late")
    frozen = open_value(files[artifact(p, "frozen")], key, "research-loop-freeze")
    cycle = state["cycles"][p["id"]]
    if {k: v for k, v in frozen.items() if not k.startswith("review_")} != {
        k: v for k, v in cycle.items() if not k.startswith("review_")
    }:
        raise ValueError("Frozen candidate differs from current cycle")
    study = root / "study"
    study.mkdir()
    bars = acquire(study, p)  # Public data failures do not spend an allocation.
    proof = price_proof(clock=clock)
    actual = clock()
    if not p["ready"] <= actual.timestamp() < p["deadline"] - 120:
        raise ValueError("Test execution window passed")
    ident = allocate(state, p["id"], "test", actual)
    cycle["stage"] = "test_claimed"
    revision = save(state, revision, key, actual)
    Budget.initialize(root / "budget.sqlite")
    budget = PhaseBudget(
        root / "budget.sqlite", "test", actual.strftime("%Y-%m"), p["deadline"], clock=clock
    )
    client = LoopClient(os.environ["TYPESAFE_API_KEY"], budget, proof=proof, clock=clock)
    report = run_variants(
        study,
        LessonPack(**frozen["incumbent"]),
        LessonPack(**frozen["candidate"]),
        client,
        bars,
        protocol=p,
    )
    receipt = {
        "protocol": p,
        "frozen": frozen,
        "report": report,
        "usage": budget.usage(),
        "month": actual.strftime("%Y-%m"),
        "price": proof,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    }
    verify_cycle(root, frozen, p, receipt)
    assessment = assess(report, budget.usage())
    if frozen["review_choice"] is None or frozen["review_choice"]["choice"] == "inconclusive":
        assessment = {
            "selected": "original",
            "reasons": ["review_abstained", *assessment["reasons"]],
        }
    completed = clock()
    if completed.timestamp() >= p["deadline"]:
        raise ValueError("Test missed terminal publication window")
    if assessment["selected"] == "candidate":
        adopted = copy.deepcopy(frozen["candidate"])
        adopted.update(available_at=math.ceil(completed.timestamp()), training_cutoff=p["ready"])
        state["active"] = adopted
    cycle.update(stage="complete", assessment=assessment, report=report, usage=budget.usage())
    receipt["assessment"] = assessment
    data = encrypt(
        archive(
            {
                str(f.relative_to(root)): f.read_bytes()
                for f in root.rglob("*")
                if f.is_file() and (f.is_relative_to(study) or f == root / "budget.sqlite")
            },
            receipt,
        ),
        key,
        "research-loop-result",
    )
    state["evidence"] = {
        "report": report,
        "cutoff": p["ready"],
        "sha256": hash_bytes(data),
        "cycle": p["id"],
    }
    settle(state, ident, budget.usage())
    save(
        state,
        revision,
        key,
        completed,
        artifacts={artifact(p, "result"): base64.b64encode(data).decode() + "\n"},
    )
    return "fresh_test_complete_" + str(assessment["selected"])


def tick(
    state: dict[str, Any],
    revision: str,
    key: bytes,
    root: Path,
    meta: dict[str, Any],
    *,
    now: datetime,
    clock: Callable[[], datetime] | None = None,
) -> str:
    validate_state(state, config())
    clock = clock or (lambda: datetime.now(UTC))
    if now < FIRST:
        return "waiting_for_first_review"
    p = window(now)
    cycle = state["cycles"].get(p["id"])
    if cycle:
        if cycle["stage"] == "frozen" and p["ready"] <= now.timestamp() < p["deadline"] - 120:
            return evaluate(state, revision, key, root, p, now, clock)
        return "waiting_or_phase_already_claimed_no_retry"
    if not p["review"] <= now.timestamp() < p["start"] - 120:
        return "missed_freeze_wait_next_week"
    if "active" not in state:
        state.update(bootstrap(root, key, meta, now))
        revision = save(state, revision, key, now)
    elif state.get("evidence", {}).get("cycle"):
        # Each subsequent review re-authenticates and fully rebuilds its source result.
        prior = state["cycles"][state["evidence"]["cycle"]]["protocol"]
        paths, _, times = read([artifact(prior, "result"), artifact(prior, "frozen")])
        if times[artifact(prior, "frozen")] >= prior["start"]:
            raise ValueError("Previous freeze was late")
        sealed = base64.b64decode(paths[artifact(prior, "result")])
        if hash_bytes(sealed) != state["evidence"]["sha256"]:
            raise ValueError("Previous evidence identity differs")
        receipt = unpack(decrypt(sealed, key, "research-loop-result"), root / "previous")
        frozen = open_value(paths[artifact(prior, "frozen")], key, "research-loop-freeze")
        verify_cycle(root / "previous", frozen, prior, receipt)
        if receipt["report"] != state["evidence"]["report"]:
            raise ValueError("Previous findings differ")
    return review(state, revision, key, root, p, now, clock)


def hosted(mode: str, directory: Path, funding: Path, key: bytes) -> str:
    from deploy.research.followup import restore_inputs

    p = config()
    with tempfile.TemporaryDirectory(prefix="jev-recurring-") as temporary:
        root = Path(temporary)
        _, meta = restore_inputs(directory, funding, key, root)
        files, revision, _ = read([STATE])
        if mode == "verify":
            if STATE in files:
                validate_state(open_value(files[STATE], key, "research-loop-state"), p)
            write(
                revision,
                {
                    CHECK: "Recurring transport verified. No inference, market data, "
                    "phase claim, budget mutation or lesson adoption.\n"
                },
            )
            return "recurring_transport_verified"
        if STATE not in files:
            raise ValueError("Remote authority is not initialized; no automatic budget creation")
        state = open_value(files[STATE], key, "research-loop-state")
        return tick(state, revision, key, root, meta, now=datetime.now(UTC))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify", "tick"])
    parser.add_argument("--directory", type=Path, default=Path("deploy/research/frozen-week"))
    parser.add_argument("--funding", type=Path, default=Path("deploy/research/fresh-week"))
    args = parser.parse_args()
    try:
        print(
            hosted(
                args.mode,
                args.directory,
                args.funding,
                base64.b64decode(os.environ["JEV_RESEARCH_ENVELOPE_KEY"], validate=True),
            )
        )
    except Exception:
        # Raw private data and credentials must never reach public Actions logs.
        parser.exit(
            1, "Recurring research stopped safely; inspect private state and retained holds.\n"
        )


if __name__ == "__main__":
    main()
