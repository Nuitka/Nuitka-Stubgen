"""Corpus helpers used by pytest."""

from __future__ import annotations

import ast
import importlib.util
import os
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Iterable

from nuitka_stubgen import generate_stub

IGNORED_DIRS = {
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
DEFAULT_PACKAGE_CORPUS = ("pytest", "packaging", "click", "attrs", "rich", "pluggy", "PyYAML", "libcst")
PACKAGE_ENV = "NUITKA_STUBGEN_CORPUS_PACKAGES"


@dataclass(frozen=True)
class CorpusSource:
    """A Python source file selected for corpus checking."""

    path: Path
    label: str


@dataclass(frozen=True)
class CorpusFailure:
    """A single corpus check failure."""

    label: str
    path: str
    stage: str
    error: str


def enabled_package_corpus() -> tuple[str, ...]:
    """Return installed packages that should be part of normal pytest corpus runs."""
    configured = os.environ.get(PACKAGE_ENV)
    if configured is None:
        installed: list[str] = []
        for package_name in DEFAULT_PACKAGE_CORPUS:
            try:
                metadata.distribution(package_name)
            except metadata.PackageNotFoundError:
                continue
            installed.append(package_name)

        return tuple(installed)
    return tuple(package.strip() for package in configured.split(",") if package.strip())


def is_ignored(path: Path) -> bool:
    """Return true when a source path is under an ignored directory."""
    return any(part in IGNORED_DIRS for part in path.parts)


def discover_path_sources(path: Path) -> list[CorpusSource]:
    """Return Python source files under a path."""
    resolved = path.resolve()
    if resolved.is_file():
        if resolved.suffix != ".py":
            return []
        return [CorpusSource(path=resolved, label=resolved.name)]

    sources: list[CorpusSource] = []
    for source_path in sorted(resolved.rglob("*.py")):
        if is_ignored(source_path.relative_to(resolved)):
            continue
        sources.append(
            CorpusSource(
                path=source_path,
                label=str(source_path.relative_to(resolved)),
            )
        )
    return sources


def sources_from_distribution_files(package_name: str) -> list[CorpusSource]:
    distribution = metadata.distribution(package_name)
    files = distribution.files or []
    sources: list[CorpusSource] = []

    for package_file in sorted(files, key=lambda f: str(f)):
        if package_file.suffix != ".py":
            continue
        source_path = Path(distribution.locate_file(package_file)).resolve()
        if is_ignored(source_path):
            continue
        sources.append(
            CorpusSource(
                path=source_path,
                label=f"{package_name}:{package_file}",
            )
        )

    return sources


def top_level_names(package_name: str) -> list[str]:
    distribution = metadata.distribution(package_name)
    top_level = distribution.read_text("top_level.txt")
    if top_level:
        return [line.strip() for line in top_level.splitlines() if line.strip()]
    return [package_name.replace("-", "_")]


def sources_from_import_specs(package_name: str) -> list[CorpusSource]:
    sources: list[CorpusSource] = []
    for top_level_name in top_level_names(package_name):
        spec = importlib.util.find_spec(top_level_name)
        if spec is None:
            continue

        if spec.origin and spec.origin.endswith(".py"):
            source_path = Path(spec.origin).resolve()
            if not is_ignored(source_path):
                sources.append(CorpusSource(source_path, f"{package_name}:{top_level_name}.py"))

        for search_location in spec.submodule_search_locations or []:
            package_path = Path(search_location).resolve()
            for source in discover_path_sources(package_path):
                sources.append(
                    CorpusSource(
                        path=source.path,
                        label=f"{package_name}:{top_level_name}/{source.label}",
                    )
                )

    return sources


def discover_package_sources(package_name: str) -> list[CorpusSource]:
    """Return Python source files installed by a distribution package."""
    sources = sources_from_distribution_files(package_name)
    if sources:
        return sources
    return sources_from_import_specs(package_name)


def collect_sources(paths: Iterable[Path], packages: Iterable[str]) -> tuple[list[CorpusSource], list[CorpusFailure]]:
    """Collect corpus sources and package discovery failures."""
    sources: list[CorpusSource] = []
    failures: list[CorpusFailure] = []

    for path in paths:
        if not path.exists():
            failures.append(CorpusFailure(str(path), str(path), "discover", "path does not exist"))
            continue
        sources.extend(discover_path_sources(path))

    for package_name in packages:
        try:
            package_sources = discover_package_sources(package_name)
        except metadata.PackageNotFoundError:
            failures.append(CorpusFailure(package_name, "", "discover", "package is not installed"))
            continue
        if not package_sources:
            failures.append(CorpusFailure(package_name, "", "discover", "package has no discovered Python sources"))
            continue
        sources.extend(package_sources)

    return sources, failures


def format_failures(failures: Iterable[CorpusFailure]) -> str:
    """Format corpus failures for assertion messages."""
    return "\n".join(f"{failure.label} [{failure.stage}] {failure.path}: {failure.error}" for failure in failures)


def check_stub_text(source: CorpusSource, stub_text: str) -> CorpusFailure | None:
    """Run stub-quality checks beyond syntax parsing."""
    lines = stub_text.splitlines()
    if not lines or lines[0] != "from __future__ import annotations":
        return CorpusFailure(
            source.label,
            str(source.path),
            "quality",
            "stub does not start with future annotations import",
        )

    if lines.count("from __future__ import annotations") > 1:
        return CorpusFailure(source.label, str(source.path), "quality", "duplicate future annotations import")

    import_lines = [line for line in lines if line.startswith(("import ", "from "))]
    duplicate_imports = sorted({line for line in import_lines if import_lines.count(line) > 1})
    if duplicate_imports:
        return CorpusFailure(
            source.label,
            str(source.path),
            "quality",
            f"duplicate import line: {duplicate_imports[0]}",
        )

    for line in import_lines:
        if line.startswith("from typing import ") and "[" in line:
            return CorpusFailure(source.label, str(source.path), "quality", f"invalid typing import: {line}")

    if '__name__ == "__main__"' in stub_text or "__name__ == '__main__'" in stub_text:
        return CorpusFailure(source.label, str(source.path), "quality", "main guard leaked into stub")

    return None


def check_source(source: CorpusSource) -> CorpusFailure | None:
    """Generate and syntax-check one stub."""
    try:
        source_code = source.path.read_text(encoding="utf-8")
    except OSError as exc:
        return CorpusFailure(source.label, str(source.path), "read", str(exc))

    try:
        stub_text = generate_stub(source_code)
    except Exception as exc:  # noqa: BLE001
        return CorpusFailure(source.label, str(source.path), "generate", repr(exc))

    if stub_text is None:
        return CorpusFailure(source.label, str(source.path), "generate", "stub generation returned None")

    try:
        ast.parse(stub_text)
    except SyntaxError as exc:
        return CorpusFailure(source.label, str(source.path), "parse", f"{exc.msg} at line {exc.lineno}")

    return check_stub_text(source, stub_text)
