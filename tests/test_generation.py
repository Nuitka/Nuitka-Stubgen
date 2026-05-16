"""Stub generation tests.

This module intentionally covers both exact-text fixtures and semantic AST checks.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nuitka_stubgen import generate_stub
from nuitka_stubgen.generation.compat_engine.core import generate_stub as generate_stub_compat
from tests.support.ast_compare import compare_asts

CASES_ROOT = Path(__file__).parent / "fixtures" / "cases"


def test_stub(case_dir: Path, case_data: dict[str, object]) -> None:
    case_id = str(case_dir.relative_to(CASES_ROOT))
    # The legacy compatibility tests are already run separately in test_vendor.py
    if case_id.startswith("legacy/"):
        pytest.skip(reason="legacy fixtures are validated by test_vendor.py")

    assert generate_stub(str(case_data["source"])) == str(case_data["expected"])


def test_stub_generation_semantic(case_data: dict[str, object]) -> None:
    """Verify that generated stubs are semantically correct by comparing ASTs."""
    actual_code = generate_stub_compat(str(case_data["source"]))

    try:
        actual_ast = ast.parse(actual_code)
    except SyntaxError as exc:
        raise AssertionError("Generated stub has syntax error: %s\nCode:\n%s" % (exc, actual_code))

    expected_ast = ast.parse(str(case_data["expected"]))

    success, message = compare_asts(actual_ast, expected_ast)
    if not success:
        print("\n--- ACTUAL STUB ---")
        print(actual_code)
        print("-------------------")
        raise AssertionError(
            "AST mismatch for case '%s': %s" % (case_data.get("id", case_data["name"]), message)
        )
