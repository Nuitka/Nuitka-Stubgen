"""Tests for the nuitka-stubgen CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from nuitka_stubgen.cli import main, parse_args, run


@pytest.fixture()
def bubble_sort_py(tmp_path: Path) -> Path:
    p = tmp_path / "bubble_sort.py"
    source_path = Path(__file__).parent / "fixtures" / "cases" / "libcst" / "bubble_sort" / "source.py"
    p.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return p


class TestParseArgs:
    """CLI argument parsing."""

    def test_source_positional(self) -> None:
        """The source positional argument is captured."""
        args = parse_args(["myfile.py"])
        assert args.source == "myfile.py"

    def test_output_flag(self) -> None:
        """The -o flag sets the output path."""
        args = parse_args(["myfile.py", "-o", "out.pyi"])
        assert args.output == "out.pyi"

    def test_output_long_flag(self) -> None:
        """The --output flag is equivalent to -o."""
        args = parse_args(["myfile.py", "--output", "out.pyi"])
        assert args.output == "out.pyi"

    def test_output_defaults_to_none(self) -> None:
        """output is None when --output is omitted."""
        args = parse_args(["myfile.py"])
        assert args.output is None

    def test_missing_source_exits(self) -> None:
        """Omitting the source positional causes SystemExit."""
        with pytest.raises(SystemExit):
            parse_args([])


class TestRun:
    """CLI run function execution."""

    def test_generates_stub_file(self, bubble_sort_py: Path, tmp_path: Path) -> None:
        """run writes a .pyi file to the path given by -o."""
        out = tmp_path / "bubble_sort.pyi"
        args = parse_args([str(bubble_sort_py), "-o", str(out)])
        assert run(args) == 0
        assert out.exists()
        assert "def sorter(" in out.read_text()

    def test_default_output_path(self, bubble_sort_py: Path) -> None:
        """Without -o the stub is written to <source>.pyi."""
        args = parse_args([str(bubble_sort_py)])
        assert run(args) == 0
        assert bubble_sort_py.with_suffix(".pyi").exists()

    def test_missing_source_returns_error(self, tmp_path: Path) -> None:
        """run returns 1 when the source file does not exist."""
        args = parse_args([str(tmp_path / "nonexistent.py")])
        assert run(args) == 1

    def test_prints_wrote_message(
        self, bubble_sort_py: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """run prints 'Wrote <path>' on success."""
        out = tmp_path / "out.pyi"
        run(parse_args([str(bubble_sort_py), "-o", str(out)]))
        assert "Wrote" in capsys.readouterr().out

    def test_missing_source_prints_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """run prints an error message to stderr when the file is missing."""
        run(parse_args([str(tmp_path / "ghost.py")]))
        assert "error" in capsys.readouterr().err


class TestMain:
    """main() CLI entry point."""

    def test_main_success_exits_zero(self, bubble_sort_py: Path, tmp_path: Path) -> None:
        """main exits 0 when stub generation succeeds."""
        out = tmp_path / "out.pyi"
        with pytest.raises(SystemExit) as exc_info:
            main([str(bubble_sort_py), "-o", str(out)])
        assert exc_info.value.code == 0

    def test_main_missing_file_exits_one(self, tmp_path: Path) -> None:
        """main exits 1 when the source file does not exist."""
        with pytest.raises(SystemExit) as exc_info:
            main([str(tmp_path / "ghost.py")])
        assert exc_info.value.code == 1
