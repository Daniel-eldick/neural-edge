"""Convert a verified Binance monthly spot 5m ZIP into a strict replay dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.replay.engine import Candle


def convert(archive: Path, checksum: Path, symbol: str, start: int, end: int,
            output: Path) -> dict[str, Any]:
    if (type(start) is not int or type(end) is not int or start < 0
            or end <= start or start % 300 or end % 300):
        raise ValueError("Use an increasing UTC range aligned to five-minute candles")
    month = datetime.fromtimestamp(start, UTC).strftime("%Y-%m")
    if (not re.fullmatch(r"[A-Z0-9]+/[A-Z0-9]+", symbol)
            or archive.name != f'{symbol.replace("/", "")}-5m-{month}.zip'):
        raise ValueError("Archive filename does not match the requested symbol/month")
    manifest_path = output.with_suffix(".manifest.json")
    if output.exists() or manifest_path.exists() or output == manifest_path:
        raise FileExistsError("Dataset output/manifest must be new files")
    parts = checksum.read_text().strip().split()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if len(parts) != 2 or parts != [digest, archive.name]:
        raise ValueError("Archive checksum or filename does not match")
    bars: list[Candle] = []
    with zipfile.ZipFile(archive) as zipped:
        member = archive.stem + ".csv"
        if zipped.namelist() != [member] or zipped.getinfo(member).file_size > 64 * 1024 * 1024:
            raise ValueError("Expected one CSV member of at most 64 MiB")
        with zipped.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8") as stream:
            for row in csv.reader(stream):
                if len(row) != 12:
                    raise ValueError("Expected 12 Binance spot kline columns")
                timestamp = int(row[0])
                factor = 1_000_000 if timestamp >= 100_000_000_000_000 else 1000
                opened_at = timestamp // factor
                if not start <= opened_at < end:
                    continue
                if timestamp % factor or int(row[6]) != timestamp + 300 * factor - 1:
                    raise ValueError("Invalid candle open/close time")
                bars.append(Candle(symbol, opened_at, *[float(value) for value in row[1:6]]))
    bars.sort(key=lambda candle: candle.opened_at)
    if (len(bars) != (end-start)//300
            or any(c.opened_at != start + i*300 for i, c in enumerate(bars))):
        raise ValueError("Missing, duplicate or misaligned candles; no repairs applied")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(asdict(bars[0])), lineterminator="\n")
    writer.writeheader()
    writer.writerows(asdict(candle) for candle in bars)
    data = buffer.getvalue().encode()
    manifest = {"source": archive.name, "source_sha256": digest,
                "source_url": f'https://data.binance.vision/data/spot/monthly/klines/'
                f'{symbol.replace("/", "")}/5m/{archive.name}',
                "checksum_verified": True, "symbol": symbol, "interval": 300,
                "start_inclusive": start, "end_exclusive": end, "rows": len(bars),
                "csv_sha256": hashlib.sha256(data).hexdigest(), "repairs": []}
    with output.open("xb") as destination:
        destination.write(data)
    with manifest_path.open("x") as destination:
        json.dump(manifest, destination, indent=2, allow_nan=False)
        destination.write("\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checksum", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start", help="Inclusive UTC date YYYY-MM-DD", required=True)
    parser.add_argument("--end", help="Exclusive UTC date YYYY-MM-DD", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start, end = [int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC).timestamp())
                  for value in (args.start, args.end)]
    print(json.dumps(convert(args.archive, args.checksum, args.symbol, start, end, args.output),
                     indent=2))


if __name__ == "__main__":
    main()
