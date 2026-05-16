from __future__ import annotations

from typing import Collection, cast

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, ContextAwareTransformer
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import BaseMetadataProvider, QualifiedName, QualifiedNameProvider

from .constants import TYPEVAR_LIKE, TYPING_MODULES
from .imports import import_module_name

MAIN_GUARD = m.Comparison(
    left=m.Name("__name__"),
    comparisons=[
        m.ComparisonTarget(
            operator=m.Equal(),
            comparator=m.SimpleString(value='"__main__"') | m.SimpleString(value="'__main__'"),
        )
    ],
)

PLACEHOLDER = m.SimpleStatementLine(body=[m.Pass() | m.Expr(value=m.Ellipsis())])

PARAM_ANY = cst.Annotation(annotation=cst.Name("Any"))
RETURN_ANY = cst.Annotation(
    annotation=cst.Name("Any"),
    whitespace_before_indicator=cst.SimpleWhitespace(" "),
    whitespace_after_indicator=cst.SimpleWhitespace(" "),
)
RETURN_NONE = cst.Annotation(
    annotation=cst.Name("None"),
    whitespace_before_indicator=cst.SimpleWhitespace(" "),
    whitespace_after_indicator=cst.SimpleWhitespace(" "),
)


class StubTransformer(ContextAwareTransformer):
    """Transforms a Python source module into a .pyi stub in-place."""

    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    def __init__(self, context: CodemodContext, exported_names: frozenset[str] | None = None) -> None:
        super().__init__(context)
        self.exported_names = exported_names
        self.class_depth = 0
        self.lambda_depth = 0
        self.if_depth = 0
        self._overloaded: list[set[str]] = [set()]  # stack: one frame per scope (module + each class)

    @property
    def in_class(self) -> bool:
        return self.class_depth > 0

    @property
    def in_module_scope(self) -> bool:
        return not self.in_class and self.if_depth == 0

    def qname(self, node: cst.CSTNode) -> str | None:
        provider = cast("type[BaseMetadataProvider[Collection[QualifiedName]]]", QualifiedNameProvider)
        names = self.get_metadata(provider, node)
        if not names:
            return None
        return min(qn.name for qn in names)

    def add_import(self, module: str, name: str) -> None:
        AddImportsVisitor.add_needed_import(self.context, module, name)

    def has_overload(self, func: cst.FunctionDef) -> bool:
        """Return True if func carries an @overload (or @typing.overload) decorator."""
        return any(
            self.qname(dec.decorator) in {"typing.overload", "typing_extensions.overload"} for dec in func.decorators
        )

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.BaseExpression:
        qn = self.qname(original_node)
        if qn:
            parts = qn.split(".")
            if parts[0] in TYPING_MODULES:
                self.add_import(parts[0], parts[1])
                return cst.Name(parts[1])
        return updated_node

    def visit_Lambda(self, node: cst.Lambda) -> bool:
        self.lambda_depth += 1
        return True

    def leave_Lambda(self, original_node: cst.Lambda, updated_node: cst.Lambda) -> cst.BaseExpression:
        self.lambda_depth -= 1
        return updated_node

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:
        if self.lambda_depth > 0:
            return updated_node
        if updated_node.name.value in ("self", "cls"):
            return updated_node
        if updated_node.annotation is None:
            self.add_import("typing", "Any")
            updated_node = updated_node.with_changes(annotation=PARAM_ANY)
        if updated_node.default is not None:
            updated_node = updated_node.with_changes(default=cst.Ellipsis())
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        name = original_node.name.value

        if self.has_overload(original_node):
            self._overloaded[-1].add(name)
        elif name in self._overloaded[-1]:
            # Overload implementation — not needed in stubs
            return cst.RemoveFromParent()

        if self.exported_names is not None and not self.in_class and name not in self.exported_names:
            return cst.RemoveFromParent()

        if updated_node.name.value == "__init__":
            updated_node = updated_node.with_changes(returns=RETURN_NONE)
        elif updated_node.returns is None:
            self.add_import("typing", "Any")
            updated_node = updated_node.with_changes(returns=RETURN_ANY)
        return updated_node.with_changes(body=cst.SimpleStatementSuite(body=[cst.Expr(value=cst.Ellipsis())]))

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.class_depth += 1
        self._overloaded.append(set())
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        self.class_depth -= 1
        self._overloaded.pop()

        if (
            self.exported_names is not None
            and not self.in_class
            and original_node.name.value not in self.exported_names
        ):
            return cst.RemoveFromParent()

        if isinstance(updated_node.body, cst.IndentedBlock):
            non_placeholder = [s for s in updated_node.body.body if not m.matches(s, PLACEHOLDER)]
            if not non_placeholder:
                return updated_node.with_changes(body=cst.SimpleStatementSuite(body=[cst.Expr(value=cst.Ellipsis())]))
        return updated_node

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        orig = original_node.body[0]
        upd = updated_node.body[0]

        if m.matches(orig, m.ImportFrom()):
            return self.transform_import_from(
                updated_node,
                cst.ensure_type(orig, cst.ImportFrom),
                cst.ensure_type(upd, cst.ImportFrom),
            )

        if m.matches(orig, m.Import()):
            return self.transform_import(updated_node, cst.ensure_type(upd, cst.Import))

        if m.matches(orig, m.AnnAssign()):
            return self.transform_ann_assign(
                updated_node,
                cst.ensure_type(orig, cst.AnnAssign),
                cst.ensure_type(upd, cst.AnnAssign),
            )

        if not self.in_class and m.matches(orig, m.Assign()):
            return self.transform_module_assign(
                updated_node,
                cst.ensure_type(orig, cst.Assign),
                cst.ensure_type(upd, cst.Assign),
            )

        if m.matches(orig, m.Pass() | m.Expr(value=m.Ellipsis())):
            return updated_node

        return cst.RemoveFromParent()

    def transform_import_from(
        self,
        line: cst.SimpleStatementLine,
        original_import: cst.ImportFrom,
        updated_import: cst.ImportFrom,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if isinstance(updated_import.names, cst.ImportStar):
            return cst.RemoveFromParent()
        if import_module_name(original_import) == "__future__":
            return cst.RemoveFromParent()
        if self.exported_names is not None and self.in_module_scope:
            return self.apply_reexport(line, updated_import, self.exported_names)
        return line

    def transform_import(
        self,
        line: cst.SimpleStatementLine,
        imp: cst.Import,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if not isinstance(imp.names, (list, tuple)):
            return line
        filtered = [
            alias
            for alias in imp.names
            if not (isinstance(alias.name, cst.Name) and alias.name.value in TYPING_MODULES)
        ]
        if not filtered:
            return cst.RemoveFromParent()
        if len(filtered) < len(imp.names):
            return line.with_changes(body=[imp.with_changes(names=filtered)])
        return line

    def transform_ann_assign(
        self,
        line: cst.SimpleStatementLine,
        original_assign: cst.AnnAssign,
        updated_assign: cst.AnnAssign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if self.exported_names is not None and self.in_module_scope and m.matches(original_assign.target, m.Name()):
            target_name = cst.ensure_type(original_assign.target, cst.Name).value
            if target_name not in self.exported_names:
                return cst.RemoveFromParent()

        if updated_assign.value is not None:
            return line.with_changes(body=[updated_assign.with_changes(value=cst.Ellipsis())])
        return line

    def apply_reexport(
        self,
        line: cst.SimpleStatementLine,
        imp: cst.ImportFrom,
        exported: frozenset[str],
    ) -> cst.SimpleStatementLine:
        """Rewrite `from X import Y` to `from X import Y as Y` for names in __all__."""
        if isinstance(imp.names, cst.ImportStar):
            return line
        mod = import_module_name(imp)
        if mod in TYPING_MODULES or mod == "__future__":
            return line
        new_names = list(imp.names)
        changed = False
        for i, alias in enumerate(new_names):
            if isinstance(alias.name, cst.Name) and alias.name.value in exported and alias.asname is None:
                new_names[i] = alias.with_changes(
                    asname=cst.AsName(
                        whitespace_before_as=cst.SimpleWhitespace(" "),
                        whitespace_after_as=cst.SimpleWhitespace(" "),
                        name=cst.Name(alias.name.value),
                    )
                )
                changed = True
        if changed:
            return line.with_changes(body=[imp.with_changes(names=new_names)])
        return line

    def transform_module_assign(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.Assign,
        upd: cst.Assign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        target_name: str | None = None
        if len(orig.targets) == 1 and m.matches(orig.targets[0].target, m.Name()):
            target_name = cst.ensure_type(orig.targets[0].target, cst.Name).value

        if m.matches(orig.value, m.Call(func=m.Name())):
            call = cst.ensure_type(orig.value, cst.Call)
            func_name = cst.ensure_type(call.func, cst.Name).value
            qn = self.qname(call.func)
            effective = qn.rsplit(".", 1)[-1] if qn else func_name
            if effective in TYPEVAR_LIKE:
                if self.exported_names is not None and target_name not in self.exported_names:
                    return cst.RemoveFromParent()
                self.add_import("typing", effective)
                return line

        qn = self.qname(orig.value)
        if qn and any(qn.startswith(f"{mod}.") for mod in TYPING_MODULES):
            for target in orig.targets:
                if m.matches(target.target, m.Name()):
                    name_node = cst.ensure_type(target.target, cst.Name)
                    if self.exported_names is not None and name_node.value not in self.exported_names:
                        return cst.RemoveFromParent()
                    return line.with_changes(
                        body=[
                            cst.AnnAssign(
                                target=name_node,
                                annotation=cst.Annotation(annotation=upd.value),
                            )
                        ]
                    )

        # __all__ is always kept regardless of its own contents
        if target_name == "__all__":
            return line

        if self.exported_names is not None and target_name not in self.exported_names:
            return cst.RemoveFromParent()

        return line

    def visit_If(self, node: cst.If) -> bool:
        self.if_depth += 1
        return True

    def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.BaseStatement | cst.RemovalSentinel:
        self.if_depth -= 1
        if m.findall(original_node.test, MAIN_GUARD):
            return cst.RemoveFromParent()
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        self.add_import("__future__", "annotations")
        body = updated_node.body
        if body and hasattr(body[0], "leading_lines"):
            body = (body[0].with_changes(leading_lines=()), *body[1:])
        return updated_node.with_changes(header=(), body=body)
