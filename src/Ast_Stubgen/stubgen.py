from __future__ import annotations
import ast
import sys
import typing

if sys.version_info < (3, 9):
    from astunparser.astunparser import unparse

    ast.unparse = unparse


def generate_stub(
    source_file_path: str,
    output_file_path: str,
    text_only: bool = False,
) -> typing.Union[str, None]:
    with open(source_file_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    tree = ast.parse(source_code)

    class StubGenerator(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stubs: list[str] = []
            self.imports_helper_dict: dict[str, set[str]] = {}
            self.imports_output: set[str] = set()
            self.typing_imports = typing.__all__
            self.in_class = False
            self.indentation_level = 0

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                self.imports_output.add(f"import {alias.name}")

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            module = node.module if node.module is not None else "."
            for alias in node.names:
                name = alias.name
                if module:
                    if module not in self.imports_helper_dict:
                        self.imports_helper_dict[module] = set()
                    self.imports_helper_dict[module].add(name)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if self.in_class:
                self.visit_MethodDef(node)
            else:
                for parent_node in ast.walk(tree):
                    if isinstance(parent_node, ast.ClassDef):
                        for child_node in parent_node.body:
                            if (
                                isinstance(child_node, ast.FunctionDef)
                                and child_node.name == node.name
                                and child_node.lineno == node.lineno
                            ):
                                # This is a method within a class
                                return
                self.visit_RegularFunctionDef(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    target_type = ast.unparse(node.value).strip()
                    if target_type in self.typing_imports:
                        self.imports_output.add(target_type)
                    if target_type in self.typing_imports:
                        stub = f"{target_name}: {target_type}\n"
                        self.stubs.append(stub)
                    else:
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name):
                                if node.value.func.id == "frozenset":
                                    stub = f"{target_name} = frozenset({', '.join([ast.unparse(arg).strip() for arg in node.value.args])})\n"
                                    self.stubs.append(stub)
                                elif node.value.func.id == "namedtuple":
                                    tuple_name = ast.unparse(node.value.args[0]).strip()

                                    stub = f"{target_name} =  namedtuple({tuple_name}, {', '.join([ast.unparse(arg).strip() for arg in node.value.args[1:]])})\n"
                                    self.stubs.append(stub)
                        elif isinstance(node.value, ast.Subscript):
                            if isinstance(node.value.value, ast.Name):
                                target_name = node.value.value.id
                            target_type = ast.unparse(node.value).strip()
                            if "typing_extensions" not in self.imports_helper_dict:
                                self.imports_helper_dict["typing_extensions"] = set()
                            self.imports_helper_dict["typing_extensions"].add(
                                "TypeAlias"
                            )
                            stub = f"{target_name}: TypeAlias = {target_type}\n"
                            self.stubs.append(stub)

                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    else:
                        continue
                    target_type = ast.unparse(node.value).strip()
                    stub = f"{target_name}: {target_type}\n"
                    self.stubs.append(stub)

        def visit_MethodDef(self, node: ast.FunctionDef) -> None:
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "Any"
                # Add typing import for Any
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")

            # Add indentation based on current indentation level (for regular and nested classes)
            indent = "    " * (self.indentation_level + 1)
            
            # handle the case where the node.name is __init__, __init__ is a special case which always returns None
            if node.name == "__init__":
                return_type = "None"
            if node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id == "classmethod":
                            args_list = args_list[1:]
                            stub = f"{indent}@classmethod\n{indent}def {node.name}(cls, {', '.join(args_list)}) -> {return_type}: ...\n"
                            self.stubs.append(stub)
                            return
                        elif decorator.id == "staticmethod":
                            stub = f"{indent}@staticmethod\n{indent}def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
                            self.stubs.append(stub)
                            return
                        else:
                            stub = f"{indent}def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
                            self.stubs.append(stub)
                            return
            stub = f"{indent}def {node.name}({', '.join(args_list)}) -> {return_type}: ...\n"
            self.stubs.append(stub)

        def visit_RegularFunctionDef(self, node: ast.FunctionDef) -> None:
            args_list = []
            for arg in node.args.args:
                arg_type = self.get_arg_type(arg)
                args_list.append(f"{arg.arg}: {arg_type}")
            if node.returns:
                return_type = self.get_return_type(node.returns)
            else:
                return_type = "Any"
                # Add typing import for Any
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")

            stub = (
                f"def {node.name}({', '.join(args_list)}) -> {return_type}:\n    ...\n"
            )
            self.stubs.append(stub)
            self.stubs.append("\n")

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            previous_in_class = self.in_class
            self.in_class = True
            previous_indent = self.indentation_level
            
            # Add indentation for nested classes
            if previous_in_class:
                self.indentation_level += 1
                
            class_name = node.name
            indent = "    " * self.indentation_level
            stub = ""
            case = self.special_cases(node)
            
            if case == "TypedDict":
                stub = f"{indent}class {class_name}(TypedDict):\n"
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("TypedDict")
                for key in node.body:
                    if isinstance(key, ast.Assign):
                        for target in key.targets:
                            if isinstance(target, ast.Name):
                                target_name = target.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"{indent}    {target_name}: {target_type}\n"
                            elif isinstance(target, ast.Subscript):
                                if isinstance(target.value, ast.Name):
                                    target_name = target.value.id
                                target_type = ast.unparse(key.value).strip()
                                stub += f"{indent}    {target_name}: {target_type}\n"
                    elif isinstance(key, ast.AnnAssign):
                        target = key.target
                        if isinstance(target, ast.Name):
                            target_name = target.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += f"{indent}    {target_name}: {target_type}\n"
                        elif isinstance(target, ast.Subscript):
                            if isinstance(target.value, ast.Name):
                                target_name = target.value.id
                            target_type = ast.unparse(key.annotation).strip()
                            stub += f"{indent}    {target_name}: {target_type}\n"
                # No extra newline needed here
            elif case == "Exception":
                if not any(isinstance(n, ast.FunctionDef) for n in node.body):
                    stub = f"{indent}class {class_name}(Exception): ..."
                else:
                    stub = f"{indent}class {class_name}(Exception):"
            elif case == "NamedTuple":
                stub = f"{indent}class {class_name}(NamedTuple):\n"
                self.imports_output.add("from typing import NamedTuple")
            else:
                is_dataclass = any(isinstance(n, ast.AnnAssign) for n in node.body)
                if is_dataclass:
                    stub = f"{indent}@dataclass\n"
                    self.imports_output.add("from dataclasses import dataclass")
                stub += f"{indent}class {class_name}:"

            self.stubs.append(stub)
            
            # Handle methods and nested classes
            methods_or_classes = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
            if methods_or_classes:
                # Add a newline to separate class body from its methods or nested classes
                self.stubs.append("\n")
                
                # Process all child nodes
                class_nodes = []
                method_nodes = []
                
                # Separate class definitions from methods
                for child in methods_or_classes:
                    if isinstance(child, ast.ClassDef):
                        class_nodes.append(child)
                    else:
                        method_nodes.append(child)
                
                # Visit nested classes first
                for class_node in class_nodes:
                    self.visit(class_node)
                
                # Add a blank line after nested classes if there are methods in the outer class
                if class_nodes and method_nodes:
                    # Add a blank line between nested classes and methods
                    self.stubs.append("\n")
                
                # Visit methods
                for method_node in method_nodes:
                    self.visit(method_node)
            
            # Restore previous state
            self.indentation_level = previous_indent
            self.in_class = previous_in_class
            
            # Add a newline after each class definition for consistent spacing
            if not previous_in_class:  # Only for top-level classes
                self.stubs.append("\n")

        def special_cases(self, node: ast.ClassDef) -> typing.Union[str, bool]:
            for obj in node.bases:
                ob_instance = isinstance(obj, ast.Name)
                if ob_instance:
                    if obj.id == "TypedDict":  # type: ignore
                        return "TypedDict"
                    elif obj.id == "Exception":  # type: ignore
                        return "Exception"
                    elif obj.id == "NamedTuple":  # type: ignore
                        return "NamedTuple"
                    else:
                        return False
            return False

        def get_arg_type(self, arg_node: ast.arg) -> str:
            selfs = ["self", "cls"]
            if arg_node.arg in selfs:
                if (
                    arg_node.arg == "self"
                    and "typing_extensions" not in self.imports_helper_dict
                ):
                    self.imports_helper_dict["typing_extensions"] = set()
                    self.imports_helper_dict["typing_extensions"].add("Self")
                return "Self" if arg_node.arg == "self" else arg_node.arg
            elif arg_node.annotation:
                unparsed = ast.unparse(arg_node.annotation).strip()
                # Check if the type is a fully qualified typing import
                if unparsed.startswith("typing."):
                    type_name = unparsed.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    return type_name
                return unparsed
            else:
                # No annotation means Any type
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
                return "Any"

        def get_return_type(self, return_node: ast.AST) -> str:
            if return_node:
                unparsed = ast.unparse(return_node).strip()
                # Check if the type is a fully qualified typing import
                if unparsed.startswith("typing."):
                    type_name = unparsed.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    return type_name
                return unparsed
            else:
                # No annotation means Any type
                if "typing" not in self.imports_helper_dict:
                    self.imports_helper_dict["typing"] = set()
                self.imports_helper_dict["typing"].add("Any")
                return "Any"

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            target = node.target
            if isinstance(node.annotation, ast.Name):
                target_type = node.annotation.id
            else:
                target_type = ast.unparse(node.annotation).strip()
                # Check if the type is a fully qualified typing import
                if target_type.startswith("typing."):
                    type_name = target_type.split(".")[-1]
                    if "typing" not in self.imports_helper_dict:
                        self.imports_helper_dict["typing"] = set()
                    self.imports_helper_dict["typing"].add(type_name)
                    target_type = type_name

            indent = "    " * (self.indentation_level + 1)
            
            if isinstance(node.annotation, ast.Subscript):
                if isinstance(target, ast.Name):
                    stub = f"{indent}{target.id}: {target_type}\n"
                elif isinstance(target, ast.Name):
                    stub = f"{indent}{target.id}: {target_type}\n"
            elif isinstance(node.annotation, ast.Name):
                if isinstance(target, ast.Name):
                    stub = f"{indent}{target.id}: {target_type}\n"
                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                    stub = f"{indent}{target_name}: {target_type}\n"
            elif isinstance(node.annotation, ast.BinOp):
                # Handle binary operations like Union types (int | str)
                if isinstance(target, ast.Name):
                    stub = f"{indent}{target.id}: {target_type}\n"
                elif isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name):
                        target_name = target.value.id
                        stub = f"{indent}{target_name}: {target_type}\n"
                    else:
                        stub = f"{indent}{ast.unparse(target)}: {target_type}\n"
                else:
                    stub = f"{indent}{ast.unparse(target)}: {target_type}\n"
            else:
                raise NotImplementedError(
                    f"Type {type(node.annotation)} not implemented, report this issue"
                )

            self.stubs.append(stub)

        def generate_imports(self) -> str:
            imports = []
            imports.append("from __future__ import annotations\n")

            sorted_items = sorted(self.imports_helper_dict.items())
            for module, names in sorted_items:
                if names:
                    imports.append(f"from {module} import {', '.join(sorted(names))}\n")

            for imp in sorted(self.imports_output):
                if imp != "from __future__ import annotations":
                    imports.append(f"{imp}\n")

            return "".join(imports) + "\n" if imports else ""

    stub_generator = StubGenerator()
    stub_generator.visit(tree)
    out_str = ""

    imports_str = stub_generator.generate_imports()
    if imports_str:
        out_str += imports_str

    for stub in stub_generator.stubs:
        out_str += stub

    if text_only:
        return out_str
    else:
        with open(output_file_path, "w") as output_file:
            output_file.write(out_str)
        return None


def generate_text_stub(source_file_path: str) -> str:
    stubs = generate_stub(source_file_path, "", text_only=True)
    if stubs:
        return stubs
    else:
        raise ValueError("Stub generation failed")