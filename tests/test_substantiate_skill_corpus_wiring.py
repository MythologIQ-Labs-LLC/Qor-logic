"""Phase 217 (GH #314): the seal records which corpus produced it.

A schema field with no producer is a governance record asserting a property
nothing supplies -- the shape catalogued in GH #319. These tests pin the field
and its wiring together so neither can outlive the other.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "qor" / "gates" / "schema" / "substantiate.schema.json"
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_accepts_skill_corpus():
    """The field exists, is optional, and constrains its members."""
    block = _schema()["properties"]["skill_corpus"]

    assert block["type"] == "object"
    assert set(block["properties"]) == {"digest", "scope", "drift_count"}
    assert block["properties"]["drift_count"]["type"] == "integer"
    assert block["properties"]["drift_count"]["minimum"] == 0
    assert "skill_corpus" not in _schema().get("required", [])


def test_schema_rejects_a_malformed_digest(tmp_path):
    """A digest that is not a sha256 hex string must not validate.

    Exercised through the real artifact validator rather than a hand-rolled
    jsonschema call, so the test fails if the validator stops enforcing the
    schema it loads.
    """
    from qor.scripts import validate_gate_artifact as vga

    def payload(digest):
        return {"phase": "substantiate", "ts": "2026-08-11T00:00:00Z",
                "session_id": "2026-08-11T0000-000000", "verdict": "PASS",
                "merkle_seal": "a" * 64, "phase_number": 217,
                "change_class": "feature", "plan_path": "docs/p.md",
                "skill_corpus": {"digest": digest, "scope": "repo", "drift_count": 0}}

    def errors_for(digest):
        artifact = tmp_path / f"{digest[:8]}.json"
        artifact.write_text(json.dumps(payload(digest)), encoding="utf-8")
        return vga.validate_one("substantiate", artifact)

    assert errors_for("b" * 64) == []
    assert errors_for("not-a-digest-x" * 4) != []


def test_seal_step_invokes_the_check():
    """The producer must exist wherever the field does.

    If the wiring is removed while the schema field remains, the field becomes
    a slot nothing fills -- and a seal that omits it is indistinguishable from
    a seal produced by a clean corpus. This test is the coupling.
    """
    body = SEAL_SKILL.read_text(encoding="utf-8")

    # The unit under test is a prompt, not a runtime: there is nothing to invoke,
    # and the failure guarded is the wiring being deleted while the schema field
    # remains. Text presence IS the contract here.
    assert "skill_corpus" in body, "must name the artifact field"  # prose-lint: ok=wiring-contract for a prompt-only unit
    assert "install_drift_check" in body, "must invoke the drift check"  # prose-lint: ok=wiring-contract for a prompt-only unit
    assert "--scope auto" in body, "must check the installed scope"  # prose-lint: ok=wiring-contract for a prompt-only unit


def test_seal_skill_stays_under_the_headroom_lock():
    """Phase 3 adds a step to a file with 313 bytes of slack.

    Phase 216 consumed 807 bytes of this same file against a 360-byte
    estimate. The audit made measurement binding rather than advisory.
    """
    size = len(SEAL_SKILL.read_bytes().decode("utf-8").replace("\r\n", "\n").encode())
    assert size <= 39936, f"qor-substantiate at {size} B breaches the 39936 lock"
