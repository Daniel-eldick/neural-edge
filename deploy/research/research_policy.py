"""Default context selection for future bounded research runs, frozen per checkpoint."""

from __future__ import annotations

import base64
import json
import math
from dataclasses import asdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from deploy.research.cloud import CODE_SHA, decrypt, encrypt, hash_bytes
from deploy.research.learning import encoded
from deploy.research.promotion import validate_record, validate_rule
from deploy.research.promotion_store import ACTIVE, read_snapshot
from src.agents.lessons import LessonPolicy

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.agents.budget import Budget
    from src.agents.lessons import LessonPack
    from src.agents.responses import ResponseStore
    from src.replay.engine import Recorder


class ResearchPolicy(LessonPolicy):
    """Selection snapshot is private/durable; checkpoints carry only its fixed digest."""

    selection_snapshot: str

    def save_state(self) -> dict[str, object]:
        return {
            **super().save_state(),
            "research_selection_sha256": hash_bytes(self.selection_snapshot.encode()),
        }


def make_research_policy(
    parent: LessonPack,
    store: ResponseStore,
    recorder: Recorder,
    *,
    api_key: str,
    budget: Budget,
    key: bytes,
    now: datetime,
    max_attempts: int = 20,
    clock: Callable[[], datetime] | None = None,
    selection_snapshot: str | None = None,
) -> ResearchPolicy:
    """New runs read private selection once; resume reuses its authenticated snapshot."""
    from src.agents.jev import JevClient
    from src.agents.lessons import LessonPack
    from src.evaluation.lesson_week import implementation_hash

    if implementation_hash() != CODE_SHA:
        raise ValueError("Research runtime differs from verified scientific source")
    config = validate_rule()
    parent_sha = hash_bytes(encoded(asdict(parent)))
    config_sha = hash_bytes(encoded(config))
    if parent_sha != config["parent_pack_sha256"]:
        raise ValueError("Research fallback is not the verified original lesson")
    moment = clock or (lambda: datetime.now(UTC))
    if now.tzinfo is None:
        raise ValueError("Research clock must be timezone-aware")
    is_new = selection_snapshot is None
    snapshot: dict[str, Any]
    if selection_snapshot is None:
        files, _, _ = read_snapshot([ACTIVE])
        observed = moment()
        if observed.tzinfo is None:
            raise ValueError("Selection observation clock must be aware")
        snapshot = {
            "schema": 1,
            "parent_sha256": parent_sha,
            "config_sha256": config_sha,
            "selector": files.get(ACTIVE),
            "observed_at": math.ceil(observed.timestamp()),
        }
        selection_snapshot = base64.b64encode(
            encrypt(encoded(snapshot), key, "research-selection-snapshot")
        ).decode()
    else:
        snapshot = json.loads(
            decrypt(base64.b64decode(selection_snapshot), key, "research-selection-snapshot")
        )
        observed = moment()
    if (
        snapshot["schema"] != 1
        or snapshot["parent_sha256"] != parent_sha
        or snapshot["config_sha256"] != config_sha
        or type(snapshot["observed_at"]) is not int
        or snapshot["observed_at"] > math.ceil(observed.timestamp())
    ):
        raise ValueError("Persisted research selection snapshot differs")
    pack = parent
    if snapshot["selector"] is not None:
        record = json.loads(
            decrypt(base64.b64decode(snapshot["selector"]), key, "research-selection")
        )
        selected = validate_record(record, asdict(parent), config, now=observed)
        if (
            record["assessment"]["selected"] != "candidate"
            or snapshot["observed_at"] < record["available_at"]
        ):
            raise ValueError("Active record was not observed after approval")
        # Reading the private pointer is itself an availability boundary. No backdating
        # to the producer's pre-push decision stamp is permitted for a new research run.
        selected = {
            **selected,
            "available_at": max(selected["available_at"], snapshot["observed_at"]),
        }
        pack = LessonPack(**selected)
    if now.timestamp() < parent.available_at:
        raise ValueError("Original research lesson was unavailable")
    if selection_snapshot is None:
        raise ValueError("No durable selection snapshot")
    if is_new:
        recorder.record(
            {
                "kind": "LESSON_SELECTION",
                "time": int(observed.timestamp()),
                "lesson_sha256": pack.sha256,
                "selection_snapshot": selection_snapshot,
            }
        )
    policy = ResearchPolicy(
        JevClient(api_key, budget, clock=moment),
        store,
        recorder,
        lesson=pack,
        max_attempts=max_attempts,
    )
    policy.selection_snapshot = selection_snapshot
    policy.checkpoint_id += f":research-selection:{hash_bytes(selection_snapshot.encode())}"
    return policy
