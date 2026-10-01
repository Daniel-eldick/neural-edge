"""Build an offline results cockpit from saved archives and completed replay journals."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.cockpit.report import load_archive, load_journal, render


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, action="append", default=[])
    parser.add_argument("--journal", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("user_data/cockpit/index.html"))
    args = parser.parse_args()
    runs = [run for path in args.archive for run in load_archive(path)]
    runs.extend(load_journal(path) for path in args.journal)
    output = args.output.resolve()
    if output in {p.resolve() for p in [*args.archive, *args.journal]}:
        parser.error("Output must not overwrite an input file")
    page = render(runs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"Cockpit: {output} ({len(runs)} saved runs)")


if __name__ == "__main__":
    main()
