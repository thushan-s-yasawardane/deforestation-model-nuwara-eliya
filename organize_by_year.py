#!/usr/bin/env python3
"""organize_by_year.py

Organize Landsat files into year folders by extracting a YYYYMMDD token from the filename.

This repo's notebooks expect Landsat Collection 2 Level-2 GeoTIFFs (e.g. *_SR_B4.TIF, *_QA_PIXEL.TIF)
to live under year folders such as 2014/, 2015/, ...

Example filename pattern:
    LC08_L2SP_141055_20150414_20200908_02_T1_SR_B4.TIF
                              ^^^^^^^^

Usage (copy into year folders):
    python organize_by_year.py --source "C:\\path\\to\\Satelite Images" --dest "C:\\path\\to\\Landsat_By_Year" --mode copy

Usage (dry-run):
    python organize_by_year.py --source "C:\\path\\to\\Satelite Images" --dest "C:\\path\\to\\Landsat_By_Year" --mode copy --dry-run
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def extract_year_from_filename(filename: str) -> str | None:
    """Extract year from a Landsat filename by finding the first YYYYMMDD token."""
    parts = filename.split("_")
    for part in parts:
        if len(part) == 8 and part.isdigit():
            return part[:4]
    return None


@dataclass(frozen=True)
class OrganizeOptions:
    source: Path
    dest: Path
    mode: str  # "copy" or "move"
    recursive: bool
    dry_run: bool


def iter_candidate_files(source: Path, recursive: bool) -> Iterable[Path]:
    globber = source.rglob("*") if recursive else source.glob("*")
    for path in globber:
        if path.is_file() and not path.name.startswith("."):
            yield path


def organize_files_by_year(options: OrganizeOptions) -> None:
    if not options.source.exists():
        raise FileNotFoundError(f"Source folder not found: {options.source}")

    options.dest.mkdir(parents=True, exist_ok=True)

    candidates = list(iter_candidate_files(options.source, options.recursive))
    to_process: list[tuple[Path, Path]] = []
    skipped: list[Path] = []

    for file_path in candidates:
        if file_path.name == Path(__file__).name:
            continue
        year = extract_year_from_filename(file_path.name)
        if not year:
            skipped.append(file_path)
            continue
        year_dir = options.dest / year
        dest_path = year_dir / file_path.name
        to_process.append((file_path, dest_path))

    print(f"Source: {options.source}")
    print(f"Dest:   {options.dest}")
    print(f"Mode:   {options.mode}  |  Recursive: {options.recursive}  |  Dry-run: {options.dry_run}")
    print(f"Found {len(candidates)} files; {len(to_process)} matched a year; {len(skipped)} skipped")

    if not to_process:
        print("Nothing to do.")
        return

    copier = shutil.copy2 if options.mode == "copy" else shutil.move

    # Create year folders first
    for year in sorted({dst.parent.name for _, dst in to_process}):
        (options.dest / year).mkdir(parents=True, exist_ok=True)

    # Execute
    moved = 0
    for src, dst in to_process:
        if dst.exists():
            # Avoid clobbering silently
            continue
        if options.dry_run:
            moved += 1
            continue
        try:
            copier(str(src), str(dst))
            moved += 1
        except Exception as exc:
            print(f"Error processing {src.name}: {exc}")

    print("=" * 60)
    print(f"Done. {moved} files {'planned' if options.dry_run else 'written'} into year folders.")
    if skipped:
        print(f"Skipped {len(skipped)} files without a YYYYMMDD token.")
    print("Note: existing destination files were left untouched.")


def parse_args() -> OrganizeOptions:
    parser = argparse.ArgumentParser(description="Organize Landsat files into year folders")
    parser.add_argument("--source", required=True, help="Folder containing Landsat GeoTIFFs")
    parser.add_argument("--dest", required=True, help="Destination folder where YYYY/ subfolders will be created")
    parser.add_argument("--mode", choices=["copy", "move"], default="copy", help="Copy or move files")
    parser.add_argument("--recursive", action="store_true", help="Scan source folder recursively")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without copying/moving")
    args = parser.parse_args()
    return OrganizeOptions(
        source=Path(args.source),
        dest=Path(args.dest),
        mode=args.mode,
        recursive=bool(args.recursive),
        dry_run=bool(args.dry_run),
    )


if __name__ == "__main__":
    organize_files_by_year(parse_args())
