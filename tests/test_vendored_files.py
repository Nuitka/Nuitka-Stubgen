"""Verify the vendored bundle (src/) meets Nuitka inline_copy expectations."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
SRC_DIR_STR = str(SRC_DIR)

REQUIRED_FILES = frozenset({"stubgen.py", "astunparse.py", "six.py"})


class TestVendoredFiles:
    def test_required_files_exist(self) -> None:
        actual = {p.name for p in SRC_DIR.iterdir() if p.suffix == ".py"}
        missing = REQUIRED_FILES - actual
        assert not missing, f"Missing vendored files: {sorted(missing)}"

    def test_stubgen_importable_via_sys_path(self) -> None:
        """Mirrors Nuitka's importFromInlineCopy() mechanism."""
        sys.path.insert(0, SRC_DIR_STR)
        try:
            import stubgen  # noqa: F401
        finally:
            sys.path.remove(SRC_DIR_STR)

    def test_generate_stub_from_source_signature(self) -> None:
        """Nuitka calls generate_stub_from_source(source_code, output_file_path, text_only)."""
        import stubgen  # already on sys.path via conftest / pyproject

        sig = inspect.signature(stubgen.generate_stub_from_source)
        params = list(sig.parameters.keys())
        assert params == ["source_code", "output_file_path", "text_only"], (
            f"Unexpected signature: {params}"
        )

    def test_generate_stub_from_source_idempotent(self) -> None:
        import stubgen

        source = "def f(x: int) -> str: return str(x)"
        first = stubgen.generate_stub_from_source(source, text_only=True)
        second = stubgen.generate_stub_from_source(source, text_only=True)
        assert first == second

    def test_astunparse_usable_on_old_python(self) -> None:
        """astunparse.py must be importable (used on Python < 3.9)."""
        spec = importlib.util.spec_from_file_location("astunparse", SRC_DIR / "astunparse.py")
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "unparse")

    def test_six_usable(self) -> None:
        """six.py must be importable (used by astunparse)."""
        spec = importlib.util.spec_from_file_location("six", SRC_DIR / "six.py")
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "string_types")
