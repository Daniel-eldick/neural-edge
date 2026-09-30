"""Dependency-free, accessible SVG views of recorded research evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from math import ceil, floor, log10
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cockpit.report import Run

MINT = "#9ae6bf"
BLUE = "#91a9ef"
AMBER = "#ecc38c"
RED = "#ef9c9c"


def label(run: Run) -> str:
    return {
        "jev-breakout-filter-v1": "Jev agent",
        "breakout-baseline-v1": "Simple strategy",
        "AlphaStrategy": "Earlier strategy",
    }.get(run.name, run.name)


def stamp(timestamp: int, fmt: str = "%d %b %Y · %H:%M UTC") -> str:
    instant = datetime.fromtimestamp(timestamp, UTC)
    return f'<time datetime="{instant.isoformat()}">{instant.strftime(fmt)}</time>'


def empty(message: str) -> str:
    return f'<div class="empty-visual"><span aria-hidden="true">—</span>{escape(message)}</div>'


def axis_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, UTC).strftime("%d %b")


def line_plot(
    series: list[tuple[str, str, list[tuple[int, float]]]],
    *,
    percent: bool,
    title: str,
    below_zero: bool = False,
    compact: bool = False,
) -> str:
    series = [(name, color, points) for name, color, points in series if len(points) >= 2]
    if not series:
        return empty("No recorded equity curve available for this run.")
    values = [value for _, _, points in series for _, value in points]
    first = min(points[0][0] for _, _, points in series)
    last = max(points[-1][0] for _, _, points in series)
    low, high = min(values), max(values)
    if percent:
        low, high = min(0, low), max(0, high)
    if high == low:
        padding = 0.001 if percent else max(1, abs(high) * 0.001)
        low, high = low - padding, high + padding
    raw_step = (high - low) / 3
    magnitude: float = 10.0 ** floor(log10(raw_step))
    step = next(n for n in (1, 2, 2.5, 5, 10) if n >= raw_step / magnitude) * magnitude
    low, high = floor(low / step) * step, ceil(high / step) * step
    if below_zero:
        high = 0
    width, height = (510 if compact else 720), 244
    right = width - 18

    def x(t: int) -> float:
        return 62 + (t - first) / max(1, last - first) * (right - 62)

    def y(v: float) -> float:
        return 202 - (v - low) / (high - low) * 174

    def value_text(value: float) -> str:
        return f"{value:+.2%}" if percent else f"{value:,.2f}"

    parts = [
        f'<svg class="line-plot" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(title)}"><title>{escape(title)}</title>'
    ]
    for index in range(round((high - low) / step) + 1):
        value = low + step * index
        pos = y(value)
        tick = (f"{value * 100:+g}%" if value else "0%") if percent else f"{value:,.0f}"
        parts.append(
            f'<path class="grid-line" d="M62 {pos:.2f}H{right}"/>'
            f'<text class="axis" x="51" y="{pos + 4:.2f}" text-anchor="end">'
            f"{tick}</text>"
        )
    if percent:
        parts.append(f'<path class="zero-line" d="M62 {y(0):.2f}H{right}"/>')
    for index in range(5):
        t = round(first + (last - first) * index / 4)
        parts.append(
            f'<text class="axis" x="{x(t):.2f}" y="230" '
            f'text-anchor="{"start" if index == 0 else "end" if index == 4 else "middle"}">'
            f"{axis_date(t)}</text>"
        )
    for index, (name, color, points) in enumerate(series):
        coordinates = " ".join(f"{x(t):.2f},{y(v):.2f}" for t, v in points)
        if index == 0:
            area_base = y(0) if percent else 202
            parts.append(
                f'<polygon points="{x(points[0][0]):.2f},{area_base:.2f} {coordinates} '
                f'{x(points[-1][0]):.2f},{area_base:.2f}" fill="{color}" opacity=".075"/>'
            )
        dash = ' stroke-dasharray="6 5"' if index else ""
        parts.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            f'stroke-width="2.4" stroke-linejoin="round"{dash}><title>'
            f"{escape(name)} · {value_text(points[-1][1])}</title></polyline>"
        )
        # A small, bounded set of keyboard-focusable exact observations, not interpolation.
        chosen = sorted({round(i * (len(points) - 1) / 6) for i in range(7)})
        for point_index in chosen:
            t, value = points[point_index]
            px, py = x(t), y(value)
            tooltip_x = min(width - 180, max(62, px - 70))
            tooltip_y = max(3, py - 46)
            text = f"{axis_date(t)} {datetime.fromtimestamp(t, UTC):%H:%M} · {value_text(value)}"
            parts.append(
                f'<g class="plot-point" tabindex="0" role="img" aria-label="'
                f'{escape(name)} {escape(text)} UTC">'
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="8" fill="transparent"/>'
                f'<circle class="point-dot" cx="{px:.2f}" cy="{py:.2f}" r="3" '
                f'fill="{color}"/><g class="plot-tip" aria-hidden="true">'
                f'<rect x="{tooltip_x:.2f}" y="{tooltip_y:.2f}" width="161" height="30" rx="6"/>'
                f'<text x="{tooltip_x + 8:.2f}" y="{tooltip_y + 19:.2f}">{text}</text>'
                "</g></g>"
            )
    return "".join(parts) + "</svg>"


def responsive_plot(
    series: list[tuple[str, str, list[tuple[int, float]]]], *, percent: bool, title: str
) -> str:
    return (
        '<div class="desktop-plot">'
        + line_plot(series, percent=percent, title=title)
        + '</div><div class="mobile-plot">'
        + line_plot(series, percent=percent, title=title, compact=True)
        + "</div>"
    )


def performance(run: Run, matching: list[Run]) -> str:
    candidates = [
        other for other in matching if other is not run and other.name != run.name and other.equity
    ]
    others = sorted(candidates, key=lambda item: item.name != "breakout-baseline-v1")[:1]
    view_label = "Return vs baseline" if others else "Trading return"
    series = []
    for index, item in enumerate([run, *others]):
        points = list(item.equity)
        if points and item.started_at is not None and item.started_at < points[0][0]:
            points.insert(0, (item.started_at, item.starting_equity))
        series.append((label(item), MINT if index == 0 else BLUE, points))
    returns = [
        (name, color, [(t, value / item.starting_equity - 1) for t, value in points])
        for (name, color, points), item in zip(series, [run, *others], strict=True)
    ]
    legend = "".join(
        f'<span><i style="--series:{color}" class="legend-dot '
        f'{"dashed" if index else ""}"></i>{escape(name)}</span>'
        for index, (name, color, _) in enumerate(series)
    )
    return (
        '<article class="performance panel" id="performance"><div class="panel-heading">'
        '<div><span class="eyebrow">The big picture</span><h2>Performance</h2></div>'
        '<span class="mini-badge">After trading costs</span></div>'
        '<fieldset class="chart-switch"><legend class="sr-only">Performance chart view</legend>'
        '<input type="radio" name="chart-view" id="view-return" checked>'
        f'<label for="view-return">{view_label}</label>'
        '<input type="radio" name="chart-view" id="view-equity">'
        '<label for="view-equity">Account value</label>'
        '<div class="chart-panels"><div class="return-panel">'
        + responsive_plot(returns, percent=True, title="Recorded cumulative trading return")
        + '</div><div class="equity-panel">'
        + responsive_plot(series, percent=False, title="Recorded account equity in USDT")
        + "</div></div></fieldset>"
        f'<div class="chart-footer"><div class="legend">{legend}</div>'
        "<span>Sampled · UTC</span></div></article>"
    )


def daily_chart(run: Run) -> str:
    if not run.daily_returns:
        return empty("No recorded daily returns")
    days = run.daily_returns[-14:]
    magnitude = max(abs(value) for _, value in days) or 0.001
    step = 440 / len(days)
    parts = [
        '<svg class="bar-plot" viewBox="0 0 510 210" role="img" '
        'aria-label="Daily returns, complete UTC days"><title>Daily returns</title>'
        '<path class="zero-line" d="M48 96H488"/>'
        '<text class="axis" x="38" y="100" text-anchor="end">0%</text>'
    ]
    for index, (t, value) in enumerate(days):
        px = 48 + step * (index + 0.5)
        bar_height = abs(value) / magnitude * 59
        py = 96 - bar_height if value >= 0 else 96
        day = t - 86400
        text = f"{axis_date(day)} · {value:+.2%}"
        color = MINT if value > 0 else RED if value < 0 else "#617582"
        parts.append(
            f'<g tabindex="0" class="daily-bar" role="img" aria-label="{text}" '
            f'data-value="{value}"><title>{text}</title>'
            f'<rect x="{px - min(16, step * 0.3):.2f}" y="{py:.2f}" '
            f'width="{min(32, step * 0.6):.2f}" height="{max(2, bar_height):.2f}" '
            f'rx="3" fill="{color}"/>'
            f'<text class="bar-value" x="{px:.2f}" y="'
            f'{py - 9 if value >= 0 else 96 + bar_height + 15:.2f}" text-anchor="middle">'
            f'{value:+.2%}</text><text class="axis" x="{px:.2f}" y="191" '
            f'text-anchor="middle">{datetime.fromtimestamp(day, UTC):%d %b}</text></g>'
        )
    return (
        "".join(parts)
        + '</svg><span class="chart-caption">Last 14 complete days at most · UTC</span>'
    )


def decisions(run: Run) -> str:
    counts = [
        ("Wait", run.choice_counts.get("wait", 0), BLUE),
        ("Enter", run.choice_counts.get("enter", 0), MINT),
        ("Unavailable", run.policy_errors or 0, AMBER),
    ]
    total = sum(value for _, value, _ in counts)
    if not total:
        return empty("No recorded model decisions")
    parts = [
        '<div class="decision-graphic"><svg viewBox="0 0 180 180" role="img" '
        'aria-label="Recorded evaluation outcomes"><title>'
        + escape(", ".join(f"{name}: {value}" for name, value, _ in counts))
        + '</title><circle cx="90" cy="90" r="66" class="ring-track"/>'
    ]
    offset = 0.0
    for name, value, color in counts:
        length = value / total * 100
        if value:
            parts.append(
                f'<circle cx="90" cy="90" r="66" fill="none" stroke="{color}" '
                f'stroke-width="12" pathLength="100" stroke-dasharray="{length} '
                f'{100 - length}" stroke-dashoffset="{-offset}" '
                f'transform="rotate(-90 90 90)"><title>{name}: {value}</title></circle>'
            )
        offset += length
    parts.append(
        f'<text x="90" y="88" text-anchor="middle" class="ring-number">{total}</text>'
        '<text x="90" y="109" text-anchor="middle" class="axis">evaluations</text>'
        '</svg></div><ul class="decision-legend">'
    )
    for name, value, color in counts:
        parts.append(
            f'<li><span><i class="legend-dot" style="--series:{color}"></i>{name}</span>'
            f'<strong>{value}</strong><span class="muted">{value / total:.0%}</span></li>'
        )
    return "".join(parts) + "</ul>"


def timeline(run: Run) -> str:
    if not run.activity:
        return empty("No recorded trades")
    rows = []
    for item in reversed(run.activity):
        entered = item.kind == "ENTER"
        amount = f"{item.price:,.2f} USDT" if entered else f"{item.profit:+.2f} USDT"
        tone = (
            "positive" if entered or (item.profit is not None and item.profit >= 0) else "negative"
        )
        rows.append(
            f'<li><span class="event-icon {tone}" aria-hidden="true">'
            f'{"↗" if entered else "↙"}</span><div class="event-content">'
            f'<div class="event-title"><strong>{"Bought" if entered else "Closed"} '
            f'{escape(item.symbol)}</strong><span class="{tone}">{amount}</span></div>'
            f"{stamp(item.time)}<small>{'Fill price' if entered else 'Trade P&L after fees'}"
            "</small></div></li>"
        )
    return '<ol class="activity-list">' + "".join(rows) + "</ol>"


def milestones() -> str:
    return (
        '<section class="progress-strip" aria-label="Agent development milestones">'
        '<div><span class="milestone-icon done">✓</span><span><strong>Jev connected</strong>'
        '<small>30 Sep 2026</small></span></div><span class="progress-connector"></span>'
        '<div><span class="milestone-icon current">◷</span><span><strong>Testing</strong>'
        "<small>First pilot · 30 Sep 2026</small></span></div>"
        '<span class="progress-connector pending"></span>'
        '<div><span class="milestone-icon">◇</span><span><strong>Learning</strong>'
        "<small>Teacher &amp; memory not active</small></span></div></section>"
    )


def dashboard(run: Run, runs: list[Run]) -> str:
    matching = [
        other
        for other in runs
        if run.comparison_key is not None and other.comparison_key == run.comparison_key
    ]
    cost = f"${run.inference_cost_usd:.4f}" if run.inference_cost_usd is not None else "Unknown"
    if run.inference_cost_usd is not None and 0 < run.inference_cost_usd < 0.0001:
        cost = "<$0.0001"
    profit = run.ending_equity - run.starting_equity
    metrics = [
        (
            "Trading return",
            f"{run.net_return:+.2%}",
            f"{profit:+.2f} USDT",
            "↗" if run.net_return >= 0 else "↘",
        ),
        ("Biggest dip", f"{run.drawdown:.2%}", "Peak to trough", "↘"),
        (
            "Closed trades",
            str(run.closed_trades),
            f"{run.open_positions if run.open_positions is not None else 'Unknown'} open",
            "⇄",
        ),
        ("AI cost · this run", cost, "USD · recorded calls", "✧"),
    ]
    cards = "".join(
        f'<div class="metric-card"><dt><span>{escape(title)}</span>'
        f'<span class="metric-icon" aria-hidden="true">{icon}</span></dt>'
        f'<dd>{escape(value)}</dd><span class="metric-sub">{escape(sub)}</span></div>'
        for title, value, sub, icon in metrics
    )
    tone = "positive" if run.net_return >= 0 else "negative"
    cards = cards.replace("<dd>", f'<dd class="{tone}">', 1)
    period = (
        f'{stamp(run.started_at, "%d %b %Y")}<span aria-hidden="true"> → </span>'
        f"{stamp(run.ended_at, '%d %b %Y')}<small>Historical window · UTC</small>"
        if run.started_at is not None and run.ended_at is not None
        else escape(run.period)
    )
    warning = ""
    if run.policy_errors:
        warning = (
            f'<aside class="warning"><span class="warning-icon" aria-hidden="true">!</span>'
            f"<strong>Incomplete test</strong><span>{run.policy_errors} candidate evaluations "
            'unavailable · full performance unproven</span><a href="#evidence">Details ↗</a>'
            "</aside>"
        )
    if run.halted:
        warning += (
            '<aside class="warning"><strong>Risk halt recorded</strong>New entries stopped.</aside>'
        )
    symbols = " · ".join(run.symbols) if run.symbols else run.kind
    days = str(run.complete_days) if run.complete_days is not None else "—"
    return (
        '<section class="overview" aria-label="Selected experiment"><div class="intro">'
        '<div><div class="eyebrow">Your research workspace</div>'
        f'<h1>{escape(label(run))}<span class="status-pill">Research only · Not live</span></h1>'
        f'<span class="instrument">{escape(symbols)}<span> / </span>'
        "Historical backtest</span></div>"
        f'<div class="period">{period}</div></div><dl class="metrics">{cards}</dl>'
        '<div class="metric-note">Trading fees included · AI costs separate</div>'
        + warning
        + '<div class="visual-grid"><div class="main-column">'
        + performance(run, matching)
        + '<div class="secondary-grid"><article class="panel"><div class="panel-heading">'
        '<div><span class="eyebrow">Day by day</span><h2>Daily returns</h2></div>'
        f'<span class="mini-badge">{days} days'
        "</span></div>" + daily_chart(run) + "</article>"
        '<article class="panel drawdown-panel"><div class="panel-heading"><div>'
        '<span class="eyebrow">Risk in view</span><h2>Drawdown</h2></div>'
        f'<span class="drawdown-value">{run.drawdown:.2%}<small>max overall</small></span></div>'
        + (
            line_plot(
                [("Candle-close drawdown", RED, [(t, -v) for t, v in run.close_drawdowns])],
                percent=True,
                below_zero=True,
                compact=True,
                title="Drawdown at recorded candle closes",
            )
            if len(run.close_drawdowns) > 1
            else empty("No recorded drawdown curve")
        )
        + '<span class="chart-caption">Candle closes · intrabar extremes not shown</span>'
        "</article></div>" + milestones() + '</div><div class="side-column">'
        '<article class="panel decisions-panel"><div class="panel-heading"><div>'
        '<span class="eyebrow">Selectivity</span><h2>Decisions</h2></div>'
        '<span class="tiny-dot" aria-hidden="true"></span></div>'
        + decisions(run)
        + '</article><article class="panel activity-panel"><div class="panel-heading"><div>'
        '<span class="eyebrow">Historical activity</span><h2>Trade timeline</h2></div>'
        '<span class="mini-badge">UTC</span></div>'
        + timeline(run)
        + '<span class="chart-caption">Last 6 fills · simulated market time</span></article>'
        "</div></div></section>"
    )
