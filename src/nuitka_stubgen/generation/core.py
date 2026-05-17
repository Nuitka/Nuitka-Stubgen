from __future__ import annotations

from pathlib import Path

import libcst as cst
from libcst.codemod import Codemod, CodemodContext
from libcst.codemod.visitors import AddImportsVisitor

from .exports import extract_exported_names
from .imports import StubImportPruner, UsedNamesCollector
from .transform import StubTransformer


class StubGenerationCodemod(Codemod):
    """Coordinate stub rewriting, import insertion, and import pruning."""

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        exported = extract_exported_names(tree)

        source_names = UsedNamesCollector()
        tree.visit(source_names)

        stub = StubTransformer(self.context, exported).transform_module(tree)
        stub = stub.visit(AddImportsVisitor(self.context))

        stub_names = UsedNamesCollector()
        stub.visit(stub_names)
        return stub.visit(
            StubImportPruner(
                source_names=source_names.used,
                stub_names=stub_names.used,
                exported_names=exported,
            )
        )


def generate_stub(source_code: str) -> str:
    module = cst.parse_module(source_code)
    code = StubGenerationCodemod(CodemodContext()).transform_module(module).code
    # Normalize: avoid trailing blank lines in generated stubs while keeping a final newline.
    return code.rstrip() + "\n"


def write_stub(source_file_path: str | Path, output_file_path: str | Path) -> None:
    source = Path(source_file_path).read_text(encoding="utf-8")
    Path(output_file_path).write_text(generate_stub(source), encoding="utf-8")
