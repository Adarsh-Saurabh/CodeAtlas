"""Graph assembly and deterministic Mermaid compilation."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .bottleneck_rules import find_bottlenecks
from .python_extractor import extract_python_file


def build_graph(repo: str | Path) -> dict:
    root = Path(repo).resolve()
    nodes, edges = [], []
    for path in sorted(root.rglob("*.py")):
        if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(root).parts):
            continue
        result = extract_python_file(path, root)
        flags = find_bottlenecks(path, root)
        for node in result["nodes"]:
            node["bottlenecks"] = flags.get(node["id"], [])
        nodes.extend(result["nodes"])
        edges.extend(result["edges"])
    return {"nodes": nodes, "edges": edges, "meta": {"repo": root.name, "languages": ["python"],
            "generated_at": datetime.now(timezone.utc).isoformat()}}


def _escape(value: str) -> str:
    return value.replace('"', "'").replace("[", "(").replace("]", ")")


def to_mermaid(graph: dict, expanded: set[str] | None = None) -> str:
    """Compile top modules plus direct children of expanded nodes."""
    expanded = expanded or set()
    nodes = {node["id"]: node for node in graph["nodes"]}
    visible = {node["id"] for node in nodes.values() if node["type"] == "module"}
    for node_id in expanded:
        visible.update(nodes.get(node_id, {}).get("children", []))
    ordered = sorted(visible)
    aliases = {node_id: f"n{index}" for index, node_id in enumerate(ordered)}
    lines = ["flowchart TD"]
    for node_id in ordered:
        node = nodes[node_id]
        lines.append(f'{aliases[node_id]}["{_escape(node["label"])}"]')
        if node["bottlenecks"]:
            lines.append(f"style {aliases[node_id]} fill:#fff1f1,stroke:#dc2626,stroke-width:2px")
    for edge in graph["edges"]:
        if edge["from"] in aliases and edge["to"] in aliases:
            lines.append(f"{aliases[edge['from']]} --> {aliases[edge['to']]}")
    return "\n".join(lines)
