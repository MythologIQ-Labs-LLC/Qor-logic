"""Risk-tiered gate depth guard (Phase 168; GH #248).

Shape 3 per research entry #394: the plan artifact declares
``required_gate_artifacts`` explicitly; this module computes which set the
change is ALLOWED to declare (composing the two existing axes -- risk routing
over affected files + change_class) and verifies declarations for the three
consumers (gate_chain implement-prior carve-out, gate_chain_completeness,
gate_provenance verify-committed). The short chain omits ONLY the audit
phase, is permitted ONLY for L1-risk hotfix changes, and is never silent
(severity-1 gate_override shadow event on declaration).
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.capabilities.risk import route_risk
from qor.scripts import shadow_process

SHORT_CHAIN = ("plan", "implement", "substantiate")
FULL_CHAIN = ("plan", "audit", "implement", "substantiate")
_MINIMUM = frozenset(SHORT_CHAIN)


def allowed_artifact_set(changed_files: tuple[str, ...] | list[str],
                         change_class: str) -> tuple[str, ...]:
    """Short chain iff risk routing yields L1 AND change_class is hotfix."""
    grade = route_risk(".", tuple(changed_files)).risk_grade
    if grade == "L1" and change_class == "hotfix":
        return SHORT_CHAIN
    return FULL_CHAIN


def check_declaration(declared: list[str] | tuple[str, ...],
                      changed_files: tuple[str, ...] | list[str],
                      change_class: str) -> list[str]:
    """Mismatch strings when the declaration exceeds what the guard allows."""
    declared_set = set(declared)
    if not _MINIMUM.issubset(declared_set):
        missing = sorted(_MINIMUM - declared_set)
        return [f"declaration omits mandatory artifact(s): {', '.join(missing)}"]
    if "audit" in declared_set:
        return []
    grade = route_risk(".", tuple(changed_files)).risk_grade
    mismatches: list[str] = []
    if grade != "L1":
        mismatches.append(
            f"short chain declared but risk routing yields {grade}; "
            "audit is mandatory for L2/L3 surfaces"
        )
    if change_class != "hotfix":
        mismatches.append(
            f"short chain declared but change_class is {change_class!r}; "
            "release classes may never omit audit"
        )
    return mismatches


def declared_artifacts(plan_artifact: Path) -> tuple[str, ...]:
    """The session's declared artifact set; FULL_CHAIN when absent/unreadable.

    Absent field == full chain: every pre-168 session is grandfathered by
    construction, and an unreadable plan.json can never LOOSEN the contract.
    """
    try:
        payload = json.loads(Path(plan_artifact).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return FULL_CHAIN
    declared = payload.get("required_gate_artifacts")
    if not isinstance(declared, list) or not declared:
        return FULL_CHAIN
    declared_set = set(declared)
    if not _MINIMUM.issubset(declared_set) or not declared_set.issubset(set(FULL_CHAIN)):
        return FULL_CHAIN
    return tuple(p for p in FULL_CHAIN if p in declared_set)


def verify_session(session_id: str, gates_dir: Path) -> list[str]:
    """Implement-time fail-closed consumer: validate the session's declaration
    against the guard using the plan payload's affected_files + change_class."""
    plan_artifact = Path(gates_dir) / session_id / "plan.json"
    try:
        payload = json.loads(plan_artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"plan artifact unreadable: {plan_artifact}: {exc}"]
    declared = payload.get("required_gate_artifacts")
    if not isinstance(declared, list):
        return ["no short-chain declaration present"]
    return check_declaration(
        declared,
        tuple(payload.get("affected_files") or ()),
        str(payload.get("change_class") or ""),
    )


def emit_short_chain_event(session_id: str, declared: list[str], reason: str) -> str:
    """Never-silent discipline (Phase 59/75 precedent): record the audit skip."""
    return shadow_process.append_event(
        {
            "ts": shadow_process.now_iso(),
            "skill": "qor-plan",
            "session_id": session_id,
            "event_type": "gate_override",
            "severity": 1,
            "details": {"gate": "audit", "reason": reason, "declared": declared},
            "addressed": False,
            "issue_url": None,
            "addressed_ts": None,
            "addressed_reason": None,
            "source_entry_id": None,
        },
        attribution="LOCAL",
    )
