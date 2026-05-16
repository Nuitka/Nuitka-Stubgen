from __future__ import annotations

import libcst as cst
from libcst import matchers as m


def evaluate_string(expr: cst.BaseExpression) -> str | None:
    """Return the string value of a static string expression, or None if dynamic."""
    if isinstance(expr, cst.SimpleString):
        val = expr.evaluated_value
        return val if isinstance(val, str) else None
    if isinstance(expr, cst.ConcatenatedString):
        left = evaluate_string(expr.left)
        right = evaluate_string(expr.right)
        return left + right if left is not None and right is not None else None
    return None


def collect_all_names(collection_expr: cst.BaseExpression) -> set[str] | None:
    """Return string literal names from a List/Tuple/Set, or None if dynamic."""
    if not isinstance(collection_expr, (cst.List, cst.Tuple, cst.Set)):
        return None
    names: set[str] = set()
    for elt in collection_expr.elements:
        val = evaluate_string(elt.value)
        if val is None:
            return None
        names.add(val)
    return names


def extract_exported_names(module: cst.Module) -> frozenset[str] | None:
    """Scan module body for static __all__ mutations."""
    accumulated: set[str] | None = None
    for stmt in module.body:
        if not isinstance(stmt, cst.SimpleStatementLine):
            continue
        body0 = stmt.body[0]

        if m.matches(body0, m.Assign()):
            assign = cst.ensure_type(body0, cst.Assign)
            if any(m.matches(t.target, m.Name("__all__")) for t in assign.targets):
                names = collect_all_names(assign.value)
                if names is not None:
                    accumulated = names if accumulated is None else accumulated | names

        elif m.matches(body0, m.AugAssign(target=m.Name("__all__"), operator=m.AddAssign())):
            if accumulated is not None:
                aug = cst.ensure_type(body0, cst.AugAssign)
                names = collect_all_names(aug.value)
                if names is not None:
                    accumulated |= names

        elif m.matches(body0, m.Expr(value=m.Call(func=m.Attribute(value=m.Name("__all__"))))):
            if accumulated is not None:
                call = cst.ensure_type(cst.ensure_type(body0, cst.Expr).value, cst.Call)
                method = cst.ensure_type(call.func, cst.Attribute).attr.value
                if method == "extend" and len(call.args) == 1:
                    names = collect_all_names(call.args[0].value)
                    if names is not None:
                        accumulated |= names
                elif method == "append" and len(call.args) == 1:
                    arg = call.args[0].value
                    if isinstance(arg, cst.SimpleString) and isinstance(arg.evaluated_value, str):
                        accumulated.add(arg.evaluated_value)

    return frozenset(accumulated) if accumulated is not None else None
