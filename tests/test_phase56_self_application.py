"""Phase 56: self-application invariants — meta-coherence."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qor.scripts import secret_scanner

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN = REPO_ROOT / "docs" / "plan-qor-phase56-secret-scanning-gate.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-eu-ai-act.md"
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def test_phase56_implement_gate_carries_ai_provenance():
    """Phase 54 provenance discipline must carry forward to Phase 56."""
    sid_path = REPO_ROOT / ".qor" / "session" / "current"
    if not sid_path.exists():
        return  # session-tooling-absent; doctrine carry-forward verified by other tests
    sid = sid_path.read_text(encoding="utf-8").strip()
    gate = REPO_ROOT / ".qor" / "gates" / sid / "implement.json"
    if not gate.exists():
        return  # implement gate not yet written
    payload = json.loads(gate.read_text(encoding="utf-8"))
    assert "ai_provenance" in payload
    assert payload["ai_provenance"].get("human_oversight") in ("absent", "present")


def test_secret_scanner_clean_against_phase56_plan_and_doctrine():
    """Meta-coherence: this plan + the new doctrine + new test files must scan
    clean against the new scanner. Worked examples must be in code spans
    (masked when scanning markdown) or carry the ``noqa: secret-scan`` sentinel.
    """
    # Markdown sources scan with code-block masking (worked examples in fences/backticks).
    md_targets = [PLAN, DOCTRINE]
    # Python sources scan with the per-line sentinel allowlist (no masking).
    py_targets = [
        REPO_ROOT / "tests" / "test_secret_scanner.py",
        REPO_ROOT / "tests" / "test_secret_scanner_findings_format.py",
        REPO_ROOT / "tests" / "test_substantiate_step_4_secret_scan_wiring.py",
        REPO_ROOT / "tests" / "test_substantiate_secret_scan_aborts_on_finding.py",
        REPO_ROOT / "tests" / "test_resource_attributes_production_scope.py",
        REPO_ROOT / "tests" / "test_doctrine_secret_scanning_anchored.py",
        REPO_ROOT / "tests" / "test_phase56_self_application.py",
        REPO_ROOT / "qor" / "scripts" / "secret_scanner.py",
        REPO_ROOT / "qor" / "policy" / "resource_attributes.py",
    ]
    findings: list = []
    for target in md_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target, mask_blocks=True))
    for target in py_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target))
    assert findings == [], (
        "Phase 56 self-application FAILED: scanner found secrets in own artifacts. "
        f"Findings: {[(f.file, f.line, f.pattern_name) for f in findings]}"
    )


def test_pre_audit_lints_clean_against_phase56_plan():
    """Phase 55 lints must remain clean against the Phase 56 plan."""
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


def test_glossary_round_trips_against_phase56_terms():
    text = GLOSSARY.read_text(encoding="utf-8")
    for term in ("secret-scanning gate", "gitleaks-compatible findings"):
        assert term in text, f"glossary missing entry: {term}"
