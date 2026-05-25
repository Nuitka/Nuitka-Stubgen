from __future__ import annotations
from typing import List


class TreeNode:
    def __init__(self, left: TreeNode, right: TreeNode) -> None: ...

    def children(self) -> List[TreeNode]: ...
