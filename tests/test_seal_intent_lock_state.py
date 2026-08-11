"""Phase 220 (GH #324): the intent lock's state must be legible in the seal.

`intent_lock` is deliberately NOT added to CI. CI has no session and no lock
file, so the check is local by construction; a job there would assert a
guarantee the environment cannot provide -- the GH #314 shape this project has
already paid for twice.

Instead the state becomes a first-class field, so a reader counts occurrences
from the ledger rather than by grepping shadow events. Self-reported by the same
actor who skipped it, which is weak evidence -- but the change is from an
omission that leaves no trace to a field that must be actively falsified.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "qor" / "gates" / "schema" / "substantiate.schema.json"
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_accepts_lock_state():
    """The field exists with the three states a seal can honestly report."""
    field = _schema()["properties"]["intent_lock_state"]

    assert field["type"] == "string"
    assert sorted(field["enum"]) == ["absent", "overridden", "verified"]
    assert "intent_lock_state" not in _schema().get("required", [])


def test_schema_rejects_unknown_state(tmp_path: Path):
    """The enum is closed: a new state forces a deliberate amendment.

    Free text here would let 'partially verified' or 'n/a' accumulate, and the
    field would stop being countable -- which is its only purpose.
    """
    from qor.scripts import validate_gate_artifact as vga

    def errors_for(state):
        art = tmp_path / f"{state}.json"
        art.write_text(json.dumps({
            "phase": "substantiate", "ts": "2026-08-11T00:00:00Z",
            "session_id": "2026-08-11T0000-000000", "verdict": "PASS",
            "merkle_seal": "a" * 64, "phase_number": 220,
            "change_class": "feature", "plan_path": "docs/p.md",
            "intent_lock_state": state,
        }), encoding="utf-8")
        return vga.validate_one("substantiate", art)

    assert errors_for("verified") == []
    assert errors_for("absent") == []
    assert errors_for("probably-fine") != []


def test_seal_skill_records_the_state():
    """The wiring coupling: a field with no producer is a slot nothing fills.

    Precedent: Phase 217's `test_seal_step_invokes_the_check` and Phase 219's
    boundary equivalent, both shipped after a field or module arrived without
    the step that populates it.
    """
    body = SEAL_SKILL.read_text(encoding="utf-8")
    assert "intent_lock_state" in body  # prose-lint: ok=wiring-contract for a prompt-only unit


def test_seal_skill_stays_under_the_headroom_lock():
    """Third consecutive phase to add to this file. Measured, not assumed."""
    size = len(SEAL_SKILL.read_bytes().decode("utf-8").replace("\r\n", "\n").encode())
    assert size <= 39936, f"qor-substantiate at {size} B breaches the lock"
