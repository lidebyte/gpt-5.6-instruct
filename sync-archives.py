#!/usr/bin/env python3
"""Synchronize public ZIP archives from ignored local Markdown/Python sources."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROMPT_RELATIVE_PATHS = (
    Path("gpt-5.6-sol-unrestricted.md"),
    Path("examples/gpt-5.6-sol-unrestricted.md"),
)


def archive_path_for(source: Path) -> Path:
    return source.with_suffix(".zip")


def write_single_file_archive(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(
        temporary,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        archive.write(source, arcname=source.name)
    temporary.replace(destination)


def sources() -> list[Path]:
    prompt_sources = [PROJECT_ROOT / relative for relative in PROMPT_RELATIVE_PATHS]
    script_sources = sorted((PROJECT_ROOT / "scripts").glob("*.py"))
    return prompt_sources + script_sources


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update same-name ZIP archives for ignored prompt and test-script sources."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that every archive exists and exactly matches its local source.",
    )
    args = parser.parse_args()

    missing = [path for path in sources() if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[错误] 缺少源文件: {path.relative_to(PROJECT_ROOT)}", file=sys.stderr)
        return 2

    failed = False
    for source in sources():
        destination = archive_path_for(source)
        relative_source = source.relative_to(PROJECT_ROOT)
        relative_destination = destination.relative_to(PROJECT_ROOT)
        if args.check:
            try:
                with zipfile.ZipFile(destination) as archive:
                    names = [name for name in archive.namelist() if not name.endswith("/")]
                    matches = names == [source.name] and archive.read(source.name) == source.read_bytes()
            except (FileNotFoundError, KeyError, zipfile.BadZipFile):
                matches = False
            print(f"[{'OK' if matches else '过期'}] {relative_destination}")
            failed |= not matches
        else:
            write_single_file_archive(source, destination)
            print(f"[已同步] {relative_source} -> {relative_destination}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
