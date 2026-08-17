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


def test_mark_addressed_preserves_per_event_enforcers(tmp_path, monkeypatch):
    events = [
        {"id": "SG-A", "addressed": False},
        {"id": "SG-B", "addressed": False},
    ]
    writes = _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    changed, missing, _skipped = subject.mark_addressed(
        {
            "SG-A": "/qor-substantiate Step 4.6",
            "SG-B": "/qor-audit Step 4",
        },
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
        repo_root=tmp_path,
    )

    assert changed == 2
    assert missing == []
    assert events[0]["closure_enforcer"] == "/qor-substantiate Step 4.6"
    assert events[1]["closure_enforcer"] == "/qor-audit Step 4"
    assert all(event["addressed"] for event in events)
    assert len(writes) == 1


def test_invalid_member_prevents_entire_batch_mutation(tmp_path, monkeypatch):
    events = [
        {"id": "SG-A", "addressed": False},
        {"id": "SG-B", "addressed": False},
    ]
    writes = _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    with pytest.raises(subject.ClosureEnforcerError):
        subject.mark_addressed(
            {"SG-A": "/qor-audit Step 4", "SG-B": "not-an-enforcer"},
            session_id="phase226",
            review_pass_artifact_path=audit,
            remediate_gate_path=gate,
            repo_root=tmp_path,
        )

    assert not writes
    assert not any(event["addressed"] for event in events)


def test_correct_closure_enforcers_repairs_only_citation(tmp_path, monkeypatch):
    events = [
        {
            "id": "SG-A",
            "addressed": True,
            "addressed_reason": "remediated",
            "addressed_ts": "2026-08-12T00:00:00Z",
            "closure_enforcer": "/qor-substantiate Step 4.6",
        },
        {
            "id": "SG-B",
            "addressed": False,
            "addressed_reason": None,
            "addressed_ts": None,
            "closure_enforcer": None,
        },
    ]
    writes = _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    changed, missing, _skipped = subject.correct_closure_enforcers(
        {"SG-A": "/qor-audit Step 4", "SG-B": "/qor-plan Step 2"},
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
        repo_root=tmp_path,
    )

    assert changed == 1
    assert missing == []
    assert events[0]["closure_enforcer"] == "/qor-audit Step 4"
    assert events[0]["addressed_ts"] == "2026-08-12T00:00:00Z"
    assert events[1]["closure_enforcer"] is None
    assert len(writes) == 1


def test_list_signature_remains_supported(tmp_path, monkeypatch):
    events = [{"id": "SG-A", "addressed": False}]
    _shadow(monkeypatch, events)
    audit, gate = _attestation(tmp_path)

    changed, missing, _skipped = subject.mark_addressed(
        ["SG-A"],
        session_id="phase226",
        review_pass_artifact_path=audit,
        remediate_gate_path=gate,
        closure_enforcer="/qor-audit Step 4",
        repo_root=tmp_path,
    )

    assert (changed, missing) == (1, [])
    assert events[0]["closure_enforcer"] == "/qor-audit Step 4"
