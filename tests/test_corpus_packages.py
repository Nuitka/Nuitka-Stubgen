"""Installed package corpus tests."""

from __future__ import annotations

import pytest

from .support.corpus import check_source, collect_sources, enabled_package_corpus, format_failures

pytestmark = pytest.mark.corpus


def test_installed_package_corpus_generates_parseable_stubs() -> None:
    """Configured installed packages must generate parseable stubs."""
    sources, failures = collect_sources([], enabled_package_corpus())
    failures.extend(failure for source in sources if (failure := check_source(source)) is not None)

    if failures:
        raise AssertionError(format_failures(failures))
