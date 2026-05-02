"""Phase 57: self-application invariants — meta-coherence."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qor.scripts import secret_scanner

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN = REPO_ROOT / "docs" / "plan-qor-phase57-gate-written-observer-channel.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-hook-contract.md"
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def test_secret_scanner_clean_against_phase57_plan_and_doctrine():
    """Meta-coherence: this plan + the new doctrine must scan clean.
    Markdown sources use auto-mask (.md suffix); Python sources use noqa sentinels.
    """
    md_targets = [PLAN, DOCTRINE]
    py_targets = [
        REPO_ROOT / "qor" / "scripts" / "gate_hooks.py",
        REPO_ROOT / "qor" / "scripts" / "gate_chain.py",
    ]
    findings: list = []
    for target in md_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target, mask_blocks=True))
    for target in py_targets:
        if target.exists():
            findings.extend(secret_scanner.scan(target))
    assert findings == [], (
        "Phase 57 self-application FAILED: scanner found secrets in own artifacts. "
        f"Findings: {[(f.file, f.line, f.pattern_name) for f in findings]}"
    )


def test_pre_audit_lints_clean_against_phase57_plan():
    """Phase 55 lints must remain clean against the Phase 57 plan."""
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


def test_glossary_round_trips_against_phase57_terms():
    text = GLOSSARY.read_text(encoding="utf-8")
    for term in ("gate_written hook", "hook contract"):
        assert term in text, f"glossary missing entry: {term}"
    # Each new term must declare home doctrine and introduced_in_plan
    assert "qor/references/doctrine-hook-contract.md" in text
    assert "phase57-gate-written-observer-channel" in text


def test_phase57_implement_gate_carries_ai_provenance():
    """Phase 54 provenance discipline must carry forward."""
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
