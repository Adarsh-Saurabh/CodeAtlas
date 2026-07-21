"""Best-effort JS/TS extraction with regexes, never high confidence."""
from __future__ import annotations

import re
from pathlib import Path

IMPORT_RE = re.compile(r"""(?:import\s+.*?\s+from\s+|require\()\s*["']([^"']+)["']""")
FUNCTION_RE = re.compile(r"""(?:export\s+)?function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>""")
ROUTE_RE = re.compile(r"""(?:app|router)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']\s*,\s*(\w+)?""")


def module_name(path: Path, root: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def node(node_id: str, kind: str, label: str, path: Path, root: Path, line: int, confidence: str) -> dict:
    return {"id": node_id, "type": kind, "label": label, "file": str(path.relative_to(root)),
            "line": line, "confidence": confidence, "children": [], "calls": [], "bottlenecks": []}


def extract_js_file(path: Path, root: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"nodes": [], "edges": []}
    module = module_name(path, root)
    module_node = node(module, "module", module, path, root, 1, "medium")
    nodes, edges = [module_node], []
    for match in IMPORT_RE.finditer(source):
        edges.append({"from": module, "to": match.group(1), "type": "imports"})
    for match in FUNCTION_RE.finditer(source):
        name = match.group(1) or match.group(2)
        child = node(f"{module}.{name}", "function", name, path, root, source.count("\n", 0, match.start()) + 1, "medium")
        module_node["children"].append(child["id"])
        nodes.append(child)
    function_ids = {item["label"]: item["id"] for item in nodes if item["type"] == "function"}
    for match in ROUTE_RE.finditer(source):
        method, route, handler = match.groups()
        endpoint = node(f"{module}:{method.upper()}:{route}", "endpoint", f"{method.upper()} {route}",
                        path, root, source.count("\n", 0, match.start()) + 1, "low")
        module_node["children"].append(endpoint["id"])
        nodes.append(endpoint)
        if handler and handler in function_ids:
            edges.append({"from": endpoint["id"], "to": function_ids[handler], "type": "routes_to"})
    return {"nodes": nodes, "edges": edges}
