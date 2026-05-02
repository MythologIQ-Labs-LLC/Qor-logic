"""Phase 58: self-application invariants — meta-coherence."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qor.scripts import secret_scanner

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN = REPO_ROOT / "docs" / "plan-qor-phase58-procedural-fidelity-and-tech-debt-wrapup.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-procedural-fidelity.md"
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def test_secret_scanner_clean_against_phase58_plan_and_doctrine():
    """Phase 56 carry-forward."""
    md_targets = [PLAN, DOCTRINE]
    py_targets = [
        REPO_ROOT / "qor" / "scripts" / "procedural_fidelity.py",
    ]
    findings: list = []
    for target in md_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target, mask_blocks=True))
    for target in py_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target))
    assert findings == [], (
        "Phase 58 self-application FAILED. "
        f"Findings: {[(f.file, f.line, f.pattern_name) for f in findings]}"
    )


def test_pre_audit_lints_clean_against_phase58_plan():
    test_lint = subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_test_lint", "--plan", str(PLAN)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert test_lint.returncode == 0, f"plan_test_lint: {test_lint.stdout}\n{test_lint.stderr}"

    grep_lint = subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_grep_lint",
         "--plan", str(PLAN), "--repo-root", str(REPO_ROOT)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert grep_lint.returncode == 0, f"plan_grep_lint: {grep_lint.stdout}\n{grep_lint.stderr}"


def test_glossary_round_trips_against_phase58_terms():
    text = GLOSSARY.read_text(encoding="utf-8")
    for term in (
        "procedural-fidelity check",
        "procedural deviation",
        "doc-surface coverage",
    ):
        assert term in text, f"glossary missing entry: {term}"
    assert "qor/references/doctrine-procedural-fidelity.md" in text
    assert "phase58-procedural-fidelity-and-tech-debt-wrapup" in text


def test_phase58_implement_gate_carries_ai_provenance():
    """Phase 54 provenance discipline."""
    sid_path = REPO_ROOT / ".qor" / "session" / "current"
    if not sid_path.exists():
        return
    sid = sid_path.read_text(encoding="utf-8").strip()
    gate = REPO_ROOT / ".qor" / "gates" / sid / "implement.json"
    if not gate.exists():
        return
    payload = json.loads(gate.read_text(encoding="utf-8"))
    assert "ai_provenance" in payload
    assert payload["ai_provenance"].get("human_oversight") in ("absent", "present")


def test_phase59_ideation_plan_file_exists_at_renamed_path():
    """Regression: Phase 58 Phase 3 renamed the ideation plan; verify."""
    new_path = REPO_ROOT / "docs" / "plan-qor-phase59-ideation-readiness-phase.md"
    old_path = REPO_ROOT / "docs" / "plan-qor-phase58-ideation-readiness-phase.md"
    assert new_path.exists(), f"renamed ideation plan missing at {new_path}"
    assert not old_path.exists(), f"old ideation plan path should be gone: {old_path}"
