"""Phase 135 (pre-1.0 skill-corpus consolidation) behavioral tests.

Verifies the two largest governance skills (qor-audit, qor-substantiate) are
brought under the 40 KB `skill_size_budget_lint` EXCEEDED budget by *progressive
disclosure* -- multi-paragraph rationale relocates to ``references/`` while the
operative spine (Critical Invariants, Step headers, gate commands, VETO/ABORT
checklists) stays inline. The "moved-not-deleted" assertions make a silent cut
of any operative contract fail red.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import skill_size_budget_lint as ssbl

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "qor" / "skills"
AUDIT = SKILLS / "governance" / "qor-audit" / "SKILL.md"
SUBST = SKILLS / "governance" / "qor-substantiate" / "SKILL.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace so hard-wrapped prose matches as a contiguous span."""
    return " ".join(text.split())


def _exceeded_paths() -> set[str]:
    """Resolved paths of every SKILL.md the lint grades EXCEEDED (>=40 KB)."""
    findings = ssbl.check_skills(SKILLS)
    return {
        str(Path(f.skill_path).resolve())
        for f in findings
        if f.category == "skill-over-exceeded-threshold"
    }


# --- under-budget (invokes the lint, asserts on its findings) ---------------

def test_audit_under_budget() -> None:
    assert AUDIT.stat().st_size < ssbl.EXCEEDED_BYTES
    assert str(AUDIT.resolve()) not in _exceeded_paths()


def test_substantiate_under_budget() -> None:
    assert SUBST.stat().st_size < ssbl.EXCEEDED_BYTES
    assert str(SUBST.resolve()) not in _exceeded_paths()


def test_corpus_no_exceeded() -> None:
    findings = ssbl.check_skills(SKILLS)
    exceeded = [f for f in findings if f.category == "skill-over-exceeded-threshold"]
    assert exceeded == [], f"still EXCEEDED: {[f.skill_path for f in exceeded]}"


# --- spine preserved (a dropped contract fails these) -----------------------

AUDIT_INVARIANTS = [
    "plan-iteration lint failure -> ABORT",
    "Prompt Injection Pass failure -> ABORT",
    "L3 Risk Grade VETO",
    "OWASP Top-10 violation -> VETO",
    "Ghost-UI / Razor / self-application violation -> VETO",
    "Test Functionality Pass violation -> VETO",
    "Filter-Stage Pass violation -> VETO",
    "Infrastructure Alignment Pass grep-verify violation -> VETO",
    "Feature Test Declaration Pass violation -> VETO",
]
AUDIT_STEPS = [
    "### Step 0:", "### Step 0.3:", "### Step 0.4:", "### Step 0.5:",
    "### Step 0.6:", "### Step 1:", "### Step 2:", "### Step 3:",
    "### Step 4:", "### Step 5:", "### Step 6:", "### Step 7:", "### Step Z:",
]
AUDIT_COMMANDS = [
    "plan_iteration_status_lint", "prompt_injection_canaries", "audit_risk_score",
    "runtime_contract_walk", "plan_test_lint", "plan_feature_tdd_lint",
    "findings_categories", "infrastructure-mismatch", "prompt-injection",
]


@pytest.mark.parametrize("token", AUDIT_INVARIANTS + AUDIT_STEPS + AUDIT_COMMANDS)
def test_audit_spine_preserved(token: str) -> None:
    assert token in _read(AUDIT), f"qor-audit lost spine token: {token!r}"


SUBST_INVARIANTS = [
    "Step 4.6 reliability gates -> non-zero exit aborts substantiate",
    "Step 6.5 README badge currency check -> `|| ABORT`",
    "Step 7.8 gate-chain completeness check -> `|| ABORT`",
    "Constraints section at file foot",
]
SUBST_STEPS = [
    "### Step 4.6:", "### Step 4.6.5:", "### Step 4.6.8:", "### Step 4.6.9:",
    "### Step 4.6.10:", "### Step 4.7:", "### Step 4.7.5:", "### Step 7.5:",
    "### Step 7.6:", "### Step 7.8:", "### Step 9.5.5:", "### Step 9.7:",
]
SUBST_COMMANDS = [
    "intent_lock verify", "skill_admission", "gate_skill_matrix",
    "secret_scanner --staged", "merge_velocity_check", "data_api_acl_lint",
    "governance-index", "--enforce", "gate_chain_completeness", "dist_compile",
    "seal_trailer_check", "substantiate-capability",
]


@pytest.mark.parametrize("token", SUBST_INVARIANTS + SUBST_STEPS + SUBST_COMMANDS)
def test_substantiate_spine_preserved(token: str) -> None:
    assert token in _read(SUBST), f"qor-substantiate lost spine token: {token!r}"


# --- references resolve -----------------------------------------------------

def _cited_refs(skill_md: Path) -> list[str]:
    """Skill-local ``references/X.md`` citations only (not repo ``qor/references/``)."""
    import re
    text = _read(skill_md)
    return sorted(set(re.findall(r"(?<!qor/)references/([A-Za-z0-9._-]+\.md)", text)))


def test_audit_references_resolve() -> None:
    base = AUDIT.parent / "references"
    cited = _cited_refs(AUDIT)
    assert cited, "expected qor-audit to cite reference files"
    for name in cited:
        assert (base / name).is_file(), f"dangling audit reference: {name}"


def test_substantiate_references_resolve() -> None:
    base = SUBST.parent / "references"
    cited = _cited_refs(SUBST)
    assert cited, "expected qor-substantiate to cite reference files"
    for name in cited:
        assert (base / name).is_file(), f"dangling substantiate reference: {name}"


# --- rationale moved, not deleted -------------------------------------------

# Each (reference-file, distinctive sentence) pair: the sentence must live in
# the reference file (relocation target has the prose) AND no longer inline in
# the SKILL.md (proving the move).
AUDIT_MOVED = [
    ("pre-audit-lints.md",
     "Catches the COREFORGE-class credibility failure where a phase seals"),
    ("adversarial-mode.md",
     "Independent reviewers with no plan-authorship context naturally check different sources"),
    ("phase37-subpasses.md",
     "constructs the **pipeline stage dependency graph**"),
]
SUBST_MOVED = [
    ("seal-gate-ladder.md",
     "the canonical SKILL.md corpus grew from 91 KB"),
    ("release-and-tag-timing.md",
     "producing off-by-one tags across v0.19.0"),
]


@pytest.mark.parametrize("ref_name,sentence", AUDIT_MOVED)
def test_audit_rationale_moved(ref_name: str, sentence: str) -> None:
    ref = AUDIT.parent / "references" / ref_name
    assert ref.is_file(), f"missing reference file: {ref_name}"
    assert sentence in _norm(_read(ref)), f"{ref_name} missing relocated prose"
    assert sentence not in _norm(_read(AUDIT)), f"prose not moved out of SKILL.md: {sentence!r}"


@pytest.mark.parametrize("ref_name,sentence", SUBST_MOVED)
def test_substantiate_rationale_moved(ref_name: str, sentence: str) -> None:
    ref = SUBST.parent / "references" / ref_name
    assert ref.is_file(), f"missing reference file: {ref_name}"
    assert sentence in _norm(_read(ref)), f"{ref_name} missing relocated prose"
    assert sentence not in _norm(_read(SUBST)), f"prose not moved out of SKILL.md: {sentence!r}"


# --- admission still passes after edit ---------------------------------------

@pytest.mark.parametrize("skill", ["qor-audit", "qor-substantiate"])
def test_both_skills_admission_passes(skill: str) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "qor.reliability.skill_admission", skill],
        cwd=str(REPO), capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"skill_admission failed for {skill}: {proc.stderr or proc.stdout}"
