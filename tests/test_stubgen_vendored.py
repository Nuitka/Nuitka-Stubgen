"""Tests for the vendored legacy stub generator (AST-based).

Covers the same fixture cases as the Docker py35 runner at
``tests/run_vendor_py35.py`` but runs locally on Python 3.9+, plus
production-readiness assertions matching how Nuitka uses this code.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from nuitka_stubgen.generation.validate import compare_asts

VENDORED_DIR = Path(__file__).resolve().parent.parent / "src" / "nuitka_stubgen" / "vendored" / "stubgen"
VENDORED_DIR_STR = str(VENDORED_DIR)
LEGACY_ROOT = Path(__file__).parent / "fixtures" / "cases" / "ast" / "legacy"


NUITKA_INLINE_COPY_FILES = frozenset(
    {
        "stubgen.py",
        "astunparse.py",
        "six.py",
        "astunparse_LICENSE.txt",
    }
)


class TestVendoredPackage:
    """Verifies the vendored directory matches Nuitka's inline_copy expectations."""

    def test_required_files_exist(self) -> None:
        actual = {p.name for p in VENDORED_DIR.iterdir() if not p.name.startswith(".") and p.name != "__pycache__"}
        missing = NUITKA_INLINE_COPY_FILES - actual
        extra = actual - NUITKA_INLINE_COPY_FILES
        assert not missing, f"Missing files required by Nuitka inline_copy: {sorted(missing)}"
        assert not extra, f"Unexpected files in vendored directory: {sorted(extra)}"

    def test_stubgen_module_is_importable_via_sys_path(self) -> None:
        """Matches Nuitka's importFromInlineCopy() mechanism."""
        sys.path.insert(0, VENDORED_DIR_STR)
        try:
            import stubgen  # noqa: F401
        finally:
            del sys.path[0]

    def test_generate_stub_from_source_has_correct_signature(self) -> None:
        """Nuitka calls generate_stub_from_source(source_code, output_file_path, text_only)."""
        sys.path.insert(0, VENDORED_DIR_STR)
        try:
            import inspect

            import stubgen  # noqa: F401

            sig = inspect.signature(stubgen.generate_stub_from_source)
            param_names = list(sig.parameters.keys())
            assert param_names == ["source_code", "output_file_path", "text_only"], (
                f"Expected parameters (source_code, output_file_path, text_only), got {param_names}"
            )
        finally:
            del sys.path[0]

    def test_multiple_calls_are_idempotent(self) -> None:
        """Stub generation for the same input returns identical output."""
        sys.path.insert(0, VENDORED_DIR_STR)
        try:
            import stubgen  # noqa: F401

            source = "def f(x: int) -> str: return str(x)"
            first = stubgen.generate_stub_from_source(source, output_file_path=None, text_only=True)
            second = stubgen.generate_stub_from_source(source, output_file_path=None, text_only=True)
            assert first == second
        finally:
            del sys.path[0]


# ---------------------------------------------------------------------------
# Vendored stubgen fixture (matches importFromInlineCopy pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vendored_stubgen():
    sys.path.insert(0, VENDORED_DIR_STR)
    try:
        import stubgen  # noqa: F401

        return stubgen
    finally:
        del sys.path[0]


def _iter_legacy_cases():
    for source_path in sorted(LEGACY_ROOT.rglob("source.py")):
        case_dir = source_path.parent
        expected_path = case_dir / "expected.pyi"
        yield {
            "id": str(case_dir.relative_to(LEGACY_ROOT)),
            "source": source_path.read_text(encoding="utf-8"),
            "expected": expected_path.read_text(encoding="utf-8"),
        }


def test_generated_stubs(vendored_stubgen) -> None:
    failures = []
    for case in _iter_legacy_cases():
        actual = vendored_stubgen.generate_stub_from_source(case["source"], output_file_path=None, text_only=True)
        if actual.rstrip() != case["expected"].rstrip():
            failures.append(f"{case['id']}: output mismatch")
    assert not failures, "\n".join(failures)


def test_generated_stubs_semantic(vendored_stubgen) -> None:
    failures = []
    for case in _iter_legacy_cases():
        actual = vendored_stubgen.generate_stub_from_source(case["source"], output_file_path=None, text_only=True)
        try:
            actual_ast = ast.parse(actual)
        except SyntaxError as exc:
            failures.append(f"{case['id']}: syntax error: {exc}")
            continue

        expected_ast = ast.parse(case["expected"])
        ok, msg = compare_asts(actual_ast, expected_ast)
        if not ok:
            failures.append(f"{case['id']}: {msg}")

    assert not failures, "\n".join(failures)
