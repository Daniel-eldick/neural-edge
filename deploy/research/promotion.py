"""Deterministic adoption for future research only; no inference or budget mutation."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from deploy.research.cloud import WORKSPACE, decrypt, encrypt, hash_bytes, unpack
from deploy.research.followup import READY, RUN_AT, START, frozen_payload, restore_inputs
from deploy.research.followup import source_hash as fresh_hash
from deploy.research.followup_private import FROZEN, RESULT
from deploy.research.learning import encoded
from deploy.research.promotion_store import (
    ACTIVE,
    DECISION,
    publish_check,
    publish_selection,
    read_snapshot,
)

if TYPE_CHECKING:
    from collections.abc import Callable

PARENT_PACK_SHA256 = "03db9ec0de9ef5b7a41412477b809065a687cb16cc9b49b59fd643008062d661"
RULE: dict[str, Any] = {
    "version": "fresh-adoption-v1",
    "scope": "future_bounded_research_context_only",
    "minimum_closed_per_ai_variant": 10,
    "minimum_return_margin": 0.001,
    "controls": ["original", "frozen", "baseline"],
    "positive_net_trading_profit": True,
    "drawdown_not_worse_than": ["original", "frozen"],
    "maximum_drawdown_exclusive": 0.10,
    "require_complete_verified_replay": True,
    "maximum_verified_inference_nano_usd": 432_000_000,
    "uncertain_usage_allowed": False,
    "new_paid_calls": 0,
}
CONFIG = Path(__file__).with_name("promotion-rule") / "runner.json"


def source_hash() -> str:
    return hash_bytes(
        encoded(
            {
                "fresh_source": fresh_hash(),
                **{
                    name: hash_bytes(Path(__file__).with_name(name).read_bytes())
                    for name in ["promotion.py", "promotion_store.py", "research_policy.py"]
                },
            }
        )
    )


def rule_config(declared_at: int) -> dict[str, Any]:
    if type(declared_at) is not int or not 0 < declared_at < START:
        raise ValueError("Declare adoption rule before fresh data")
    return {
        "schema": 1,
        "declared_at": declared_at,
        "rule": RULE,
        "source_sha256": source_hash(),
        "parent_pack_sha256": PARENT_PACK_SHA256,
    }


def validate_rule(path: Path | None = None) -> dict[str, Any]:
    value = json.loads((path or CONFIG).read_bytes())
    if value != rule_config(value["declared_at"]):
        raise ValueError("Predeclared selection source/rules changed")
    return dict(value)


def number(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Nonfinite or invalid result")
    return Decimal(str(value))


def count(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Invalid coverage counter")
    return value


def assess(report: dict[str, Any], usage: dict[str, int]) -> dict[str, Any]:
    reasons = []
    if report.get("status") != "complete":
        return {"selected": "original", "reasons": ["fresh_comparison_incomplete"]}
    try:
        runs = report["runs"]
        if [r["variant"] for r in runs] != ["baseline", "frozen", "original", "candidate"]:
            raise ValueError("Incomplete arms")
        by = {r["variant"]: r for r in runs}
        for r in runs:
            if count(r["open_positions"]) or count(r["policy_errors"]):
                reasons.append("open_position_or_policy_error")
            count(r["closed_trades"])
            count(r["model_choices"])
            if r["variant"] != "baseline" and r["model_choices"] > 48:
                raise ValueError("Coverage cap exceeded")
            for field in ["net_return", "net_profit_usdt", "max_drawdown", "inference_cost_usd"]:
                number(r[field])
            if number(r["inference_cost_usd"]) < 0:
                raise ValueError("Negative provider cost")
            if not 0 <= number(r["max_drawdown"]) <= 1:
                raise ValueError("Invalid drawdown")
        if any(count(r["closed_trades"]) < 10 for r in runs[1:]):
            reasons.append("insufficient_completed_trades")
        c = by["candidate"]
        if number(c["net_profit_usdt"]) <= 0 or number(c["net_return"]) <= 0:
            reasons.append("candidate_not_profitable")
        if any(
            number(c["net_return"]) - number(by[v]["net_return"]) < Decimal("0.001")
            for v in RULE["controls"]
        ):
            reasons.append("return_margin_not_met")
        if number(c["max_drawdown"]) >= Decimal("0.10") or any(
            number(c["max_drawdown"]) > number(by[v]["max_drawdown"])
            for v in ["original", "frozen"]
        ):
            reasons.append("drawdown_not_acceptable")
        for key in [
            "attempts",
            "pending_calls",
            "settled_nano_usd",
            "accounted_nano_usd",
            "input_tokens",
        ]:
            count(usage[key])
        cost = sum(round(float(r["inference_cost_usd"]) * 1e9) for r in runs)
        if (
            usage["pending_calls"]
            or usage["settled_nano_usd"] != usage["accounted_nano_usd"]
            or usage["settled_nano_usd"] > 432_000_000
            or cost != usage["settled_nano_usd"]
            or sum(r["model_choices"] for r in runs) != usage["attempts"]
            or usage["attempts"] > 144
            or usage["input_tokens"] * 42 != usage["settled_nano_usd"]
        ):
            reasons.append("unknown_or_inconsistent_costs")
    except (KeyError, TypeError, ValueError, OverflowError):
        reasons.append("invalid_comparison_metrics")
    return {"selected": "original" if reasons else "candidate", "reasons": sorted(set(reasons))}


def candidate_pack(
    parent: dict[str, Any], frozen: dict[str, Any], *, available_at: int, validated: bool
) -> dict[str, Any]:
    c = frozen["binding"]["candidate"]
    return {
        "sha256": frozen["candidate_sha256"],
        "available_at": available_at,
        "training_cutoff": max(READY, c["training_cutoff"]) if validated else c["training_cutoff"],
        "payload": {
            "status": "candidate_only",
            "original_candidate": parent["payload"],
            "post_test_review": c["context"],
            "meaning": (
                "Unproven post-test context, no risk override or permission; "
                "evaluated only on later data."
            ),
        },
    }


def verify_result(root: Path, key: bytes, meta: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    from deploy.research.followup_budget import FollowupBudget
    from deploy.research.followup_replay import run_variants, verify_data
    from src.agents.lessons import LessonPack

    files, revision, times = read_snapshot([FROZEN, RESULT, DECISION, ACTIVE])
    if FROZEN not in files or RESULT not in files or times[FROZEN] >= START:
        raise ValueError("Missing or late fresh evidence")
    frozen = frozen_payload(files[FROZEN], key, meta, root)
    sealed = base64.b64decode(files[RESULT])
    receipt = unpack(decrypt(sealed, key, "fresh-result"), root / "outcome")
    if (
        receipt["allocation"] != meta
        or receipt["frozen"] != frozen
        or receipt["github_run_id"] != run_id
    ):
        raise ValueError("Fresh result identities differ")
    budget = FollowupBudget(root / "outcome/budget.sqlite", meta)
    usage = budget.usage()
    if usage != receipt["usage"]:
        raise ValueError("Fresh usage differs")
    parent = asdict(LessonPack.load(root / "runtime" / WORKSPACE, "pilot-jev-1"))
    if parent["sha256"] != frozen["parent_sha256"]:
        raise ValueError("Fresh parent lesson differs")
    report = receipt["report"]
    if report["status"] == "complete":
        if frozen["status"] != "ready":
            raise ValueError("Complete test lacks usable candidate")
        pack = LessonPack(
            **candidate_pack(
                parent, frozen, available_at=frozen["binding"]["saved_at"], validated=False
            )
        )

        class CachedOnly:
            def choose(self, *args: Any) -> Any:
                raise ValueError("Adoption cannot invoke provider")

        rebuilt = run_variants(
            root / "outcome/study",
            LessonPack(**parent),
            pack,
            CachedOnly(),
            verify_data(root / "outcome/study"),
            verify_only=True,
        )
        if rebuilt != report:
            raise ValueError("Fresh replay does not reproduce")
    elif report["status"] == "skipped":
        if frozen["status"] != "skipped_inconclusive_candidate" or usage["attempts"]:
            raise ValueError("Skipped result has paid usage")
    elif report["status"] != "failed":
        raise ValueError("Fresh result is not terminal")
    return {
        "report": report,
        "usage": usage,
        "frozen": frozen,
        "parent": parent,
        "fresh_run_id": run_id,
        "evidence_sha256": hash_bytes(sealed),
        "private_revision": revision,
        "existing": {k: v for k, v in files.items() if k in {DECISION, ACTIVE}},
    }


def make_record(
    evidence: dict[str, Any], config: dict[str, Any], *, now: datetime
) -> dict[str, Any]:
    if now.tzinfo is None or now.timestamp() < RUN_AT:
        raise ValueError("No adoption before fresh validation finishes")
    assessment = assess(evidence["report"], evidence["usage"])
    stamp = int(now.timestamp())
    return {
        "schema": 1,
        "rule_config": json.loads(encoded(config)),
        "assessment": assessment,
        "available_at": stamp,
        "parent": evidence["parent"],
        "candidate_pack": candidate_pack(
            evidence["parent"], evidence["frozen"], available_at=stamp, validated=True
        )
        if assessment["selected"] == "candidate"
        else None,
        **{
            k: evidence[k]
            for k in [
                "report",
                "usage",
                "frozen",
                "fresh_run_id",
                "evidence_sha256",
                "private_revision",
            ]
        },
    }


def validate_record(
    record: dict[str, Any], parent: dict[str, Any], config: dict[str, Any], *, now: datetime
) -> dict[str, Any]:
    from deploy.research.followup import validate_frozen

    if (
        hash_bytes(encoded(parent)) != config["parent_pack_sha256"]
        or record["schema"] != 1
        or record["rule_config"] != config
        or record["parent"] != parent
        or type(record["available_at"]) is not int
        or not RUN_AT <= record["available_at"] <= now.timestamp()
        or record["assessment"] != assess(record["report"], record["usage"])
    ):
        raise ValueError("Active research selection identity/time/rules differ")
    validate_frozen(record["frozen"])
    if record["frozen"]["parent_sha256"] != parent["sha256"]:
        raise ValueError("Active parent differs")
    if record["assessment"]["selected"] == "candidate":
        expected = candidate_pack(
            parent, record["frozen"], available_at=record["available_at"], validated=True
        )
        if record["candidate_pack"] != expected:
            raise ValueError("Active payload differs from tested context")
        return expected
    if record["candidate_pack"] is not None:
        raise ValueError("Retained lesson includes unapproved context")
    return parent


def render(record: dict[str, Any]) -> str:
    a = record["assessment"]
    lines = [
        "# Automatic research lesson selection",
        "",
        (
            "Candidate selected for future research."
            if a["selected"] == "candidate"
            else "Original lesson retained."
        ),
        "",
        "This is a provisional pilot decision; repeatable improvement is unproven.",
        "No real trading, model-weight update or new paid research run is activated.",
        "",
        f"Reasons: {', '.join(a['reasons']) or 'all predeclared checks passed'}.",
        (
            "Rule:10completed trades per Jev arm; candidate profitable; >=0.10pp above "
            "original/frozen/baseline; no worse drawdown than original/frozen and <10%; "
            "verified complete evidence and costs."
        ),
        "",
        (
            "Actual adoption inference cost: USD0 (no provider request). Fresh-test settled "
            f"inference: USD{record['usage']['settled_nano_usd'] / 1e9:.9f}; "
            f"pending calls:{record['usage']['pending_calls']}."
        ),
        "Original budget/holds remain untouched; collection handles accounting independently.",
        "USD provider cost is separate from simulated USDT profit.",
        "",
    ]
    for r in record["report"].get("runs", []):
        lines.append(
            f"{r['variant']}: {r['closed_trades']} completed; "
            f"net return {r['net_return'] * 100:.6f}%; net USDT {r['net_profit_usdt']:.6f}; "
            f"drawdown {r['max_drawdown'] * 100:.6f}%."
        )
    return "\n".join(lines) + "\n"


def hosted(
    mode: str,
    directory: Path,
    funding: Path,
    key: bytes,
    *,
    now: datetime,
    clock: Callable[[], datetime] | None = None,
) -> str:
    config = validate_rule()
    moment = clock or (lambda: datetime.now(UTC))
    with tempfile.TemporaryDirectory(prefix="jev-adoption-") as temporary:
        root = Path(temporary).resolve()
        _, meta = restore_inputs(directory, funding, key, root)
        if mode == "verify" or now.timestamp() < RUN_AT:
            publish_check(
                "# Research selection connection check\n\nRules, runtime and private delivery "
                "verified. No active selection, test-result read, paid request or budget change.\n"
            )
            return "selection_verified_no_change"
        evidence = verify_result(root, key, meta, run_id=os.environ["GITHUB_RUN_ID"])
        if DECISION in evidence["existing"]:
            record = json.loads(
                decrypt(base64.b64decode(evidence["existing"][DECISION]), key, "research-selection")
            )
            validate_record(record, evidence["parent"], config, now=moment())
            if (
                record["evidence_sha256"] != evidence["evidence_sha256"]
                or record["fresh_run_id"] != evidence["fresh_run_id"]
            ):
                raise ValueError("Existing decision refers to different validation")
            if (
                record["assessment"]["selected"] == "candidate"
                and evidence["existing"].get(ACTIVE) != evidence["existing"][DECISION]
            ):
                raise ValueError("Active pointer differs from approved decision")
            return "selection_already_recorded"
        record = make_record(evidence, config, now=moment())
        validate_record(record, evidence["parent"], config, now=moment())
        sealed = (
            base64.b64encode(encrypt(encoded(record), key, "research-selection")).decode() + "\n"
        )
        publish_selection(
            sealed, render(record), approved=record["assessment"]["selected"] == "candidate"
        )
        return (
            "research_candidate_selected"
            if record["assessment"]["selected"] == "candidate"
            else "original_lesson_retained"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify", "run"])
    parser.add_argument("--directory", type=Path, default=Path("deploy/research/frozen-week"))
    parser.add_argument("--funding", type=Path, required=True)
    args = parser.parse_args()
    try:
        key = base64.b64decode(os.environ["JEV_RESEARCH_ENVELOPE_KEY"], validate=True)
        print(hosted(args.mode, args.directory, args.funding, key, now=datetime.now(UTC)))
    except Exception:
        parser.exit(
            1,
            "Research selection unavailable; preserve prior lesson, evidence and "
            "budget. No paid retry.\n",
        )


if __name__ == "__main__":
    main()
