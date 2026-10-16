"""Public source import must not silently repair or relabel market observations."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from src.replay.dataset import convert

if TYPE_CHECKING:
    from pathlib import Path


def fixture(tmp_path: Path, times: list[int], factor: int = 1000) -> tuple[Path, Path]:
    month = datetime.fromtimestamp(times[0], UTC).strftime("%Y-%m")
    archive = tmp_path / f"BTCUSDT-5m-{month}.zip"
    rows = [f"{t*factor},100,102,99,101,2,{(t+300)*factor-1},202,1,1,101,0" for t in times]
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(archive.stem + ".csv", "\n".join(rows))
    checksum = tmp_path / "source.CHECKSUM"
    checksum.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name)
    return archive, checksum


@pytest.mark.parametrize("start,factor", [(1717200000, 1000), (1735689600, 1000000)])
def test_verified_contiguous_data_and_provenance(
    tmp_path: Path, start: int, factor: int,
) -> None:
    source, checksum = fixture(tmp_path, [start, start+300, start+600], factor)
    original = source.read_bytes()
    output = tmp_path / "candles.csv"
    manifest = convert(source, checksum, "BTC/USDT", start, start+600, output)
    assert manifest["rows"] == 2
    assert manifest["csv_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert str(start*factor) not in output.read_text()
    assert f"BTC/USDT,{start},100.0,102.0,99.0,101.0,2.0" in output.read_text()
    assert json.loads(output.with_suffix(".manifest.json").read_text()) == manifest
    assert source.read_bytes() == original


@pytest.mark.parametrize("offsets", [[0], [0, 0], [0, 301], [300, 600]])
def test_gaps_duplicates_or_misalignment_rejected(tmp_path: Path, offsets: list[int]) -> None:
    start = 1717200000
    source, checksum = fixture(tmp_path, [start+t for t in offsets])
    output = tmp_path / "candles.csv"
    with pytest.raises(ValueError):
        convert(source, checksum, "BTC/USDT", start, start+600, output)
    assert not output.exists()


def test_checksum_symbol_and_existing_output_rejected(tmp_path: Path) -> None:
    start = 1717200000
    source, checksum = fixture(tmp_path, [start, start+300])
    output = tmp_path / "candles.csv"
    with pytest.raises(ValueError, match="symbol"):
        convert(source, checksum, "ETH/USDT", start, start+600, output)
    checksum.write_text("0"*64 + "  " + source.name)
    with pytest.raises(ValueError, match="checksum"):
        convert(source, checksum, "BTC/USDT", start, start+600, output)
    output.write_text("preserve me")
    with pytest.raises((ValueError, FileExistsError)):
        convert(source, checksum, "BTC/USDT", start, start+600, output)
    assert output.read_text() == "preserve me"
