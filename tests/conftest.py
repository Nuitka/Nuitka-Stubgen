from pathlib import Path

import pytest

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "cases" / "ast" / "legacy"


def pytest_generate_tests(metafunc):
    if "case_dir" in metafunc.fixturenames:
        case_dirs = sorted({d.parent for d in FIXTURES_ROOT.rglob("source.py")})
        metafunc.parametrize(
            "case_dir",
            case_dirs,
            ids=[str(d.relative_to(FIXTURES_ROOT)) for d in case_dirs],
        )


@pytest.fixture
def case_data(case_dir):
    return {
        "name": case_dir.name,
        "id": str(case_dir.relative_to(FIXTURES_ROOT)),
        "source": (case_dir / "source.py").read_text(encoding="utf-8"),
        "expected": (case_dir / "expected.pyi").read_text(encoding="utf-8"),
        "path": case_dir,
    }
