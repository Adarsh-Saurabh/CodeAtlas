from analyzer.graph_builder import build_graph


def test_python_route_decorator_becomes_endpoint(tmp_path):
    app = tmp_path / "app.py"
    app.write_text('@app.get("/health")\ndef health():\n    return {"ok": True}\n')
    graph = build_graph(tmp_path)
    assert any(node["type"] == "endpoint" and node["label"] == "GET /health" for node in graph["nodes"])
    assert any(edge["type"] == "routes_to" for edge in graph["edges"])
