"""CLI entry point for nuitka-stubgen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import write_stub


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:  # noqa: UP006, UP045
    """Parse CLI arguments and return the populated namespace."""
    parser = argparse.ArgumentParser(
        prog="nuitka-stubgen",
        description="Generate a .pyi stub file from a Python source file.",
    )
    parser.add_argument("source", help="Path to the Python source file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for the stub file. Defaults to <source>.pyi",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    """Execute stub generation for the parsed arguments.

    Returns 0 on success, 1 on error.
    """
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"error: {source_path} not found", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else source_path.with_suffix(".pyi")

    write_stub(str(source_path), str(output_path))
    print(f"Wrote {output_path}")
    return 0


def main(argv: Optional[List[str]] = None) -> None:  # noqa: UP006, UP045
    """CLI entry point."""
    args = parse_args(argv)
    sys.exit(run(args))
