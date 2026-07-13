"""Phase 173 (GH #237): iteration-versioned gate artifacts.

One seal, one immutable file: every emission of a gate artifact lands in its
own `<phase>-iter<N>.json` that is never overwritten; the unversioned
`<phase>.json` singleton remains as a byte-identical latest copy for
backward compatibility. Resolution prefers the highest iteration and falls
back to the singleton for legacy (pre-173) session dirs.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from qor.scripts import audit_history, gate_chain, gate_hooks, gate_provenance
from qor.scripts import validate_gate_artifact as vga


SID = "2026-07-13T0000-it3r00"


@pytest.fixture
def gates(tmp_path, monkeypatch):
    """Redirect the gate tree, provenance key dir, and history dir to tmp."""
    gates_dir = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates_dir)
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates_dir)
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))
    return gates_dir


def _audit_payload(**overrides) -> dict:
    payload = {
        "ts": "2026-07-13T00:00:00Z",
        "target": "docs/plan.md",
        "verdict": "PASS",
    }
    payload.update(overrides)
    return payload


def _plan_payload(**overrides) -> dict:
    payload = {
        "ts": "2026-07-13T00:00:00Z",
        "plan_path": "docs/plan-a.md",
        "phases": ["p1"],
        "ci_commands": ["pytest"],
    }
    payload.update(overrides)
    return payload


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ----- Phase 1: versioned writer + sidecar duality + history binding -----

def test_first_write_creates_iter1_and_identical_singleton(gates):
    returned = gate_chain.write_gate_artifact("audit", _audit_payload(), session_id=SID)
    versioned = gates / SID / "audit-iter1.json"
    singleton = gates / SID / "audit.json"
    assert returned == versioned
    assert versioned.exists() and singleton.exists()
    assert versioned.read_bytes() == singleton.read_bytes()
    assert json.loads(versioned.read_text(encoding="utf-8"))["verdict"] == "PASS"


def test_rerun_preserves_sealed_iter1_bytes(gates):
    # GH #237 acceptance: seal iter-1's hash, re-run the phase, verify the
    # sealed bytes still exist and hash identically.
    gate_chain.write_gate_artifact(
        "audit",
        _audit_payload(verdict="VETO", findings_categories=["specification-drift"]),
        session_id=SID,
    )
    iter1 = gates / SID / "audit-iter1.json"
    sealed_hash = _sha(iter1)

    returned = gate_chain.write_gate_artifact(
        "audit", _audit_payload(verdict="PASS"), session_id=SID
    )
    iter2 = gates / SID / "audit-iter2.json"
    singleton = gates / SID / "audit.json"
    assert iter1.exists() and _sha(iter1) == sealed_hash
    assert returned == iter2 and iter2.exists()
    assert singleton.read_bytes() == iter2.read_bytes()
    assert json.loads(iter1.read_text(encoding="utf-8"))["verdict"] == "VETO"
    assert json.loads(iter2.read_text(encoding="utf-8"))["verdict"] == "PASS"


def test_rerun_preserves_iter1_provenance_sidecar(gates):
    gate_chain.write_gate_artifact(
        "audit",
        _audit_payload(verdict="VETO", findings_categories=["test-failure"]),
        session_id=SID,
    )
    iter1_side = gates / SID / "audit-iter1.provenance"
    sealed_side_hash = _sha(iter1_side)

    gate_chain.write_gate_artifact("audit", _audit_payload(verdict="PASS"), session_id=SID)
    assert _sha(iter1_side) == sealed_side_hash
    for name in ("audit-iter1.json", "audit-iter2.json", "audit.json"):
        res = gate_provenance.verify_sidecar(gates / SID / name)
        assert res.payload_ok and res.hmac_ok, f"{name}: {res.errors}"


def test_audit_history_rows_carry_versioned_filenames(gates):
    gate_chain.write_gate_artifact(
        "audit",
        _audit_payload(verdict="VETO", findings_categories=["coverage-gap"]),
        session_id=SID,
    )
    gate_chain.write_gate_artifact("audit", _audit_payload(verdict="PASS"), session_id=SID)
    rows = audit_history.read(SID)
    assert [r["artifact_filename"] for r in rows] == [
        "audit-iter1.json", "audit-iter2.json",
    ]
    assert [r["verdict"] for r in rows] == ["VETO", "PASS"]


def test_collision_advances_iteration_never_overwrites(gates):
    session_dir = gates / SID
    session_dir.mkdir(parents=True)
    sentinel = session_dir / "plan-iter1.json"
    sentinel.write_bytes(b"SENTINEL-DO-NOT-TOUCH")

    returned = gate_chain.write_gate_artifact("plan", _plan_payload(), session_id=SID)
    assert returned == session_dir / "plan-iter2.json"
    assert sentinel.read_bytes() == b"SENTINEL-DO-NOT-TOUCH"


def test_hook_event_binds_versioned_path(gates, monkeypatch):
    captured: list = []
    monkeypatch.setattr(gate_hooks, "dispatch_gate_written", captured.append)

    gate_chain.write_gate_artifact("plan", _plan_payload(), session_id=SID)
    assert len(captured) == 1
    event = captured[0]
    assert event.artifact_path.name == "plan-iter1.json"
    assert event.payload_sha256 == _sha(event.artifact_path)


# ----- Phase 2: latest-iteration resolution with legacy fallback -----

def _place(gates, name: str, payload: dict) -> None:
    session_dir = gates / SID
    session_dir.mkdir(parents=True, exist_ok=True)
    body = {"phase": "plan", "session_id": SID, **payload}
    (session_dir / name).write_text(json.dumps(body, indent=2), encoding="utf-8")


def test_check_prior_artifact_resolves_highest_iteration(gates):
    _place(gates, "plan-iter1.json", _plan_payload(plan_path="docs/plan-a.md"))
    _place(gates, "plan-iter2.json", _plan_payload(plan_path="docs/plan-b.md"))
    _place(gates, "plan.json", _plan_payload(plan_path="docs/plan-b.md"))

    result = gate_chain.check_prior_artifact("audit", session_id=SID)
    assert result.found and result.valid
    assert result.path.name == "plan-iter2.json"


def test_read_phase_artifact_returns_latest_payload(gates):
    _place(gates, "plan-iter1.json", _plan_payload(plan_path="docs/plan-a.md"))
    _place(gates, "plan-iter2.json", _plan_payload(plan_path="docs/plan-b.md"))
    _place(gates, "plan.json", _plan_payload(plan_path="docs/plan-b.md"))

    data = gate_chain.read_phase_artifact("plan", session_id=SID)
    assert data["plan_path"] == "docs/plan-b.md"


def test_legacy_singleton_only_session_still_resolves(gates):
    _place(gates, "plan.json", _plan_payload(plan_path="docs/plan-legacy.md"))

    result = gate_chain.check_prior_artifact("audit", session_id=SID)
    assert result.found and result.valid
    assert result.path.name == "plan.json"
    assert gate_chain.read_phase_artifact("plan", session_id=SID)["plan_path"] == (
        "docs/plan-legacy.md"
    )


def test_stale_singleton_does_not_shadow_iterations(gates):
    _place(gates, "plan-iter2.json", _plan_payload(plan_path="docs/plan-b.md"))
    _place(gates, "plan.json", _plan_payload(plan_path="docs/plan-a.md"))  # stale

    result = gate_chain.check_prior_artifact("audit", session_id=SID)
    assert result.path.name == "plan-iter2.json"
    assert gate_chain.read_phase_artifact("plan", session_id=SID)["plan_path"] == (
        "docs/plan-b.md"
    )
