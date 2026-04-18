"""Phase 28 Phase 2: plan-skill wiring for doc-integrity fields.

Covers the mechanical contract that /qor-plan Step 1b + Step Z produce:
the plan gate artifact accepts new optional fields, legacy tier is
schema-rejected without rationale, and legacy declarations emit a
severity-2 degradation shadow event (kind=doc_tier_legacy_declared).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402
import gate_chain  # noqa: E402


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "plan.schema.json"
)


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_payload(**overrides):
    payload = {
        "phase": "plan",
        "ts": "2026-04-17T23:35:05Z",
        "session_id": "sess-12345",
        "plan_path": "docs/plan-qor-phase99.md",
        "phases": ["Phase 1"],
    }
    payload.update(overrides)
    return payload


def test_step_z_writes_doc_tier_when_declared(tmp_path, monkeypatch):
    from qor.scripts import validate_gate_artifact as vga
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    payload = _base_payload(doc_tier="standard")
    gate_chain.write_gate_artifact("plan", payload, session_id="sess-12345")
    written = json.loads(
        (tmp_path / ".qor" / "gates" / "sess-12345" / "plan.json").read_text(encoding="utf-8")
    )
    assert written["doc_tier"] == "standard"


def test_step_z_omits_doc_tier_when_undeclared(tmp_path, monkeypatch):
    from qor.scripts import validate_gate_artifact as vga
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    gate_chain.write_gate_artifact("plan", _base_payload(), session_id="sess-12345")
    written = json.loads(
        (tmp_path / ".qor" / "gates" / "sess-12345" / "plan.json").read_text(encoding="utf-8")
    )
    assert "doc_tier" not in written


def test_step_z_writes_terms_array_format(tmp_path, monkeypatch):
    from qor.scripts import validate_gate_artifact as vga
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    payload = _base_payload(
        terms=[
            {"term": "Foo", "home": "README.md"},
            {"term": "Bar", "home": "docs/x.md"},
        ]
    )
    gate_chain.write_gate_artifact("plan", payload, session_id="sess-12345")
    written = json.loads(
        (tmp_path / ".qor" / "gates" / "sess-12345" / "plan.json").read_text(encoding="utf-8")
    )
    assert len(written["terms"]) == 2
    assert written["terms"][0] == {"term": "Foo", "home": "README.md"}


def test_step_z_writes_boundaries_sub_object(tmp_path, monkeypatch):
    from qor.scripts import validate_gate_artifact as vga
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    payload = _base_payload(
        boundaries={
            "limitations": ["a"],
            "non_goals": ["b"],
            "exclusions": ["c"],
        }
    )
    gate_chain.write_gate_artifact("plan", payload, session_id="sess-12345")
    written = json.loads(
        (tmp_path / ".qor" / "gates" / "sess-12345" / "plan.json").read_text(encoding="utf-8")
    )
    assert written["boundaries"]["limitations"] == ["a"]
    assert written["boundaries"]["non_goals"] == ["b"]
    assert written["boundaries"]["exclusions"] == ["c"]


def test_plan_legacy_tier_rejected_without_rationale():
    """Addresses VETO Ground 4 (Rule 4: Rule = Test).

    Schema-level enforcement via if-then: doc_tier=legacy requires
    doc_tier_rationale. No runtime code path needed; jsonschema catches it.
    """
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_payload(doc_tier="legacy"), _schema())


def test_plan_legacy_tier_accepted_with_rationale():
    jsonschema.validate(
        _base_payload(doc_tier="legacy", doc_tier_rationale="legacy repo; migration queued"),
        _schema(),
    )


def test_plan_legacy_tier_shadow_event_emitted(tmp_path):
    """Helper doc_integrity.emit_legacy_tier_event writes a severity-2
    degradation event with kind=doc_tier_legacy_declared.
    """
    log = tmp_path / "shadow.jsonl"
    doc_integrity.emit_legacy_tier_event(
        session_id="sess-12345",
        rationale="legacy repo; migration queued",
        log_path=log,
    )
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event_type"] == "degradation"
    assert event["severity"] == 2
    assert event["skill"] == "qor-plan"
    assert event["details"]["kind"] == "doc_tier_legacy_declared"
    assert event["details"]["rationale"] == "legacy repo; migration queued"
