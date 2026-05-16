import ast


def compare_asts(actual, expected):
    """Deeply compare two AST trees, ignoring positions and docstrings if needed."""
    if type(actual) != type(expected):
        return False, "Type mismatch: %s != %s" % (type(actual), type(expected))

    if isinstance(actual, ast.AST):
        for name, value in ast.iter_fields(actual):
            # Skip docstrings for now as they might be normalized differently
            if (
                name == "body"
                and value
                and isinstance(value[0], ast.Expr)
                and isinstance(value[0].value, (getattr(ast, "Str", ()), getattr(ast, "Constant", (None,))))
            ):
                # This is a docstring — we might want to compare it later but for now skip
                # pass
                pass

            # Skip positions
            if name in ("lineno", "col_offset", "end_lineno", "end_col_offset", "ctx"):
                continue

            expected_value = getattr(expected, name)

            res, msg = compare_asts(value, expected_value)
            if not res:
                return False, "%s.%s: %s" % (type(actual).__name__, name, msg)
        return True, ""

    if isinstance(actual, list):
        if len(actual) != len(expected):
            return False, "List length mismatch: %d != %d" % (len(actual), len(expected))
        for i, (a, e) in enumerate(zip(actual, expected)):
            res, msg = compare_asts(a, e)
            if not res:
                return False, "[%d]: %s" % (i, msg)
        return True, ""

    if actual != expected:
        return False, "Value mismatch: %r != %r" % (actual, expected)

    return True, ""
