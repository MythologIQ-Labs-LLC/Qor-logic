"""Phase 226 (GH #333): edge contracts of the per-event enforcer surface.

Companion to the adopted ``test_remediate_per_event_enforcers``: the three
implemented-but-untested behaviors (empty-mapping rejection, mixed-form
rejection, unknown-id surfacing at the mapping surface) plus the corrective
path's non-reopening sharpness. Per the audited red mechanisms, the mapping
calls OMIT ``closure_enforcer`` entirely -- passing ``None`` explicitly would
fake the red via a wrong-reason ``ClosureEnforcerError`` at v0.147.0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import remediate_mark_addressed as subject


def _attestation(tmp_path: Path) -> tuple[str, str]:
    gate = tmp_path / "remediate.json"
    gate.write_text("{}", encoding="utf-8")
    audit = tmp_path / "audit.json"
    audit.write_text(
        json.dumps(
            {
                "phase": "audit",
                "verdict": "PASS",
                "reviews_remediate_gate": str(gate),
            }
        ),
        encoding="utf-8",
    )
    return str(audit), str(gate)


def _shadow(monkeypatch: pytest.MonkeyPatch, events: list[dict]) -> list[list[dict]]:
    writes: list[list[dict]] = []
    monkeypatch.setattr(subject.shadow_process, "read_all_events", lambda: events)
    monkeypatch.setattr(
        subject.shadow_process,
        "id_source_map",
        lambda: {event["id"]: "docs/SHADOW_GENOME.md" for event in events},
    )
    monkeypatch.setattr(
        subject.shadow_process,
        "write_events_per_source",
        lambda updated, _src_map: writes.append([dict(item) for item in updated]),
    )
    return writes


def test_empty_mapping_is_rejected_before_any_mutation(tmp_path, monkeypatch):
    writes = _shadow(monkeypatch, [{"id": "SG-A", "addressed": False}])
    audit, gate = _attestation(tmp_path)

    with pytest.raises(subject.ClosureEnforcerError):
        subject.mark_addressed(
            {},
            session_id="phase226",
            review_pass_artifact_path=audit,
            remediate_gate_path=gate,
            repo_root=tmp_path,
        )
    assert writes == []


def test_mapping_plus_shared_enforcer_is_rejected(tmp_path, monkeypatch):
    """The shared enforcer here is VALID by design: the pre-change red must be
    'no error raised', never a wrong-reason error from enforcer validation."""
    writes = _shadow(monkeypatch, [{"id": "SG-A", "addressed": False}])
    audit, gate = _attestation(tmp_path)

    with pytest.raises(subject.ClosureEnforcerError):
        subject.mark_addressed(
            {"SG-A": "/qor-audit Step 4"},
            session_id="phase226",
            review_pass_artifact_path=audit,
            remediate_gate_path=gate,
            closure_enforcer="/qor-audit Step 4",
            repo_root=tmp_path,
        )
    assert writes == []


def test_unknown_mapping_ids_surface_in_missing(tmp_path, monkeypatch):
    """SG-032 at the mapping surface: unknown ids surface, known ids still flip."""
    events = [{"id": "SG-A", "addressed": False}]
    writes = _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    changed, missing, _skipped = subject.mark_addressed(
        {
            "SG-A": "/qor-audit Step 4",
            "SG-GHOST": "/qor-audit Step 4",
        },
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
    )

    assert changed == 1
    assert missing == ["SG-GHOST"]
    written = {event["id"]: event for event in writes[-1]}
    assert written["SG-A"]["addressed"] is True
    assert written["SG-A"]["closure_enforcer"] == "/qor-audit Step 4"


# --- Phase 230 (GH #341): nothing-to-do stops reading as nothing-matched ----


def test_already_addressed_batch_surfaces_in_skipped(tmp_path, monkeypatch):
    """The #341 outcome, distinguishable at last: an all-already-addressed batch
    is 'nothing to do', not 'nothing matched'."""
    events = [{"id": "SG-A", "addressed": True}, {"id": "SG-B", "addressed": True}]
    _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    result = subject.mark_addressed(
        {"SG-A": "/qor-audit Step 4", "SG-B": "/qor-audit Step 4"},
        session_id="phase230", review_pass_artifact_path=audit,
        remediate_gate_path=gate
    )

    assert result.changed == 0
    assert result.missing == []
    assert result.skipped == ["SG-A", "SG-B"]


def test_mixed_batch_partitions_changed_missing_skipped(tmp_path, monkeypatch):
    events = [{"id": "SG-A", "addressed": False}, {"id": "SG-B", "addressed": True}]
    _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    result = subject.mark_addressed(
        {"SG-A": "/qor-audit Step 4", "SG-B": "/qor-audit Step 4",
         "SG-GHOST": "/qor-audit Step 4"},
        session_id="phase230", review_pass_artifact_path=audit,
        remediate_gate_path=gate
    )

    assert result.changed == 1
    assert result.missing == ["SG-GHOST"]
    assert result.skipped == ["SG-B"]


def test_corrective_noop_and_ineligible_surface_in_skipped(tmp_path, monkeypatch):
    events = [
        {"id": "SG-EQ", "addressed": True, "addressed_reason": "remediated",
         "addressed_ts": "2026-01-01T00:00:00Z", "closure_enforcer": "/qor-audit Step 4"},
        {"id": "SG-PEND", "addressed": False},
    ]
    _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    result = subject.correct_closure_enforcers(
        {"SG-EQ": "/qor-audit Step 4", "SG-PEND": "/qor-audit Step 4"},
        session_id="phase230", review_pass_artifact_path=audit,
        remediate_gate_path=gate
    )

    assert result.changed == 0
    assert sorted(result.skipped) == ["SG-EQ", "SG-PEND"]


def test_pending_flip_surfaces_already_addressed_in_skipped(monkeypatch):
    """LD-5: the pending path's guard is the legacy helper's own eligibility
    test -- already-addressed events populate skipped."""
    events = [{"id": "SG-A", "addressed": False}, {"id": "SG-B", "addressed": True}]
    _shadow(monkeypatch, events)

    result = subject.mark_addressed_pending(["SG-A", "SG-B"], session_id="phase230")

    assert result.changed == 1
    assert result.skipped == ["SG-B"]


def test_corrective_repair_leaves_addressed_true(tmp_path, monkeypatch):
    """The repair changes the citation and nothing else: addressed stays true,
    the timestamp is untouched."""
    events = [{
        "id": "SG-A",
        "addressed": True,
        "addressed_reason": "remediated",
        "addressed_ts": "2026-08-12T05:06:24Z",
        "closure_enforcer": "qor.scripts.cycle_count_escalator",
    }]
    writes = _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    changed, missing, _skipped = subject.correct_closure_enforcers(
        {"SG-A": "/qor-audit Step 4"},
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
    )

    assert (changed, missing) == (1, [])
    repaired = writes[-1][0]
    assert repaired["addressed"] is True
    assert repaired["addressed_ts"] == "2026-08-12T05:06:24Z"
    assert repaired["closure_enforcer"] == "/qor-audit Step 4"
