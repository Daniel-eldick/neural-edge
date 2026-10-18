"""Atomic private research selection, using the existing restricted Git transport."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deploy.research.followup_private import FROZEN, RESULT, session

if TYPE_CHECKING:
    from collections.abc import Callable

DECISION = "lesson-selection/decision-v1.enc.base64"
ACTIVE = "lesson-selection/active.enc.base64"
REPORT = "lesson-selection/README.md"
CHECK = "lesson-selection/connection-check.md"


def read_snapshot(paths: list[str]) -> tuple[dict[str, str], str, dict[str, int]]:
    if not paths or not set(paths) <= {DECISION, ACTIVE, FROZEN, RESULT}:
        raise ValueError("Unapproved selection read")

    def operation(
        git: Callable[..., str], parent: str
    ) -> tuple[dict[str, str], str, dict[str, int]]:
        files, times = {}, {}
        for name in paths:
            if git("ls-tree", parent, "--", name).strip():
                if int(git("cat-file", "-s", f"{parent}:{name}")) > 12_000_000:
                    raise ValueError("Selection input exceeds bound")
                files[name] = git("show", f"{parent}:{name}")
                times[name] = int(git("log", "-1", "--format=%ct", parent, "--", name))
        return files, parent, times

    result = session(operation)
    return result  # type: ignore[no-any-return]


def publish_check(text: str) -> None:
    _write({CHECK: text})


def publish_selection(sealed: str, text: str, *, approved: bool) -> None:
    files = {DECISION: sealed, REPORT: text}
    if approved:
        files[ACTIVE] = sealed
    _write(files)


def _write(files: dict[str, str]) -> None:
    if (
        not files
        or not set(files) <= {CHECK, DECISION, ACTIVE, REPORT}
        or sum(len(s.encode()) for s in files.values()) > 256_000
    ):
        raise ValueError("Selection output exceeds fixed scope")

    def operation(git: Callable[..., str], parent: str) -> None:
        git("read-tree", parent)
        for name, value in sorted(files.items()):
            blob = git("hash-object", "-w", "--stdin", data=value).strip()
            existing = git("ls-tree", parent, "--", name).strip()
            if name != CHECK and existing and existing.split()[2] != blob:
                raise ValueError("Existing selection version is immutable")
            git("update-index", "--add", "--cacheinfo", "100644", blob, name)
        tree = git("write-tree").strip()
        if tree == git("rev-parse", f"{parent}^{{tree}}").strip():
            return
        commit = git(
            "commit-tree", tree, "-p", parent, data="Save private research lesson selection\n"
        ).strip()
        git("push", "origin", f"{commit}:refs/heads/reports")

    session(operation)
