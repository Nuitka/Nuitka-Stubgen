# Contributing

Thanks for working on `nuitka-stubgen`. This project is intentionally small:
changes should keep the generated stubs deterministic, easy to inspect, and
compatible with the vendored single-file output.

## Development Setup

Install dependencies with `uv`:

```bash
uv sync
```

Run the main checks before submitting a change:

```bash
uv run prek run
```

Install Git hooks, including the Commitizen `commit-msg` hook:

```bash
uv run prek install --hook-type pre-commit --hook-type commit-msg
```

The corpus test uses installed packages as smoke-test input. By default it uses
`pytest`. Override the package list with `NUITKA_STUBGEN_CORPUS_PACKAGES`:

```bash
NUITKA_STUBGEN_CORPUS_PACKAGES=pytest,packaging uv run pytest tests/test_corpus.py
```

## Adding Stub Cases

Most behavior changes should add or update a case in `tests/cases.py`. Each case
is a source string and the exact expected `.pyi` output.

Keep cases focused on one behavior where possible. If a bug only appears when
several constructs interact, add the smallest source sample that reproduces that
interaction.

## Vendored Output

`nuitka-stubgen-vendor` generates a standalone `stubgen.py` for Nuitka to vendor.
Do not hand-edit generated output. Change the package source under
`src/nuitka_stubgen/` and verify vendoring through `tests/test_vendor.py`.

Generate a vendored bundle manually when needed:

```bash
uv run nuitka-stubgen-vendor -o stubgen
```

### Python 3.5 Compatibility

The vendored tool must support Python 3.5. We use Docker to verify this within the test suite:

```bash
# Run the integrated syntax check
uv run pytest tests/test_vendor.py -k test_vendored_tool_syntax_35
```

This check is also automated via GitHub Actions in `.github/workflows/compat_35.yml`.

## Pull Requests

Use the [pull request template](.github/pull_request_template.md) when opening a
PR. It covers the expected summary, test notes, and checks for generator
behavior changes.

Prefer narrowly scoped changes. Refactors are welcome when they remove real
duplication or make generator behavior easier to test.

## Commit Messages

Use Commitizen for Conventional Commits:

```bash
uvx --from commitizen cz commit
```

For repeated use, `uv tool install commitizen` installs the same `cz` command
persistently.

Commitizen is configured with `cz_conventional_commits` in `pyproject.toml` and
validates commit messages through the `commit-msg` hook. It is intentionally not
installed as a project dependency, so its Python requirements do not affect the
package's Python 3.9 support.
