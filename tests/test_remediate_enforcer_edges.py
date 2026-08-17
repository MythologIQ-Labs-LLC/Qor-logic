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

    changed, missing = subject.mark_addressed(
        {
            "SG-A": "/qor-audit Step 4",
            "SG-GHOST": "/qor-audit Step 4",
        },
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
        repo_root=tmp_path,
    )

    assert changed == 1
    assert missing == ["SG-GHOST"]
    written = {event["id"]: event for event in writes[-1]}
    assert written["SG-A"]["addressed"] is True
    assert written["SG-A"]["closure_enforcer"] == "/qor-audit Step 4"


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

    changed, missing = subject.correct_closure_enforcers(
        {"SG-A": "/qor-audit Step 4"},
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
        repo_root=tmp_path,
    )

    assert (changed, missing) == (1, [])
    repaired = writes[-1][0]
    assert repaired["addressed"] is True
    assert repaired["addressed_ts"] == "2026-08-12T05:06:24Z"
    assert repaired["closure_enforcer"] == "/qor-audit Step 4"
