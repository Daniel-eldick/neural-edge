"""Charts must reflect recorded evidence, including unavailable and negative values."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from src.cockpit.report import load_journal, render
from src.replay.engine import Candle, Decision, Observation, Replay, Settings
from src.replay.journal import Journal


def recorded_run(path: Path) -> None:
    class Waiting:
        def decide(self, observation: Observation) -> Decision:
            return Decision()

    journal = Journal(path)
    journal.record({"kind": "MANIFEST", "policy": "jev-breakout-filter-v1", "sha256": "a" * 64})
    Replay(Settings(), journal).run(
        [Candle("BTC/USDT", i * 300, 100, 100, 100, 100, 1) for i in range(576)],
        Waiting(),
    )
    journal.close()


def test_visual_import_uses_recorded_days_and_preserves_source(tmp_path: Path) -> None:
    path = tmp_path / "journal.sqlite"
    recorded_run(path)
    before = path.read_bytes()
    run = load_journal(path)
    assert run.daily_returns == [(86400, 0.0), (172800, 0.0)]
    assert run.started_at == 0 and run.ended_at == 172800
    assert run.symbols == ("BTC/USDT",)
    assert run.choice_counts == {}
    assert run.activity == []
    assert path.read_bytes() == before
    html = render([run])
    assert "Daily returns" in html and "Historical activity" in html
    assert "No recorded model decisions" in html
    assert "No recorded trades" in html
    assert 'datetime="1970-01-03T00:00:00+00:00"' in html


def test_comparison_chart_excludes_different_inputs_and_handles_flat_returns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.sqlite"
    recorded_run(path)
    agent = load_journal(path)
    wrong = replace(agent, name="wrong-data", comparison_key="other", ending_equity=2000)
    baseline = replace(agent, name="breakout-baseline-v1")
    html = render([wrong, baseline, agent])
    overview = html.split('<details class="evidence"')[0]
    assert "Return vs baseline" in overview
    assert "Simple strategy" in overview
    assert "wrong-data" not in overview
    assert "nan" not in overview.lower() and "inf%" not in overview
    assert 'name="chart-view"' in overview


def test_daily_chart_negative_zero_and_positive_values(tmp_path: Path) -> None:
    path = tmp_path / "journal.sqlite"
    recorded_run(path)
    run = replace(load_journal(path), daily_returns=[(86400, -0.02), (172800, 0), (259200, 0.01)])
    html = render([run])
    assert "-2.00%" in html and "+1.00%" in html
    assert 'data-value="-0.02"' in html
    assert 'data-value="0"' in html
    assert 'data-value="0.01"' in html


def test_visual_trade_events_and_decision_counts(tmp_path: Path) -> None:
    path = tmp_path / "events.sqlite"
    journal = Journal(path)
    events = [
        {
            "kind": "START",
            "time": 0,
            "symbols": ["BTC/USDT"],
            "settings": {"fee": 0, "slippage": 0},
        },
        {
            "kind": "MODEL_CHOICE",
            "time": 300,
            "symbol": "BTC/USDT",
            "model": "jev",
            "choice": "wait",
            "cost_nano_usd": 10,
        },
        {
            "kind": "MODEL_CHOICE",
            "time": 600,
            "symbol": "BTC/USDT",
            "model": "jev",
            "choice": "enter",
            "cost_nano_usd": 10,
        },
        {"kind": "ENTER", "time": 600, "symbol": "<img src=x>", "price": 100},
        {"kind": "EXIT", "time": 900, "symbol": "<img src=x>", "price": 99, "net_profit": -1},
        {"kind": "EQUITY", "time": 900, "equity": 999},
        {
            "kind": "RESULT",
            "time": 900,
            "starting_equity": 1000,
            "ending_equity": 999,
            "max_drawdown": 0.001,
            "closed_trades": 1,
            "open_positions": 0,
            "halted": False,
        },
    ]
    for event in events:
        journal.record(event)
    journal.close()
    run = load_journal(path)
    assert run.choice_counts == {"wait": 1, "enter": 1}
    assert [(event.time, event.kind) for event in run.activity] == [(600, "ENTER"), (900, "EXIT")]
    assert run.activity[-1].profit == -1
    html = render([run])
    assert "&lt;img src=x&gt;" in html and "<img src=x>" not in html
    assert "1970-01-01T00:15:00+00:00" in html
    # Recorded choice counts are decisions, not executed trade counts.
    assert "Decisions" in html and "Wait" in html and "Enter" in html


@pytest.mark.parametrize("bad_choice", ["maybe", "WAIT", "<script>"])
def test_unrecognized_model_choice_does_not_become_wait(tmp_path: Path, bad_choice: str) -> None:
    path = tmp_path / "invalid.sqlite"
    journal = Journal(path)
    journal.record(
        {
            "kind": "MODEL_CHOICE",
            "time": 0,
            "symbol": "BTC",
            "model": "jev",
            "choice": bad_choice,
            "cost_nano_usd": 0,
        }
    )
    journal.close()
    with pytest.raises(ValueError, match="choice"):
        load_journal(path)


def test_drawdown_axis_cannot_imply_positive_drawdown() -> None:
    from src.cockpit.visuals import line_plot

    html = line_plot(
        [("Risk", "#ef9c9c", [(0, 0), (300, -0.0036)])], percent=True, title="Risk", below_zero=True
    )
    assert ">0%</text>" in html
    assert ">+" not in html
    assert "-0.4%" in html


def test_memory_chart_prefers_frozen_control_and_labels_window(tmp_path: Path) -> None:
    path = tmp_path / 'journal.sqlite'
    recorded_run(path)
    frozen = load_journal(path)
    baseline = replace(frozen, name='breakout-baseline-v1')
    memory = replace(frozen, name='jev-memory-filter-v1')
    page = render([baseline, frozen, memory])
    overview = page.split('<details class="evidence"')[0]
    assert 'Return vs frozen Jev' in overview
    assert 'Simple strategy' not in overview
    assert 'Jev agent' in overview and 'Jev with memory' in overview
    assert 'Same-input comparison · 1970-01-01' in page
