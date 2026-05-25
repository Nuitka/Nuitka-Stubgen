"""Stub generation tests: fixture cases (exact text) for the AST-based generator."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import stubgen


def _asts_equal(a, b) -> tuple[bool, str]:
    """Structural AST equality, ignoring position and context fields."""
    skip = frozenset({"lineno", "col_offset", "end_lineno", "end_col_offset", "ctx", "type_ignores"})

    if type(a) is not type(b):
        return False, f"type mismatch: {type(a).__name__} vs {type(b).__name__}"

    if isinstance(a, ast.AST):
        for field in a._fields:
            if field in skip:
                continue
            ok, msg = _asts_equal(getattr(a, field, None), getattr(b, field, None))
            if not ok:
                return False, f".{field}: {msg}"
        return True, ""

    if isinstance(a, list):
        if len(a) != len(b):
            return False, f"list length {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            ok, msg = _asts_equal(x, y)
            if not ok:
                return False, f"[{i}]: {msg}"
        return True, ""

    if a != b:
        return False, f"value {a!r} vs {b!r}"
    return True, ""


def test_fixture_exact(case_dir: Path, case_data: dict) -> None:
    """Generated stub matches the expected .pyi file exactly (modulo trailing whitespace)."""
    actual = stubgen.generate_stub_from_source(case_data["source"], text_only=True)
    assert actual.rstrip() == case_data["expected"].rstrip()


def test_fixture_semantic(case_dir: Path, case_data: dict) -> None:
    """Generated stub is AST-equivalent to the expected .pyi even if formatting differs."""
    actual = stubgen.generate_stub_from_source(case_data["source"], text_only=True)

    try:
        actual_ast = ast.parse(actual)
    except SyntaxError as exc:
        pytest.fail(f"Generated stub has syntax error: {exc}\n---\n{actual}")

    expected_ast = ast.parse(case_data["expected"])
    ok, msg = _asts_equal(actual_ast, expected_ast)
    if not ok:
        print("\n--- ACTUAL ---\n" + actual + "\n--------------")
        pytest.fail(f"AST mismatch for '{case_data['id']}': {msg}")
