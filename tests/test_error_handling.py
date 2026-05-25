"""Tests for generator error handling.

Covers edge cases where ``generate_stub`` receives malformed or unusual
input: syntax errors, non-Python content, BOM, and ``# coding:`` declarations.
"""

from pathlib import Path
from unittest.mock import patch

import libcst
import pytest

from nuitka_stubgen import generate_stub


class TestSyntaxErrors:
    def test_invalid_syntax_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("def foo(: int) -> None: ...")

    def test_unterminated_string_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("x = 'hello")

    def test_partial_truncated_code_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("class Foo:\n    def bar(")


class TestNonPythonContent:
    def test_binary_junk_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("\x00\x01\x02\x03\xff\xfe")

    def test_html_content_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("<html><body>Hello</body></html>")


class TestBOMHandling:
    def test_utf8_bom_results_in_empty_stub(self) -> None:
        source = "\ufeff" + "\n"
        result = generate_stub(source)
        assert result == "from __future__ import annotations\n"

    def test_utf8_bom_with_code_strips_bom(self) -> None:
        source = "\ufeff" + "x: int = 42\n"
        result = generate_stub(source)
        assert "x: int" in result


class TestCodingDeclarations:
    def test_coding_comment_doesnt_break_generation(self) -> None:
        source = "# -*- coding: utf-8 -*-\nx: int\n"
        result = generate_stub(source)
        assert "x: int" in result

    def test_function_after_coding_declaration(self) -> None:
        source = "# coding: utf-8\ndef f() -> None: ...\n"
        result = generate_stub(source)
        assert "def f()" in result

    def test_encoding_cookie_doesnt_break_generation(self) -> None:
        source = "# vim: set fileencoding=utf-8 :\ndef f() -> None: ...\n"
        result = generate_stub(source)
        assert "def f()" in result


class TestFallback:
    """Verifies the vendored AST-based stubgen fallback works."""

    def test_fallback_produces_valid_stub(self) -> None:
        from nuitka_stubgen.generation.core import fallback_generate

        source = "def f(x: int) -> str: return str(x)"
        result = fallback_generate(source)
        assert result is not None
        assert "def f(x: int) -> str: ..." in result
        assert result.startswith("from __future__ import annotations")

    def test_fallback_returns_none_on_invalid_input(self) -> None:
        from nuitka_stubgen.generation.core import fallback_generate

        result = fallback_generate("def broken(:")
        assert result is None


class TestFallbackPaths:
    """Edge cases in the libcst→vendored fallback pipeline."""

    def test_load_vendored_fails_on_missing_file(self) -> None:
        import importlib.util

        from nuitka_stubgen.generation import core

        with patch.object(importlib.util, "spec_from_file_location", return_value=None):
            result = core.load_vendored_stubgen()
            assert result is None

    def test_generate_stub_fallback_success(self) -> None:
        with patch("libcst.parse_module", side_effect=Exception("libcst failed")):
            result = generate_stub("def f(x: int) -> str: return str(x)\n")
            assert result is not None
            assert "def f(x: int) -> str: ..." in result

    def test_fallback_generate_stubgen_not_module(self) -> None:
        from nuitka_stubgen.generation import core

        with patch.object(core, "load_vendored_stubgen", return_value="not a module"):
            result = core.fallback_generate("def f() -> None: pass\n")
            assert result is None
