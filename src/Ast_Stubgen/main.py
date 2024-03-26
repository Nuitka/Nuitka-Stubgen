import ast
import typing


def generate_stub(source_file_path: str, output_file_path: str) -> None:
    with open(source_file_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    tree = ast.parse(source_code)

    class StubGenerator(ast.NodeVisitor):
        def __init__(self):
            self.stubs = []
            self.imports_output = set()
            self.typing_imports = typing.__all__

        def visit_FunctionDef(self, node):
            if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
                if self.is_method(node):
                    self.visit_MethodDef(node)
                else:
                    self.visit_RegularFunctionDef(node)
            else:
                self.visit_RegularFunctionDef(node)

        def is_method(self, node):
            for parent_node in ast.walk(tree):
                if isinstance(parent_node, ast.ClassDef):
                    for child_node in parent_node.body:
                        if isinstance(child_node, ast.FunctionDef) and child_node.name == node.name:
                            return True
            return False

        def visit_MethodDef(self, node: ast.FunctionDef):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")

            return_type = self.get_return_type(node.returns)
            if return_type in self.typing_imports:
                self.imports_output.add(return_type)
            # handle the case where the node.name is __init__, __init__ is a special case which always returns None
            if node.name == "__init__":
                return_type = "None"
            stub = f"    def {node.name}({', '.join(args_list)}) -> {return_type}:\n        ...\n"
            self.stubs.append(stub)

        def visit_RegularFunctionDef(self, node: ast.FunctionDef):
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")

            return_type = self.get_return_type(node.returns)
            stub = f"def {node.name}({', '.join(args_list)}) -> {return_type}:\n    ...\n"
            self.stubs.append(stub)

        def visit_ClassDef(self, node):
            class_name = node.name
            stub = ""
            case = self.special_cases(node)
            if case == "TypedDict":
                stub = f"class {class_name}(typing.TypedDict):\n"
                for key in node.body:
                    if isinstance(key, ast.AnnAssign):
                        key_type = ast.unparse(key.annotation).strip()
                        stub += f"    {key.target.id}: {key_type}\n"
                stub += "\n"
            elif case == "Exception":
                stub = f"class {class_name}(Exception):\n"

                if not any(isinstance(n, ast.FunctionDef) for n in node.body):
                    stub += "    ...\n"
            else:
                is_dataclass = any(isinstance(n, ast.AnnAssign) for n in node.body)
                if is_dataclass:
                    stub = "@dataclass\n"
                    self.imports_output.add("from dataclasses import dataclass")
                stub += f"class {class_name}:\n"
            self.stubs.append(stub)
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            if methods:
                self.stubs.append("\n")
                for method in methods:
                    self.visit_FunctionDef(method)

        def special_cases(self, node) -> str:
            for obj in node.bases:
                if isinstance(obj, ast.Name) and obj.id == "TypedDict":
                    return "TypedDict"
                elif isinstance(obj, ast.Name) and obj.id == "Exception":
                    return "Exception"
                else:
                    print(f"Skipping {obj.id} in {node.lineno}, of type {type(obj)}")
            return False

        def get_arg_type(self, arg_node: ast.arg) -> str:
            selfs = ["self", "cls"]
            if arg_node.arg in selfs:
                return "Self"
            elif arg_node.annotation:
                unparsed = ast.unparse(arg_node.annotation).strip()
                return unparsed

            raise ValueError(f"Argument {arg_node.arg} in {arg_node.lineno} has no type annotation")

        def get_return_type(self, return_node: ast.AST) -> str:
            if return_node:
                unparsed = ast.unparse(return_node).strip()
                return unparsed
            return "typing.Any"

        def generate_imports(self):
            self.imports_output.add("from typing import Any, Optional, Self")
            self.imports_output.add("import typing")
            self.imports_output.add("from __future__ import annotations")
            imports = "\n".join(sorted(self.imports_output))
            imports += "\n\n"
            return imports

    stub_generator = StubGenerator()
    stub_generator.visit(tree)

    with open(output_file_path, "w") as output_file:
        sempt = stub_generator.generate_imports()
        if sempt:
            output_file.write(sempt)
        for stub in stub_generator.stubs:
            output_file.write(stub)
