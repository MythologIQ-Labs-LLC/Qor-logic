#!/usr/bin/env python3
"""remediate: classify grouped shadow events into one of 5 skill patterns.

Step 2 of the /qor-remediate skill protocol. Pattern precedence (highest
priority first): aged-high-severity, hallucination, regression, gate-loop,
capability-shortfall aggregation. Priority matters when one session yields
events matching multiple patterns — the highest-priority pattern wins per group.
"""
from __future__ import annotations


# Highest-priority first. Matching is one-per-group.
PATTERN_RULES = [
    ("aged-high-severity",
     lambda events: any(e["event_type"] == "aged_high_severity_unremediated"
                        for e in events)),
    ("hallucination",
     lambda events: any(e["event_type"] == "hallucination" for e in events)),
    ("regression",
     lambda events: any(e["event_type"] == "regression" for e in events)),
    ("gate-loop",
     lambda events: (sum(1 for e in events if e["event_type"] == "gate_override")
                     >= 2)),
    ("capability-shortfall aggregation",
     lambda events: (sum(1 for e in events if e["event_type"] == "capability_shortfall")
                     >= 3)),
]


def classify(groups: dict[tuple[str, str, str], list[dict]]) -> list[dict]:
    """Classify each group into zero or one patterns. Returns a list of matches.

    Each match dict: {"pattern": str, "event_ids": list[str], "skill": str,
    "session_id": str, "event_type": str}.
    """
    results: list[dict] = []
    for key, events in groups.items():
        event_type, skill, session_id = key
        for pattern_name, predicate in PATTERN_RULES:
            if predicate(events):
                results.append({
                    "pattern": pattern_name,
                    "event_ids": [e["id"] for e in events],
                    "skill": skill,
                    "session_id": session_id,
                    "event_type": event_type,
                })
                break
    return results
