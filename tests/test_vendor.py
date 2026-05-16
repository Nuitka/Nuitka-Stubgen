"""Tests for the Nuitka-vendorable stubgen output."""

from __future__ import annotations

import ast
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from nuitka_stubgen.vendor import main

if TYPE_CHECKING:
    from types import ModuleType


_LEGACY_FIXTURES = Path(__file__).parent / "fixtures" / "cases" / "legacy"
_LEGACY_SOURCES = {d.name: (d / "source.py").read_text(encoding="utf-8") for d in sorted(_LEGACY_FIXTURES.iterdir()) if d.is_dir()}

requires_python35 = pytest.mark.skipif(
    sys.version_info[:2] != (3, 5),
    reason="Only runs under CPython 3.5",
)

# Marker-based expected substrings used by both TestVendorRuntime and TestVendorPy35.
_PY35_CASES = {
    "basic": ["a: int", "b: str", "c: Optional[int] = ...", "async def query", "sql: str", "params: tuple = ..."],
    "generics": [
        "windows: dict[str, list[tuple[int, str]]] = ...",
        "casts: List[Callable[[int], str]] = ...",
        "def nested() -> Any: ...",
    ],
    "async": ["async def async_func", "x: int", "-> int", "async def from_data", "data: Any", "-> 'AsyncContainer'"],
    "unicode": ["def rocket_test() -> str: ..."],
    "decorators": ["@abc.abstractmethod", "def run(self) -> None: ..."],
}


@pytest.fixture()
def vendored_path(tmp_path: Path) -> Path:
    """Generate the vendored module directory."""
    output_dir = tmp_path / "vendored_output" / "stubgen"
    main(["-o", str(output_dir)])
    return output_dir / "stubgen.py"


@pytest.fixture()
def vendored_source(vendored_path: Path) -> str:
    """Read the generated vendored module source."""
    return vendored_path.read_text(encoding="utf-8")


@pytest.fixture()
def vendored_tree(vendored_source: str) -> ast.Module:
    """Parse the generated vendored module."""
    return ast.parse(vendored_source)


@pytest.fixture()
def vendored_module(vendored_path: Path) -> ModuleType:
    """Import the generated vendored module from its temporary path."""
    spec = importlib.util.spec_from_file_location("vendored_stubgen", vendored_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not create import spec for vendored stubgen")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class TestVendorTransform:
    """AST-level structural invariants for the generated vendored file."""

    def test_relative_project_imports_are_removed(self, vendored_tree: ast.Module) -> None:
        """Project modules are inlined; no relative imports should remain.

        ``from .astunparse import unparse`` is the one intentional exception —
        it is injected into the vendored preamble so the file can locate its
        sibling shim at runtime.
        """
        relative_imports = [
            node for node in ast.walk(vendored_tree)
            if isinstance(node, ast.ImportFrom)
            and node.level > 0
            and not (node.module == "astunparse" and [a.name for a in node.names] == ["unparse"])
        ]
        assert relative_imports == []

    def test_libcst_imports_are_absent(self, vendored_tree: ast.Module) -> None:
        """The vendored file has no dependency on LibCST."""
        top_imports = [
            alias.name
            for node in ast.walk(vendored_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        from_imports = [
            node.module
            for node in ast.walk(vendored_tree)
            if isinstance(node, ast.ImportFrom)
        ]
        assert "libcst" not in top_imports
        assert "libcst" not in from_imports

    def test_f_strings_are_converted(self, vendored_tree: ast.Module) -> None:
        """The vendored file contains no f-string (JoinedStr) nodes."""
        joined_strings = [node for node in ast.walk(vendored_tree) if isinstance(node, ast.JoinedStr)]
        assert joined_strings == []

    def test_python35_syntax_compatible(self, vendored_source: str) -> None:
        """The vendored file parses cleanly as Python 3.5 syntax."""
        ast.parse(vendored_source, feature_version=(3, 5))


class TestVendorRuntime:
    """Importability and functional correctness of the vendored module."""

    def test_generated_module_imports(self, vendored_module: ModuleType) -> None:
        """The generated file is importable as a standalone module."""
        assert hasattr(vendored_module, "generate_stub")
        assert hasattr(vendored_module, "generate_text_stub")

    def test_output_can_target_inline_copy_directory(self, tmp_path: Path) -> None:
        """The vendor command accepts Nuitka's inline_copy/stubgen directory shape."""
        main(["-o", str(tmp_path)])

        assert (tmp_path / "stubgen.py").exists()
        assert (tmp_path / "astunparse.py").exists()
        assert (tmp_path / "six.py").exists()
        assert (tmp_path / "astunparse_LICENSE.txt").exists()

    def test_astunparse_runtime_is_copied_next_to_file(self, vendored_path: Path) -> None:
        """The Python 3.5-3.8 ast.unparse shim is placed beside stubgen.py."""
        assert (vendored_path.parent / "astunparse.py").exists()
        assert (vendored_path.parent / "six.py").exists()
        assert (vendored_path.parent / "astunparse_LICENSE.txt").exists()

    @pytest.mark.parametrize("name", _PY35_CASES.keys())
    def test_legacy_type_comments_extraction(self, vendored_module: ModuleType, name: str) -> None:
        """The vendored generator correctly extracts types from Python 3.5 style comments."""
        source = _LEGACY_SOURCES[name]
        actual = vendored_module.generate_stub(source)
        for marker in _PY35_CASES[name]:
            assert marker in actual, (
                "Marker %r missing from stub for case %r.\nActual:\n%s" % (marker, name, actual)
            )


class TestVendorPy35:
    """Native Python 3.5 execution tests.

    Skipped on all other interpreters; run in CI via a ``python:3.5`` GHA job.
    """

    @requires_python35
    @pytest.mark.parametrize("name", _PY35_CASES.keys())
    def test_legacy_cases_run_under_35(self, vendored_module: ModuleType, name: str) -> None:
        """Every legacy source produces a stub containing all expected markers."""
        source = _LEGACY_SOURCES[name]
        actual = vendored_module.generate_stub(source)
        for marker in _PY35_CASES[name]:
            assert marker in actual, (
                "Marker %r missing from stub for case %r.\nActual:\n%s" % (marker, name, actual)
            )
