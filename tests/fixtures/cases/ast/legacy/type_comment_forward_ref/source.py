from typing import List


class TreeNode:
    def __init__(self, left, right):
        # type: (TreeNode, TreeNode) -> None
        self.left = left
        self.right = right

    def children(self):
        # type: () -> List[TreeNode]
        return [self.left, self.right]
