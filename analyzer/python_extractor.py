"""Static Python extraction using only the standard library."""
from __future__ import annotations

import ast
import warnings
from pathlib import Path


def module_name(path: Path, root: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or root.name


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return call_name(node.func)
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


class Extractor(ast.NodeVisitor):
    def __init__(self, path: Path, root: Path):
        self.path, self.root = path, root
        self.module = module_name(path, root)
        self.nodes = [self.node(self.module, "module", self.module, 1)]
        self.by_id = {self.module: self.nodes[0]}
        self.edges, self.stack = [], [self.module]
        self.imports, self.aliases = [], {}

    def node(self, node_id: str, kind: str, label: str, line: int) -> dict:
        return {"id": node_id, "type": kind, "label": label, "file": str(self.path.relative_to(self.root)),
                "line": line, "confidence": "high", "children": [], "calls": [], "bottlenecks": []}

    def add_child(self, node: dict) -> None:
        self.by_id[self.stack[-1]]["children"].append(node["id"])
        self.nodes.append(node)
        self.by_id[node["id"]] = node

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        node_id = f"{self.stack[-1]}.{node.name}"
        self.add_child(self.node(node_id, "class", node.name, node.lineno))
        self.stack.append(node_id)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _function(self, node: ast.FunctionDef) -> None:
        node_id = f"{self.stack[-1]}.{node.name}"
        self.add_child(self.node(node_id, "function", node.name, node.lineno))
        self.stack.append(node_id)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            target = item.name
            self.aliases[item.asname or target.split(".")[0]] = target
            self.edges.append({"from": self.module, "to": target, "type": "imports"})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = node.module or ""
        if base:
            self.edges.append({"from": self.module, "to": base, "type": "imports"})
        for item in node.names:
            self.aliases[item.asname or item.name] = f"{base}.{item.name}".strip(".")

    def visit_Call(self, node: ast.Call) -> None:
        if len(self.stack) > 1:
            name = call_name(node.func)
            name = self.aliases.get(name, name)
            current = self.by_id[self.stack[-1]]
            if name and name not in current["calls"]:
                current["calls"].append(name)
                self.edges.append({"from": current["id"], "to": name, "type": "calls"})
        self.generic_visit(node)


def extract_python_file(path: Path, root: Path) -> dict:
    """Extract one file without importing or executing it."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as error:
        warnings.warn(f"Skipping {path}: {error}", stacklevel=2)
        return {"nodes": [], "edges": []}
    extractor = Extractor(path, root)
    extractor.visit(tree)
    return {"nodes": extractor.nodes, "edges": extractor.edges}
