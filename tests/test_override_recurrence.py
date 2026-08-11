"""Phase 220 (GH #324): a repeated override must stop looking like a first one.

`override_friction` counts per session. Every phase rotates its session, so a
per-phase-recurring override resets the counter each time. Measured against the
live log when this was found: per-session 3 / 2 / 2 across three phases, while
`intent_lock` stood at 4 across sessions.

Four identical overrides is the exact shape the per-session mechanism cannot
see, and the shape most worth seeing -- one override is judgment, four is a
routine.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import override_friction as of


def _log(tmp_path: Path, events: list[tuple[str, str]]) -> Path:
    """Write a shadow log of (session_id, gate) override events."""
    p = tmp_path / "PROCESS_SHADOW_GENOME.md"
    lines = []
    for sid, gate in events:
        lines.append(json.dumps({
            "id": f"{sid}-{gate}", "ts": "2026-08-11T00:00:00Z",
            "skill": "qor-substantiate", "session_id": sid,
            "event_type": "gate_override", "severity": 1,
            "details": {"gate": gate},
        }))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_same_gate_across_sessions_escalates(tmp_path: Path):
    """THE COUNTERFACTUAL. Fails at HEAD, which counts only within a session."""
    log = _log(tmp_path, [
        ("2026-08-11T0526-a", "intent_lock"),
        ("2026-08-11T0639-b", "intent_lock"),
        ("2026-08-11T1304-c", "intent_lock"),
    ])

    result = of.gate_recurrence("intent_lock", log_path=log)

    assert result.threshold_reached, (
        "three overrides of one gate across three sessions is a habit forming; "
        "the per-session counter cannot see it because each phase rotates"
    )
    assert result.count == 3


def test_two_occurrences_do_not_escalate(tmp_path: Path):
    """The threshold is 3; a second occurrence is still coincidence.

    Pins the value against silent drift downward, which would reintroduce the
    alarm fatigue Phase 217 was sealed to remove.
    """
    log = _log(tmp_path, [
        ("2026-08-11T0526-a", "intent_lock"),
        ("2026-08-11T0639-b", "intent_lock"),
    ])

    assert not of.gate_recurrence("intent_lock", log_path=log).threshold_reached


def test_distinct_gates_do_not_aggregate(tmp_path: Path):
    """Four overrides of four gates is not a recurrence.

    Aggregating would make every busy session escalate, and the signal would be
    lost the same way it was lost before.
    """
    log = _log(tmp_path, [
        ("2026-08-11T0526-a", "intent_lock"),
        ("2026-08-11T0526-a", "plan_artifact_backfill"),
        ("2026-08-11T0526-a", "merge_velocity_check"),
        ("2026-08-11T0526-a", "feature_index_verify"),
    ])

    assert not of.gate_recurrence("intent_lock", log_path=log).threshold_reached


def test_recurrence_reports_the_gate_and_count(tmp_path: Path):
    """The operator is told what to fix, not that something is wrong."""
    log = _log(tmp_path, [(f"s{i}", "intent_lock") for i in range(4)])

    result = of.gate_recurrence("intent_lock", log_path=log)

    assert result.gate == "intent_lock"
    assert result.count == 4
    assert result.threshold == of.DEFAULT_THRESHOLD


def test_per_session_threshold_still_fires(tmp_path: Path):
    """REGRESSION. The existing axis is added to, not replaced."""
    log = _log(tmp_path, [("same-session", f"gate{i}") for i in range(3)])

    assert of.check("same-session", log_path=log).threshold_reached
