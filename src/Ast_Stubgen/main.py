import ast
import typing


def generate_stub(source_file_path: str, output_file_path: str) -> None:
    with open(source_file_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    tree = ast.parse(source_code)

    class StubGenerator(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stubs: list[str] = []
            self.imports_helper_dict: dict[str, set[str]] = {}
            self.imports_output: set[str] = set()
            self.typing_imports = typing.__all__

        def visit_Import(self, node: ast.Import) -> typing.Any:
            for alias in node.names:
                name = alias.name
                self.imports_output.add(f"import {name}")

        def visit_ImportFrom(self, node: ast.ImportFrom) -> typing.Any:
            module = node.module
            for alias in node.names:
                name = alias.name
                if module:
                    if module not in self.imports_helper_dict:
                        self.imports_helper_dict[module] = set()
                    self.imports_helper_dict[module].add(name)

        def visit_FunctionDef(self, node) -> None:
            if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
                if self.is_method(node):
                    self.visit_MethodDef(node)
                else:
                    self.visit_RegularFunctionDef(node)
            else:
                self.visit_RegularFunctionDef(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    target_type = ast.unparse(node.value).strip()
                    stub = f"{target_name} = {target_type}\n"
                    self.stubs.append(stub)
                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    target_type = ast.unparse(node.value).strip()
                    stub = f"{target_name}: {target_type}\n"
                    self.stubs.append(stub)

        def is_method(self, node) -> bool:
            for parent_node in ast.walk(tree):
                if isinstance(parent_node, ast.ClassDef):
                    for child_node in parent_node.body:
                        if (
                            isinstance(child_node, ast.FunctionDef)
                            and child_node.name == node.name
                        ):
                            return True
            return False

        def visit_MethodDef(self, node: ast.FunctionDef) -> None:
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "typing.Any"

            if return_type in self.typing_imports:
                self.imports_output.add(return_type)
            # handle the case where the node.name is __init__, __init__ is a special case which always returns None
            if node.name == "__init__":
                return_type = "None"
            stub = f"    def {node.name}({', '.join(args_list)}) -> {return_type}:\n        ...\n"
            self.stubs.append(stub)

        def visit_RegularFunctionDef(self, node: ast.FunctionDef) -> None:
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            stub = (
                f"def {node.name}({', '.join(args_list)}) -> {return_type}:\n    ...\n"
            )
            self.stubs.append(stub)

        def visit_ClassDef(self, node) -> None:
            class_name = node.name
            stub = ""
            case = self.special_cases(node)
            if case == "TypedDict":
                stub = f"class {class_name}(TypedDict):\n"
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("TypedDict")
                for key in node.body:
                    if isinstance(key, ast.Assign):
                        for target in key.targets:
                            if isinstance(target, ast.Name):
                                target_name = target.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"    {target_name}: {target_type}\n"
                            elif isinstance(target, ast.Subscript):
                                if isinstance(target.value, ast.Name):
                                    target_name = target.value.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"    {target_name}: {target_type}\n"
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

        def special_cases(self, node) -> str | bool:
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
                if not "Self" in self.imports_output:
                    self.imports_helper_dict["typing"].add("Self")
                return "Self"
            elif arg_node.annotation:
                unparsed = ast.unparse(arg_node.annotation).strip()
                return unparsed

            raise ValueError(
                f"Argument {arg_node.arg} in {arg_node.lineno} has no type annotation"
            )

        def get_return_type(self, return_node: ast.AST) -> str:
            if return_node:
                unparsed = ast.unparse(return_node).strip()
                return unparsed
            else:
                return "typing.Any"

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            target = node.target
            if isinstance(node.annotation, ast.Name):
                target_type = node.annotation.id
            else:
                target_type = ast.unparse(node.annotation).strip()

            if isinstance(node.annotation, ast.Subscript):
                if isinstance(target, ast.Name):
                    stub = f"{target.id}: {target_type}\n"
                elif isinstance(target, ast.Name):
                    stub = f"{target.id}: {target_type}\n"
            self.stubs.append(stub)

        def generate_imports(self) -> str:
            imports = ""
            for module, names in self.imports_helper_dict.items():
                imports += f"\nfrom {module} import {', '.join(names)}"

            self.imports_output.add("from __future__ import annotations")
            for import_name in self.imports_output:
                imports += f"\n{import_name}"

            imports += "\n\n"

            return imports

    stub_generator = StubGenerator()
    stub_generator.visit(tree)

    with open(output_file_path, "w") as output_file:
        out_str = ""
        sempt = stub_generator.generate_imports()
        if sempt:
            out_str += sempt
        for stub in stub_generator.stubs:
            out_str += stub

        output_file.write(out_str)
