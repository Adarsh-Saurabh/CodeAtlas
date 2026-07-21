from pathlib import Path

from analyzer.graph_builder import build_graph, to_mermaid


def test_schema_and_mermaid_are_deterministic():
    root = Path(__file__).parents[1] / "fixtures" / "sample_repo_with_bottlenecks"
    graph = build_graph(root)
    assert set(graph) == {"nodes", "edges", "meta"}
    assert all({"id", "type", "confidence", "children", "calls", "bottlenecks"} <= set(node) for node in graph["nodes"])
    assert to_mermaid(graph, {"bottlenecks"}) == to_mermaid(graph, {"bottlenecks"})
    assert "flowchart TD" in to_mermaid(graph, {"bottlenecks"})


def test_js_ts_extraction_is_heuristic(tmp_path):
    app = tmp_path / "app.js"
    app.write_text('import express from "express";\nfunction listUsers() {}\napp.get("/users", listUsers)\n')
    graph = build_graph(tmp_path)
    assert "javascript" in graph["meta"]["languages"]
    assert any(node["type"] == "endpoint" and node["confidence"] == "low" for node in graph["nodes"])
    assert any(edge["type"] == "routes_to" for edge in graph["edges"])


def test_dependency_folders_are_skipped(tmp_path):
    vendor = tmp_path / "node_modules" / "package"
    vendor.mkdir(parents=True)
    (vendor / "index.js").write_text("function noisy() {}")
    graph = build_graph(tmp_path)
    assert graph["nodes"] == []
