"""Command line entry point for CodeAtlas."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graph_builder import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(prog="codeatlas")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Write a graph for a Python repository")
    analyze.add_argument("path")
    analyze.add_argument("--out", default="graph.json")
    args = parser.parse_args()
    graph = build_graph(args.path)
    Path(args.out).write_text(json.dumps(graph, indent=2), encoding="utf-8")
    print(f"Wrote {len(graph['nodes'])} nodes and {len(graph['edges'])} edges to {args.out}")


if __name__ == "__main__":
    main()
