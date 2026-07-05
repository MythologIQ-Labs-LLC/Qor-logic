"""Shadow Genome causal-graph layer (Phase 113, #139).

A Python causal graph over qor-logic's append-only shadow-event model: typed
nodes (checkpoint / state / failure / governance) linked by typed edges
(produced / occurred_during / triggered_by / applies_to), persisted as
append-only JSONL with deterministic sequence ids. `trace_chain` walks inbound
edges back to root(s) for operator / `/qor-debug` / `/qor-remediate` root-cause
traceback.

Scope (per `qor/references/doctrine-shadow-genome-graph.md`): the core causal
layer plus the #213 producer surfaces (trust-transitions, federation-peer
status, failure-node maturity) under an emitter-API + derive model -- qor-logic
owns the schema and surfaces them in `to_dict`; the consumer (a sibling governance repository, #196)
feeds trust/federation and qor derives maturity. The governance dashboard web
API stays a consumer concern. Strictly append-only; no retention/pruning
automation in V1.
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
    TRUST = "trust"  # #213: a CBT/KBT/IBT trust-level transition event


class GenomeEdgeType(str, Enum):
    PRODUCED = "produced"
    OCCURRED_DURING = "occurred_during"
    TRIGGERED_BY = "triggered_by"
    APPLIES_TO = "applies_to"


# #213 producer surfaces (emitter-API + derive). Consumer = a sibling governance repository (#196).
class TrustLevel(str, Enum):
    CBT = "CBT"
    KBT = "KBT"
    IBT = "IBT"


_TRUST_ORDER = {TrustLevel.CBT: 0, TrustLevel.KBT: 1, TrustLevel.IBT: 2}


class PeerState(str, Enum):
    SYNCED = "synced"
    SYNCING = "syncing"
    STALE = "stale"
    DEGRADED = "degraded"
    INCOMPATIBLE = "incompatible"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"


class MaturityStage(str, Enum):
    OBSERVED = "observed"
    CLASSIFIED = "classified"
    CONSTRAINT_EXTRACTED = "constraint_extracted"
    DETECTABLE = "detectable"
    ENFORCED = "enforced"
    VERIFIED = "verified"


def derive_maturity_stage(annotation: dict) -> MaturityStage:
    """Map a failure-node maturity annotation to its highest satisfied stage.
    Pure: highest evidence wins (verified > enforced > detectable >
    constraint_extracted > classified > observed)."""
    if annotation.get("verified_window"):
        return MaturityStage.VERIFIED
    if annotation.get("enforced_by"):
        return MaturityStage.ENFORCED
    if annotation.get("detector_id"):
        return MaturityStage.DETECTABLE
    if annotation.get("constraint_id"):
        return MaturityStage.CONSTRAINT_EXTRACTED
    if annotation.get("classified"):
        return MaturityStage.CLASSIFIED
    return MaturityStage.OBSERVED


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
        self.peers: dict[str, dict] = {}      # #213: federation peer status, latest-wins
        self.maturity: dict[str, dict] = {}   # #213: failure-node maturity annotations, latest-wins
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
        elif op["op"] == "peer":  # #213: federation peer status (latest-wins)
            self.peers[op["id"]] = {
                "id": op["id"], "name": op.get("name"), "state": op["state"],
                "last_sync": op.get("last_sync"), "origin": op.get("origin"),
            }
        elif op["op"] == "maturity":  # #213: failure-node maturity (latest-wins)
            self.maturity[op["node"]] = {
                k: op[k] for k in ("classified", "constraint_id", "detector_id",
                                   "enforced_by", "verified_window") if k in op
            }

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

    # ----- #213 producer emitters (append-only) -----

    def record_trust_transition(self, from_level, to_level, *, triggering_evidence=(),
                                governance_node_id=None, at=None) -> str:
        """Record a CBT/KBT/IBT trust-level transition as a `trust` node, linked
        `triggered_by` from each evidence node and `applies_to` the governance
        node. Returns the trust node id. Raises ValueError on an unknown level."""
        fl, tl = TrustLevel(from_level), TrustLevel(to_level)
        direction = "promotion" if _TRUST_ORDER[tl] > _TRUST_ORDER[fl] else "demotion"
        evidence = list(triggering_evidence)
        tid = self.add_node(GenomeNodeType.TRUST, f"{fl.value}->{tl.value}", {
            "from_level": fl.value, "to_level": tl.value, "direction": direction,
            "at": at, "triggering_evidence": evidence, "governance_node_id": governance_node_id,
        })
        for ev in evidence:
            self.add_edge(ev, tid, GenomeEdgeType.TRIGGERED_BY)
        if governance_node_id is not None:
            self.add_edge(tid, governance_node_id, GenomeEdgeType.APPLIES_TO)
        return tid

    def set_federation_peer(self, peer_id: str, *, name, state, last_sync=None, origin=None) -> None:
        """Append a federation peer-status record (latest-wins per id). Raises
        ValueError on an unknown state."""
        st = PeerState(state)
        rec = {"op": "peer", "id": peer_id, "name": name, "state": st.value,
               "last_sync": last_sync, "origin": origin}
        self._append(rec)
        self._apply(rec)

    def annotate_failure_maturity(self, failure_node_id: str, *, classified=None,
                                  constraint_id=None, detector_id=None,
                                  enforced_by=None, verified_window=None) -> None:
        """Append a maturity annotation for a FAILURE node (latest-wins). Raises
        ValueError if the node is not a failure node."""
        node = self.nodes.get(failure_node_id)
        if node is None or node.type != GenomeNodeType.FAILURE.value:
            raise ValueError(f"maturity annotation requires a failure node: {failure_node_id!r}")
        fields = {"classified": classified, "constraint_id": constraint_id,
                  "detector_id": detector_id, "enforced_by": enforced_by,
                  "verified_window": verified_window}
        rec = {"op": "maturity", "node": failure_node_id,
               **{k: v for k, v in fields.items() if v is not None}}
        self._append(rec)
        self._apply(rec)

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

    # --- Export (Phase 134; GH #164 accepted capability) ---
    def _node_dict(self, n: GenomeNode) -> dict:
        d = {"id": n.id, "type": n.type, "label": n.label, "metadata": n.metadata}
        if n.type == GenomeNodeType.FAILURE.value:  # #213: maturity on failure nodes
            ann = self.maturity.get(n.id, {})
            d["maturity"] = {"stage": derive_maturity_stage(ann).value, **ann}
        return d

    def to_dict(self) -> dict:
        """Serialize the full graph. Back-compat `nodes`/`edges`, plus the #213
        producer surfaces: `trust_transitions`, `federation_peers`, and a
        `maturity` field on failure nodes."""
        return {
            "nodes": [self._node_dict(n) for n in self.nodes.values()],
            "edges": [
                {"id": e.id, "source": e.source, "target": e.target,
                 "type": e.type, "metadata": e.metadata}
                for e in self.edges.values()
            ],
            "trust_transitions": [
                {"id": n.id, **n.metadata}
                for n in self.nodes.values() if n.type == GenomeNodeType.TRUST.value
            ],
            "federation_peers": list(self.peers.values()),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def to_dot(self) -> str:
        """Render as a Graphviz digraph."""
        lines = ["digraph shadow_genome {"]
        for n in self.nodes.values():
            label = n.label.replace('"', '\\"')
            lines.append(f'  "{n.id}" [label="{label}"];')
        for e in self.edges.values():
            lines.append(f'  "{e.source}" -> "{e.target}" [label="{e.type}"];')
        lines.append("}")
        return "\n".join(lines)


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
    sp_export = sub.add_parser("export")
    sp_export.add_argument("--format", choices=("json", "dot"), default="json")
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
    elif args.cmd == "export":
        print(graph.to_json() if args.format == "json" else graph.to_dot())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
