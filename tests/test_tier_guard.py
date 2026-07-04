"""Phase 168 (GH #248): risk-tiered gate depth.

Behavioral tests across every guard cell and all four consumer seams:
schema (write time), tier_guard (implement prior), gate_chain_completeness
(seal/CI), gate_provenance verify-committed (merge). Governor decisions per
research entry #394: Shape 3 declared artifact set; audit-skip only for
L1-risk hotfix, never silent.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from qor.scripts import gate_chain, shadow_process, tier_guard

_SHORT = ["plan", "implement", "substantiate"]
_FULL = ["plan", "audit", "implement", "substantiate"]


def test_allowed_set_short_only_for_l1_hotfix():
    docs_only = ("docs/research-brief-x.md", "CHANGELOG.md")
    assert tier_guard.allowed_artifact_set(docs_only, "hotfix") == tier_guard.SHORT_CHAIN
    assert tier_guard.allowed_artifact_set(docs_only, "feature") == tier_guard.FULL_CHAIN
    l3_path = ("qor/scripts/hash_guard.py",)
    assert tier_guard.allowed_artifact_set(l3_path, "hotfix") == tier_guard.FULL_CHAIN
    l2_path = ("docs/META_LEDGER.md",)
    assert tier_guard.allowed_artifact_set(l2_path, "hotfix") == tier_guard.FULL_CHAIN


def test_check_declaration_names_the_violation():
    mismatches = tier_guard.check_declaration(
        _SHORT, ("qor/scripts/hash_guard.py",), "hotfix"
    )
    assert mismatches and "L3" in mismatches[0]
    assert tier_guard.check_declaration(_FULL, ("qor/scripts/hash_guard.py",), "breaking") == []
    assert tier_guard.check_declaration(_SHORT, ("docs/notes.md",), "hotfix") == []


def _plan_payload(**overrides) -> dict:
    payload = {
        "phase": "plan",
        "ts": "2026-07-04T12:00:00Z",
        "session_id": "2026-07-04T1200-aaaaaa",
        "plan_path": "docs/plan-x.md",
        "phases": ["one"],
        "ci_commands": ["python -m pytest -q"],
    }
    payload.update(overrides)
    return payload


def test_schema_rules_for_required_gate_artifacts():
    import jsonschema

    from qor.scripts import validate_gate_artifact as vga

    schema = vga.load_schema("plan")
    jsonschema.validate(_plan_payload(), schema)  # absent field: grandfathered
    jsonschema.validate(
        _plan_payload(change_class="hotfix", required_gate_artifacts=_SHORT), schema
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _plan_payload(change_class="feature", required_gate_artifacts=_SHORT), schema
        )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _plan_payload(change_class="hotfix",
                          required_gate_artifacts=["plan", "substantiate", "audit"]),
            schema,
        )


_PHASE_MINIMS = {
    "implement": {"files_touched": ["docs/notes.md"]},
    "substantiate": {"verdict": "PASS", "merkle_seal": "d" * 64},
}


def _write_session(gates: Path, sid: str, phases: list[str], plan_extra: dict) -> None:
    sess = gates / sid
    sess.mkdir(parents=True, exist_ok=True)
    for ph in phases:
        if ph == "plan":
            payload = _plan_payload(session_id=sid, **plan_extra)
        else:
            payload = {"phase": ph, "ts": "2026-07-04T12:00:00Z", "session_id": sid,
                       **_PHASE_MINIMS.get(ph, {})}
        (sess / f"{ph}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_implement_prior_accepts_legal_short_chain(tmp_path):
    gates = tmp_path / "gates"
    sid = "2026-07-04T1200-bbbbbb"
    _write_session(gates, sid, ["plan"], {
        "change_class": "hotfix",
        "required_gate_artifacts": _SHORT,
        "affected_files": ["docs/notes.md"],
    })
    with mock.patch.object(gate_chain, "GATES_DIR", gates):
        result = gate_chain.check_prior_artifact("implement", session_id=sid)
    assert result.found and result.valid
    assert result.path is not None and result.path.name == "plan.json"
    # illegal declaration (L3 path) keeps the legacy missing-prior error
    sid2 = "2026-07-04T1200-cccccc"
    _write_session(gates, sid2, ["plan"], {
        "change_class": "hotfix",
        "required_gate_artifacts": _SHORT,
        "affected_files": ["qor/scripts/hash_guard.py"],
    })
    with mock.patch.object(gate_chain, "GATES_DIR", gates):
        result = gate_chain.check_prior_artifact("implement", session_id=sid2)
    assert not result.found


_LEDGER_TMPL = """# LEDGER

### Entry #1: SESSION SEAL -- Phase {num} something

**Session**: `{sid}`
**Content Hash**: `{h}`
"""


def test_completeness_honors_declared_set(tmp_path):
    from qor.reliability import gate_chain_completeness as gcc

    gates = tmp_path / ".qor" / "gates"
    sid = "2026-07-04T1200-dddddd"
    _write_session(gates, sid, _SHORT, {
        "change_class": "hotfix",
        "required_gate_artifacts": _SHORT,
        "affected_files": ["docs/notes.md"],
    })
    ledger = tmp_path / "docs" / "META_LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(_LEDGER_TMPL.format(num=200, sid=sid, h="a" * 64), encoding="utf-8")
    result = gcc.check(tmp_path, phase_min=52)
    assert result.ok, f"legal short chain must satisfy completeness: {result.missing}"
    # undeclared session still requires all four
    sid2 = "2026-07-04T1200-eeeeee"
    _write_session(gates, sid2, _SHORT, {})
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        + _LEDGER_TMPL.format(num=201, sid=sid2, h="b" * 64).replace("Entry #1", "Entry #2"),
        encoding="utf-8",
    )
    result = gcc.check(tmp_path, phase_min=52)
    assert not result.ok
    assert any("audit.json" in what for _, what in result.missing)


def test_provenance_verify_committed_honors_declared_set(tmp_path):
    from qor.scripts import gate_provenance as gp

    gates = tmp_path / ".qor" / "gates"
    sid = "2026-07-04T1200-ffffff"
    _write_session(gates, sid, _SHORT, {
        "change_class": "hotfix",
        "required_gate_artifacts": _SHORT,
        "affected_files": ["docs/notes.md"],
    })
    for ph in _SHORT:
        art = gates / sid / f"{ph}.json"
        sidecar = gates / sid / f"{ph}.provenance"
        sidecar.write_text(json.dumps(
            {"payload_sha256": gp.payload_digest(art.read_bytes()), "session_id": sid}
        ), encoding="utf-8")
    ledger = tmp_path / "docs" / "META_LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(_LEDGER_TMPL.format(num=200, sid=sid, h="c" * 64), encoding="utf-8")
    result = gp.verify_committed(tmp_path, phase_min=158)
    assert result.ok, f"legal short chain must satisfy provenance: {result.mismatches}"


def test_short_chain_event_emitted(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    local.write_text("", encoding="utf-8")
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream), \
         mock.patch.object(shadow_process, "LOG_PATH", local):
        tier_guard.emit_short_chain_event(
            "2026-07-04T1200-aaaaaa", list(tier_guard.SHORT_CHAIN),
            reason="short-chain declared: L1 non-release",
        )
        events = shadow_process.read_events(local)
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_override"
    assert events[0]["severity"] == 1
    assert events[0]["details"]["gate"] == "audit"
