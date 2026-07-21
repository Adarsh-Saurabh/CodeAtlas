# Devpost submission notes

## Project name

CodeAtlas

## Tagline

An honest code-to-architecture visualizer that maps repositories, expands modules interactively, and flags bottlenecks directly on the diagram.

## Description

CodeAtlas helps developers understand unfamiliar codebases faster. It statically analyzes a local repository, emits a structured graph of modules, classes, functions, imports, calls, and endpoints, then renders that graph as an expandable Mermaid diagram. Instead of claiming perfect accuracy, it labels confidence and highlights heuristic bottlenecks so judges can verify each finding quickly.

## What to demo in under 3 minutes

1. Problem: unfamiliar repos hide architecture and performance risks across many files.
2. Run: `python -m analyzer.cli analyze ./fixtures/sample_repo_with_bottlenecks --out frontend/graph.json`.
3. Launch: `python server.py`, then open `http://localhost:8001`.
4. Click the `bottlenecks` module, then the red `slow` function.
5. Show the inspector listing nested loop, blocking I/O in loop, and query-like call in loop.
6. Explain Codex usage: graph contract, AST extractor, bottleneck fixtures/tests, and frontend were built iteratively with Codex.

## Submission checklist

- Hosted prototype URL: TODO
- Demo video URL: TODO
- Public GitHub repo URL: TODO
- Include Codex feedback/session ID in Devpost form: TODO
- Track: Developer Tools
- License: MIT
