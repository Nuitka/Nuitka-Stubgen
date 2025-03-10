"""This file takes in the stubgen.py file and makes it compatible with nuitka
"""
from pathlib import Path
import ast

class TypeAnnotationStripper(ast.NodeTransformer):
    """AST transformer that removes type annotations from functions and classes."""
    
    def visit_FunctionDef(self, node):
        # Remove return type annotation
        node.returns = None
        
        # Remove argument type annotations
        if node.args:
            for arg in node.args.args:
                arg.annotation = None
            
            # Handle keyword-only arguments
            for arg in node.args.kwonlyargs:
                arg.annotation = None
                
            # Handle positional-only arguments (Python 3.8+)
            if hasattr(node.args, 'posonlyargs'):
                for arg in node.args.posonlyargs:
                    arg.annotation = None
                    
        # Continue traversing the tree
        self.generic_visit(node)
        return node
    
    def visit_AnnAssign(self, node):
        # Convert annotated assignments to regular assignments
        # e.g., x: int = 5 becomes x = 5
        if node.value:
            new_node = ast.Assign(targets=[node.target], value=node.value)
            # Copy location info from the original node
            ast.copy_location(new_node, node)
            return new_node
        else:
            # If it's just a type declaration without assignment (x: int), remove it
            return None


def strip_type_annotations(source_code: str) -> str:
    tree = ast.parse(source_code)
    
    transformer = TypeAnnotationStripper()
    transformed_tree = transformer.visit(tree)
    return ast.unparse(transformed_tree)


if __name__ == "__main__":
    stubgen_py = Path(__file__).parent.parent /"src" / "Ast_Stubgen" / "stubgen.py"

    with open(stubgen_py, "r") as file:
        data = file.read()

    stripped_data = strip_type_annotations(data)

    with open("stubgen_stripped.py", "w") as file:
        file.write(stripped_data)