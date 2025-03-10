from src.Ast_Stubgen.stubgen import generate_text_stub
from pathlib import Path


def test_bubble_sort() -> None:
    file_path = Path(__file__).parent / "helper_files" / "bubble_sort.py"
    assert generate_text_stub(file_path.as_posix()) == """from typing import Any

def sorter(arr: Any) -> Any:
    ...
def sorterv2(arr: Any) -> Any:
    ...
"""
