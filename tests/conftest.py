from pathlib import Path

import pytest


def pytest_generate_tests(metafunc):
    if "case_dir" in metafunc.fixturenames:
        cases_root = Path(__file__).parent / "fixtures" / "cases"
        case_dirs = sorted([d.parent for d in cases_root.glob("**/source.py")])
        metafunc.parametrize("case_dir", case_dirs, ids=[str(d.relative_to(cases_root)) for d in case_dirs])


@pytest.fixture
def case_data(case_dir):
    cases_root = Path(__file__).parent / "fixtures" / "cases"
    source_path = case_dir / "source.py"
    expected_path = case_dir / "expected.pyi"

    return {
        "name": case_dir.name,
        "id": str(case_dir.relative_to(cases_root)),
        "source": source_path.read_text(encoding="utf-8"),
        "expected": expected_path.read_text(encoding="utf-8"),
        "path": case_dir,
    }
