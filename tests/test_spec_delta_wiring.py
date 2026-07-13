"""Phase 192 (GH #277): spec-delta gate-chain wiring."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts.spec_lint import check_delta
from qor.scripts.validate_gate_artifact import _validate_data as validate_payload

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_DELTA = """## ADDED Requirements

### Requirement: Deltas fold only after PASS
The seal ceremony SHALL fold declared deltas only inside substantiate after the reliability gates.

#### Scenario: VETO session
- GIVEN a session whose audit verdict is VETO
- WHEN the session ends
- THEN no delta is folded and the delta file remains
"""


# ----- schema acceptance --------------------------------------------------------

def _plan_payload(**extra) -> dict:
    payload = {
        "phase": "plan",
        "session_id": "2026-07-13T0000-abcdef",
        "ts": "2026-07-13T16:00:00Z",
        "plan_path": "docs/plan-qor-phase99-fake.md",
        "phases": ["Phase 1"],
        "ci_commands": ["python -m pytest -q"],
        "open_questions": [],
    }
    payload.update(extra)
    return payload


def test_plan_artifact_accepts_spec_deltas():
    errs = validate_payload("plan", _plan_payload(spec_deltas=[{
        "capability": "spec-corpus",
        "delta_path": "qor/specs/spec-corpus/deltas/2026-07-13T0000-abcdef.md",
        "ops": ["ADDED"],
        "evidence": "qor/scripts/spec_fold.py",
    }]))
    assert errs == [], errs


def test_plan_artifact_rejects_bad_spec_delta_op():
    errs = validate_payload("plan", _plan_payload(spec_deltas=[{
        "capability": "spec-corpus",
        "delta_path": "qor/specs/spec-corpus/deltas/x.md",
        "ops": ["RENAMED"],
    }]))
    assert errs, "unknown op must be rejected"


def test_substantiate_artifact_accepts_corpus_hash():
    errs = validate_payload("substantiate", {
        "phase": "substantiate",
        "ts": "2026-07-13T16:00:00Z",
        "session_id": "2026-07-13T0000-abcdef",
        "verdict": "PASS",
        "merkle_seal": "a" * 64,
        "version": "0.0.0",
        "spec_corpus_hash": {"spec-corpus": "b" * 64},
    })
    assert errs == [], errs


# ----- delta lint ----------------------------------------------------------------

def test_delta_lint_valid_delta_passes():
    assert check_delta(VALID_DELTA) == []


def test_delta_lint_bad_section_flagged():
    findings = check_delta("# just prose\n\nno sections here\n")
    assert findings and findings[0].code == "delta-no-sections"


def test_delta_lint_bad_inner_block_flagged():
    bad = VALID_DELTA.replace("SHALL fold", "folds")
    findings = check_delta(bad)
    assert any(f.code == "missing-rfc2119" for f in findings)


def test_delta_lint_cli_mode(tmp_path):
    good = tmp_path / "delta.md"
    good.write_text(VALID_DELTA, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.spec_lint", "--delta", "--files", str(good)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr


# ----- skill wiring within the byte budget ----------------------------------------

_WIRED = {
    "qor/skills/sdlc/qor-plan/SKILL.md": "spec-delta-authoring",
    "qor/skills/governance/qor-audit/SKILL.md": "spec-delta-pre-pass",
    "qor/skills/governance/qor-substantiate/SKILL.md": "spec_fold",
}
_HEADROOM = 39 * 1024


def test_skill_pointer_steps_present():
    for rel, token in _WIRED.items():
        path = REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        assert token in text, f"{rel} missing its spec-delta pointer ({token})"
        if "governance" in rel:
            assert os.path.getsize(path) < _HEADROOM, f"{rel} broke the headroom lock"
    for ref in ("qor/skills/sdlc/qor-plan/references/spec-delta-authoring.md",
                "qor/skills/governance/qor-audit/references/spec-delta-pre-pass.md"):
        assert (REPO_ROOT / ref).exists(), f"missing {ref}"


def test_self_application_corpus_state():
    """Both lifecycle states are legal and both must lint: pending deltas
    (pre-seal) pass the delta grammar; every capability spec (the folded,
    current-truth state) passes the spec grammar."""
    from qor.scripts.spec_lint import check

    for delta in sorted((REPO_ROOT / "qor" / "specs").rglob("deltas/*.md")):
        findings = check_delta(delta.read_text(encoding="utf-8"))
        assert findings == [], f"{delta}: {findings}"

    specs = sorted((REPO_ROOT / "qor" / "specs").glob("*/spec.md"))
    assert specs, "the Phase 192 self-application capability spec must exist"
    for spec in specs:
        findings = check(spec.read_text(encoding="utf-8"))
        assert findings == [], f"{spec}: {findings}"
