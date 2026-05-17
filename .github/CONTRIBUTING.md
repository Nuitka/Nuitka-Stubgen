# Contributing

Thanks for working on `nuitka-stubgen`.

This project is intentionally small. Changes should keep generated stubs deterministic, easy to
inspect, and compatible with the vendored output used by Nuitka.

This document is a quick entrypoint and intentionally stays top-level.

## Code Of Conduct

This project follows the Code of Conduct in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security Issues

Please follow [SECURITY.md](SECURITY.md) for reporting security issues.

## Where To Ask / Report

- Bugs and concrete problems: open a GitHub issue.
- Feature requests / design questions: open a GitHub discussion (if enabled) or an issue with a
  clear motivating use case.

When reporting a bug, include:

- a minimal input that reproduces the behavior (ideally a new fixture case)
- expected vs. actual output
- Python version and OS

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

## Testing

Run the suite:

```bash
uv run pytest -q
```

The corpus test uses installed packages as smoke-test input. By default it uses
`pytest`. Override the package list with `NUITKA_STUBGEN_CORPUS_PACKAGES`:

```bash
NUITKA_STUBGEN_CORPUS_PACKAGES=pytest,packaging uv run pytest -m corpus
```

## Adding Stub Cases

Most behavior changes should add or update a fixture case under
`tests/fixtures/cases/`. Each case is a directory with:

- `source.py`
- `expected.pyi`

Keep cases focused on one behavior where possible. If a bug only appears when
several constructs interact, add the smallest source sample that reproduces that
interaction.

The `tests/fixtures/cases/legacy/` cases are reserved for Python 3.5 runtime
compatibility checks of the vendored output and are exercised by `test_vendor.py`
and the CI job that runs under CPython 3.5.

## Vendored Output

`nuitka-stubgen-vendor` generates a Nuitka-vendorable bundle (`stubgen.py` plus runtime shims).
Do not hand-edit generated output. Change the package source under
`src/nuitka_stubgen/` and verify vendoring through `tests/test_vendor.py`.

Most contributors will be working on the modern stub generator (the Python 3.9+
library/CLI). The Python 3.5 compatibility surface primarily matters when
changing the vendoring pipeline or the compatibility engine used to build the
vendored bundle.

Generate a vendored bundle manually when needed:

```bash
uv run nuitka-stubgen-vendor -o stubgen
```

### Python 3.5 Compatibility

The vendored tool must support Python 3.5. CI verifies this by generating the
vendored output, checking AST-level invariants, and then executing the vendored
bundle in a `python:3.5` container.

```bash
# Generate a vendored bundle locally
uv run nuitka-stubgen-vendor -o vendored_output/stubgen

# Validate structural invariants
uv run pytest tests/test_vendor.py::TestVendorTransform
```

For most changes, relying on CI for the native CPython 3.5 execution is enough.
If you are actively modifying the vendoring/compatibility path and want to run
the Python 3.5 execution locally, use Docker:

```bash
docker run --rm -v "$PWD:/work" -w /work python:3.5-slim \
  python tests/run_vendor_py35.py vendored_output/stubgen tests/fixtures/cases/legacy
```

The native CPython 3.5 execution is wired in `.github/workflows/tests.yml` via
`tests/run_vendor_py35.py` and runs automatically in pull requests.

## Pull Requests

Use the [pull request template](.github/pull_request_template.md) when opening a
PR. It covers the expected summary, test notes, and checks for generator
behavior changes.

Prefer narrowly scoped changes. Refactors are welcome when they remove real
duplication or make generator behavior easier to test.

Pull requests should:

- include a focused description and rationale
- include tests (usually a new/updated fixture case) when behavior changes
- keep formatting changes separate from behavior changes where practical

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

## Dependabot (uv)

It is considered best practice to regularly update dependencies, to avoid being exposed to
vulnerabilities, limit incompatibilities between dependencies, and avoid complex upgrades when
upgrading from a too old version.

Dependabot has announced support for `uv`, but there are some use cases that are not yet working.
See astral-sh/uv#2512 for updates.

Dependabot supports updating `uv.lock` files. To enable it, add the `uv` package-ecosystem to your
updates list in `.github/dependabot.yml`:

```yaml
version: 2

updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Dependency Cooldown

If you use uv's `exclude-newer` option, it is recommended to also set the equivalent cooldown
option in Dependabot, to avoid ending up with pull requests where uv would not be able to lock the
dependencies.

For instance, if you've set `exclude-newer` to 1 week, you can set:

```yaml
version: 2

updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    cooldown:
      default-days: 7
```

## AI Assistance

AI assistance is fine, but please make sure you understand the changes you submit and can explain
the rationale. If a PR is largely AI-authored, disclose that in the PR description to help
reviewers calibrate scrutiny.
