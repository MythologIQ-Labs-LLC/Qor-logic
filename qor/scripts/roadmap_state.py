from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

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
    superseded_by: str | None = None
    review_reason: str | None = None


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
            "nodes": {
                node_id: {
                    "id": node.id,
                    "kind": node.kind,
                    "title": node.title,
                    "resolver": node.resolver,
                    "authority_required": node.authority_required,
                    "status": node.status,
                    "evidence_pointers": list(node.evidence_pointers),
                    "rationale": node.rationale,
                    "authority": node.authority,
                    "superseded_by": node.superseded_by,
                    "review_reason": node.review_reason,
                    "predecessors": sorted(self.predecessors.get(node_id, set())),
                    "dependents": sorted(self.dependents.get(node_id, set())),
                }
                for node_id, node in sorted(self.nodes.items())
            },
            "unresolved_spaces": {
                space_id: {
                    "id": space.id,
                    "title": space.title,
                    "status": space.status,
                    "retired_reason": space.retired_reason,
                }
                for space_id, space in sorted(self.unresolved_spaces.items())
            },
            "scopes": {
                scope_id: {
                    "id": scope.id,
                    "title": scope.title,
                    "node_ids": list(scope.node_ids),
                    "unresolved_space_ids": list(scope.unresolved_space_ids),
                }
                for scope_id, scope in sorted(self.scopes.items())
            },
            "last_seq": self.last_seq,
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


def _require_node(state: RoadmapState, node_id: str) -> NodeState:
    try:
        return state.nodes[node_id]
    except KeyError as exc:
        raise InvalidHistoryError(f"unknown roadmap node reference: {node_id}") from exc


def _require_space(state: RoadmapState, space_id: str) -> UnresolvedSpaceState:
    try:
        return state.unresolved_spaces[space_id]
    except KeyError as exc:
        raise InvalidHistoryError(f"unknown unresolved-space reference: {space_id}") from exc


def _descendants(state: RoadmapState, node_id: str) -> set[str]:
    seen: set[str] = set()
    stack = list(state.dependents.get(node_id, set()))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(state.dependents.get(current, set()))
    return seen


def _would_create_cycle(state: RoadmapState, predecessor_id: str, dependent_id: str) -> bool:
    if predecessor_id == dependent_id:
        return True
    return predecessor_id in _descendants(state, dependent_id)


def reduce_events(events: Iterable[dict]) -> RoadmapState:
    state = RoadmapState()
    event_ids: set[str] = set()

    for event in events:
        validate_event(event)
        event_id = event["event_id"]
        if event_id in event_ids:
            raise InvalidHistoryError(f"duplicate event_id: {event_id}")
        event_ids.add(event_id)

        expected_seq = state.last_seq + 1
        if event["seq"] != expected_seq:
            raise InvalidHistoryError(
                f"non-contiguous roadmap seq: expected {expected_seq}, got {event['seq']}"
            )

        if state.roadmap_id is not None and event["roadmap_id"] != state.roadmap_id:
            raise InvalidHistoryError(
                f"mixed roadmap ids: {state.roadmap_id!r} and {event['roadmap_id']!r}"
            )

        event_type = event["type"]
        payload = event["payload"]

        if event_type == "roadmap_created":
            if state.roadmap_id is not None:
                raise InvalidHistoryError("roadmap_created may appear only once and must be first")
            state.roadmap_id = event["roadmap_id"]
            state.objective = payload["objective"]

        elif state.roadmap_id is None:
            raise InvalidHistoryError("roadmap_created must be the first event")

        elif event_type == "node_added":
            spec = payload["node"]
            node_id = spec["id"]
            if node_id in state.nodes:
                raise InvalidHistoryError(f"duplicate roadmap node id: {node_id}")
            authority_required = spec.get("authority_required")
            if spec["kind"] == "decision" and not authority_required:
                raise InvalidHistoryError(
                    f"decision node {node_id} requires authority_required"
                )
            if spec["kind"] != "decision" and authority_required:
                raise InvalidHistoryError(
                    f"authority_required is only legal on decision nodes: {node_id}"
                )
            state.nodes[node_id] = NodeState(
                id=node_id,
                kind=spec["kind"],
                title=spec["title"],
                resolver=spec["resolver"],
                authority_required=authority_required,
            )
            state.predecessors[node_id] = set()
            state.dependents[node_id] = set()

        elif event_type == "dependency_added":
            predecessor_id = payload["predecessor_id"]
            dependent_id = payload["dependent_id"]
            _require_node(state, predecessor_id)
            _require_node(state, dependent_id)
            if dependent_id in state.dependents[predecessor_id]:
                raise InvalidHistoryError(
                    f"duplicate dependency: {predecessor_id} -> {dependent_id}"
                )
            if _would_create_cycle(state, predecessor_id, dependent_id):
                raise InvalidHistoryError(
                    f"dependency cycle rejected: {predecessor_id} -> {dependent_id}"
                )
            state.dependents[predecessor_id].add(dependent_id)
            state.predecessors[dependent_id].add(predecessor_id)

        elif event_type == "node_resolved":
            node = _require_node(state, payload["node_id"])
            if node.status == "superseded":
                raise InvalidHistoryError(f"superseded node cannot be resolved: {node.id}")
            if node.kind == "fact" and not payload["evidence_pointers"]:
                raise InvalidHistoryError(
                    f"fact node {node.id} requires at least one evidence pointer"
                )
            authority = payload.get("authority")
            if node.kind == "decision":
                if authority != node.authority_required:
                    raise InvalidHistoryError(
                        f"decision node {node.id} requires authority {node.authority_required!r}"
                    )
            elif authority is not None:
                raise InvalidHistoryError(
                    f"authority is only legal when resolving a decision node: {node.id}"
                )
            node.status = "resolved"
            node.evidence_pointers = tuple(payload["evidence_pointers"])
            node.rationale = payload["rationale"]
            node.authority = authority
            node.review_reason = None

        elif event_type == "decision_superseded":
            old = _require_node(state, payload["decision_id"])
            replacement = _require_node(state, payload["replacement_id"])
            if old.kind != "decision" or replacement.kind != "decision":
                raise InvalidHistoryError("decision_superseded requires two decision nodes")
            if old.status != "resolved" or replacement.status != "resolved":
                raise InvalidHistoryError(
                    "both original and replacement decisions must be resolved before supersession"
                )
            old.status = "superseded"
            old.superseded_by = replacement.id
            for descendant_id in _descendants(state, old.id):
                descendant = state.nodes[descendant_id]
                if descendant.status == "resolved":
                    descendant.status = "needs_review"
                    descendant.review_reason = (
                        f"upstream decision {old.id} superseded by {replacement.id}"
                    )

        elif event_type == "unresolved_space_added":
            spec = payload["space"]
            space_id = spec["id"]
            if space_id in state.unresolved_spaces:
                raise InvalidHistoryError(f"duplicate unresolved-space id: {space_id}")
            state.unresolved_spaces[space_id] = UnresolvedSpaceState(
                id=space_id, title=spec["title"]
            )

        elif event_type == "unresolved_space_retired":
            space = _require_space(state, payload["space_id"])
            if space.status == "retired":
                raise InvalidHistoryError(f"unresolved space already retired: {space.id}")
            space.status = "retired"
            space.retired_reason = payload["reason"]

        elif event_type == "planning_scope_added":
            spec = payload["scope"]
            scope_id = spec["id"]
            if scope_id in state.scopes:
                raise InvalidHistoryError(f"duplicate planning-scope id: {scope_id}")
            for node_id in spec["node_ids"]:
                _require_node(state, node_id)
            for space_id in spec["unresolved_space_ids"]:
                _require_space(state, space_id)
            state.scopes[scope_id] = ScopeState(
                id=scope_id,
                title=spec["title"],
                node_ids=tuple(spec["node_ids"]),
                unresolved_space_ids=tuple(spec["unresolved_space_ids"]),
            )

        else:
            raise InvalidHistoryError(f"unsupported roadmap event type: {event_type}")

        state.last_seq = event["seq"]

    return state


def blockers_for(state: RoadmapState, node_id: str) -> list[str]:
    _require_node(state, node_id)
    return sorted(
        predecessor_id
        for predecessor_id in state.predecessors.get(node_id, set())
        if state.nodes[predecessor_id].status != "resolved"
    )


def _transitive_dependent_count(state: RoadmapState, node_id: str) -> int:
    return len(_descendants(state, node_id))


def frontier_report(
    state: RoadmapState,
    *,
    available_authorities: Iterable[str] = (),
) -> dict:
    authorities = set(available_authorities)
    report: list[dict] = []
    frontier: list[str] = []

    for node_id, node in sorted(state.nodes.items()):
        blockers = blockers_for(state, node_id)
        authority_missing = (
            node.kind == "decision"
            and node.authority_required is not None
            and node.authority_required not in authorities
        )
        open_status = node.status in {"open", "needs_review"}
        actionable = open_status and not blockers and not authority_missing
        if actionable:
            frontier.append(node_id)
        report.append(
            {
                "node_id": node_id,
                "status": node.status,
                "actionable": actionable,
                "blockers": blockers,
                "authority_required": node.authority_required,
                "authority_missing": authority_missing,
                "resolver": node.resolver,
                "direct_dependent_count": len(state.dependents.get(node_id, set())),
                "transitive_dependent_count": _transitive_dependent_count(state, node_id),
            }
        )

    return {"frontier": frontier, "nodes": report}


def build_plan_handoff(
    state: RoadmapState,
    *,
    scope_id: str,
    predecessor_phase: str,
    predecessor_artifact: str,
) -> dict:
    if predecessor_phase not in {"ideation", "research"}:
        raise InvalidHistoryError(
            "plan handoff predecessor_phase must be 'ideation' or 'research'"
        )
    try:
        scope = state.scopes[scope_id]
    except KeyError as exc:
        raise InvalidHistoryError(f"unknown planning-scope id: {scope_id}") from exc

    unresolved_nodes = [
        node_id for node_id in scope.node_ids
        if state.nodes[node_id].status != "resolved"
    ]
    unresolved_spaces = [
        space_id for space_id in scope.unresolved_space_ids
        if state.unresolved_spaces[space_id].status != "retired"
    ]
    if unresolved_nodes or unresolved_spaces:
        raise InvalidHistoryError(
            "planning scope is not ready: "
            f"unresolved_nodes={sorted(unresolved_nodes)}, "
            f"unresolved_spaces={sorted(unresolved_spaces)}"
        )

    facts: list[dict] = []
    decisions: list[dict] = []
    prerequisites: list[dict] = []
    for node_id in scope.node_ids:
        node = state.nodes[node_id]
        item = {
            "node_id": node.id,
            "title": node.title,
            "evidence_pointers": list(node.evidence_pointers),
            "rationale": node.rationale,
        }
        if node.kind == "fact":
            facts.append(item)
        elif node.kind == "decision":
            item["authority"] = node.authority
            decisions.append(item)
        else:
            prerequisites.append(item)

    return {
        "roadmap_id": state.roadmap_id,
        "scope": {"id": scope.id, "title": scope.title},
        "objective": state.objective,
        "predecessor": {
            "phase": predecessor_phase,
            "artifact": predecessor_artifact,
        },
        "settled_context": {
            "facts": facts,
            "decisions": decisions,
            "prerequisites": prerequisites,
        },
        "legal_next": "/qor-plan",
        "implementation_tasks": [],
    }
