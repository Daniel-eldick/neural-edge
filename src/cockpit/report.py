"""Read-only imports and an honest HTML view of completed research runs."""

from __future__ import annotations

import json
import math
import re
import sqlite3
import zipfile
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from src.cockpit.visuals import dashboard


@dataclass(frozen=True)
class Activity:
    time: int
    kind: str
    symbol: str
    price: float
    profit: float | None = None


@dataclass
class Run:
    name: str
    source: str
    kind: str
    period: str
    starting_equity: float
    ending_equity: float
    drawdown: float
    closed_trades: int
    open_positions: int | None
    win_rate: float | None
    equity: list[tuple[int, float]]
    details: list[str]
    note: str
    daily_sharpe: float | None = None
    complete_days: int | None = None
    sharpe_unavailable_reason: str = "Not reported"
    comparison_key: str | None = None
    model_choices: int | None = None
    policy_errors: int | None = None
    inference_cost_usd: float | None = None
    started_at: int | None = None
    ended_at: int | None = None
    symbols: tuple[str, ...] = ()
    daily_returns: list[tuple[int, float]] = field(default_factory=list)
    close_drawdowns: list[tuple[int, float]] = field(default_factory=list)
    activity: list[Activity] = field(default_factory=list)
    choice_counts: dict[str, int] = field(default_factory=dict)
    halted: bool | None = None
    reviewed_cases: int = 0
    memory_reads: int = 0
    last_review_at: int | None = None

    @property
    def net_return(self) -> float:
        return self.ending_equity / self.starting_equity - 1


def number(value: Any, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Expected a numeric metric")
    result = float(value)
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise ValueError("Invalid or non-finite metric")
    return result


def count(value: Any) -> int:
    result = number(value, minimum=0)
    if not result.is_integer():
        raise ValueError("Expected a nonnegative integer count")
    return int(result)


def ratio(value: Any) -> float:
    result = number(value, minimum=0)
    if result > 1:
        raise ValueError("Ratio exceeds one")
    return result


def date(value: Any) -> str:
    return datetime.fromtimestamp(number(value, minimum=0), UTC).strftime("%Y-%m-%d %H:%M UTC")


def load_archive(path: Path) -> list[Run]:
    """Import only the metrics member; never saved configuration or strategy code."""
    with zipfile.ZipFile(path) as zipped:
        member = path.stem + ".json"
        if zipped.getinfo(member).file_size > 32 * 1024 * 1024:
            raise ValueError(f"{path.name}: results member exceeds 32 MiB import limit")
        data = json.loads(zipped.read(member))
    runs = []
    for name, values in data["strategy"].items():
        start = number(values["starting_balance"], minimum=0.01)
        end = number(values["final_balance"], minimum=0)
        trades = count(values["total_trades"])
        wins = count(values["wins"])
        if wins > trades:
            raise ValueError("Wins exceed total trades")
        details = [
            f'{t["pair"]} · {number(t["profit_abs"]):+.2f} USDT · {t["exit_reason"]}'
            for t in values.get("trades", [])[-50:]
        ]
        runs.append(Run(
            str(name), path.name, "Legacy baseline",
            f'{values["backtest_start"]} → {values["backtest_end"]} UTC',
            start, end, ratio(values["max_drawdown_account"]), trades, None,
            wins / trades if trades else None, [], details,
            "Archived Freqtrade result. Costs follow that run's original configuration; "
            "no AI operating costs or new slippage stress added here. "
            "Closed-trade history is not a marked-to-market equity curve. "
            "Last 50 trade records shown. Historical baseline, not apprentice performance.",
        ))
    if not runs:
        raise ValueError(f"{path.name}: no strategy results")
    return runs


def load_journal(path: Path) -> Run:
    """Stream the existing journal in a read-only snapshot; do not fabricate partial results."""
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    start: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    policy = "Unspecified policy"
    dataset_hash: str | None = None
    points: list[tuple[int, float]] = []
    peaks: list[float] = []
    peak = 0.0
    daily_returns: deque[tuple[int, float]] = deque(maxlen=366)
    activity: deque[Activity] = deque(maxlen=6)
    choice_counts: dict[str, int] = {}
    details: deque[str] = deque(maxlen=50)
    wins = exits = 0
    model_choices = policy_errors = 0
    reviewed_cases = memory_reads = 0
    last_review_at: int | None = None
    inference_nano_usd = 0
    total_points = 0
    stride = 1
    last_kind = ""
    final_point: tuple[int, float] | None = None
    try:
        for (payload,) in connection.execute("SELECT payload FROM events ORDER BY sequence"):
            event = json.loads(payload)
            last_kind = event["kind"]
            if last_kind == "FAILED":
                raise ValueError(f"{path.name}: failed run; inspect its journal")
            if last_kind == "MANIFEST":
                policy = str(event.get("policy", policy))
                value = event.get("sha256")
                if isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value):
                    dataset_hash = value
            elif last_kind == "START":
                if start is not None:
                    raise ValueError("Journal contains multiple runs")
                start = event
            elif last_kind == "RESULT":
                if result is not None:
                    raise ValueError("Journal contains multiple results")
                result = event
            elif last_kind == "EQUITY":
                final_point = (count(event["time"]), number(event["equity"], minimum=0))
                peak = max(peak, final_point[1])
                if total_points % stride == 0:
                    points.append(final_point)
                    peaks.append(peak)
                total_points += 1
                if len(points) > 1000:
                    points = points[::2]
                    peaks = peaks[::2]
                    stride *= 2
            if last_kind == "DAILY_RETURN":
                timestamp = count(event["time"])
                if timestamp % 86400 or (daily_returns and timestamp <= daily_returns[-1][0]):
                    raise ValueError("Daily returns need ordered UTC boundaries")
                daily_returns.append((timestamp, number(event["net_return"])))
            if last_kind in {"ENTER", "EXIT"}:
                activity.append(Activity(
                    count(event["time"]), last_kind, str(event["symbol"]),
                    number(event["price"], minimum=0),
                    number(event["net_profit"]) if last_kind == "EXIT" else None,
                ))
            if last_kind == "EXIT":
                exits += 1
                wins += number(event["net_profit"]) > 0
            if last_kind == "MODEL_CHOICE":
                choice = event["choice"]
                if choice not in {"enter", "wait"}:
                    raise ValueError("Unrecognized model choice")
                choice_counts[choice] = choice_counts.get(choice, 0) + 1
                model_choices += 1
                inference_nano_usd += count(event["cost_nano_usd"])
                details.append(
                    f'{date(event["time"])} · {event["symbol"]} · {event["model"]} '
                    f'chose {event["choice"]} · inference '
                    f'${count(event["cost_nano_usd"]) / 1e9:.9f}'
                )
            if last_kind == "POLICY_ERROR":
                policy_errors += 1
            if last_kind == "TEACHER_REVIEW":
                total = count(event["reviewed_total"])
                if total != reviewed_cases + len(event["case_ids"]):
                    raise ValueError("Teacher review count disagrees with evidence")
                reviewed_cases = total
                last_review_at = count(event["time"])
            if last_kind == "CONTEXT_READ":
                closed = [date(event[key]) if event[key] is not None else "unknown"
                          for key in ("daily_last_closed_at", "weekly_last_closed_at")]
                details.append(
                    f'{date(event["time"])} · {event["symbol"]} · '
                    f'Daily {event["daily_status"]} / weekly {event["weekly_status"]} · '
                    f'closed through {closed[0]} / {closed[1]}'
                )
            if last_kind == "MEMORY_READ":
                memory_reads += 1
            if last_kind in {"DECISION", "VETO", "POLICY_ERROR", "ENTER", "EXIT", "HALT"}:
                reason = event.get("reason", event.get("error", "Drawdown halt"))
                action = event.get("action", last_kind)
                details.append(f'{date(event["time"])} · {event.get("symbol", "Portfolio")} '
                               f'· {action} · {reason}')
    finally:
        connection.close()
    if start is None or result is None or last_kind != "RESULT" or final_point is None:
        raise ValueError(f"{path.name}: no completed run; wait for a final RESULT event")
    if count(result["closed_trades"]) != exits:
        raise ValueError("Recorded trade count disagrees with exit events")
    if not math.isclose(final_point[1], number(result["ending_equity"]), abs_tol=1e-8):
        raise ValueError("Recorded ending equity disagrees with final equity event")
    if points[-1] != final_point:
        points.append(final_point)
        peaks.append(peak)
    settings = start["settings"]
    days = count(result["complete_days"]) if "complete_days" in result else None
    sharpe = number(result["daily_sharpe"]) if result.get("daily_sharpe") is not None else None
    reasons = {
        "fewer_than_30_complete_days": "fewer than 30 complete days",
        "zero_variance": "daily returns have zero variance",
    }
    reason = result.get("sharpe_unavailable_reason")
    if days is not None:
        if sharpe is not None and (days < 30 or reason is not None):
            raise ValueError("Daily Sharpe disagrees with sample length or availability")
        if sharpe is None and (reason not in reasons or
                               (reason == "fewer_than_30_complete_days") != (days < 30)):
            raise ValueError("Missing or inconsistent daily Sharpe explanation")
    elif sharpe is not None:
        raise ValueError("Daily Sharpe requires a recorded sample length")
    comparison_key = json.dumps([dataset_hash, settings, start["time"], result["time"]],
                                sort_keys=True) if dataset_hash is not None else None
    inference_known = model_choices > 0 or policy in {
        "breakout-baseline-v1", "jev-breakout-filter-v1", "jev-memory-filter-v1",
        "jev-context-filter-v1",
    }
    return Run(
        policy, path.name, "Offline replay", f'{date(start["time"])} → {date(result["time"])}',
        number(result["starting_equity"], minimum=0.01),
        number(result["ending_equity"], minimum=0), ratio(result["max_drawdown"]),
        exits, count(result["open_positions"]), wins / exits if exits else None,
        points, list(details),
        f'Fee {ratio(settings["fee"]):.2%} per side; slippage '
        f'{ratio(settings["slippage"]):.2%} per fill. '
        f'{total_points:,} recorded equity samples; {len(points):,} displayed. '
        'Last 50 decision/execution records shown. Ending equity includes open positions; '
        'future liquidation and AI operating costs are excluded. '
        f'{model_choices} model choices recorded; {policy_errors} policy errors/vetoes. '
        'Per-choice inference costs cover successful responses only; unresolved reservations '
        'remain in the shared budget ledger. '
        'Daily Sharpe uses complete UTC days, sample standard deviation, zero risk-free '
        'return and sqrt(365) annualization; partial days are excluded. '
        'At least 30 complete days are required to display this descriptive statistic. '
        'Learning improvement is not established by this run. '
        f'Run ended with risk halt: {"yes" if result["halted"] else "no"}.',
        sharpe, days, reasons.get(str(reason), "Not reported"),
        comparison_key, model_choices, policy_errors,
        inference_nano_usd / 1e9 if inference_known else None,
        count(start["time"]), count(result["time"]),
        tuple(str(symbol) for symbol in start.get("symbols", [])),
        list(daily_returns),
        [(t, 1 - value / max(number(result["starting_equity"], minimum=0.01), high))
         for (t, value), high in zip(points, peaks, strict=True)],
        list(activity), choice_counts, bool(result["halted"]),
        reviewed_cases, memory_reads, last_review_at,
    )


def chart(run: Run) -> str:
    if len(run.equity) < 2:
        return '<div class="empty-chart">No recorded equity curve available for this run.</div>'
    low = min(v for _, v in run.equity)
    high = max(v for _, v in run.equity)
    span = high - low or max(1, high * 0.01)
    first, last = run.equity[0][0], run.equity[-1][0]
    coordinates = " ".join(
        f"{20 + (t - first) / max(1, last - first) * 920:.2f},"
        f"{170 - (v - low) / span * 140:.2f}" for t, v in run.equity
    )
    return (
        '<svg viewBox="0 0 960 210" role="img" aria-label="Recorded account equity">'
        '<path d="M20 180H940" stroke="#34474a"/>'
        f'<polyline points="{coordinates}" fill="none" stroke="#8de1c1" stroke-width="3"/>'
        f'<text x="20" y="205" fill="#a8b4b1">{escape(date(first)[:10])}</text>'
        f'<text x="940" y="205" text-anchor="end" fill="#a8b4b1">{escape(date(last)[:10])}</text>'
        f'</svg><p class="muted">Displayed equity range: {low:,.2f}–{high:,.2f} USDT. '
        'Sampled curve · dip measured from full run.</p>'
    )


def display_name(run: Run) -> str:
    return {
        "jev-breakout-filter-v1": "Jev agent",
        "jev-memory-filter-v1": "Jev with memory",
        "jev-context-filter-v1": "Jev with context + memory",
        "breakout-baseline-v1": "Simple strategy",
        "AlphaStrategy": "Earlier strategy",
    }.get(run.name, run.name)


def metric_cards(metrics: list[tuple[str, str]]) -> str:
    return '<dl class="metrics">' + "".join(
        f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
        for label, value in metrics
    ) + '</dl>'


def coverage_warning(run: Run) -> str:
    if not run.policy_errors:
        return ""
    return (
        '<aside class="warning" aria-label="Evaluation warning">'
        '<strong>Incomplete test</strong>'
        f'<span>{run.policy_errors} candidate evaluations failed or were blocked. '
        'Results do not show full agent performance.</span></aside>'
    )


def render(runs: list[Run]) -> str:
    # Prefer the requested agent, never the best-performing result. Input order breaks ties;
    # do not imply a chronological "latest" ordering that imported archives cannot establish.
    selected = next((run for run in reversed(runs) if run.name in {
        "jev-breakout-filter-v1", "jev-memory-filter-v1", "jev-context-filter-v1"}),
                    runs[-1] if runs else None)
    overview = ('<article><h2>No saved runs yet</h2>'
                '<p>Import a completed backtest to begin.</p></article>')
    if selected is not None:
        overview = dashboard(selected, runs)
    sections = []
    for index, run in enumerate(runs, start=1):
        metrics = [
            ("Experience memory", "On · improvement unproven"
             if run.name in {"jev-memory-filter-v1", "jev-context-filter-v1"} else
             "Not used in this run"),
            ("Net return", f"{run.net_return:+.2%}"),
            ("Ending equity", f"{run.ending_equity:,.2f} USDT"),
            ("Max drawdown", f"{run.drawdown:.2%}"),
            ("Closed trades", str(run.closed_trades)),
            ("Win rate", f"{run.win_rate:.1%}" if run.win_rate is not None else "Not available"),
            ("Open positions", str(run.open_positions) if run.open_positions is not None
             else "Not reported"),
            ("Complete UTC days", str(run.complete_days) if run.complete_days is not None
             else "Not reported"),
            ("Daily Sharpe", f"{run.daily_sharpe:.2f}" if run.daily_sharpe is not None
             else run.sharpe_unavailable_reason),
            ("Model choices", str(run.model_choices) if run.model_choices is not None
             else "Not reported"),
            ("Policy errors", str(run.policy_errors) if run.policy_errors is not None
             else "Not reported"),
            ("Recorded AI cost (USD)", f"${run.inference_cost_usd:.9f}"
             if run.inference_cost_usd is not None else "Not reported"),
        ]
        if run.name in {"jev-memory-filter-v1", "jev-context-filter-v1"}:
            metrics.extend([
                ("Reviewed trades", str(run.reviewed_cases)),
                ("Memory reads", str(run.memory_reads)),
                ("Last review", date(run.last_review_at) if run.last_review_at is not None
                 else "No matured trades yet"),
            ])
        records = "".join(f"<li>{escape(row)}</li>" for row in run.details)
        window = f" · {date(run.started_at)[:10]}" if run.started_at is not None else ""
        sections.append(
            f'<details class="run-detail" id="run-{index}"><summary>'
            f'{escape(display_name(run))} <span class="muted">· {escape(run.kind)} '
            f'· {run.net_return:+.2%}{escape(window)}'
            + (' · Incomplete test' if run.policy_errors else '')
            + '</span></summary><div class="detail-body">'
            f'<h3>{escape(run.name)}</h3><p class="muted">{escape(run.period)}</p>'
            + coverage_warning(run) + metric_cards(metrics) + chart(run)
            + f'<details><summary>Decisions and trade records ({len(run.details)})</summary>'
            f'<ol>{records or "<li>No records available.</li>"}</ol></details>'
            '<details><summary>Evidence and assumptions</summary>'
            f'<p>{escape(run.note)}</p><p>Source: {escape(run.source)}</p>'
            '</details></div></details>'
        )
    groups: dict[str, list[Run]] = {}
    for run in runs:
        if run.comparison_key is not None:
            groups.setdefault(run.comparison_key, []).append(run)
    comparisons = []
    for group in groups.values():
        if len(group) < 2:
            continue
        rows = []
        for run in group:
            cost = (f"${run.inference_cost_usd:.9f}" if run.inference_cost_usd is not None
                    else "Not reported")
            values = [run.name, f"{run.net_return:+.3%}", f"{run.drawdown:.3%}",
                      str(run.closed_trades), str(run.open_positions),
                      str(run.model_choices), str(run.policy_errors), cost]
            rows.append("<tr>" + "".join(f"<td>{escape(v)}</td>" for v in values) + "</tr>")
        headers = ["Policy", "Trading return", "Drawdown", "Closed trades", "Open positions",
                   "Model choices", "Policy errors", "Recorded AI cost (USD)"]
        window = (date(group[0].started_at)[:10] if group[0].started_at is not None
                  else "full metrics")
        comparisons.append(
            f'<details><summary>Same-input comparison · {escape(window)}</summary>'
            f'<p class="muted">{escape(group[0].period)}</p>'
            '<p>Matching input-file hash, period and execution settings. '
            'Cash reference: 0% trading return. AI cost is separate from USDT trading P&amp;L; '
            'unresolved reservations are not included in recorded successful-call costs.</p>'
            + ('<p>Degraded evaluation: policy errors or model limits occurred.</p>'
               if any(run.policy_errors for run in group) else '')
            + '<div class="comparison"><table><thead><tr>'
            + "".join(f"<th scope=\"col\">{escape(h)}</th>" for h in headers)
            + '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div></details>'
        )
    evidence = (
        '<details class="evidence" id="evidence"><summary>'
        f'All experiments &amp; evidence <span class="muted">({len(runs)} saved runs)</span>'
        '</summary><div class="detail-body">' + ''.join(sections + comparisons)
        + '<p class="muted">Learning improvement unproven. '
        'Saved results do not monitor a running agent.</p>'
        '</div></details>'
    ) if runs else ''
    generated_at = datetime.now(UTC)
    generated = generated_at.strftime("%d %b %Y · %H:%M UTC")
    template = Path(__file__).with_name("template.html").read_text(encoding="utf-8")
    return (template.replace("{{generated}}", generated)
            .replace("{{generated_iso}}", generated_at.isoformat())
            .replace("{{runs}}", overview + evidence))
