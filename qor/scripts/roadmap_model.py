from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

from qor import resources as _resources

CONTRACT_VERSION = "1"
SCHEMA_PATH = Path(str(_resources.schema("roadmap_event.schema.json")))


class RoadmapError(ValueError):
    """Base class for fail-visible Roadmap contract violations."""


class UnsupportedVersionError(RoadmapError):
    """Raised when a history uses a contract version this runtime does not support."""


class InvalidHistoryError(RoadmapError):
    """Raised when an event history is malformed or semantically illegal."""


@dataclass
class NodeState:
    id: str
    kind: str
    title: str
    resolver: str
    authority_required: str | None = None
    status: str = "open"
    evidence_pointers: tuple[str, ...] = ()
    rationale: str = ""
    authority: str | None = None


@dataclass
class UnresolvedSpaceState:
    id: str
    title: str
    status: str = "open"
    retired_reason: str | None = None


@dataclass
class ScopeState:
    id: str
    title: str
    node_ids: tuple[str, ...]
    unresolved_space_ids: tuple[str, ...]


@dataclass
class RoadmapState:
    roadmap_id: str | None = None
    objective: dict | None = None
    nodes: dict[str, NodeState] = field(default_factory=dict)
    predecessors: dict[str, set[str]] = field(default_factory=dict)
    dependents: dict[str, set[str]] = field(default_factory=dict)
    unresolved_spaces: dict[str, UnresolvedSpaceState] = field(default_factory=dict)
    scopes: dict[str, ScopeState] = field(default_factory=dict)
    last_seq: int = 0

    def to_dict(self) -> dict:
        return {
            "roadmap_id": self.roadmap_id,
            "objective": self.objective,
            "nodes": _nodes_dict(self),
            "unresolved_spaces": _spaces_dict(self),
            "scopes": _scopes_dict(self),
            "last_seq": self.last_seq,
        }


def _nodes_dict(state: RoadmapState) -> dict[str, dict]:
    rows = {}
    for node_id, node in sorted(state.nodes.items()):
        rows[node_id] = {
            "id": node.id,
            "kind": node.kind,
            "title": node.title,
            "resolver": node.resolver,
            "authority_required": node.authority_required,
            "status": node.status,
            "evidence_pointers": list(node.evidence_pointers),
            "rationale": node.rationale,
            "authority": node.authority,
            "predecessors": sorted(state.predecessors.get(node_id, set())),
            "dependents": sorted(state.dependents.get(node_id, set())),
        }
    return rows


def _spaces_dict(state: RoadmapState) -> dict[str, dict]:
    return {
        space_id: {
            "id": space.id,
            "title": space.title,
            "status": space.status,
            "retired_reason": space.retired_reason,
        }
        for space_id, space in sorted(state.unresolved_spaces.items())
    }


def _scopes_dict(state: RoadmapState) -> dict[str, dict]:
    return {
        scope_id: {
            "id": scope.id,
            "title": scope.title,
            "node_ids": list(scope.node_ids),
            "unresolved_space_ids": list(scope.unresolved_space_ids),
        }
        for scope_id, scope in sorted(state.scopes.items())
    }


_SCHEMA_CACHE: dict | None = None


def _schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def validate_event(event: dict) -> None:
    version = event.get("contract_version")
    if version != CONTRACT_VERSION:
        raise UnsupportedVersionError(
            f"unsupported roadmap contract_version {version!r}; supported={CONTRACT_VERSION!r}"
        )
    try:
        jsonschema.validate(event, _schema())
    except jsonschema.ValidationError as exc:
        raise InvalidHistoryError(f"invalid roadmap event: {exc.message}") from exc
