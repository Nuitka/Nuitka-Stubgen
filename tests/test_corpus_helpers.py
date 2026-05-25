"""Tests for corpus discovery and quality helpers."""

from __future__ import annotations

import ast
from pathlib import Path

from nuitka_stubgen.generation.validate import has_live_body, roundtrip

from .support.corpus import (
    CorpusFailure,
    CorpusSource,
    check_source,
    check_stub_text,
    collect_sources,
    discover_package_sources,
    discover_path_sources,
)


def test_discover_path_sources_recurses_and_skips_ignored_dirs(tmp_path: Path) -> None:
    """Path discovery finds Python files while skipping cache-like directories."""
    source = tmp_path / "pkg" / "module.py"
    ignored = tmp_path / ".venv" / "ignored.py"
    source.parent.mkdir()
    ignored.parent.mkdir()
    source.write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")
    ignored.write_text("def hidden():\n    return None\n", encoding="utf-8")

    sources = discover_path_sources(tmp_path)

    assert sources == [CorpusSource(path=source.resolve(), label="pkg/module.py")]


def test_check_source_accepts_valid_stub_output(tmp_path: Path) -> None:
    """A valid source file generates a parseable stub."""
    source = tmp_path / "module.py"
    source.write_text("def ok(value: int) -> int:\n    return value\n", encoding="utf-8")

    failure = check_source(CorpusSource(source, "module.py"))

    assert failure is None


def test_check_source_reports_generation_failure(tmp_path: Path) -> None:
    """Invalid Python source is reported as a generation failure."""
    source = tmp_path / "broken.py"
    source.write_text("def broken(:\n", encoding="utf-8")

    failure = check_source(CorpusSource(source, "broken.py"))

    assert failure is not None
    assert failure.stage == "generate"


def test_check_stub_text_requires_future_annotations_import(tmp_path: Path) -> None:
    """Corpus quality checks require the standard stub header."""
    source = CorpusSource(tmp_path / "module.py", "module.py")

    failure = check_stub_text(source, "def f() -> None:\n    ...\n")

    assert failure is not None
    assert failure.stage == "quality"
    assert "future annotations" in failure.error


def test_check_stub_text_rejects_duplicate_imports(tmp_path: Path) -> None:
    """Corpus quality checks catch repeated import lines."""
    source = CorpusSource(tmp_path / "module.py", "module.py")

    failure = check_stub_text(
        source,
        "from __future__ import annotations\nfrom typing import Any\nfrom typing import Any\n",
    )

    assert failure is not None
    assert failure.stage == "quality"
    assert "duplicate import" in failure.error


def test_check_stub_text_rejects_invalid_typing_import(tmp_path: Path) -> None:
    """Corpus quality checks catch imported subscript expressions."""
    source = CorpusSource(tmp_path / "module.py", "module.py")

    failure = check_stub_text(
        source,
        "from __future__ import annotations\nfrom typing import Generator[int, None, None]\n",
    )

    assert failure is not None
    assert failure.stage == "quality"
    assert "invalid typing import" in failure.error


def test_check_stub_text_rejects_main_guard_leaks(tmp_path: Path) -> None:
    """Corpus quality checks catch source-only main guards."""
    source = CorpusSource(tmp_path / "module.py", "module.py")

    failure = check_stub_text(
        source,
        'from __future__ import annotations\nif __name__ == "__main__":\n    ...\n',
    )

    assert failure is not None
    assert failure.stage == "quality"
    assert "main guard" in failure.error


def test_collect_sources_reports_missing_paths(tmp_path: Path) -> None:
    """Missing path inputs are reported as discovery failures."""
    sources, failures = collect_sources([tmp_path / "missing"], [])

    assert sources == []
    assert failures == [
        CorpusFailure(str(tmp_path / "missing"), str(tmp_path / "missing"), "discover", "path does not exist")
    ]


def test_package_discovery_finds_installed_pytest_sources() -> None:
    """Installed package discovery falls back to import specs when needed."""
    sources = discover_package_sources("pytest")

    assert sources
    assert all(source.path.suffix == ".py" for source in sources)


class TestBodyCheck:
    def _first_body(self, source: str) -> list[ast.stmt]:
        stmt = ast.parse(source).body[0]
        assert isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
        return stmt.body

    def test_detects_real_code_in_function_body(self) -> None:
        assert has_live_body(self._first_body("def f() -> None:\n    return 1\n"))

    def test_accepts_ellipsis_body(self) -> None:
        assert not has_live_body(self._first_body("def f() -> None: ..."))

    def test_accepts_pass_body(self) -> None:
        assert not has_live_body(self._first_body("def f() -> None: pass"))

    def test_accepts_raise_body(self) -> None:
        assert not has_live_body(self._first_body("def f() -> None: raise NotImplementedError"))


class TestRoundtripCheck:
    def test_valid_stub_is_stable(self) -> None:
        stub = "from __future__ import annotations\n\ndef f(x: int) -> str: ...\n"
        second = roundtrip(stub)
        assert second.rstrip() == stub.rstrip()

    def test_real_code_in_stub_detected(self) -> None:
        stub = "from __future__ import annotations\n\ndef f(x: int) -> str:\n    return str(x)\n"
        second = roundtrip(stub)
        assert second.rstrip() != stub.rstrip()


def test_check_source_reports_roundtrip_failure(tmp_path: Path) -> None:
    """Source that generates a stub which changes on second pass is reported."""
    source = tmp_path / "unstable.py"
    source.write_text("from typing import Optional\ndef f(x: Optional[int] = None) -> None: ...\n", encoding="utf-8")
    failure = check_source(CorpusSource(source, "unstable.py"))
    assert failure is None  # roundtrip should succeed for real


def test_check_source_reports_missing_name(tmp_path: Path) -> None:
    """Source that creates __all__ that excludes a function reports missing name."""
    source = tmp_path / "filtered.py"
    source.write_text('__all__ = ["f"]\ndef f() -> None: ...\ndef g() -> None: ...\n', encoding="utf-8")
    failure = check_source(CorpusSource(source, "filtered.py"))
    assert failure is not None
    assert failure.stage == "quality"
    assert "names missing" in failure.error
