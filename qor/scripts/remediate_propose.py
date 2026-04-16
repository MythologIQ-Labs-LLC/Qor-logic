#!/usr/bin/env python3
"""remediate: produce a remediation proposal skeleton from a classification.

Step 3 of the /qor-remediate skill protocol. Maps each pattern to a
proposal_kind (skill | agent | gate | doctrine) and a templated proposal_text.
The text is a skeleton — the governor (operator or Codex) fills in specifics.
"""
from __future__ import annotations


PATTERN_TO_KIND = {
    "gate-loop": "gate",
    "regression": "skill",
    "hallucination": "skill",
    "capability-shortfall aggregation": "agent",
    "aged-high-severity": "doctrine",
}


PROPOSAL_TEMPLATES = {
    "gate-loop": (
        "Tighten gate rubric for skill {skill}: repeated gate_override events "
        "indicate plan-quality or audit-calibration drift. Review the rubric "
        "and add a grounding check or verification hint that prevents the loop."
    ),
    "regression": (
        "Review skill {skill}: a regression event was recorded. Confirm prior "
        "cycle state restored or documented; add a guard test to prevent "
        "recurrence."
    ),
    "hallucination": (
        "Review skill {skill}: a hallucination event was recorded. Add a "
        "grounding check to the skill's Step 2 (plan-time) verification so "
        "the unverified mechanism is caught at plan review instead of "
        "substantiate."
    ),
    "capability-shortfall aggregation": (
        "Review agent capability for session {session_id}: 3+ capability_"
        "shortfall events indicate a structural gap. Consider adding a "
        "specialist agent, revising delegation-table, or documenting the "
        "shortfall in the relevant skill's constraints."
    ),
    "aged-high-severity": (
        "Escalate aged high-severity event in {skill}: unaddressed >90 days. "
        "Either mark resolved with rationale or promote to a first-class "
        "doctrine change (new SG entry) so the failure surface is prevented."
    ),
}


def propose(classification: dict) -> dict:
    """Produce a remediation proposal from a single classification record.

    Input shape: {"pattern": str, "event_ids": list[str], "skill": str, ...}.
    Output shape: {"pattern": str, "proposal_kind": str, "proposal_text": str,
    "addressed_event_ids": list[str]}.
    """
    pattern = classification["pattern"]
    kind = PATTERN_TO_KIND.get(pattern, "skill")
    template = PROPOSAL_TEMPLATES.get(pattern, "Review pattern {pattern} for skill {skill}.")
    text = template.format(
        pattern=pattern,
        skill=classification.get("skill", "<unknown>"),
        session_id=classification.get("session_id", "<unknown>"),
    )
    return {
        "pattern": pattern,
        "proposal_kind": kind,
        "proposal_text": text,
        "addressed_event_ids": list(classification["event_ids"]),
    }
