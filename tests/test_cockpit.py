"""Saved evidence must remain honest, read-only and safe to display."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import zipfile
from typing import TYPE_CHECKING

import pytest

from src.cockpit.__main__ import main
from src.cockpit.report import load_archive, load_journal, render
from src.replay.engine import Candle, Decision, Observation, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


def archive(path: Path) -> None:
    data = {"strategy": {"AlphaStrategy": {
        "starting_balance": 1000, "final_balance": 990, "profit_total_abs": -10,
        "max_drawdown_account": 0.02, "total_trades": 2, "wins": 1,
        "backtest_start": "2024-06-01", "backtest_end": "2024-08-31",
        "trades": [{"pair": "BTC/USDT", "profit_abs": 5, "exit_reason": "roi"},
                   {"pair": "ETH/USDT", "profit_abs": -15, "exit_reason": "stop"}],
    }}}
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr(path.stem + ".json", json.dumps(data))
        zipped.writestr(path.stem + "_config.json", '{"secret":"NEVER-DISPLAY-ME"}')


def test_archive_metrics_are_not_presented_as_learning_or_fake_equity(tmp_path: Path) -> None:
    path = tmp_path / "backtest.zip"
    archive(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    runs = load_archive(path)
    assert len(runs) == 1
    run = runs[0]
    assert run.net_return == pytest.approx(-0.01)
    assert run.win_rate == 0.5
    assert run.equity == []
    page = render(runs)
    assert "NEVER-DISPLAY-ME" not in page
    assert "Learning not evaluated" in page
    assert "Legacy baseline" in page
    assert "No recorded equity curve" in page
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_replay_journal_report_preserves_marked_equity_and_escapes_text(tmp_path: Path) -> None:
    class Policy:
        def decide(self, observation: Observation) -> Decision:
            return Decision(reason="<script>alert('x')</script>")

    path = tmp_path / "run.sqlite"
    journal = Journal(path)
    journal.record({"kind": "MANIFEST", "policy": "test-fixture-policy"})
    Replay(Settings(), journal).run([Candle("BTC", 0, 100, 100, 100, 100, 1)], Policy())
    journal.close()
    before = path.read_bytes()
    run = load_journal(path)
    assert run.ending_equity == 1000
    assert run.equity == [(300, 1000.0)]
    assert run.win_rate is None
    page = render([run])
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page
    assert "Closed trades" in page
    assert "Complete UTC days" in page
    assert "fewer than 30 complete days" in page
    assert path.read_bytes() == before


def test_incomplete_and_missing_journal_fail_without_creating_files(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises((OSError, sqlite3.Error)):
        load_journal(path)
    assert not path.exists()
    journal = Journal(path)
    journal.record({"kind": "START", "time": 0})
    journal.close()
    with pytest.raises(ValueError, match="completed"):
        load_journal(path)


@pytest.mark.parametrize("days,score,reason,valid", [
    (30, 1.25, None, True),
    (30, None, "zero_variance", True),
    (29, 1.25, None, False),
    (30, float("inf"), None, False),
    (30, None, None, False),
])
def test_daily_score_is_read_from_summary_and_validated(
    tmp_path: Path, days: int, score: float | None, reason: str | None, valid: bool,
) -> None:
    path = tmp_path / "metrics.sqlite"
    journal = Journal(path)
    journal.record({"kind": "START", "time": 0, "settings": {"fee": 0, "slippage": 0}})
    journal.record({"kind": "EQUITY", "time": 30 * 86400, "equity": 1100})
    # Deliberately write raw JSON to include a corrupt nonfinite fixture.
    journal.connection.execute("INSERT INTO events(payload) VALUES (?)", (json.dumps({
        "kind": "RESULT", "time": 30 * 86400, "starting_equity": 1000,
        "ending_equity": 1100, "max_drawdown": 0, "closed_trades": 0,
        "open_positions": 1, "halted": False, "daily_sharpe": score,
        "complete_days": days, "sharpe_unavailable_reason": reason,
    }),))
    journal.connection.commit()
    journal.close()
    if not valid:
        with pytest.raises(ValueError):
            load_journal(path)
    else:
        run = load_journal(path)
        assert run.daily_sharpe == score
        assert run.complete_days == days
        page = render([run])
        assert "1.25" in page if score is not None else "zero variance" in page


def test_invalid_numbers_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.zip"
    archive(path)
    with zipfile.ZipFile(path) as zipped:
        data = json.loads(zipped.read(path.stem + ".json"))
    data["strategy"]["AlphaStrategy"]["final_balance"] = float("nan")
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr(path.stem + ".json", json.dumps(data))
    with pytest.raises(ValueError):
        load_archive(path)


def test_failed_journal_is_not_presented_as_completed(tmp_path: Path) -> None:
    path = tmp_path / "failed.sqlite"
    journal = Journal(path)
    journal.record({"kind": "FAILED", "error": "Provider unavailable"})
    journal.close()
    with pytest.raises(ValueError, match="failed run"):
        load_journal(path)


def test_cli_refuses_to_overwrite_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "backtest.zip"
    archive(path)
    before = path.read_bytes()
    monkeypatch.setattr(sys, "argv", ["cockpit", "--archive", str(path), "--output", str(path)])
    with pytest.raises(SystemExit):
        main()
    assert path.read_bytes() == before


def test_cli_generates_empty_or_real_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "cockpit" / "index.html"
    monkeypatch.setattr(sys, "argv", ["cockpit", "--output", str(output)])
    main()
    assert "No saved runs yet" in output.read_text()
    path = tmp_path / "backtest.zip"
    archive(path)
    monkeypatch.setattr(sys, "argv", ["cockpit", "--archive", str(path), "--output", str(output)])
    main()
    assert "AlphaStrategy" in output.read_text()
