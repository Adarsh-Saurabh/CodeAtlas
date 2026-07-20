"""Small, intentionally conservative bottleneck heuristics."""
from __future__ import annotations

import ast
from pathlib import Path

from .python_extractor import call_name, module_name


def find_bottlenecks(path: Path, root: Path) -> dict[str, list[dict]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return {}
    findings: dict[str, list[dict]] = {}
    module = module_name(path, root)
    stack = [module]

    def add(kind: str, severity: str, detail: str) -> None:
        if len(stack) > 1:
            findings.setdefault(stack[-1], []).append({"kind": kind, "severity": severity, "detail": detail})

    class Rules(ast.NodeVisitor):
        def __init__(self) -> None:
            self.loops: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            stack.append(f"{stack[-1]}.{node.name}")
            self.generic_visit(node)
            stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            stack.append(f"{stack[-1]}.{node.name}")
            self.generic_visit(node)
            stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_For(self, node: ast.For) -> None:
            iterable = ast.unparse(node.iter)
            if iterable in self.loops:
                add("nested_loop", "medium", f"Nested loop over {iterable} at line {node.lineno}")
            self.loops.append(iterable)
            self.generic_visit(node)
            self.loops.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if self.loops:
                name = call_name(node.func)
                if name in {"open", "time.sleep", "requests.get"}:
                    add("blocking_io", "high", f"{name} inside a loop at line {node.lineno}")
                elif any(word in name.lower() for word in ("query", "get", "find")):
                    add("n_plus_one", "medium", f"{name} inside a loop at line {node.lineno}")
            self.generic_visit(node)

    Rules().visit(tree)
    return findings
