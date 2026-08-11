"""Phase 220 (GH #324): both recording paths must be guarded.

The friction check lives in `gate_chain.emit_gate_override`.
`shadow_process.append_event` has none -- and all four `intent_lock` overrides
used `append_event` directly, because that is what an operator reaches for when
disclosing a gate they have already decided to pass.

Phase 219's session reached three overrides and would have fired. It did not,
because none of the three went through the checking path. Raising the
sensitivity of a control nothing calls would change nothing.

Friction is a cost, not a wall. An override that cannot be RECORDED past the
threshold leaves the operator choosing between undisclosed progress and no
progress, and the first is strictly worse than today.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import override_friction as of
from qor.scripts import shadow_process


def _event(session_id: str, gate: str, **extra) -> dict:
    base = {
        "ts": shadow_process.now_iso(), "skill": "qor-substantiate",
        "session_id": session_id, "event_type": "gate_override", "severity": 1,
        "details": {"gate": gate}, "addressed": False, "issue_url": None,
        "addressed_ts": None, "addressed_reason": None, "source_entry_id": None,
    }
    base.update(extra)
    return base


def _seed(log: Path, session_id: str, gate: str, n: int) -> None:
    lines = [json.dumps({"id": f"seed{i}", **_event(session_id, gate)}) for i in range(n)]
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_append_event_consults_friction(tmp_path: Path):
    """THE COUNTERFACTUAL. Fails at HEAD, where append_event has no friction."""
    log = tmp_path / "log.md"
    _seed(log, "sess", "intent_lock", of.DEFAULT_THRESHOLD)

    with pytest.raises(of.OverrideFrictionRequired):
        shadow_process.append_event(_event("sess", "intent_lock"), log_path=log)


def test_justified_override_past_threshold_still_records(tmp_path: Path):
    """Friction is a COST, not a wall.

    Without this, the fix would make disclosure impossible exactly when it
    matters and convert disclosed overrides into undisclosed ones -- strictly
    worse than the defect being fixed.
    """
    log = tmp_path / "log.md"
    _seed(log, "sess", "intent_lock", of.DEFAULT_THRESHOLD)

    event = _event("sess", "intent_lock", justification="x" * 60)
    event_id = shadow_process.append_event(event, log_path=log)

    assert event_id
    assert "justification" in log.read_text(encoding="utf-8").splitlines()[-1]


def test_non_override_events_are_unaffected(tmp_path: Path):
    """A capability_shortfall still appends freely; friction is override-only."""
    log = tmp_path / "log.md"
    _seed(log, "sess", "intent_lock", of.DEFAULT_THRESHOLD + 2)

    shortfall = _event("sess", "agent-teams")
    shortfall["event_type"] = "capability_shortfall"
    shortfall["details"] = {"capability": "agent-teams"}

    assert shadow_process.append_event(shortfall, log_path=log)


def test_below_threshold_records_without_justification(tmp_path: Path):
    """The first override of a phase is ordinary and must stay frictionless."""
    log = tmp_path / "log.md"
    log.write_text("", encoding="utf-8")

    assert shadow_process.append_event(_event("sess", "intent_lock"), log_path=log)


def test_third_occurrence_is_charged_not_the_fourth(tmp_path: Path):
    """The threshold counts the event being recorded, not only its predecessors.

    Entry #556 chose 3 on the grounds that it fires one phase before a human
    noticed the pattern. Comparing prior-count alone charges the FOURTH
    occurrence -- exactly when the operator already knew -- and delivers none of
    the reasoning that selected the number. Found by dogfooding the shipped
    check against the live log.
    """
    log = tmp_path / "log.md"
    _seed(log, "sess-a", "intent_lock", 2)

    with pytest.raises(of.OverrideFrictionRequired):
        shadow_process.append_event(_event("sess-b", "intent_lock"), log_path=log)


def test_second_occurrence_is_not_charged(tmp_path: Path):
    """One prior occurrence plus this one is two: still coincidence."""
    log = tmp_path / "log.md"
    _seed(log, "sess-a", "intent_lock", 1)

    assert shadow_process.append_event(_event("sess-b", "intent_lock"), log_path=log)

