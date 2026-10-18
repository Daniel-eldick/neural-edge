"""Fixed private fresh-study paths; existing repository-scoped SSH key only."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from deploy.research.summary import HOST_KEY, REMOTE, assert_private

FROZEN = "fresh-replay/frozen.enc.base64"
RESULT = "fresh-replay/result.enc.base64"
REPORT = "fresh-replay/README.md"
CHECK = "fresh-replay/connection-check.md"
CANDIDATE = "lessons/lesson-week-v2-review-v1.json"
LEARNING = "learning-receipts/lesson-week-v2-review-v1.enc.base64"


def session(operation: Callable[[Callable[..., str], str], Any]) -> Any:
    assert_private()
    with tempfile.TemporaryDirectory(prefix="jev-fresh-private-") as temporary:
        root = Path(temporary).resolve()
        key, hosts = root / "key", root / "known_hosts"
        key.write_text(os.environ["JEV_RESEARCH_REPORT_DEPLOY_KEY"].strip() + "\n")
        key.chmod(0o600)
        hosts.write_text(HOST_KEY)
        env = {
            "PATH": os.environ["PATH"],
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Jev research reporter",
            "GIT_AUTHOR_EMAIL": "research@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "Jev research reporter",
            "GIT_COMMITTER_EMAIL": "research@users.noreply.github.com",
            "GIT_SSH_COMMAND": (
                f"ssh -F /dev/null -i {shlex.quote(str(key))} "
                f"-o IdentitiesOnly=yes -o UserKnownHostsFile={shlex.quote(str(hosts))} "
                "-o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=15 "
                "-o HostKeyAlgorithms=ssh-ed25519"
            ),
        }

        def git(*args: str, data: str | None = None) -> str:
            return subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-c", "init.templateDir=", *args],
                cwd=root,
                env=env,
                input=data,
                text=True,
                capture_output=True,
                timeout=60,
                check=True,
            ).stdout

        git("init", "-b", "reports")
        git("remote", "add", "origin", REMOTE)
        git("fetch", "--depth=64", "origin", "reports")
        return operation(git, git("rev-parse", "FETCH_HEAD").strip())


def read(paths: list[str]) -> tuple[dict[str, str], str, int]:
    if not set(paths) <= {FROZEN, RESULT, CANDIDATE, LEARNING}:
        raise ValueError("Unapproved private read")

    def operation(git: Callable[..., str], parent: str) -> tuple[dict[str, str], str, int]:
        files = {}
        for name in paths:
            if git("ls-tree", parent, "--", name).strip():
                if int(git("cat-file", "-s", f"{parent}:{name}")) > 12_000_000:
                    raise ValueError("Private input exceeds bound")
                files[name] = git("show", f"{parent}:{name}")
        times = [int(git("log", "-1", "--format=%ct", parent, "--", name)) for name in files]
        return files, parent, max(times, default=0)

    result = session(operation)
    return result  # type: ignore[no-any-return]


def write(files: dict[str, str], *, deadline: int | None = None) -> None:
    if (
        not files
        or not set(files) <= {FROZEN, RESULT, REPORT, CHECK}
        or sum(len(v.encode()) for v in files.values()) > 12_000_000
    ):
        raise ValueError("Unapproved private fresh output")

    def operation(git: Callable[..., str], parent: str) -> None:
        git("read-tree", parent)
        for name, value in sorted(files.items()):
            blob = git("hash-object", "-w", "--stdin", data=value).strip()
            existing = git("ls-tree", parent, "--", name).strip()
            if name != CHECK and existing and existing.split()[2] != blob:
                raise ValueError("Private fresh version is immutable")
            git("update-index", "--add", "--cacheinfo", "100644", blob, name)
        tree = git("write-tree").strip()
        if tree == git("rev-parse", f"{parent}^{{tree}}").strip():
            return
        commit = git(
            "commit-tree", tree, "-p", parent, data="Save private fresh replay evidence\n"
        ).strip()
        assert_private()
        if deadline is not None and datetime.now(UTC).timestamp() >= deadline - 120:
            raise ValueError("Fresh freeze publication deadline passed")
        git("push", "origin", f"{commit}:refs/heads/reports")

    session(operation)
