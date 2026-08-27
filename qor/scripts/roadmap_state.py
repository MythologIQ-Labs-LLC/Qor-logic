from __future__ import annotations

from collections.abc import Callable, Iterable

from qor.scripts.roadmap_model import (
    CONTRACT_VERSION,
    InvalidHistoryError,
    NodeState,
    RoadmapError,
    RoadmapState,
    ScopeState,
    UnsupportedVersionError,
    UnresolvedSpaceState,
    validate_event,
)


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


def _created(state: RoadmapState, payload: dict, event: dict) -> None:
    if state.roadmap_id is not None:
        raise InvalidHistoryError("roadmap_created may appear only once and must be first")
    state.roadmap_id = event["roadmap_id"]
    state.objective = payload["objective"]


def _node_added(state: RoadmapState, payload: dict, _event: dict) -> None:
    spec = payload["node"]
    node_id = spec["id"]
    if node_id in state.nodes:
        raise InvalidHistoryError(f"duplicate roadmap node id: {node_id}")
    authority_required = spec.get("authority_required")
    if spec["kind"] == "decision" and not authority_required:
        raise InvalidHistoryError(f"decision node {node_id} requires authority_required")
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


def _dependency_added(state: RoadmapState, payload: dict, _event: dict) -> None:
    predecessor_id = payload["predecessor_id"]
    dependent_id = payload["dependent_id"]
    _require_node(state, predecessor_id)
    _require_node(state, dependent_id)
    if dependent_id in state.dependents[predecessor_id]:
        raise InvalidHistoryError(f"duplicate dependency: {predecessor_id} -> {dependent_id}")
    if predecessor_id == dependent_id or predecessor_id in _descendants(state, dependent_id):
        raise InvalidHistoryError(
            f"dependency cycle rejected: {predecessor_id} -> {dependent_id}"
        )
    state.dependents[predecessor_id].add(dependent_id)
    state.predecessors[dependent_id].add(predecessor_id)


def _node_resolved(state: RoadmapState, payload: dict, _event: dict) -> None:
    node = _require_node(state, payload["node_id"])
    if node.status == "superseded":
        raise InvalidHistoryError(f"superseded node cannot be resolved: {node.id}")
    if node.kind == "fact" and not payload["evidence_pointers"]:
        raise InvalidHistoryError(f"fact node {node.id} requires at least one evidence pointer")
    authority = payload.get("authority")
    if node.kind == "decision" and authority != node.authority_required:
        raise InvalidHistoryError(
            f"decision node {node.id} requires authority {node.authority_required!r}"
        )
    if node.kind != "decision" and authority is not None:
        raise InvalidHistoryError(
            f"authority is only legal when resolving a decision node: {node.id}"
        )
    node.status = "resolved"
    node.evidence_pointers = tuple(payload["evidence_pointers"])
    node.rationale = payload["rationale"]
    node.authority = authority
    node.review_reason = None


def _decision_superseded(state: RoadmapState, payload: dict, _event: dict) -> None:
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


def _space_added(state: RoadmapState, payload: dict, _event: dict) -> None:
    spec = payload["space"]
    if spec["id"] in state.unresolved_spaces:
        raise InvalidHistoryError(f"duplicate unresolved-space id: {spec['id']}")
    state.unresolved_spaces[spec["id"]] = UnresolvedSpaceState(
        id=spec["id"], title=spec["title"]
    )


def _space_retired(state: RoadmapState, payload: dict, _event: dict) -> None:
    space = _require_space(state, payload["space_id"])
    if space.status == "retired":
        raise InvalidHistoryError(f"unresolved space already retired: {space.id}")
    space.status = "retired"
    space.retired_reason = payload["reason"]


def _scope_added(state: RoadmapState, payload: dict, _event: dict) -> None:
    spec = payload["scope"]
    if spec["id"] in state.scopes:
        raise InvalidHistoryError(f"duplicate planning-scope id: {spec['id']}")
    for node_id in spec["node_ids"]:
        _require_node(state, node_id)
    for space_id in spec["unresolved_space_ids"]:
        _require_space(state, space_id)
    state.scopes[spec["id"]] = ScopeState(
        id=spec["id"],
        title=spec["title"],
        node_ids=tuple(spec["node_ids"]),
        unresolved_space_ids=tuple(spec["unresolved_space_ids"]),
    )


_HANDLERS: dict[str, Callable[[RoadmapState, dict, dict], None]] = {
    "roadmap_created": _created,
    "node_added": _node_added,
    "dependency_added": _dependency_added,
    "node_resolved": _node_resolved,
    "decision_superseded": _decision_superseded,
    "unresolved_space_added": _space_added,
    "unresolved_space_retired": _space_retired,
    "planning_scope_added": _scope_added,
}


def _apply_event(state: RoadmapState, event: dict) -> None:
    validate_event(event)
    if state.roadmap_id is None and event["type"] != "roadmap_created":
        raise InvalidHistoryError("roadmap_created must be the first event")
    if state.roadmap_id is not None and event["roadmap_id"] != state.roadmap_id:
        raise InvalidHistoryError(
            f"mixed roadmap ids: {state.roadmap_id!r} and {event['roadmap_id']!r}"
        )
    try:
        handler = _HANDLERS[event["type"]]
    except KeyError as exc:
        raise InvalidHistoryError(
            f"unsupported roadmap event type: {event['type']}"
        ) from exc
    handler(state, event["payload"], event)


def reduce_events(events: Iterable[dict]) -> RoadmapState:
    state = RoadmapState()
    event_ids: set[str] = set()
    for event in events:
        if event.get("event_id") in event_ids:
            raise InvalidHistoryError(f"duplicate event_id: {event.get('event_id')}")
        expected_seq = state.last_seq + 1
        if event.get("seq") != expected_seq:
            raise InvalidHistoryError(
                f"non-contiguous roadmap seq: expected {expected_seq}, got {event.get('seq')}"
            )
        _apply_event(state, event)
        event_ids.add(event["event_id"])
        state.last_seq = event["seq"]
    return state
