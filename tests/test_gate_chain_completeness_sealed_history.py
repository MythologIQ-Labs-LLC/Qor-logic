"""Phase 248 scope item 4 (GH #394): sealed history is exempt from prohibition
rules added after the fact.

A schema tightening must not retroactively invalidate artifacts that were
already sealed under an earlier schema. Enforcement of a new prohibition
belongs at authoring time (``gate_chain.write_gate_artifact`` validates the
full current schema before writing, which is forward-only by construction);
the sealed-history readers verify that the protocol was followed at the time,
which a later prohibition says nothing about.

The exemption is narrow: only the schema's top-level ``not`` clause is dropped.
``required`` / ``type`` / ``properties`` / ``$ref`` still apply, so GAP-GOV-14
holds -- an empty, malformed, or required-field-missing artifact still fails.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.reliability import gate_chain_completeness as gcc
from qor.scripts import evidence_bundle, validate_gate_artifact as vga


_SID = "2026-07-13T1025-96f825"


def _sealed_plan_payload(sid: str) -> dict:
    """A plan artifact in the shape phases 187/191/192 actually sealed."""
    return {
        "phase": "plan",
        "ts": "2026-07-13T10:14:34Z",
        "session_id": sid,
        "plan_path": "docs/plan-qor-phase187-negative-constraints.md",
        "phases": ["Phase 1: doctrine + pointer lines"],
        "ci_commands": ["python -m pytest -q"],
        "doc_tier": "standard",
        # The retired alias. Legal when these artifacts were written; prohibited
        # by the GH #394 schema rule this phase adds.
        "terms_introduced": [
            {"term": "Negative constraint", "home": "qor/references/doctrine-negative-constraints.md"}
        ],
    }


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_validate_one_rejects_retired_alias_by_default(tmp_path):
    """Authoring-time posture is unchanged: the alias is still prohibited.

    Guards against the sealed-history exemption leaking into the default path,
    which would silently undo the GH #394 fix.
    """
    artifact = _write(tmp_path / "plan.json", _sealed_plan_payload(_SID))

    errors = vga.validate_one("plan", artifact)

    assert errors, "default posture must still reject the retired terms_introduced alias"
    assert any("terms_introduced" in e for e in errors)


def test_validate_one_sealed_history_exempts_prohibition_rules(tmp_path):
    """The same payload validates when read as sealed history."""
    artifact = _write(tmp_path / "plan.json", _sealed_plan_payload(_SID))

    errors = vga.validate_one("plan", artifact, sealed_history=True)

    assert errors == [], f"sealed history must not be judged by a later prohibition: {errors}"


def test_sealed_history_still_rejects_structurally_invalid_artifact(tmp_path):
    """The exemption is narrow: `required` still applies under the flag.

    Preserves GAP-GOV-14 -- existence alone must not satisfy completeness.
    """
    payload = _sealed_plan_payload(_SID)
    del payload["ci_commands"]  # schema-`required`
    artifact = _write(tmp_path / "plan.json", payload)

    errors = vga.validate_one("plan", artifact, sealed_history=True)

    assert errors, "a required-field-missing artifact must fail even as sealed history"
    assert any("ci_commands" in e for e in errors)


def _sealed_session(tmp_path: Path, sid: str, phase_num: int) -> Path:
    """A repo root with one sealed phase whose plan artifact carries the alias."""
    gates = tmp_path / ".qor" / "gates" / sid
    _write(gates / "plan.json", _sealed_plan_payload(sid))
    for ph in ("audit", "implement", "substantiate"):
        base = {"phase": ph, "ts": "2026-07-13T10:20:00Z", "session_id": sid}
        if ph == "audit":
            base |= {"target": "docs/p.md", "verdict": "PASS",
                     "report_path": ".agent/staging/AUDIT_REPORT.md", "risk_grade": "L2"}
        if ph == "implement":
            base |= {"files_touched": ["qor/x.py"]}
        if ph == "substantiate":
            base |= {"verdict": "PASS", "merkle_seal": "a" * 64}
        _write(gates / f"{ph}.json", base)

    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "META_LEDGER.md").write_text(
        f"### Entry #1: SESSION SEAL -- Phase {phase_num} demo\n\n"
        f"**Phase**: SEAL (Phase {phase_num})\n"
        f"**Session**: {sid}\n\n"
        "**Decision**: sealed.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_check_passes_with_alias_carrying_sealed_artifact(tmp_path):
    """End-to-end regression for the Phase 248 seal-time abort.

    Before the fix this returned ok=False citing the `not` rule, which meant no
    seal in a repository holding such history could ever complete again.
    """
    root = _sealed_session(tmp_path, "2026-07-13T1025-96f825", 187)

    result = gcc.check(root, phase_min=52)

    assert result.ok, f"sealed history must not abort completeness: {result.missing}"
    assert not result.zero_population, "fixture must actually inspect a session"


def test_evidence_bundle_marks_alias_carrying_sealed_artifact_valid(tmp_path):
    """Tribunal ground V-3 (entry #676).

    An evidence packet attests that a sealed session's gate chain was intact.
    Calling a validly sealed artifact invalid, over a prohibition introduced
    after it was written, is the same false statement the seal-time abort made
    -- failing open into a document instead of closed into a gate.
    """
    sid = "2026-07-13T1025-96f825"
    root = _sealed_session(tmp_path, sid, 187)

    section = evidence_bundle._gate_artifacts(root, sid)

    plan_row = next(a for a in section["artifacts"] if a["phase"] == "plan")
    assert plan_row["valid"], f"sealed plan artifact must bundle as valid: {plan_row['errors']}"
