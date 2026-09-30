"""Generate a read-only comparison from completed, matched window directories."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from src.cockpit.report import load_archive, load_journal, render
from src.evaluation.screen import (
    candidates,
    checkpoint,
    load_candles,
    receipt_evidence,
    window_runs,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--window",
        type=Path,
        action="append",
        required=True,
        help="Directory with candles.csv and baseline/jev/memory.sqlite",
    )
    parser.add_argument("--output", type=Path, required=True, help="New JSON summary path")
    parser.add_argument("--html", type=Path, required=True, help="New cockpit HTML path")
    parser.add_argument("--archive", type=Path, action="append", default=[],
                        help="Earlier archive to retain in cockpit evidence")
    parser.add_argument("--journal", type=Path, action="append", default=[],
                        help="Earlier completed journal to retain in cockpit evidence")
    args = parser.parse_args()
    if args.output.exists() or args.html.exists() or args.output.resolve() == args.html.resolve():
        parser.error("Report paths must be distinct new files; evidence is never overwritten")
    if len({p.resolve() for p in args.window}) != len(args.window):
        parser.error("Each window must be listed once")
    all_runs = [run for path in args.archive for run in load_archive(path)]
    all_runs.extend(load_journal(path) for path in args.journal)
    windows = []
    for directory in args.window:
        runs = window_runs(directory)
        all_runs.extend(runs)
        frozen, memory = runs[-2:]
        receipts = receipt_evidence(
            directory / "memory.sqlite.responses.sqlite",
            memory,
            checkpoint(directory / "memory.sqlite")["policy_state"]["response_store"],
        )
        windows.append(
            {
                "window": directory.name,
                "period": memory.period,
                "csv_sha256": hashlib.sha256((directory / "candles.csv").read_bytes()).hexdigest(),
                "raw_candidate_upper_bound": candidates(load_candles(directory / "candles.csv")),
                "memory_minus_frozen_percentage_points": (memory.net_return - frozen.net_return)
                * 100,
                "memory_exposed_choices": receipts["choices_with_trade_memory"],
                "runs": [
                    {
                        "policy": r.name,
                        "net_return": r.net_return,
                        "ending_equity": r.ending_equity,
                        "max_drawdown": r.drawdown,
                        "closed_trades": r.closed_trades,
                        "open_positions": r.open_positions,
                        "model_choices": r.model_choices,
                        "policy_errors": r.policy_errors,
                        "inference_cost_usd": r.inference_cost_usd,
                        "reviewed_cases": r.reviewed_cases,
                        "memory_reads": r.memory_reads,
                    }
                    for r in runs
                ],
            }
        )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "windows": windows,
        "interpretation": "Descriptive comparison, not proof of improvement. "
        "Memory mode changes instructions as well as evidence; a single stochastic "
        "run per variant cannot isolate a reliable learning effect. "
        "USD AI costs are separate from USDT trading returns. "
        "Cash/buy-and-hold references are not risk-governed policies.",
    }
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    page = render(all_runs)
    with args.output.open("x") as f:
        f.write(payload)
    with args.html.open("x") as f:
        f.write(page)
    print(f"Validated {len(windows)} windows; {len(all_runs)} recorded/reference runs")


if __name__ == "__main__":
    main()
