# This file must stay Python 3.5 compatible.

import ast
import os
import sys


def _read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _iter_case_dirs(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip __pycache__ etc.
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]

        if "source.py" in filenames and "expected.pyi" in filenames:
            yield dirpath


def _import_stubgen(bundle_dir):
    # Ensure vendored runtime modules (astunparse.py, six.py) are importable.
    sys.path.insert(0, bundle_dir)
    try:
        stubgen_path = os.path.join(bundle_dir, "stubgen.py")
        if not os.path.isfile(stubgen_path):
            raise SystemExit("Expected stubgen.py at: %s" % stubgen_path)

        import importlib.util

        spec = importlib.util.spec_from_file_location("vendored_stubgen", stubgen_path)
        if spec is None:
            raise SystemExit("Failed to create import spec for: %s" % stubgen_path)
        if spec.loader is None:
            raise SystemExit("Failed to create loader for: %s" % stubgen_path)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        del sys.path[0]


def _normalize_ast(node):
    """Walk an AST and replace version-specific nodes with a common form.

    Python 3.5-3.7 use ``ast.Str`` / ``ast.Num`` / ``ast.NameConstant``;
    3.8+ folds them into ``ast.Constant``.  Normalize to the 3.8+ form.
    Also strip position and context metadata.
    """
    # Safely reference nodes that don't exist on Python 3.9+
    str_node = getattr(ast, "Str", None)
    num_node = getattr(ast, "Num", None)
    nameconst_node = getattr(ast, "NameConstant", None)
    bytes_node = getattr(ast, "Bytes", None)
    ellipsis_node = getattr(ast, "Ellipsis", None)

    if isinstance(node, ast.AST):
        if str_node is not None and isinstance(node, str_node):
            return ast.Constant(value=node.s)
        if num_node is not None and isinstance(node, num_node):
            return ast.Constant(value=node.n)
        if nameconst_node is not None and isinstance(node, nameconst_node):
            return ast.Constant(value=node.value)
        if bytes_node is not None and isinstance(node, bytes_node):
            return ast.Constant(value=node.s)
        if ellipsis_node is not None and isinstance(node, ellipsis_node):
            return ast.Constant(value=Ellipsis)

        kwargs = {}
        for name in node._fields:
            if name in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
                continue
            kwargs[name] = _normalize_ast(getattr(node, name))
        return type(node)(**kwargs)

    if isinstance(node, list):
        return [_normalize_ast(item) for item in node]

    return node


def _ast_equal(a, b):
    """Structural equality for two normalized ASTs, ignoring position."""
    if type(a) != type(b):
        return False

    if isinstance(a, ast.AST):
        for name in a._fields:
            if name in ("lineno", "col_offset", "end_lineno", "end_col_offset", "ctx"):
                continue
            if not _ast_equal(getattr(a, name), getattr(b, name)):
                return False
        return True

    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_ast_equal(ai, bi) for ai, bi in zip(a, b))

    return a == b


def main(argv):
    if len(argv) != 3:
        raise SystemExit("Usage: run_vendor_py35.py <bundle_dir> <cases_dir>")

    bundle_dir = os.path.abspath(argv[1])
    cases_dir = os.path.abspath(argv[2])

    stubgen = _import_stubgen(bundle_dir)

    failures = []

    for case_dir in sorted(_iter_case_dirs(cases_dir)):
        source_path = os.path.join(case_dir, "source.py")
        expected_path = os.path.join(case_dir, "expected.pyi")

        source_text = _read_text(source_path)
        expected_text = _read_text(expected_path)

        try:
            compile(source_text, source_path, "exec")
        except SyntaxError:
            continue

        try:
            actual_text = stubgen.generate_stub_from_source(source_text, output_file_path=None, text_only=True)
        except Exception as e:
            failures.append((case_dir, "generate", repr(e)))
            continue

        # Try exact match first (fast path)
        if actual_text.rstrip() == expected_text.rstrip():
            continue

        # Fall back to AST-structural comparison (handles quote style etc.)
        try:
            actual_ast = _normalize_ast(ast.parse(actual_text))
            expected_ast = _normalize_ast(ast.parse(expected_text))
        except SyntaxError as e:
            failures.append((case_dir, "parse", repr(e)))
            continue

        if not _ast_equal(actual_ast, expected_ast):
            failures.append((case_dir, "mismatch", "AST structure differs from expected.pyi"))

    if failures:
        for case_dir, stage, message in failures:
            print("%s [%s] : %s" % (case_dir, stage, message))
        raise SystemExit(1)

    print("OK (%d cases)" % (len(list(_iter_case_dirs(cases_dir))),))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
