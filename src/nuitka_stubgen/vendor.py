"""Entry point: nuitka-stubgen-vendor.

Thin CLI wrapper to generate a Nuitka-vendorable stubgen.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .generation.compat_engine.transform import write_nuitka_compat


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="nuitka-stubgen-vendor",
        description=("Generate a Nuitka-compatible vendored stubgen.py from the modern nuitka_stubgen implementation."),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="stubgen",
        help="Output directory for Nuitka inline_copy/stubgen (default: stubgen)",
    )
    args = parser.parse_args(argv)

    generation_dir = Path(__file__).parent / "generation"
    output_path = Path(args.output)
    write_nuitka_compat(generation_dir, output_path)
    print(f"Wrote Nuitka-compatible stub: {output_path}")


if __name__ == "__main__":
    main()
