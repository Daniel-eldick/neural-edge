"""Encrypted recurring state on the existing private reports branch, with Git CAS."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from deploy.research.followup_private import session
from deploy.research.summary import assert_private

if TYPE_CHECKING:
    from collections.abc import Callable

STATE = "loop-v1/state.enc.base64"
REPORT = "loop-v1/README.md"
CHECK = "loop-v1/connection-check.md"


def allowed(path: str) -> bool:
    return (
        path in {STATE, REPORT, CHECK}
        or re.fullmatch(r"loop-v1/cycles/\d{4}-\d{2}-\d{2}/(frozen|result)\.enc\.base64", path)
        is not None
    )


def read(paths: list[str]) -> tuple[dict[str, str], str, dict[str, int]]:
    if not paths or not all(allowed(p) for p in paths):
        raise ValueError("Unapproved recurring read")

    def operation(
        git: Callable[..., str], parent: str
    ) -> tuple[dict[str, str], str, dict[str, int]]:
        files, times = {}, {}
        for name in paths:
            if git("ls-tree", parent, "--", name).strip():
                if int(git("cat-file", "-s", f"{parent}:{name}")) > 12_000_000:
                    raise ValueError("Recurring private input too large")
                files[name] = git("show", f"{parent}:{name}")
                # A shallow boundary is not the file's actual last modification.
                for _ in range(8):
                    touched = git("log", "-1", "--format=%H", parent, "--", name).strip()
                    parents = git("rev-list", "--parents", "-n", "1", touched).split()
                    shallow = git("rev-parse", "--is-shallow-repository").strip() == "true"
                    if len(parents) > 1 or not shallow:
                        times[name] = int(git("show", "-s", "--format=%ct", touched))
                        break
                    git("fetch", "--deepen=512", "origin", "reports")
                else:
                    raise ValueError("Freeze history proof unavailable within bounded fetch")
        return files, parent, times

    result = session(operation)
    return result  # type: ignore[no-any-return]


def write(expected: str, files: dict[str, str], *, deadline: int | None = None) -> str:
    if (
        not files
        or not all(allowed(p) for p in files)
        or sum(len(v.encode()) for v in files.values()) > 12_000_000
    ):
        raise ValueError("Unapproved or oversized recurring output")

    def operation(git: Callable[..., str], parent: str) -> str:
        if parent != expected:
            raise ValueError("Private state changed; no inference allowed")
        git("read-tree", parent)
        for name, value in sorted(files.items()):
            blob = git("hash-object", "-w", "--stdin", data=value).strip()
            prior = git("ls-tree", parent, "--", name).strip()
            if name not in {STATE, REPORT, CHECK} and prior and prior.split()[2] != blob:
                raise ValueError("Frozen recurring artifact is immutable")
            git("update-index", "--add", "--cacheinfo", "100644", blob, name)
        tree = git("write-tree").strip()
        if tree == git("rev-parse", f"{parent}^{{tree}}").strip():
            return parent
        commit = git(
            "commit-tree", tree, "-p", parent, data="Save private recurring research state\n"
        ).strip()
        assert_private()
        if deadline is not None:
            from datetime import UTC, datetime

            if datetime.now(UTC).timestamp() >= deadline - 120:
                raise ValueError("Recurring freeze deadline passed")
        # Explicit lease is a compare-and-swap, never a force overwrite of newer history.
        git(
            "push",
            f"--force-with-lease=refs/heads/reports:{parent}",
            "origin",
            f"{commit}:refs/heads/reports",
        )
        return commit

    result = session(operation)
    return result  # type: ignore[no-any-return]
