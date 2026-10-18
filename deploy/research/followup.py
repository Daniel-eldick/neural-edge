"""One predeclared fresh replay; no recursive learner or automatic promotion."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from deploy.research.cloud import (
    CODE_SHA,
    EXPIRY,
    REPO,
    STUDY,
    WORKSPACE,
    archive,
    decrypt,
    encrypt,
    git_api,
    hash_bytes,
    restore,
    unpack,
)
from deploy.research.followup_private import CANDIDATE, CHECK, FROZEN, LEARNING, REPORT, RESULT
from deploy.research.followup_private import read as private_read
from deploy.research.followup_private import write as private_write
from deploy.research.learning import encoded as encoded
from deploy.research.learning import source_hash as learning_hash

START = int(datetime(2026, 10, 26, tzinfo=UTC).timestamp())
END = int(datetime(2026, 10, 30, tzinfo=UTC).timestamp())
READY = int(datetime(2026, 10, 31, tzinfo=UTC).timestamp())
RUN_AT = READY + 6 * 3600 + 30 * 60
CLAIM = "research/lesson-fresh-v1-claimed"
VERSION = "lesson-fresh-v1"
OPERATOR = Path("user_data/research/lesson-week-cloud-v2-approved")
FUNDING = Path("user_data/research/lesson-fresh-v1")


def source_hash() -> str:
    return hash_bytes(
        encoded(
            {
                "learning_source": learning_hash(),
                **{
                    name: hash_bytes(Path(__file__).with_name(name).read_bytes())
                    for name in [
                        "followup.py",
                        "followup_budget.py",
                        "followup_private.py",
                        "followup_replay.py",
                    ]
                },
            }
        )
    )


def protocol(declared: int) -> dict[str, Any]:
    if (
        type(declared) is not int
        or not int(datetime(2026, 10, 18, tzinfo=UTC).timestamp()) <= declared < START
    ):
        raise ValueError("Declare fresh dates before entry starts")
    return {
        "schema": 1,
        "study": VERSION,
        "declared_at": declared,
        "entry_start": START,
        "entry_end": END,
        "end": READY,
        "expiry": EXPIRY,
        "source_sha256": source_hash(),
        "max_attempts_per_ai_variant": 48,
        "cap_nano_usd": 432_000_000,
        "order": ["baseline", "frozen", "original", "candidate"],
        "sampling": "first_20_bar_breakout_per_symbol_per_6h_slot_no_replacement",
        "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        "model": "jev-1.13.0",
        "minimum_closed_per_ai_variant": 10,
        "promotion_allowed": False,
        "primary": "candidate_minus_original_completed_return_after_trading_costs",
    }


def prepare(funding: Path, directory: Path, *, now: datetime) -> dict[str, Any]:
    from deploy.research.followup_budget import export
    from src.agents.budget import Budget
    from src.agents.jev import LEDGER

    if funding.exists():
        raise ValueError("Fresh preparation exists")
    p = protocol(int(now.timestamp()))
    replay = json.loads((directory / "allocation.json").read_bytes())
    learning_dir = directory.parent / "lesson-week-learning-v1"
    learned = json.loads((learning_dir / "allocation.json").read_bytes())
    funding.mkdir(mode=0o700)
    meta = export(
        Budget(LEDGER),
        funding / "budget.sqlite",
        {replay["escrow_id"], learned["escrow_id"]},
        now=now,
    )
    meta.update(
        protocol=p,
        replay_input_sha256=hash_bytes((directory / "input.enc").read_bytes()),
        learning_input_sha256=hash_bytes((learning_dir / "input.enc").read_bytes()),
    )
    sealed = encrypt(
        archive({"budget.sqlite": (funding / "budget.sqlite").read_bytes()}, meta),
        (directory / "envelope.key").read_bytes(),
        "fresh-input",
    )
    config = {"protocol": p, "input_sha256": hash_bytes(sealed)}
    for name, data in [
        ("allocation.json", encoded(meta)),
        ("input.enc", sealed),
        ("runner.json", encoded(config)),
    ]:
        (funding / name).write_bytes(data)
        (funding / name).chmod(0o600)
    return config


def restore_inputs(
    directory: Path, funding: Path, key: bytes, root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    original = restore(directory / "runner.json", directory / "input.enc", key, root / "runtime")
    sys.path.insert(0, str(root / "runtime"))
    config = json.loads((funding / "runner.json").read_bytes())
    p = config["protocol"]
    sealed = (funding / "input.enc").read_bytes()
    if p != protocol(p["declared_at"]) or hash_bytes(sealed) != config["input_sha256"]:
        raise ValueError("Fresh source or funding differs")
    meta = unpack(decrypt(sealed, key, "fresh-input"), root / "funding")
    if meta["protocol"] != p or meta["replay_input_sha256"] != hash_bytes(
        (directory / "input.enc").read_bytes()
    ):
        raise ValueError("Fresh allocation or replay differs")
    from deploy.research.followup_budget import FollowupBudget

    FollowupBudget(root / "funding/budget.sqlite", meta)
    return original, meta


def bind_candidate(
    candidate: dict[str, Any], saved_at: int, *, now: datetime
) -> dict[str, Any] | None:
    if (
        candidate["review_status"] != "jev_reviewed"
        or candidate.get("context", {}).get("stance") == "inconclusive"
    ):
        return None
    if (
        not candidate["training_cutoff"] < START
        or not candidate["available_at"] <= saved_at <= now.timestamp() < START
    ):
        raise ValueError("Candidate saved too late for predeclared fresh data")
    return {"candidate": candidate, "saved_at": saved_at, "frozen_at": int(now.timestamp())}


def authenticate_candidate(
    directory: Path,
    key: bytes,
    root: Path,
    original: dict[str, Any],
    meta: dict[str, Any],
    *,
    now: datetime,
) -> dict[str, Any]:
    from deploy.research.learning import load_funding, make_candidate
    from deploy.research.learning_budget import LearningBudget
    from deploy.research.summary import download_result, validate_outcome
    from src.agents.lessons import LessonPack
    from src.agents.responses import ResponseStore

    funding = directory.parent / "learning-week"
    # Local operator uses the named ignored preparation instead of the public layout.
    if not funding.exists():
        funding = directory.parent / "lesson-week-learning-v1"
    lm = load_funding(funding, key, root / "learning-funding")
    if (
        hash_bytes((funding / "input.enc").read_bytes()) != meta["learning_input_sha256"]
        or lm["replay_escrow_id"] != original["escrow_id"]
    ):
        raise ValueError("Wrong original learning allocation")
    files, revision, saved_at = private_read([CANDIDATE, LEARNING])
    if set(files) != {CANDIDATE, LEARNING}:
        raise ValueError("Saved private candidate or receipt unavailable")
    candidate = json.loads(files[CANDIDATE])
    receipt = unpack(
        decrypt(base64.b64decode(files[LEARNING], validate=False), key, "learning-result"),
        root / "learning-outcome",
    )
    evidence = root / "learning-outcome"
    if (
        receipt != json.loads((evidence / "receipt.json").read_bytes())
        or receipt["allocation"] != lm
        or receipt["status"] != "complete"
        or encoded(candidate) != (evidence / "candidate.json").read_bytes()
    ):
        raise ValueError("Candidate receipt identity differs")
    usage = LearningBudget(evidence / "execution-budget.sqlite", lm).usage()
    if (
        receipt["usage"] != usage
        or usage["pending_calls"]
        or usage["settled_nano_usd"] != candidate["research_cost_nano_usd"]
        or receipt["source_run_id"] != candidate["source_run_id"]
    ):
        raise ValueError("Candidate usage is uncertain or inconsistent")
    result = root / "original-result.enc"
    if not download_result(result):
        raise ValueError("Original comparison result unavailable")
    report, _, _ = validate_outcome(
        result,
        key,
        original,
        (root / "runtime" / STUDY / "protocol.json").read_bytes(),
        candidate["source_run_id"],
        root / "original-result",
    )
    parent = LessonPack.load(root / "runtime" / WORKSPACE, "pilot-jev-1")

    class Cached:
        def choose(self, *args: Any) -> Any:
            raise ValueError("Freeze must not invoke Jev")

    store = ResponseStore(evidence / "responses.sqlite", resume=True)
    try:
        rebuilt = make_candidate(
            report,
            {"sha256": parent.sha256, "payload": parent.payload},
            Cached(),
            store,
            now=datetime.fromtimestamp(candidate["review_started_at"], UTC),
            clock=lambda: datetime.fromtimestamp(candidate["available_at"], UTC),
            result_sha=hash_bytes(result.read_bytes()),
            run_id=candidate["source_run_id"],
        )
    finally:
        store.close()
    if rebuilt != candidate:
        raise ValueError("Candidate does not reconstruct from original evidence")
    bound = bind_candidate(candidate, saved_at, now=now)
    return {
        "status": "ready" if bound else "skipped_inconclusive_candidate",
        "binding": bound,
        "private_revision": revision,
        "candidate_sha256": hash_bytes(encoded(candidate)),
        "parent_sha256": parent.sha256,
        "protocol": meta["protocol"],
        "allocation_id": meta["escrow_id"],
    }


def claim() -> None:
    git_api(
        "POST",
        f"/repos/{REPO}/git/refs",
        os.environ["GH_TOKEN"],
        {"ref": f"refs/heads/{CLAIM}", "sha": os.environ["GITHUB_SHA"]},
    )


def execute(root: Path, meta: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any]:
    from deploy.research.followup_budget import FollowupBudget
    from deploy.research.followup_replay import acquire, run_variants
    from src.agents.jev import JevClient
    from src.agents.lessons import LessonPack

    parent = LessonPack.load(root / "runtime" / WORKSPACE, "pilot-jev-1")
    if frozen["parent_sha256"] != parent.sha256:
        raise ValueError("Fresh parent lesson differs")
    binding = frozen["binding"]
    candidate = binding["candidate"]
    pack = LessonPack(
        frozen["candidate_sha256"],
        binding["saved_at"],
        candidate["training_cutoff"],
        {
            "status": "candidate_only",
            "original_candidate": parent.payload,
            "post_test_review": candidate["context"],
            "meaning": (
                "Unproven post-test context, no risk override or permission; "
                "evaluated only on later data."
            ),
        },
    )
    study = root / "study"
    study.mkdir()
    client = JevClient(
        os.environ["TYPESAFE_API_KEY"], FollowupBudget(root / "funding/budget.sqlite", meta)
    )
    return run_variants(study, parent, pack, client, acquire(study))


def frozen_payload(text: str, key: bytes, meta: dict[str, Any], root: Path) -> dict[str, Any]:
    value = unpack(decrypt(base64.b64decode(text), key, "fresh-freeze"), root / "frozen")
    if (
        value["protocol"] != meta["protocol"]
        or value["allocation_id"] != meta["escrow_id"]
        or value["status"] not in {"ready", "skipped_inconclusive_candidate"}
    ):
        raise ValueError("Frozen fresh identity differs")
    validate_frozen(value)
    return value


def validate_frozen(value: dict[str, Any]) -> None:
    binding = value.get("binding")
    if value["status"] == "ready":
        if not isinstance(binding, dict):
            raise ValueError("Missing fresh candidate binding")
        candidate = binding["candidate"]
        check = bind_candidate(
            candidate, binding["saved_at"], now=datetime.fromtimestamp(binding["frozen_at"], UTC)
        )
        if (
            check != binding
            or hash_bytes(encoded(candidate)) != value["candidate_sha256"]
            or candidate["parent_lesson_sha256"] != value["parent_sha256"]
        ):
            raise ValueError("Fresh candidate identity or time differs")
    elif binding is not None:
        raise ValueError("Skipped candidate has a usable binding")


def hosted(
    mode: str,
    directory: Path,
    funding: Path,
    key: bytes,
    *,
    now: datetime,
    clock: Callable[[], datetime] | None = None,
) -> str:
    moment = clock or (lambda: datetime.now(UTC))
    with tempfile.TemporaryDirectory(prefix="jev-fresh-") as temporary:
        root = Path(temporary).resolve()
        original, meta = restore_inputs(directory, funding, key, root)
        if mode == "verify" or (mode == "run" and now.timestamp() < RUN_AT):
            private_write(
                {
                    CHECK: (
                        "# Fresh candidate replay connection check\n\n"
                        "Funding and private transport verified. No candidate freeze, market "
                        "request, Jev call or execution claim.\n"
                    )
                }
            )
            return "fresh_verified_waiting_for_data"
        if moment().timestamp() >= EXPIRY:
            raise ValueError("October authorization expired")
        if mode == "freeze":
            if moment().timestamp() >= START - 600:
                raise ValueError("Fresh freeze deadline missed")
            existing, _, published = private_read([FROZEN])
            if FROZEN in existing:
                if published >= START:
                    raise ValueError("Existing freeze was published too late")
                frozen_payload(existing[FROZEN], key, meta, root)
                return "fresh_already_frozen"
            frozen = authenticate_candidate(directory, key, root, original, meta, now=moment())
            if moment().timestamp() >= START - 600:
                raise ValueError("Fresh freeze deadline missed after authentication")
            private_write(
                {
                    FROZEN: base64.b64encode(
                        encrypt(archive({}, frozen), key, "fresh-freeze")
                    ).decode()
                    + "\n"
                },
                deadline=START,
            )
            return (
                "fresh_candidate_bound"
                if frozen["status"] == "ready"
                else "fresh_skipped_inconclusive_candidate"
            )
        from deploy.research.followup_budget import FollowupBudget
        from deploy.research.followup_replay import render

        files, _, saved_at = private_read([FROZEN])
        if saved_at >= START:
            raise ValueError("Fresh candidate seal was published after its data began")
        frozen = frozen_payload(files[FROZEN], key, meta, root)
        budget = FollowupBudget(root / "funding/budget.sqlite", meta)
        report = {
            "status": "skipped",
            "assessment": "No new conclusive candidate; no paid follow-up",
        }
        if frozen["status"] == "ready":
            if not RUN_AT <= moment().timestamp() < EXPIRY:
                raise ValueError("Fresh execution authorization window closed")
            claim()
            report = {"status": "failed", "assessment": "Attempt failed; full uncertainty retained"}
            try:
                report = execute(root, meta, frozen)
            finally:
                save_result(root, meta, frozen, report, key, budget.usage())
        else:
            save_result(root, meta, frozen, report, key, budget.usage())
        private_write({REPORT: render(report, budget.usage())})
        if report["status"] == "failed":
            raise ValueError("Fresh test failed; preserve evidence and hold")
        return "fresh_private_outcome_saved"


def save_result(
    root: Path,
    meta: dict[str, Any],
    frozen: dict[str, Any],
    report: dict[str, Any],
    key: bytes,
    usage: dict[str, int],
) -> None:
    files = (
        {
            str(p.relative_to(root)): p.read_bytes()
            for p in (root / "study").rglob("*")
            if p.is_file() and not p.name.endswith(("-wal", "-shm"))
        }
        if (root / "study").exists()
        else {}
    )
    files["budget.sqlite"] = (root / "funding/budget.sqlite").read_bytes()
    receipt = {
        "allocation": meta,
        "frozen": frozen,
        "report": report,
        "usage": usage,
        "github_run_id": os.environ["GITHUB_RUN_ID"],
    }
    private_write(
        {
            RESULT: base64.b64encode(encrypt(archive(files, receipt), key, "fresh-result")).decode()
            + "\n"
        }
    )


def collect(funding: Path, directory: Path) -> dict[str, Any]:
    from src.evaluation.lesson_week import implementation_hash

    if implementation_hash() != CODE_SHA:
        raise ValueError("Original scientific source changed; no budget reconciliation")
    from deploy.research.followup_budget import FollowupBudget, reconcile
    from deploy.research.followup_replay import run_variants, verify_data
    from src.agents.budget import Budget
    from src.agents.jev import LEDGER
    from src.agents.lessons import LessonPack

    meta = json.loads((funding / "allocation.json").read_bytes())
    key = (directory / "envelope.key").read_bytes()
    with tempfile.TemporaryDirectory(prefix="jev-fresh-collect-") as temporary:
        root = Path(temporary).resolve()
        receipt = unpack(
            decrypt((funding / "result.enc").read_bytes(), key, "fresh-result"), root / "outcome"
        )
        if receipt["allocation"] != meta or meta["protocol"] != protocol(
            meta["protocol"]["declared_at"]
        ):
            raise ValueError("Fresh terminal binding differs")
        usage = FollowupBudget(root / "outcome/budget.sqlite", meta).usage()
        if usage != receipt["usage"]:
            raise ValueError("Fresh terminal usage differs")
        frozen = receipt["frozen"]
        validate_frozen(frozen)
        report = receipt["report"]
        if frozen["protocol"] != meta["protocol"] or frozen["allocation_id"] != meta["escrow_id"]:
            raise ValueError("Fresh candidate allocation differs")
        if report["status"] == "complete":
            restore(directory / "runner.json", directory / "input.enc", key, root / "runtime")
            parent = LessonPack.load(root / "runtime" / WORKSPACE, "pilot-jev-1")
            if parent.sha256 != frozen["parent_sha256"]:
                raise ValueError("Collected parent differs")
            binding = frozen["binding"]
            c = binding["candidate"]
            pack = LessonPack(
                frozen["candidate_sha256"],
                binding["saved_at"],
                c["training_cutoff"],
                {
                    "status": "candidate_only",
                    "original_candidate": parent.payload,
                    "post_test_review": c["context"],
                    "meaning": (
                        "Unproven post-test context, no risk override or permission; "
                        "evaluated only on later data."
                    ),
                },
            )

            class Cached:
                def choose(self, *args: Any) -> Any:
                    raise ValueError("Collector cannot call Jev")

            rebuilt = run_variants(
                root / "outcome/study",
                parent,
                pack,
                Cached(),
                verify_data(root / "outcome/study"),
                verify_only=True,
            )
            cost = sum(round((r["inference_cost_usd"] or 0) * 1e9) for r in rebuilt["runs"])
            if (
                rebuilt != report
                or cost != usage["settled_nano_usd"]
                or usage["pending_calls"]
                or sum(r["model_choices"] for r in rebuilt["runs"]) != usage["attempts"]
            ):
                raise ValueError("Fresh report does not reconstruct from evidence")
        elif report["status"] == "skipped":
            if frozen["status"] != "skipped_inconclusive_candidate" or usage["attempts"]:
                raise ValueError("Skipped follow-up has paid usage")
        elif report["status"] != "failed":
            raise ValueError("No terminal fresh status")
        result = (
            "full_hold_retained_uncertain_usage"
            if usage["pending_calls"]
            else reconcile(Budget(LEDGER), meta, usage)
        )
        unpack(
            decrypt((funding / "result.enc").read_bytes(), key, "fresh-result"),
            funding / "collected",
            reuse=True,
        )
        return {
            "status": result,
            "usage": usage,
            "original_october_budget": Budget(LEDGER).snapshot(
                now=datetime(2026, 10, 31, tzinfo=UTC)
            ),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "verify", "freeze", "run", "collect"])
    parser.add_argument("--directory", type=Path, default=Path("deploy/research/frozen-week"))
    parser.add_argument("--funding", type=Path, required=True)
    args = parser.parse_args()
    try:
        result: Any
        if args.mode == "prepare":
            result = prepare(args.funding, args.directory, now=datetime.now(UTC))
        elif args.mode == "collect":
            result = collect(args.funding, args.directory)
        else:
            result = hosted(
                args.mode,
                args.directory,
                args.funding,
                base64.b64decode(os.environ["JEV_RESEARCH_ENVELOPE_KEY"], validate=True),
                now=datetime.now(UTC),
            )
        print(json.dumps(result, sort_keys=True))
    except Exception:
        parser.exit(1, "Fresh comparison stopped; preserve all holds/evidence. No paid retry.\n")


if __name__ == "__main__":
    main()
