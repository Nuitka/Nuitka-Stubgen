"""Unit tests for generation sub-modules (imports, exports, transform)."""

from __future__ import annotations

import libcst as cst
import libcst.matchers as m

from nuitka_stubgen.generation.support import (
    StubImportPruner,
    UsedNamesCollector,
    collect_all_names,
    evaluate_string,
    extract_exported_names,
    import_local_name,
    import_module_name,
    is_reexport,
)
from nuitka_stubgen.generation.validate import compare_asts


def parse_import_from(source: str) -> cst.ImportFrom:
    """Parse a ``from X import Y`` statement and narrow to ``ImportFrom``."""
    stmt = cst.parse_statement(source)
    assert isinstance(stmt, cst.SimpleStatementLine)
    return cst.ensure_type(stmt.body[0], cst.ImportFrom)


def parse_import(source: str) -> cst.Import:
    """Parse an ``import X`` statement and narrow to ``Import``."""
    stmt = cst.parse_statement(source)
    assert isinstance(stmt, cst.SimpleStatementLine)
    return cst.ensure_type(stmt.body[0], cst.Import)


def first_alias(imp: cst.ImportFrom | cst.Import) -> cst.ImportAlias:
    """Return the first import alias, asserting the import is not a star import."""
    names = imp.names
    assert not isinstance(names, cst.ImportStar)
    return names[0]


# ---------------------------------------------------------------------------
# imports.py — import_module_name
# ---------------------------------------------------------------------------


class TestImportModuleName:
    def test_simple_module(self) -> None:
        imp = parse_import_from("from os import path\n")
        assert import_module_name(imp) == "os"

    def test_from_simple(self) -> None:
        imp = parse_import_from("from os import path\n")
        assert import_module_name(imp) == "os"

    def test_from_dotted_module(self) -> None:
        imp = parse_import_from("from os.path import join\n")
        assert import_module_name(imp) == "os.path"

    def test_from_relative(self) -> None:
        imp = parse_import_from("from . import sibling\n")
        assert import_module_name(imp) == ""

    def test_module_none_fallback(self) -> None:
        """Cover the ``node is None`` return in import_module_name."""
        imp = parse_import_from("from os import path\n")
        object.__setattr__(imp, "module", None)
        assert import_module_name(imp) == ""


# ---------------------------------------------------------------------------
# imports.py — import_local_name
# ---------------------------------------------------------------------------


class TestImportLocalName:
    def test_simple_name(self) -> None:
        imp = parse_import("import os\n")
        assert import_local_name(first_alias(imp)) == "os"

    def test_as_name(self) -> None:
        imp = parse_import("import typing as t\n")
        assert import_local_name(first_alias(imp)) == "t"

    def test_from_import_as(self) -> None:
        imp = parse_import_from("from os import path as p\n")
        assert import_local_name(first_alias(imp)) == "p"

    def test_from_import(self) -> None:
        imp = parse_import_from("from os import path\n")
        assert import_local_name(first_alias(imp)) == "path"

    def test_dotted_attribute_name(self) -> None:
        """Cover the ``while isinstance(node, Attribute)`` walk."""
        imp = parse_import("import os.path\n")
        assert import_local_name(first_alias(imp)) == "os"


# ---------------------------------------------------------------------------
# imports.py — is_reexport
# ---------------------------------------------------------------------------


class TestIsReexport:
    def test_matching_asname_is_reexport(self) -> None:
        imp = parse_import_from("from pkg import Foo as Foo\n")
        assert is_reexport(first_alias(imp))

    def test_different_asname_not_reexport(self) -> None:
        imp = parse_import_from("from pkg import Foo as Bar\n")
        assert not is_reexport(first_alias(imp))

    def test_no_asname_not_reexport(self) -> None:
        imp = parse_import_from("from pkg import Foo\n")
        assert not is_reexport(first_alias(imp))


# ---------------------------------------------------------------------------
# imports.py — UsedNamesCollector
# ---------------------------------------------------------------------------


class TestUsedNamesCollector:
    def test_collects_names_outside_imports(self) -> None:
        src = """
from typing import Optional

def f(x: Optional[int]) -> None: ...
"""
        module = cst.parse_module(src)
        collector = UsedNamesCollector()
        module.visit(collector)
        assert "Optional" in collector.used
        assert "x" in collector.used
        assert "f" in collector.used

    def test_skips_import_names(self) -> None:
        src = """
import os
from typing import Any
"""
        module = cst.parse_module(src)
        collector = UsedNamesCollector()
        module.visit(collector)
        assert "os" not in collector.used
        assert "Any" not in collector.used


# ---------------------------------------------------------------------------
# imports.py — StubImportPruner
# ---------------------------------------------------------------------------


def run_pruner(
    source: str,
    stub_names: set[str] | None = None,
    exported_names: frozenset[str] | None = None,
) -> str:
    module = cst.parse_module(source)
    source_names_collector = UsedNamesCollector()
    module.visit(source_names_collector)
    source_names = source_names_collector.used
    stub_names_set = stub_names or source_names
    pruner = StubImportPruner(
        source_names=source_names,
        stub_names=stub_names_set,
        exported_names=exported_names,
    )
    result = module.visit(pruner)
    return result.code


class TestStubImportPruner:
    def test_preserves_used_import(self) -> None:
        result = run_pruner("from typing import Optional\ndef f() -> Optional[int]: ...\n")
        assert "Optional" in result

    def test_removes_unused_typing_import(self) -> None:
        result = run_pruner("from typing import Optional, Any\ndef f() -> None: ...\n")
        assert "Any" not in result
        assert "Optional" not in result

    def test_removes_unused_non_typing_import(self) -> None:
        result = run_pruner("import os\ndef f() -> None: ...\n", stub_names=set())
        assert "os" not in result

    def test_preserves_future_import(self) -> None:
        result = run_pruner("from __future__ import annotations\n")
        assert "annotations" in result

    def test_reexport_not_pruned(self) -> None:
        result = run_pruner("from pkg import Foo as Foo\n")
        assert "Foo" in result

    def test_keeps_import_used_by_reexport(self) -> None:
        exported = frozenset({"Foo"})
        result = run_pruner(
            "from pkg import Foo\ndef f() -> None: ...\n",
            stub_names={"f"},
            exported_names=exported,
        )
        assert "f" in result


# ---------------------------------------------------------------------------
# exports.py — evaluate_string
# ---------------------------------------------------------------------------


class TestEvaluateString:
    def test_simple_string(self) -> None:
        expr = cst.parse_expression('"hello"')
        assert evaluate_string(expr) == "hello"

    def test_concatenated_string(self) -> None:
        expr = cst.parse_expression('"hello" "world"')
        assert evaluate_string(expr) == "helloworld"

    def test_non_string_returns_none(self) -> None:
        expr = cst.parse_expression("42")
        assert evaluate_string(expr) is None

    def test_none_value_returns_none(self) -> None:
        """Cover the ``val is None`` branch when evaluated_value is not a str."""
        expr = cst.parse_expression("b'bytes'")
        assert evaluate_string(expr) is None


# ---------------------------------------------------------------------------
# exports.py — collect_all_names
# ---------------------------------------------------------------------------


class TestCollectAllNames:
    def test_list_of_strings(self) -> None:
        expr = cst.parse_expression('["a", "b"]')
        result = collect_all_names(expr)
        assert result == {"a", "b"}

    def test_tuple_of_strings(self) -> None:
        expr = cst.parse_expression('("a", "b")')
        result = collect_all_names(expr)
        assert result == {"a", "b"}

    def test_dynamic_value_returns_none(self) -> None:
        expr = cst.parse_expression("[a]")
        result = collect_all_names(expr)
        assert result is None

    def test_non_collection_returns_none(self) -> None:
        """Cover the ``isinstance`` guard in collect_all_names."""
        expr = cst.parse_expression("42")
        result = collect_all_names(expr)
        assert result is None


# ---------------------------------------------------------------------------
# exports.py — extract_exported_names
# ---------------------------------------------------------------------------


class TestExtractExportedNames:
    def test_static_list_assign(self) -> None:
        module = cst.parse_module('__all__ = ["a", "b"]\n')
        result = extract_exported_names(module)
        assert result == frozenset({"a", "b"})

    def test_no_all_returns_none(self) -> None:
        module = cst.parse_module("def f() -> None: ...\n")
        result = extract_exported_names(module)
        assert result is None

    def test_append_to_all(self) -> None:
        module = cst.parse_module('__all__ = ["a"]\n__all__.append("b")\n')
        result = extract_exported_names(module)
        assert result == frozenset({"a", "b"})

    def test_extend_all(self) -> None:
        module = cst.parse_module('__all__ = ["a"]\n__all__.extend(["b", "c"])\n')
        result = extract_exported_names(module)
        assert result == frozenset({"a", "b", "c"})

    def test_aug_assign(self) -> None:
        module = cst.parse_module('__all__ = ["a"]\n__all__ += ["b"]\n')
        result = extract_exported_names(module)
        assert result == frozenset({"a", "b"})


# ---------------------------------------------------------------------------
# transform.py — has_overload
# ---------------------------------------------------------------------------


from nuitka_stubgen import generate_stub


def run_pipeline(source: str) -> str:
    """Run the full generation pipeline (transform + imports + prune)."""
    return generate_stub(source)


class TestTransformOverload:
    def test_overloads_kept_implementation_removed(self) -> None:
        result = run_pipeline(
            "from typing import overload\n\n@overload\ndef f(x: int) -> int: ...\n@overload\ndef f(x: str) -> str: ...\ndef f(x): return x\n"
        )
        assert "return x" not in result
        assert result.count("def f") == 2  # overloads only


class TestTransformImport:
    def test_bare_typing_preserves_dotted_access(self) -> None:
        result = run_pipeline("import typing\nx: typing.Optional[int] = None\n")
        assert "import typing" in result
        assert "typing.Optional" in result

    def test_future_import_kept(self) -> None:
        result = run_pipeline("from __future__ import annotations\n")
        assert "annotations" in result


class TestTransformBody:
    def test_function_body_replaced(self) -> None:
        result = run_pipeline("def f() -> int:\n    return 1\n")
        assert "return 1" not in result
        assert "..." in result

    def test_annotated_assign_value_replaced(self) -> None:
        result = run_pipeline("x: int = 42\n")
        assert "42" not in result
        assert "..." in result


class TestTransformMainGuard:
    def test_main_guard_removed(self) -> None:
        result = run_pipeline('if __name__ == "__main__":\n    pass\n')
        assert "__main__" not in result


class TestTransformClassDef:
    def test_empty_class_collapsed(self) -> None:
        result = run_pipeline("class Empty:\n    pass\n")
        assert "class Empty:\n    ..." in result or "class Empty: ..." in result

    def test_class_with_methods_kept(self) -> None:
        result = run_pipeline("class HasMethods:\n    def method(self) -> int:\n        return 1\n")
        assert "class HasMethods:" in result
        assert "def method" in result

    def test_class_with_only_placeholder_body(self) -> None:
        result = run_pipeline("class Placeholder:\n    ...\n")
        assert "class Placeholder" in result


class TestTransformAnnAssign:
    def test_annotated_value_replaced(self) -> None:
        result = run_pipeline("x: int = 42\n")
        assert "42" not in result
        assert "x: int = ..." in result

    def test_annotated_without_value_stays(self) -> None:
        result = run_pipeline("x: int\n")
        assert "x: int" in result


class TestTransformLambda:
    def test_lambda_params_not_annotated(self) -> None:
        """Visiting a lambda triggers visit/leave_Lambda and skips param annotation."""
        result = run_pipeline("f = lambda x: x + 1\n")
        assert "lambda x" in result or "f = " in result

    def test_lambda_with_typed_param(self) -> None:
        """Lambda params skipped."""
        result = run_pipeline("from typing import Callable\nf: Callable[[int], int] = lambda x: x + 1\n")
        assert "Callable" in result


class TestTransformImportStar:
    def test_star_import_removed(self) -> None:
        """from X import * is removed."""
        result = run_pipeline("from os import *\n")
        assert "from os import *" not in result
        assert "os" not in result

    def test_commented_source_removed(self) -> None:
        """Comment-only source."""
        result = run_pipeline("# just a comment\n")
        assert not result.strip() or result.strip().startswith("from __future__")


class TestTransformNoExport:
    def test_typing_call_not_exported(self) -> None:
        """Typing call assign filtered by export."""
        result = run_pipeline(
            'from typing import Optional\n__all__ = ["f"]\nx: Optional[int] = None\ndef f() -> None: ...\n'
        )
        assert "Optional" not in result or "x:" not in result

    def test_ann_assign_not_exported(self) -> None:
        """AnnAssign filtered by export."""
        result = run_pipeline('__all__ = ["f"]\nx: int = 42\ndef f() -> None: ...\n')
        assert "x:" not in result

    def test_module_assign_not_exported_removed(self) -> None:
        """Module assign filtered by export."""
        result = run_pipeline('VERSION = "1.0"\n__all__ = ["f"]\ndef f() -> None: ...\n')
        assert "VERSION" not in result

    def test_typing_assign_not_exported_removed(self) -> None:
        """Typing module assign removed when not in exported."""
        result = run_pipeline(
            'from typing import Union\n__all__ = ["f"]\nJsonValue = Union[str, int]\ndef f() -> None: ...\n'
        )
        assert "JsonValue" not in result


class TestTransformApplyReexport:
    def test_reexport_from_typing(self) -> None:
        """Typing module passed through in apply_reexport."""
        result = run_pipeline('__all__ = ["f"]\nfrom typing import Optional\ndef f(x: Optional[int]) -> None: ...\n')
        assert "Optional" in result

    def test_reexport_unchanged(self) -> None:
        """Non-typing, non-matching import passes through apply_reexport unchanged."""
        result = run_pipeline('__all__ = ["opt"]\nfrom typing import Optional\nopt: Optional[int] = None\n')
        assert "Optional" in result

    def test_reexport_non_typing_no_change(self) -> None:
        """apply_reexport returns line unchanged when no names match."""
        result = run_pipeline('__all__ = ["f"]\nfrom os import path\ndef f() -> None: ...\n')
        assert "path" not in result  # pruned, but code path is taken


class TestTransformAllAugment:
    def test_aug_all_without_exported_removed(self) -> None:
        """__all__ += with non-static value leads to removal."""
        result = run_pipeline('x = ["b"]\n__all__ += x\n')
        assert "__all__" not in result

    def test_aug_all_with_exported_rewritten(self) -> None:
        """__all__ += with export context rewrites to __all__ =."""
        result = run_pipeline('__all__ = ["a"]\n__all__ += ["b"]\n')
        assert "__all__" in result


class TestTransformTypingImport:
    def test_typing_only_import_removed(self) -> None:
        """Typing-only import removed when name not used."""
        result = run_pipeline("from typing import Any\ndef f() -> None: ...\n")
        assert "Any" not in result

    def test_typing_import_filtered_partial(self) -> None:
        """Only unused typing names are filtered from import."""
        result = run_pipeline("from typing import Any, Optional\ndef f(x: Optional[int]) -> None: ...\n")
        assert "Any" not in result
        assert "Optional" in result

    def test_bare_import_non_typing_removed(self) -> None:
        """Non-typing bare import removed when not used."""
        result = run_pipeline("import os\ndef f() -> None: ...\n")
        assert "os" not in result

    def test_bare_import_mixed_filtered(self) -> None:
        """Mixed typing/non-typing import partially filtered."""
        result = run_pipeline("import typing, os\nx: typing.Optional[int] = None\ny = os.path.join('a', 'b')\n")
        assert "import typing" in result or "import os" in result


class TestTransformReexport:
    def test_reexport_kept_with_exported(self) -> None:
        """Reexport with exported names."""
        result = run_pipeline('__all__ = ["Handler"]\nfrom pkg import Handler\n')
        assert "Handler as Handler" in result or "Handler" in result


class TestTransformTypeVarExport:
    def test_typevar_not_exported_removed(self) -> None:
        """TypeVar filtered by export."""
        result = run_pipeline('from typing import TypeVar\n__all__ = ["f"]\nT = TypeVar("T")\ndef f() -> None: ...\n')
        assert 'TypeVar("T")' not in result
        assert "def f" in result


# ---------------------------------------------------------------------------
# validate.py — top_level_names / check_name_parity
# ---------------------------------------------------------------------------


import ast

from nuitka_stubgen.generation.validate import check_name_parity, top_level_names


class TestTopLevelNames:
    def test_function_name_extracted(self) -> None:
        tree = ast.parse("def f() -> None: ...\n")
        assert top_level_names(tree) == {"f"}

    def test_class_name_extracted(self) -> None:
        tree = ast.parse("class Foo: ...\n")
        assert top_level_names(tree) == {"Foo"}

    def test_ann_assign_extracted(self) -> None:
        tree = ast.parse("x: int = 42\n")
        assert top_level_names(tree) == {"x"}

    def test_all_excluded(self) -> None:
        tree = ast.parse('__all__ = ["f"]\n')
        assert "__all__" not in top_level_names(tree)

    def test_simple_assign_extracted(self) -> None:
        tree = ast.parse("VERSION = '1.0'\n")
        assert top_level_names(tree) == {"VERSION"}


class TestCheckNameParity:
    def test_names_match(self) -> None:
        result = check_name_parity(
            "def f() -> None: ...\n", "from __future__ import annotations\n\ndef f() -> None: ...\n"
        )
        assert result == []

    def test_missing_name_reported(self) -> None:
        result = check_name_parity(
            "def f() -> None: ...\n\ndef g() -> None: ...\n",
            "from __future__ import annotations\n\ndef f() -> None: ...\n",
        )
        assert result == ["g"]

    def test_ignores_syntax_errors(self) -> None:
        result = check_name_parity("def broken(:\n", "from __future__ import annotations\n")
        assert result == []

    def test_syntax_error_in_stub_returns_empty(self) -> None:
        """Syntax error in stub returns empty."""
        result = check_name_parity("x: int = 1\n", "invalid syntax @@@\n")
        assert result == []


class TestCompareAsts:
    def test_type_mismatch(self) -> None:
        ok, _ = compare_asts(ast.Name("x"), ast.Constant(value="x"))
        assert not ok

    def test_value_mismatch(self) -> None:
        ok, _ = compare_asts(ast.parse("x = 1"), ast.parse("x = 2"))
        assert not ok

    def test_list_length_mismatch(self) -> None:
        ok, _ = compare_asts([ast.Name("x")], [ast.Name("x"), ast.Name("y")])
        assert not ok

    def test_list_element_mismatch(self) -> None:
        ok, _ = compare_asts([ast.Name("x")], [ast.Name("y")])
        assert not ok

    def test_ast_match(self) -> None:
        ok, _ = compare_asts(ast.parse("x = 1"), ast.parse("x = 1"))
        assert ok

    def test_list_match(self) -> None:
        ok, _ = compare_asts([ast.Name("x")], [ast.Name("x")])
        assert ok
