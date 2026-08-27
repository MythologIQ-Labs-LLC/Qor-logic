#!/usr/bin/env python3
"""remediate: classify grouped shadow events + session gate history into patterns.

Step 2 of the /qor-remediate skill protocol. Pattern precedence (highest
priority first):
  1. aged-high-severity
  2. hallucination
  3. regression
  4. repeated-veto-pattern (GH #362: /qor-audit's own repeated-VETO advisory)
  5. gate-loop            (Phase 37: unions gate_override | orchestration_override)
  6. plan-replay           (Phase 37: session gate-artifact-based; reads stall_walk)
  7. capability-shortfall aggregation

Priority matters when one session yields events matching multiple patterns — the
highest-priority pattern wins per group. The Phase 37 plan-replay match is
session-scoped and dropped if any gate-loop match covers the same session
(gate-loop dominates).
"""
from __future__ import annotations


# Event-type-based classifiers run over grouped shadow events.
# Highest-priority first.
PATTERN_RULES = [
    ("aged-high-severity",
     lambda events: any(e["event_type"] == "aged_high_severity_unremediated"
                        for e in events)),
    ("hallucination",
     lambda events: any(e["event_type"] == "hallucination" for e in events)),
    ("regression",
     lambda events: any(e["event_type"] == "regression" for e in events)),
    ("repeated-veto-pattern",
     lambda events: any(e["event_type"] == "repeated_veto_pattern" for e in events)),
    ("gate-loop",
     lambda events: (sum(1 for e in events
                         if e["event_type"] in ("gate_override", "orchestration_override"))
                     >= 2)),
    ("capability-shortfall aggregation",
     lambda events: (sum(1 for e in events if e["event_type"] == "capability_shortfall")
                     >= 3)),
]


def classify(
    groups: dict[tuple[str, str, str], list[dict]],
    session_id: str | None = None,
) -> list[dict]:
    """Classify each group into zero or one patterns. Returns a list of matches.

    When ``session_id`` is provided, also evaluates the Phase 37 plan-replay
    classifier by delegating to ``stall_walk.run`` for the session's gate
    artifacts. plan-replay is dropped if any gate-loop match exists for the
    same session (gate-loop dominates).
    """
    results: list[dict] = []
    for key, events in groups.items():
        event_type, skill, group_sid = key
        for pattern_name, predicate in PATTERN_RULES:
            if predicate(events):
                results.append({
                    "pattern": pattern_name,
                    "event_ids": [e["id"] for e in events],
                    "skill": skill,
                    "session_id": group_sid,
                    "event_type": event_type,
                })
                break

    if session_id is not None:
        _maybe_append_plan_replay(results, session_id)
    return results


def _maybe_append_plan_replay(results: list[dict], session_id: str) -> None:
    """Evaluate plan-replay from session gate artifacts; append if criteria met."""
    from qor.scripts import stall_walk

    count, signature, first_match_ts = stall_walk.run(session_id)
    if count < 3:
        return

    gate_loop_in_session = any(
        r["pattern"] == "gate-loop" and r["session_id"] == session_id
        for r in results
    )
    if gate_loop_in_session:
        return  # F6: gate-loop dominates plan-replay.

    results.append({
        "pattern": "plan-replay",
        "event_ids": [],
        "skill": "qor-plan",
        "session_id": session_id,
        "event_type": "plan-replay",
        "details": {
            "signature": signature,
            "cycle_count": count,
            "first_match_ts": first_match_ts,
        },
    })
