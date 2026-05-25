from pathlib import Path

import pytest

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "cases"


def pytest_generate_tests(metafunc):
    if "case_dir" in metafunc.fixturenames:
        cases_root = FIXTURES_ROOT / "libcst"
        case_dirs = sorted({d.parent for d in cases_root.rglob("source.py")})
        metafunc.parametrize("case_dir", case_dirs, ids=[str(d.relative_to(cases_root)) for d in case_dirs])


@pytest.fixture
def case_data(case_dir):
    source_path = case_dir / "source.py"
    expected_path = case_dir / "expected.pyi"
    return {
        "name": case_dir.name,
        "id": str(case_dir.relative_to(FIXTURES_ROOT)),
        "source": source_path.read_text(encoding="utf-8"),
        "expected": expected_path.read_text(encoding="utf-8"),
        "path": case_dir,
    }
