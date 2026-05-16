# Nuitka-Stubgen

A deterministic type stub generator for Python packages, designed for use in Nuitka.

## Overview

`nuitka-stubgen` generates type stubs (`.pyi` files) for Python modules and packages. It prioritizes:
1.  **Deterministic output**: Generating the exact same stub every time for the same source.
2.  **Compatibility**: Supporting modern type annotations while remaining robust for legacy codebases.
3.  **Vendoring**: Providing a standalone, dependency-free version for Nuitka's `inline_copy`.

The package provides two engines:
-   **Modern Engine**: Uses `libcst` to generate high-quality stubs with preserved formatting and comments. Requires Python 3.9+.
-   **Compatibility Engine**: An AST-based engine that generates `stubgen.py` for Nuitka. It is kept parseable as Python 3.5 syntax and has no external dependencies beyond the bundled `astunparse` and `six`.

## Features

-   **Nuitka Integration**: Automates the generation of `stubgen.py` for Nuitka's `inline_copy`, ensuring full Python 3.5 runtime compatibility.
-   **Legacy Support**: Extracts types from Python 2/3 style type comments (`# type: int`).
-   **Deterministic Output**: Consistent stub generation across multiple runs and Python versions.

## Usage

### Main Tool
Install with `uv` or `pip`:
```bash
uv tool install nuitka-stubgen
```

Generate stubs for a package:
```bash
nuitka-stubgen my_package
```

### Vendoring Tool
The vendoring tool generates a Nuitka-ready bundle:
```bash
nuitka-stubgen-vendor -o stubgen/
```
This produces a `stubgen/` directory containing `stubgen.py`, `astunparse.py`, and `six.py`.

## License

Apache-2.0
