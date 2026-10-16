"""Dashboard observation must not mutate or invent replay evidence."""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest

from src.cockpit.live import LiveFeed, journal_status
from src.replay.__main__ import BreakoutBaseline
from src.replay.engine import Candle, Replay, Settings
from src.replay.journal import Journal

if TYPE_CHECKING:
    from pathlib import Path


def bars() -> list[Candle]:
    return [Candle("BTC", i * 300, 100, 100, 100, 100, 1) for i in range(24)]


def test_committed_progress_running_paused_and_completed(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    j = Journal(path)
    Replay(Settings(), j).run(bars(), BreakoutBaseline(), stop_after=21)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    assert journal_status(path)["state"] == "running"
    assert journal_status(path)["steps"] == 21
    assert "policy_state" not in journal_status(path)
    j.close()
    assert journal_status(path)["state"] == "paused"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with pytest.raises(FileNotFoundError):
        journal_status(tmp_path / "missing.sqlite")
    assert not (tmp_path / "missing.sqlite").exists()
    j = Journal(path, resume=True)
    Replay(Settings(), j).run(bars(), BreakoutBaseline(), resume=True)
    j.close()
    assert journal_status(path)["state"] == "complete"


def test_invalid_checkpoint_is_not_shown_as_live(tmp_path: Path) -> None:
    path = tmp_path / "run.sqlite"
    j = Journal(path)
    Replay(Settings(), j).run(bars(), BreakoutBaseline(), stop_after=21)
    j.connection.execute("UPDATE checkpoint SET checksum='wrong'")
    j.connection.commit()
    j.close()
    with pytest.raises(ValueError, match="checkpoint"):
        journal_status(path)


def test_feed_refreshes_completed_results_and_retains_them_on_error(tmp_path: Path) -> None:
    source = tmp_path / "research"
    source.mkdir()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": []}))
    feed = LiveFeed(config)
    first, html = feed.sample(now=1000)
    assert first["agent_state"] == "idle" and first["completed_runs"] == 0
    assert html is not None and "No saved runs" in html
    j = Journal(source / "new.sqlite")
    Replay(Settings(), j).run(bars(), BreakoutBaseline(), stop_after=21)
    progress, partial_html = feed.sample(now=1060)
    assert partial_html is None
    assert progress["report_updated_at"] == first["report_updated_at"]
    assert progress["agent_state"] == "running" and progress["completed_runs"] == 0
    j.close()
    j = Journal(source / "new.sqlite", resume=True)
    Replay(Settings(), j).run(bars(), BreakoutBaseline(), resume=True)
    j.close()
    done, html = feed.sample(now=1120)
    assert done["completed_runs"] == 1 and html is not None
    assert done["report_revision"] != first["report_revision"]
    same, unchanged = feed.sample(now=1180)
    assert unchanged is None and same["report_revision"] == done["report_revision"]
    assert same["report_updated_at"] == 1120 and same["updated_at"] == 1180
    (source / "broken.sqlite").write_bytes(b"not a database")
    broken, html = feed.sample(now=1240)
    assert broken["agent_state"] == "unavailable" and broken["source_errors"]
    assert html is None and broken["report_revision"] == done["report_revision"]
    assert broken["report_updated_at"] == 1120


def test_removed_journal_keeps_warning_and_report_on_later_polls(tmp_path: Path) -> None:
    source = tmp_path / "research"
    source.mkdir()
    path = source / "run.sqlite"
    j = Journal(path)
    Replay(Settings(), j).run(bars(), BreakoutBaseline())
    j.close()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": []}))
    feed = LiveFeed(config)
    before, _ = feed.sample(now=1000)
    path.unlink()
    for now in (1060, 1120):
        status, html = feed.sample(now=now)
        assert status["source_errors"] and html is None
        assert status["report_revision"] == before["report_revision"]


@pytest.mark.parametrize("tamper", ["data", "settings"])
def test_reference_must_match_recorded_baseline(tmp_path: Path, tamper: str) -> None:
    source = tmp_path / "research"
    source.mkdir()
    path, csv = source / "baseline.sqlite", source / "candles.csv"
    csv.write_text("symbol,opened_at,open,high,low,close,volume\n" + "\n".join(
        f"BTC,{c.opened_at},100,100,100,100,1" for c in bars()
    ))
    j = Journal(path)
    j.record({"kind": "MANIFEST", "policy": "breakout-baseline-v1",
              "sha256": hashlib.sha256(csv.read_bytes()).hexdigest()})
    Replay(Settings(), j).run(bars(), BreakoutBaseline())
    j.close()
    settings = {"fee": 0.002} if tamper == "settings" else {}
    if tamper == "data":
        csv.write_text(csv.read_text().replace(",100,1", ",100,2"))
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": [
        {"baseline": str(path), "candles": str(csv), "settings": settings},
    ]}))
    status, html = LiveFeed(config).sample(now=1000)
    assert status["source_errors"] and html is None


@pytest.mark.parametrize("corruption", ["zip", "structure"])
def test_corrupt_archive_retains_last_report_then_recovers(
    tmp_path: Path, corruption: str,
) -> None:
    import zipfile

    source = tmp_path / "research"
    source.mkdir()
    archive = tmp_path / "archive.zip"
    def write_archive() -> None:
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("archive.json", json.dumps({"strategy": {"Baseline": {
                "starting_balance": 1000, "final_balance": 1000, "total_trades": 0,
                "wins": 0, "max_drawdown_account": 0, "backtest_start": "2024-01-01",
                "backtest_end": "2024-01-02", "trades": [],
            }}}))
    write_archive()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [str(archive)],
                                  "references": []}))
    feed = LiveFeed(config)
    before, _ = feed.sample(now=1000)
    if corruption == "zip":
        archive.write_bytes(b"corrupt archive")
    else:
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("archive.json", json.dumps({"strategy": []}))
    failed, html = feed.sample(now=1060)
    assert failed["source_errors"] and html is None
    assert failed["report_revision"] == before["report_revision"]
    write_archive()
    restored, html = feed.sample(now=1120)
    assert not restored["source_errors"] and html is not None


def test_cloud_failure_retries_without_advancing_confirmed_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from src.cockpit.live import CloudPublisher

    calls: list[list[str]] = []
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, args, stderr="SECRET")
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    publisher = CloudPublisher(tmp_path)
    assert not publisher.send("a" * 64, now=0)
    assert publisher.revision is None
    assert not publisher.send("a" * 64, now=59)
    assert len(calls) == 1
    assert publisher.send("a" * 64, now=60)
    assert publisher.revision == "a" * 64
    assert publisher.send("b" * 64, now=120)
    assert "a" * 64 in calls[-1]


def test_observer_excludes_second_writer_and_restarts_after_sigterm(tmp_path: Path) -> None:
    import select
    import subprocess
    import sys

    source = tmp_path / "research"
    source.mkdir()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": []}))
    command = [sys.executable, "-m", "src.cockpit.live", "--config", str(config),
               "--output", str(tmp_path / "live")]
    first = subprocess.Popen([*command, "--watch"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        assert first.stdout is not None
        ready, _, _ = select.select([first.stdout], [], [], 10)
        assert ready and json.loads(first.stdout.readline())["agent_state"] == "idle"
        other = subprocess.run(command, capture_output=True, text=True, timeout=10)
        assert other.returncode != 0 and "BlockingIOError" in other.stderr
    finally:
        first.terminate()
        first.communicate(timeout=10)
    # The inode remains, but the OS lock is released; no manual deletion needed.
    assert (tmp_path / "live/publisher.lock").is_file()
    restarted = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert restarted.returncode == 0
    assert json.loads(restarted.stdout)["agent_state"] == "idle"


def test_cloud_retries_are_bounded_and_do_not_log_provider_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    import subprocess

    from src.cockpit.live import CloudPublisher

    def fail(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, "node", stderr="SECRET")
    monkeypatch.setattr(subprocess, "run", fail)
    publisher = CloudPublisher(tmp_path)
    for now, delay in ((0, 60), (60, 120), (180, 240), (420, 300), (720, 300)):
        assert not publisher.send("a" * 64, now=now)
        assert publisher.next_attempt == now + delay
        assert publisher.revision is None
    captured = capsys.readouterr()
    assert "SECRET" not in captured.out + captured.err
    assert '"cloud": "unavailable"' in captured.out


def test_restart_restores_verified_report_and_missing_journal_warning(tmp_path: Path) -> None:
    source = tmp_path / "research"
    source.mkdir()
    path = source / "run.sqlite"
    journal = Journal(path)
    Replay(Settings(), journal).run(bars(), BreakoutBaseline())
    journal.close()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": []}))
    output = tmp_path / "live"
    output.mkdir()
    feed = LiveFeed(config)
    before, html = feed.sample(now=1000)
    assert html is not None
    (output / "report.html").write_text(html)
    feed.persist(output)
    unchanged, page = LiveFeed(config, output=output).sample(now=1030)
    assert page is None
    assert unchanged["report_revision"] == before["report_revision"]
    assert unchanged["report_updated_at"] == before["report_updated_at"]
    path.unlink()
    restarted = LiveFeed(config, output=output)
    after, html = restarted.sample(now=1060)
    assert after["source_errors"] and html is None
    for key in ("report_revision", "report_updated_at", "completed_runs"):
        assert after[key] == before[key]
    (output / "report.html").write_text("tampered")
    with pytest.raises(ValueError, match="Saved report"):
        LiveFeed(config, output=output)


def test_journal_disappearing_during_scan_retains_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    source = tmp_path / "research"
    source.mkdir()
    path = source / "run.sqlite"
    journal = Journal(path)
    Replay(Settings(), journal).run(bars(), BreakoutBaseline())
    journal.close()
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"roots": [str(source)], "archives": [], "references": []}))
    feed = LiveFeed(config)
    before, _ = feed.sample(now=1000)
    def vanish(*args: object) -> object:
        yield path
        path.unlink()
    monkeypatch.setattr(Path, "rglob", vanish)
    after, html = feed.sample(now=1060)
    assert after["source_errors"] and html is None
    assert after["report_revision"] == before["report_revision"]
