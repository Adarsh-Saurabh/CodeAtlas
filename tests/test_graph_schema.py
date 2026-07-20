from pathlib import Path

from analyzer.graph_builder import build_graph, to_mermaid


def test_schema_and_mermaid_are_deterministic():
    root = Path(__file__).parents[1] / "fixtures" / "sample_repo_with_bottlenecks"
    graph = build_graph(root)
    assert set(graph) == {"nodes", "edges", "meta"}
    assert all({"id", "type", "confidence", "children", "calls", "bottlenecks"} <= set(node) for node in graph["nodes"])
    assert to_mermaid(graph, {"bottlenecks"}) == to_mermaid(graph, {"bottlenecks"})
    assert "flowchart TD" in to_mermaid(graph, {"bottlenecks"})
