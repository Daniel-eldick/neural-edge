"""Read-only imports and an honest HTML view of completed research runs."""

from __future__ import annotations

import json
import math
import sqlite3
import zipfile
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any


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
    points: list[tuple[int, float]] = []
    details: deque[str] = deque(maxlen=50)
    wins = exits = 0
    model_choices = policy_errors = 0
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
                if total_points % stride == 0:
                    points.append(final_point)
                total_points += 1
                if len(points) > 1000:
                    points = points[::2]
                    stride *= 2
            if last_kind == "EXIT":
                exits += 1
                wins += number(event["net_profit"]) > 0
            if last_kind == "MODEL_CHOICE":
                model_choices += 1
                details.append(
                    f'{date(event["time"])} · {event["symbol"]} · {event["model"]} '
                    f'chose {event["choice"]} · inference '
                    f'${count(event["cost_nano_usd"]) / 1e9:.9f}'
                )
            if last_kind == "POLICY_ERROR":
                policy_errors += 1
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
        'Learning comparisons are not available yet. '
        f'Run ended with risk halt: {"yes" if result["halted"] else "no"}.',
        sharpe, days, reasons.get(str(reason), "Not reported"),
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
        f'<text x="20" y="205" fill="#a8b4b1">{escape(date(first))}</text>'
        f'<text x="940" y="205" text-anchor="end" fill="#a8b4b1">{escape(date(last))}</text>'
        f'</svg><p class="muted">Displayed equity range: {low:,.2f}–{high:,.2f} USDT. '
        'Chart samples may omit intraperiod extremes; drawdown comes from the run summary.</p>'
    )


def render(runs: list[Run]) -> str:
    sections = []
    for index, run in enumerate(runs, start=1):
        metrics = [
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
        ]
        cards = "".join(f'<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in metrics)
        records = "".join(f"<li>{escape(row)}</li>" for row in run.details)
        sections.append(
            f'<article id="run-{index}"><div class="eyebrow">'
            f'{escape(run.kind)} / RUN {index:02}</div>'
            f'<h2>{escape(run.name)}</h2><p class="muted">{escape(run.period)}</p>'
            f'<dl class="metrics">{cards}</dl>{chart(run)}'
            f'<p>Started with {run.starting_equity:,.2f} USDT. '
            'This run alone does not establish profitability or improvement.</p>'
            f'<details><summary>Decisions and trade records ({len(run.details)})</summary>'
            f'<ol>{records or "<li>No records available.</li>"}</ol></details>'
            f'<details><summary>Evidence and assumptions</summary><p>{escape(run.note)}</p>'
            f'<p>Source: {escape(run.source)}</p></details></article>'
        )
    body = "".join(sections) or (
        "<article><h2>No saved runs yet</h2><p>Import a completed replay journal "
        "or saved backtest to see actual results here.</p></article>"
    )
    generated = datetime.now(UTC).strftime("%d %b %Y · %H:%M UTC")
    template = Path(__file__).with_name("template.html").read_text(encoding="utf-8")
    return template.replace("{{generated}}", generated).replace("{{runs}}", body)
