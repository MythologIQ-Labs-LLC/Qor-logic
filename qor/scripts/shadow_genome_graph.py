"""Shadow Genome causal-graph layer (Phase 113, #139).

A Python causal graph over qor-logic's append-only shadow-event model: typed
nodes (checkpoint / state / failure / governance) linked by typed edges
(produced / occurred_during / triggered_by / applies_to), persisted as
append-only JSONL with deterministic sequence ids. `trace_chain` walks inbound
edges back to root(s) for operator / `/qor-debug` / `/qor-remediate` root-cause
traceback.

Scope (per `qor/references/doctrine-shadow-genome-graph.md`): this is the core
causal layer only. The originating proposal's governance dashboard API, CBT/KBT/
IBT trust-level transitions, and cross-module federation gossip are DECLINED for
qor-logic — they realize their advantage in a consuming product/UI that this
repo does not have. Strictly append-only; no retention/pruning automation in V1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

DEFAULT_PATH = ".qor/genome.jsonl"


class GenomeNodeType(str, Enum):
    CHECKPOINT = "checkpoint"
    STATE = "state"
    FAILURE = "failure"
    GOVERNANCE = "governance"


class GenomeEdgeType(str, Enum):
    PRODUCED = "produced"
    OCCURRED_DURING = "occurred_during"
    TRIGGERED_BY = "triggered_by"
    APPLIES_TO = "applies_to"


@dataclass
class GenomeNode:
    id: str
    type: str
    label: str
    metadata: dict = field(default_factory=dict)


@dataclass
class GenomeEdge:
    id: str
    source: str
    target: str
    type: str
    metadata: dict = field(default_factory=dict)


class ShadowGenomeGraph:
    """Append-only causal graph with an in-memory inbound/outbound index."""

    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.nodes: dict[str, GenomeNode] = {}
        self.edges: dict[str, GenomeEdge] = {}
        self._out: dict[str, list[str]] = {}
        self._in: dict[str, list[str]] = {}
        self._n = 0
        self._e = 0
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self._apply(json.loads(line))

    def _apply(self, op: dict) -> None:
        if op["op"] == "node":
            n = GenomeNode(op["id"], op["type"], op["label"], op.get("metadata", {}))
            self.nodes[n.id] = n
            self._out.setdefault(n.id, [])
            self._in.setdefault(n.id, [])
            self._n = max(self._n, int(n.id[1:]) + 1)
        elif op["op"] == "edge":
            e = GenomeEdge(op["id"], op["source"], op["target"], op["type"], op.get("metadata", {}))
            self.edges[e.id] = e
            self._out.setdefault(e.source, []).append(e.id)
            self._in.setdefault(e.target, []).append(e.id)
            self._e = max(self._e, int(e.id[1:]) + 1)

    def _append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    def add_node(self, node_type: GenomeNodeType | str, label: str, metadata: dict | None = None) -> str:
        nid = f"n{self._n}"
        rec = {"op": "node", "id": nid, "type": GenomeNodeType(node_type).value, "label": label, "metadata": metadata or {}}
        self._append(rec)
        self._apply(rec)
        return nid

    def add_edge(self, source: str, target: str, edge_type: GenomeEdgeType | str, metadata: dict | None = None) -> str:
        eid = f"e{self._e}"
        rec = {"op": "edge", "id": eid, "source": source, "target": target,
               "type": GenomeEdgeType(edge_type).value, "metadata": metadata or {}}
        self._append(rec)
        self._apply(rec)
        return eid

    def trace_chain(self, node_id: str, max_depth: int | None = None) -> list[list[str]]:
        """Return causal paths (root -> ... -> node_id) by walking inbound edges.
        Cycle-safe (a node already on the current path is not revisited) and
        depth-limited when ``max_depth`` is given."""
        paths: list[list[str]] = []

        def walk(current: str, path: list[str], depth: int) -> None:
            if max_depth is not None and depth >= max_depth:
                paths.append(list(reversed(path)))
                return
            sources = [
                self.edges[eid].source
                for eid in self._in.get(current, [])
                if self.edges[eid].source not in path
            ]
            if not sources:
                paths.append(list(reversed(path)))
                return
            for src in sources:
                walk(src, path + [src], depth + 1)

        walk(node_id, [node_id], 0)
        return paths

    def snapshot(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "node_types": dict(Counter(n.type for n in self.nodes.values())),
            "edge_types": dict(Counter(e.type for e in self.edges.values())),
        }

    def query(self, node_type: GenomeNodeType | str | None = None, label_contains: str | None = None) -> list[GenomeNode]:
        wanted = GenomeNodeType(node_type).value if node_type is not None else None
        out = []
        for n in self.nodes.values():
            if wanted is not None and n.type != wanted:
                continue
            if label_contains is not None and label_contains not in n.label:
                continue
            out.append(n)
        return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.shadow_genome_graph")
    parser.add_argument("--path", default=os.environ.get("QOR_GENOME_PATH", DEFAULT_PATH))
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    sp_trace = sub.add_parser("trace")
    sp_trace.add_argument("node_id")
    sp_trace.add_argument("--max-depth", type=int, default=None)
    sp_query = sub.add_parser("query")
    sp_query.add_argument("--type", default=None)
    args = parser.parse_args(argv)
    graph = ShadowGenomeGraph(args.path)
    if args.cmd == "snapshot":
        print(json.dumps(graph.snapshot(), indent=2, sort_keys=True))
    elif args.cmd == "trace":
        for chain in graph.trace_chain(args.node_id, max_depth=args.max_depth):
            print(" -> ".join(chain))
    elif args.cmd == "query":
        for n in graph.query(node_type=args.type):
            print(f"{n.id}\t{n.type}\t{n.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
