"""Unit tests for stubgen internal helpers."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import stubgen


# ---------------------------------------------------------------------------
# dotted_name
# ---------------------------------------------------------------------------

class TestDottedName:
    def test_simple_name(self) -> None:
        node = ast.parse("foo", mode="eval").body
        assert stubgen.dotted_name(node) == "foo"

    def test_attribute(self) -> None:
        node = ast.parse("os.path", mode="eval").body
        assert stubgen.dotted_name(node) == "os.path"

    def test_deeply_nested(self) -> None:
        node = ast.parse("a.b.c", mode="eval").body
        assert stubgen.dotted_name(node) == "a.b.c"

    def test_non_name_returns_none(self) -> None:
        node = ast.parse("42", mode="eval").body
        assert stubgen.dotted_name(node) is None


# ---------------------------------------------------------------------------
# call_name
# ---------------------------------------------------------------------------

class TestCallName:
    def test_simple_call(self) -> None:
        node = ast.parse("foo()", mode="eval").body
        assert stubgen.call_name(node) == "foo"

    def test_dotted_call(self) -> None:
        node = ast.parse("typing.cast()", mode="eval").body
        assert stubgen.call_name(node) == "typing.cast"

    def test_non_call_returns_none(self) -> None:
        node = ast.parse("foo", mode="eval").body
        assert stubgen.call_name(node) is None


# ---------------------------------------------------------------------------
# decorator_name
# ---------------------------------------------------------------------------

class TestDecoratorName:
    def test_plain_decorator(self) -> None:
        node = ast.parse("foo", mode="eval").body
        assert stubgen.decorator_name(node) == "foo"

    def test_call_decorator(self) -> None:
        node = ast.parse("foo()", mode="eval").body
        assert stubgen.decorator_name(node) == "foo"

    def test_dotted_call_decorator(self) -> None:
        node = ast.parse("abc.abstractmethod()", mode="eval").body
        assert stubgen.decorator_name(node) == "abc.abstractmethod"


# ---------------------------------------------------------------------------
# is_main_guard
# ---------------------------------------------------------------------------

class TestIsMainGuard:
    def _test_node(self, source: str) -> ast.expr:
        tree = ast.parse(source)
        assert isinstance(tree.body[0], ast.If)
        return tree.body[0].test

    def test_recognizes_standard_guard(self) -> None:
        node = self._test_node('if __name__ == "__main__":\n    pass\n')
        assert stubgen.is_main_guard(node)

    def test_recognizes_reversed_guard(self) -> None:
        node = self._test_node('if "__main__" == __name__:\n    pass\n')
        assert stubgen.is_main_guard(node)

    def test_rejects_non_guard(self) -> None:
        node = self._test_node("if __name__ == 'other':\n    pass\n")
        assert not stubgen.is_main_guard(node)

    def test_rejects_plain_condition(self) -> None:
        node = self._test_node("if True:\n    pass\n")
        assert not stubgen.is_main_guard(node)


# ---------------------------------------------------------------------------
# static_string / static_all_names
# ---------------------------------------------------------------------------

class TestStaticString:
    def _expr(self, src: str) -> ast.expr:
        return ast.parse(src, mode="eval").body

    def _source(self, src: str) -> stubgen.Source:
        return stubgen.Source(src)

    def test_string_constant(self) -> None:
        src = '"hello"'
        assert stubgen.static_string(self._source(src), self._expr(src)) == "hello"

    def test_concatenated_strings(self) -> None:
        src = '"foo" + "bar"'
        assert stubgen.static_string(self._source(src), self._expr(src)) == "foobar"

    def test_non_string_returns_none(self) -> None:
        src = "42"
        assert stubgen.static_string(self._source(src), self._expr(src)) is None


class TestStaticAllNames:
    def _expr(self, src: str) -> ast.expr:
        return ast.parse(src, mode="eval").body

    def _source(self, src: str) -> stubgen.Source:
        return stubgen.Source(src)

    def test_list_of_strings(self) -> None:
        src = '["a", "b"]'
        result = stubgen.static_all_names(self._source(src), self._expr(src))
        assert result == {"a", "b"}

    def test_tuple_of_strings(self) -> None:
        src = '("x", "y")'
        result = stubgen.static_all_names(self._source(src), self._expr(src))
        assert result == {"x", "y"}

    def test_dynamic_element_returns_none(self) -> None:
        src = "[a, b]"
        result = stubgen.static_all_names(self._source(src), self._expr(src))
        assert result is None

    def test_non_collection_returns_none(self) -> None:
        src = "42"
        result = stubgen.static_all_names(self._source(src), self._expr(src))
        assert result is None


# ---------------------------------------------------------------------------
# extract_exported_names
# ---------------------------------------------------------------------------

class TestExtractExportedNames:
    def _parse(self, src: str):
        return ast.parse(src), stubgen.Source(src)

    def test_simple_list(self) -> None:
        tree, source = self._parse('__all__ = ["f", "g"]\n')
        assert stubgen.extract_exported_names(tree, source) == frozenset({"f", "g"})

    def test_no_all_returns_none(self) -> None:
        tree, source = self._parse("def f() -> None: ...\n")
        assert stubgen.extract_exported_names(tree, source) is None

    def test_aug_assign_extends(self) -> None:
        tree, source = self._parse('__all__ = ["a"]\n__all__ += ["b"]\n')
        assert stubgen.extract_exported_names(tree, source) == frozenset({"a", "b"})

    def test_append_call(self) -> None:
        tree, source = self._parse('__all__ = ["a"]\n__all__.append("b")\n')
        assert stubgen.extract_exported_names(tree, source) == frozenset({"a", "b"})

    def test_extend_call(self) -> None:
        tree, source = self._parse('__all__ = ["a"]\n__all__.extend(["b", "c"])\n')
        assert stubgen.extract_exported_names(tree, source) == frozenset({"a", "b", "c"})


# ---------------------------------------------------------------------------
# generate_stub_from_source — integration-level unit cases
# ---------------------------------------------------------------------------

class TestGenerateStubFromSource:
    def test_basic_function(self) -> None:
        result = stubgen.generate_stub_from_source("def f(x: int) -> str: return str(x)", text_only=True)
        assert "def f(x: int) -> str: ..." in result
        assert result.startswith("from __future__ import annotations")

    def test_function_body_stripped(self) -> None:
        result = stubgen.generate_stub_from_source("def f() -> int:\n    return 1\n", text_only=True)
        assert "return 1" not in result
        assert "..." in result

    def test_main_guard_removed(self) -> None:
        result = stubgen.generate_stub_from_source(
            'def f() -> None: pass\nif __name__ == "__main__":\n    f()\n', text_only=True
        )
        assert "__main__" not in result

    def test_annotated_assign_value_replaced(self) -> None:
        result = stubgen.generate_stub_from_source("x: int = 42\n", text_only=True)
        assert "42" not in result
        assert "x: int" in result

    def test_star_import_removed(self) -> None:
        result = stubgen.generate_stub_from_source("from os import *\n", text_only=True)
        assert "import *" not in result

    def test_type_comment_function(self) -> None:
        source = "def f(x):\n    # type: (int) -> str\n    return str(x)\n"
        result = stubgen.generate_stub_from_source(source, text_only=True)
        assert "def f(x: int) -> str: ..." in result

    def test_overload_implementation_removed(self) -> None:
        source = (
            "from typing import overload\n\n"
            "@overload\ndef f(x: int) -> int: ...\n"
            "@overload\ndef f(x: str) -> str: ...\n"
            "def f(x): return x\n"
        )
        result = stubgen.generate_stub_from_source(source, text_only=True)
        assert "return x" not in result
        assert result.count("def f") == 2

    def test_class_methods_kept(self) -> None:
        source = "class Foo:\n    def method(self) -> int:\n        return 1\n"
        result = stubgen.generate_stub_from_source(source, text_only=True)
        assert "class Foo:" in result
        assert "def method" in result
        assert "return 1" not in result

    def test_empty_source_generates_header(self) -> None:
        result = stubgen.generate_stub_from_source("", text_only=True)
        assert result.startswith("from __future__ import annotations")

    def test_write_to_file(self, tmp_path) -> None:
        out = tmp_path / "out.pyi"
        stubgen.generate_stub_from_source("def f() -> None: ...\n", output_file_path=str(out))
        assert out.exists()
        assert "def f()" in out.read_text()
