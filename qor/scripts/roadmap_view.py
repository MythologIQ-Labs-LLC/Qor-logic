from __future__ import annotations

from collections.abc import Iterable

from qor.scripts.roadmap_model import InvalidHistoryError, NodeState, RoadmapState, ScopeState
from qor.scripts.roadmap_state import _descendants, _require_node


def blockers_for(state: RoadmapState, node_id: str) -> list[str]:
    _require_node(state, node_id)
    return sorted(
        predecessor_id
        for predecessor_id in state.predecessors.get(node_id, set())
        if state.nodes[predecessor_id].status != "resolved"
    )


def _frontier_row(
    state: RoadmapState,
    node: NodeState,
    blockers: list[str],
    authority_missing: bool,
    actionable: bool,
) -> dict:
    return {
        "node_id": node.id,
        "status": node.status,
        "actionable": actionable,
        "blockers": blockers,
        "authority_required": node.authority_required,
        "authority_missing": authority_missing,
        "resolver": node.resolver,
        "direct_dependent_count": len(state.dependents.get(node.id, set())),
        "transitive_dependent_count": len(_descendants(state, node.id)),
    }


def frontier_report(
    state: RoadmapState,
    *,
    available_authorities: Iterable[str] = (),
) -> dict:
    authorities = set(available_authorities)
    rows: list[dict] = []
    frontier: list[str] = []
    for node_id, node in sorted(state.nodes.items()):
        blockers = blockers_for(state, node_id)
        authority_missing = (
            node.kind == "decision"
            and node.authority_required is not None
            and node.authority_required not in authorities
        )
        actionable = (
            node.status in {"open", "needs_review"}
            and not blockers
            and not authority_missing
        )
        if actionable:
            frontier.append(node_id)
        rows.append(_frontier_row(state, node, blockers, authority_missing, actionable))
    return {"frontier": frontier, "nodes": rows}


def _scope_for(state: RoadmapState, scope_id: str) -> ScopeState:
    try:
        return state.scopes[scope_id]
    except KeyError as exc:
        raise InvalidHistoryError(f"unknown planning-scope id: {scope_id}") from exc


def _assert_scope_ready(state: RoadmapState, scope: ScopeState) -> None:
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


def _settled_context(state: RoadmapState, scope: ScopeState) -> dict:
    grouped = {"facts": [], "decisions": [], "prerequisites": []}
    for node_id in scope.node_ids:
        node = state.nodes[node_id]
        item = {
            "node_id": node.id,
            "title": node.title,
            "evidence_pointers": list(node.evidence_pointers),
            "rationale": node.rationale,
        }
        if node.kind == "decision":
            item["authority"] = node.authority
            grouped["decisions"].append(item)
        elif node.kind == "fact":
            grouped["facts"].append(item)
        else:
            grouped["prerequisites"].append(item)
    return grouped


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
    scope = _scope_for(state, scope_id)
    _assert_scope_ready(state, scope)
    return {
        "roadmap_id": state.roadmap_id,
        "scope": {"id": scope.id, "title": scope.title},
        "objective": state.objective,
        "predecessor": {"phase": predecessor_phase, "artifact": predecessor_artifact},
        "settled_context": _settled_context(state, scope),
        "legal_next": "/qor-plan",
        "implementation_tasks": [],
    }
