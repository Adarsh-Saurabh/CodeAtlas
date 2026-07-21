# AGENTS.md — CodeAtlas

Context for Codex. Build the smallest reliable Devpost-ready version first.

## Product

CodeAtlas ingests a local repo and produces:

1. `graph.json` with modules, classes, functions, imports, calls, endpoints, confidence, and bottleneck flags.
2. A Mermaid flowchart rendered from that graph.
3. A static frontend with progressive disclosure: top-level modules first, click to expand children.
4. A bottleneck overlay for explicit heuristic anti-patterns.

Non-goal: perfect static analysis for every repo. Dynamic dispatch, generated code, reflection, and broad monorepos are known limitations. Represent uncertainty with `confidence: "high" | "medium" | "low"` and make it visible in the UI.

## Ponytail rules

- Use stdlib before dependencies.
- No database, auth, server framework, build step, or LLM calls.
- Keep files under 200 lines.
- Prefer deletion over scaffolding.
- If a shortcut has a known ceiling, mark it with a `ponytail:` comment.

## Stack

- Python analyzer.
- Python `ast` for Python files.
- Regex heuristics for JS/TS MVP only; never mark JS/TS extraction as high confidence.
- Static `frontend/index.html` using Mermaid via CDN and vanilla JS.
- Optional local `server.py` only for ZIP upload convenience.

## Commands

```bash
pip install -r requirements.txt
python -m analyzer.cli analyze ./fixtures/sample_repo_with_bottlenecks --out frontend/graph.json
python -m pytest tests -v
python server.py
```

Open `http://localhost:8001`, or open `frontend/index.html` directly and upload a generated `graph.json`.

## Graph contract

```json
{
  "nodes": [
    {
      "id": "module.ClassName.method_name",
      "type": "module | class | function | endpoint",
      "label": "method_name",
      "file": "path/to/file.py",
      "line": 42,
      "confidence": "high",
      "children": [],
      "calls": [],
      "bottlenecks": [
        {"kind": "nested_loop", "severity": "medium", "detail": "O(n^2) loop at line 45"}
      ]
    }
  ],
  "edges": [
    {"from": "module.a", "to": "module.b", "type": "calls | imports | routes_to"}
  ],
  "meta": {"repo": "name", "languages": ["python"], "generated_at": "iso8601"}
}
```

## Done for Devpost

A judge can clone the repo, run the commands above, open the UI, see a fixture graph, click nodes to expand, see a bottleneck with a legible explanation, and read clear limitations in the README.
