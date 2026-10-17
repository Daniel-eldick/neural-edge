"""Deterministic private reporting of the existing encrypted study; no inference or replay."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import requests

from deploy.research.cloud import (
    CLAIM,
    MAX_ARCHIVE,
    PROTOCOL_SHA,
    READY,
    REPO,
    STUDY,
    decrypt,
    hash_bytes,
    restore,
    unpack,
)

DESTINATION = "Daniel-eldick/jev-research-results"
PRIVACY_URL = f"https://api.github.com/repos/{DESTINATION}"
REMOTE = f"git@github.com:{DESTINATION}.git"
HOST_KEY = (
    "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n"
)
CHECK_TEXT = (
    "# Private cloud delivery verified\n\n"
    "The hosted summary job can write to this private repository without the operator computer.\n"
    "This is a connection check, not an experiment result. The future study has not run.\n"
)


def finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError("Invalid report number")
    return float(value)


def count(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 3_000_000_000:
        raise ValueError("Invalid report count")
    return int(value)


def render(
    report: dict[str, Any] | None,
    allocation: dict[str, Any],
    usage: dict[str, int] | None,
    settled: int | None,
    run_id: str,
) -> str:
    """Only fixed prose and validated numeric study metrics enter the private report."""
    if not run_id.isascii() or not run_id.isdecimal():
        raise ValueError("Invalid run identifier")
    lines = ["# Jev saved-lesson test", "", "**Verdict: Inconclusive.**", ""]
    if report is not None and report["status"] == "complete":
        runs = report["runs"]
        if [r["variant"] for r in runs] != ["baseline", "frozen", "lesson"]:
            raise ValueError("Incomplete comparison")
        for run in runs:
            if count(run["open_positions"]) or count(run["policy_errors"]):
                raise ValueError("Incomplete outcomes")
            if abs(finite(run["closed_net_profit_usdt"]) - finite(run["net_return"]) * 1000) > 1e-6:
                raise ValueError("Completed profit differs from return")
        delta = finite(report["lesson_minus_frozen_percentage_points"])
        if (
            abs(delta - (finite(runs[2]["net_return"]) - finite(runs[1]["net_return"])) * 100)
            > 1e-8
        ):
            raise ValueError("Return difference disagrees")
        adequate = all(count(r["closed_trades"]) >= 10 for r in runs[1:])
        direction = (
            "Helped in this pilot"
            if delta > 0
            else "Worsened in this pilot"
            if delta < 0
            else "Tied in this pilot"
        )
        lines[2] = f"**Verdict: {direction if adequate else 'Inconclusive'}.**"
        lines += [
            f"Observed lesson-minus-frozen return: {delta:+.6f} percentage points.",
            "Returns include simulated fees and slippage; each variant started with 1,000 USDT.",
            "",
            "| Variant | Completed trades | Net profit (USDT) | Net return | Max drawdown |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for run in runs:
            lines.append(
                f"| {run['variant']} | {count(run['closed_trades'])} | "
                f"{finite(run['closed_net_profit_usdt']):.6f} | "
                f"{finite(run['net_return']) * 100:.6f}% | "
                f"{finite(run['max_drawdown']) * 100:.6f}% |"
            )
        lines += ["| cash | 0 | 0.000000 | 0.000000% | 0.000000% |", ""]
        if not adequate:
            lines += [
                "Limited coverage: fewer than ten completed trades in at least one AI variant."
            ]
        lines += [
            "This sampled, stochastic week does not establish repeatable learning "
            "or justify promotion.",
            "",
            f"Raw candidates: {count(report['raw_candidates'])}; "
            f"selected: {count(report['selected_candidates'])}.",
        ]
        for run in runs[1:]:
            lines.append(
                f"{run['variant']}: {count(run['model_choices'])} model choices; "
                f"{count(run['selected_seen'])} selected opportunities seen; "
                f"{finite(run['mean_close_exposure_fraction']) * 100:.3f}% mean closing exposure."
            )
        pairs = report["decisions"]
        lines += [
            f"Same-market changed choices: {count(pairs['same_market_changed_choices'])} / "
            f"{count(pairs['same_market_pairs'])}.",
            f"Identical-input changed choices: {count(pairs['identical_input_changed_choices'])} / "
            f"{count(pairs['identical_input_pairs'])}.",
            "Different portfolio histories can change later inputs; "
            "these comparisons are separate.",
        ]
    else:
        lines += [
            "A complete authenticated comparison is unavailable "
            "or the execution failed/interrupted.",
            "No improvement claim or completed-trade totals can be verified from this state.",
        ]
    lines += ["", "## Costs and budget", ""]
    if usage is None or settled is None:
        lines += ["Actual study inference cost: unavailable; keep the full allocation reserved."]
    else:
        lines += [
            f"Known settled study inference: USD {count(settled) / 1e9:.9f}.",
            f"Attempts: {count(usage['attempts'])}; "
            f"uncertain calls: {count(usage['pending_calls'])}.",
            "Accounted amount including uncertain reservations: "
            f"USD {count(usage['accounted_nano_usd']) / 1e9:.9f}.",
        ]
    before = count(allocation["host_budget_before"]["used_nano_usd"])
    lines += [
        "Original host allocation: USD 0.504000000; retained until local verified reconciliation.",
        "Original monthly AI cap: USD 3.000000000.",
        f"At allocation time: USD {before / 1e9:.9f} previously accounted; "
        f"USD {(3_000_000_000 - before - 504_000_000) / 1e9:.9f} unreserved.",
        "This is a frozen snapshot, not a live global balance. "
        "No cloud reconciliation is performed.",
        "Summary inference cost: USD 0. Standard public-runner compute: USD 0; "
        "no paid storage or private Actions runs.",
        "Inference USD is separate from simulated trading profit in USDT.",
        "",
        f"[Execution run](https://github.com/{REPO}/actions/runs/{run_id})",
        "Entry window: October 17–23, 2026 UTC; protective exits through October 25 00:00 UTC.",
        "Candle execution, zero decision latency, correlated assets and sampling limit inference.",
    ]
    return "\n".join(lines) + "\n"


def validate_outcome(
    sealed: Path,
    key: bytes,
    allocation: dict[str, Any],
    protocol: bytes,
    run_id: str,
    destination: Path,
) -> tuple[dict[str, Any] | None, dict[str, int], int]:
    from deploy.research.guard import FundedBudget

    receipt = unpack(decrypt(sealed.read_bytes(), key, "result"), destination)
    if (
        receipt != json.loads((destination / "cloud-receipt.json").read_text())
        or receipt["allocation"] != allocation
        or receipt["protocol_sha256"] != PROTOCOL_SHA
        or receipt["github_run_id"] != run_id
        or type(receipt["terminal"]) is not bool
        or (destination / "study/protocol.json").read_bytes() != protocol
    ):
        raise ValueError("Outcome identities differ")
    budget = FundedBudget(destination / "execution-budget.sqlite", allocation)
    usage = budget.usage()
    if receipt["usage"] != usage:
        raise ValueError("Outcome usage differs")
    settled = sum(r[4] for r in budget.validate() if r[5] == 1)
    if not receipt["terminal"]:
        return None, usage, settled
    report = json.loads((destination / "study/result.json").read_text())
    contract = json.loads((destination / "study/result-contract.json").read_text())
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if (
        contract != {"payload": report, "sha256": hash_bytes(canonical)}
        or report["protocol_sha256"] != PROTOCOL_SHA
        or report["study"] != "lesson-week-v2"
        or report["promotion_allowed"] is not False
    ):
        raise ValueError("Report contract differs")
    if report["status"] == "complete" and (
        usage["pending_calls"]
        or report["study_receipted_cost_nano_usd"] != settled
        or report["study_successful_calls"] != usage["attempts"]
        or sum(round(finite(r["inference_cost_usd"]) * 1e9) for r in report["runs"]) != settled
    ):
        raise ValueError("Completed report costs differ")
    return dict(report), usage, settled


def assert_private() -> None:
    """Anonymous 404 plus successful repository-scoped SSH access establish a private target."""
    with requests.get(PRIVACY_URL, timeout=(5, 30), allow_redirects=False) as response:
        if response.status_code != 404:
            raise ValueError("Private destination unavailable or public")


def publish(text: str, private_key: str, *, check: bool = False) -> None:
    """Git plumbing avoids checkout/hooks, forced updates, and private output in logs."""
    if len(text.encode()) > 64_000:
        raise ValueError("Report exceeds bound")
    assert_private()
    with tempfile.TemporaryDirectory(prefix="jev-report-") as temporary:
        root = Path(temporary)
        key, hosts = root / "key", root / "known_hosts"
        key.write_text(private_key)
        key.chmod(0o600)
        hosts.write_text(HOST_KEY)
        ssh = (
            f"ssh -F /dev/null -i {shlex.quote(str(key))} -o IdentitiesOnly=yes "
            f"-o UserKnownHostsFile={shlex.quote(str(hosts))} -o StrictHostKeyChecking=yes "
            "-o BatchMode=yes -o ConnectTimeout=15 -o HostKeyAlgorithms=ssh-ed25519"
        )
        env = {
            "PATH": os.environ["PATH"],
            "GIT_SSH_COMMAND": ssh,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Jev research reporter",
            "GIT_AUTHOR_EMAIL": "research@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "Jev research reporter",
            "GIT_COMMITTER_EMAIL": "research@users.noreply.github.com",
        }

        def git(*args: str, data: str | None = None) -> str:
            result = subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-c", "init.templateDir=", *args],
                cwd=root,
                env=env,
                input=data,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            return result.stdout.strip()

        git("init", "-b", "reports")
        git("remote", "add", "origin", REMOTE)
        git("fetch", "--depth=1", "origin", "reports")
        parent = git("rev-parse", "FETCH_HEAD")
        git("read-tree", parent)
        blob = git("hash-object", "-w", "--stdin", data=text)
        target = "connection-check.md" if check else "README.md"
        git("update-index", "--add", "--cacheinfo", "100644", blob, target)
        tree = git("write-tree")
        if tree == git("rev-parse", f"{parent}^{{tree}}"):
            return
        commit = git("commit-tree", tree, "-p", parent, data="Save private research summary\n")
        assert_private()
        git("push", "origin", f"{commit}:refs/heads/reports")


def download_result(path: Path) -> bool:
    url = f"https://api.github.com/repos/{REPO}/contents/result.enc?ref={CLAIM}"
    headers = {"Accept": "application/vnd.github.raw+json"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with requests.get(
        url, headers=headers, timeout=(5, 30), allow_redirects=False, stream=True
    ) as response:
        if response.status_code == 404:
            return False
        if response.status_code != 200:
            raise ValueError("Encrypted result download unavailable")
        size = 0
        with path.open("xb") as output:
            path.chmod(0o600)
            for block in response.iter_content(65_536):
                size += len(block)
                if size > MAX_ARCHIVE:
                    raise ValueError("Encrypted result exceeds bound")
                output.write(block)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify", "run"])
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    try:
        from datetime import UTC, datetime

        key = base64.b64decode(os.environ["JEV_RESEARCH_ENVELOPE_KEY"], validate=True)
        deploy_key = os.environ["JEV_RESEARCH_REPORT_DEPLOY_KEY"]
        with tempfile.TemporaryDirectory(prefix="jev-summary-") as temporary:
            root = Path(temporary)
            metadata = restore(
                args.directory / "runner.json", args.directory / "input.enc", key, root / "input"
            )
            if args.mode == "verify" or datetime.now(UTC).timestamp() < READY:
                publish(CHECK_TEXT, deploy_key, check=True)
                print('{"status":"private_delivery_verified_waiting_for_data"}')
                return
            sys.path.insert(0, str(root / "input"))
            result_path = root / "result.enc"
            report, usage, settled = None, None, None
            if download_result(result_path):
                report, usage, settled = validate_outcome(
                    result_path,
                    key,
                    metadata,
                    (root / "input" / STUDY / "protocol.json").read_bytes(),
                    os.environ["GITHUB_RUN_ID"],
                    root / "outcome",
                )
            text = render(report, metadata, usage, settled, os.environ["GITHUB_RUN_ID"])
            publish(text, deploy_key)
            print('{"status":"private_summary_saved"}')
    except Exception:
        # Never let requests/subprocess exception output reveal private content or credentials.
        parser.exit(
            1, "Private summary unavailable; preserve encrypted evidence and original hold.\n"
        )


if __name__ == "__main__":
    main()
