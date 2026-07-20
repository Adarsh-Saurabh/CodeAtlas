import json
from pathlib import Path

from analyzer.graph_builder import build_graph


ROOT = Path(__file__).parents[1]


def test_python_fixture_matches_golden_contract():
    graph = build_graph(ROOT / "fixtures" / "sample_repo_small")
    expected = json.loads((ROOT / "fixtures" / "sample_repo_small" / "expected_graph.json").read_text())
    actual_edges = sorted((edge["from"], edge["to"], edge["type"]) for edge in graph["edges"])
    assert sorted(node["id"] for node in graph["nodes"]) == expected["node_ids"]
    assert actual_edges == [tuple(edge) for edge in expected["edges"]]
    assert all(node["confidence"] == "high" for node in graph["nodes"])
