from __future__ import annotations

from typing import Callable, Sequence

import libcst as cst

from .constants import TYPING_MODULES


def import_module_name(imp: cst.ImportFrom) -> str:
    """Return the dotted module name for an ImportFrom node, or '' if relative."""
    if imp.relative:
        return ""
    node = imp.module
    if node is None:
        return ""
    parts: list[str] = []
    while isinstance(node, cst.Attribute):
        parts.append(cst.ensure_type(node.attr, cst.Name).value)
        node = node.value
    if isinstance(node, cst.Name):
        parts.append(node.value)
    return ".".join(reversed(parts))


class UsedNamesCollector(cst.CSTVisitor):
    """Collect Name values referenced outside of import statements."""

    def __init__(self) -> None:
        self.used: set[str] = set()

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        del node
        return False

    def visit_Import(self, node: cst.Import) -> bool:
        del node
        return False

    def visit_Name(self, node: cst.Name) -> None:
        self.used.add(node.value)


def import_local_name(alias: cst.ImportAlias) -> str:
    if alias.asname is not None:
        asname = alias.asname
        if isinstance(asname, cst.AsName) and isinstance(asname.name, cst.Name):
            return asname.name.value
    if isinstance(alias.name, cst.Name):
        return alias.name.value
    node = alias.name
    while isinstance(node, cst.Attribute):
        node = node.value
    return node.value if isinstance(node, cst.Name) else ""


def is_reexport(alias: cst.ImportAlias) -> bool:
    if alias.asname is None:
        return False
    asname = alias.asname
    return (
        isinstance(asname, cst.AsName)
        and isinstance(asname.name, cst.Name)
        and isinstance(alias.name, cst.Name)
        and asname.name.value == alias.name.value
    )


class StubImportPruner(cst.CSTTransformer):
    """Prune top-level imports that only supported removed implementation code."""

    def __init__(
        self,
        *,
        source_names: set[str],
        stub_names: set[str],
        exported_names: frozenset[str] | None,
    ) -> None:
        self.source_names = source_names
        self.stub_names = stub_names
        self.exported_names = exported_names
        self.indented_depth = 0

    def visit_IndentedBlock(self, node: cst.IndentedBlock) -> None:
        del node
        self.indented_depth += 1

    def leave_IndentedBlock(
        self, original_node: cst.IndentedBlock, updated_node: cst.IndentedBlock
    ) -> cst.IndentedBlock:
        del original_node
        self.indented_depth -= 1
        return updated_node

    @property
    def in_module_body(self) -> bool:
        return self.indented_depth == 0

    def should_drop_bare_import(self, alias: cst.ImportAlias) -> bool:
        return import_local_name(alias) not in self.stub_names

    def should_drop_import_from(self, module: str, alias: cst.ImportAlias) -> bool:
        if is_reexport(alias):
            return False

        local = import_local_name(alias)
        if local in self.stub_names:
            return False

        if self.exported_names is not None and module not in TYPING_MODULES:
            return True

        return local in self.source_names

    def filter_aliases(
        self,
        aliases: Sequence[cst.ImportAlias],
        *,
        should_drop: Callable[[cst.ImportAlias], bool],
    ) -> list[cst.ImportAlias] | None:
        kept = [alias for alias in aliases if not should_drop(alias)]
        if not kept:
            return None
        if len(kept) < len(aliases):
            kept[-1] = kept[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return kept

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        del original_node
        if not self.in_module_body:
            return updated_node
        if not updated_node.body:
            return updated_node
        stmt = updated_node.body[0]

        if isinstance(stmt, cst.ImportFrom) and not isinstance(stmt.names, cst.ImportStar):
            if import_module_name(stmt) == "__future__":
                return updated_node
            module = import_module_name(stmt)
            kept = self.filter_aliases(
                stmt.names,
                should_drop=lambda alias: self.should_drop_import_from(module, alias),
            )
            if kept is None:
                return cst.RemoveFromParent()
            return updated_node.with_changes(body=[stmt.with_changes(names=kept)])

        if isinstance(stmt, cst.Import) and isinstance(stmt.names, (list, tuple)):
            kept = self.filter_aliases(stmt.names, should_drop=self.should_drop_bare_import)
            if kept is None:
                return cst.RemoveFromParent()
            return updated_node.with_changes(body=[stmt.with_changes(names=kept)])

        return updated_node
