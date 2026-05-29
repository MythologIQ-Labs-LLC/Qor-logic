"""Tests for qor/reliability/ enforcement scripts.

TDD-first: these tests are written before implementation per Phase 17 plan.
Covers Track 1 (intent-lock: 4), Track 2 (skill-admission: 3),
Track 3 (gate-skill-matrix: 3), Track 4 (skill-edit verification: 1).
Total: 11 new tests.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RELIABILITY_DIR = REPO_ROOT / "qor" / "reliability"
INTENT_LOCK = RELIABILITY_DIR / "intent_lock.py"
SKILL_ADMISSION = RELIABILITY_DIR / "skill_admission.py"
GATE_SKILL_MATRIX = RELIABILITY_DIR / "gate_skill_matrix.py"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command and capture output. cwd defaults to REPO_ROOT."""
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _init_git_repo(path: Path) -> None:
    """Initialize a minimal git repo at path with one commit."""
    _run(["git", "init", "-q"], cwd=path)
    _run(["git", "config", "user.email", "test@example.com"], cwd=path)
    _run(["git", "config", "user.name", "test"], cwd=path)
    (path / "seed.txt").write_text("seed", encoding="utf-8")
    _run(["git", "add", "seed.txt"], cwd=path)
    _run(["git", "commit", "-q", "-m", "seed"], cwd=path)


# ---- Track 1: intent-lock (4 tests) ----


def test_intent_lock_capture_writes_fingerprint(tmp_path: Path) -> None:
    """capture writes a JSON fingerprint with all required keys."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan body v1", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS\nsome notes", encoding="utf-8")

    result = _run(
        [sys.executable, str(INTENT_LOCK), "capture",
         "--session", "sess-cap-1",
         "--plan", str(plan),
         "--audit", str(audit),
         "--repo", str(tmp_path)],
    )

    assert result.returncode == 0, result.stderr
    assert "LOCKED: sess-cap-1" in result.stdout

    fingerprint_path = tmp_path / ".qor" / "intent-lock" / "sess-cap-1.json"
    assert fingerprint_path.exists()
    data = json.loads(fingerprint_path.read_text(encoding="utf-8"))
    for key in ("session", "plan_path", "plan_hash", "audit_path",
                "audit_hash", "head_commit", "captured_ts"):
        assert key in data, f"missing key: {key}"


def test_intent_lock_verify_passes_when_unchanged(tmp_path: Path) -> None:
    """verify exits 0 immediately after capture with no changes."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("stable plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    cap = _run(
        [sys.executable, str(INTENT_LOCK), "capture",
         "--session", "sess-verify-1",
         "--plan", str(plan),
         "--audit", str(audit),
         "--repo", str(tmp_path)],
    )
    assert cap.returncode == 0

    ver = _run(
        [sys.executable, str(INTENT_LOCK), "verify",
         "--session", "sess-verify-1",
         "--repo", str(tmp_path)],
    )
    assert ver.returncode == 0, ver.stderr
    assert "VERIFIED: sess-verify-1" in ver.stdout


def test_intent_lock_verify_detects_plan_drift(tmp_path: Path) -> None:
    """verify exits 1 with DRIFT: plan after plan mutation."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("original plan content", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    _run(
        [sys.executable, str(INTENT_LOCK), "capture",
         "--session", "sess-drift-1",
         "--plan", str(plan),
         "--audit", str(audit),
         "--repo", str(tmp_path)],
    )
    plan.write_text("MUTATED plan content", encoding="utf-8")

    ver = _run(
        [sys.executable, str(INTENT_LOCK), "verify",
         "--session", "sess-drift-1",
         "--repo", str(tmp_path)],
    )
    assert ver.returncode == 1
    assert "DRIFT: plan" in (ver.stdout + ver.stderr)


def test_intent_lock_capture_rejects_non_pass_audit(tmp_path: Path) -> None:
    """capture exits 1 when audit lacks PASS verdict."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: VETO\nreasons...", encoding="utf-8")

    result = _run(
        [sys.executable, str(INTENT_LOCK), "capture",
         "--session", "sess-veto",
         "--plan", str(plan),
         "--audit", str(audit),
         "--repo", str(tmp_path)],
    )
    assert result.returncode == 1
    assert "audit not PASS" in (result.stdout + result.stderr)


# ---- Phase 43: ancestry-based HEAD verification (6 tests) ----


def _capture_lock(repo: Path, session: str, plan: Path, audit: Path) -> subprocess.CompletedProcess:
    return _run(
        [sys.executable, str(INTENT_LOCK), "capture",
         "--session", session,
         "--plan", str(plan),
         "--audit", str(audit),
         "--repo", str(repo)],
    )


def _verify_lock(repo: Path, session: str) -> subprocess.CompletedProcess:
    return _run(
        [sys.executable, str(INTENT_LOCK), "verify",
         "--session", session,
         "--repo", str(repo)],
    )


def _add_commit(repo: Path, name: str, content: str, msg: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _run(["git", "add", name], cwd=repo)
    _run(["git", "commit", "-q", "-m", msg], cwd=repo)


def test_intent_lock_verify_allows_forward_head_advancement(tmp_path: Path) -> None:
    """verify exits 0 when HEAD has advanced past capture (legitimate implement commit)."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("stable plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    cap = _capture_lock(tmp_path, "sess-fwd", plan, audit)
    assert cap.returncode == 0

    # Mimic the implement commit advancing HEAD.
    _add_commit(tmp_path, "impl.txt", "implementation", "implement: feature work")

    ver = _verify_lock(tmp_path, "sess-fwd")
    assert ver.returncode == 0, ver.stderr
    assert "VERIFIED: sess-fwd" in ver.stdout


def test_intent_lock_verify_detects_history_rewrite(tmp_path: Path) -> None:
    """verify exits 1 with DRIFT: head when capture-HEAD is no longer reachable."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    # Add a commit so we can reset back past it.
    _add_commit(tmp_path, "before.txt", "before capture", "pre-capture commit")

    cap = _capture_lock(tmp_path, "sess-rewrite", plan, audit)
    assert cap.returncode == 0

    # Reset HEAD back past the captured commit, then add a divergent commit.
    _run(["git", "reset", "-q", "--hard", "HEAD~1"], cwd=tmp_path)
    _add_commit(tmp_path, "divergent.txt", "divergent", "divergent commit after rewrite")

    ver = _verify_lock(tmp_path, "sess-rewrite")
    assert ver.returncode == 1
    assert "DRIFT: head" in (ver.stdout + ver.stderr)


def test_intent_lock_verify_detects_branch_switch_to_divergent(tmp_path: Path) -> None:
    """verify exits 1 when current HEAD is on a divergent branch from capture-HEAD."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    # Build branch-A with a unique commit; capture there.
    _run(["git", "checkout", "-q", "-b", "branch-a"], cwd=tmp_path)
    _add_commit(tmp_path, "a.txt", "branch-a", "branch-a commit")

    cap = _capture_lock(tmp_path, "sess-branch", plan, audit)
    assert cap.returncode == 0

    # Build branch-B from the seed commit (divergent from branch-a's HEAD).
    _run(["git", "checkout", "-q", "-b", "branch-b", "main"], cwd=tmp_path)
    if _run(["git", "rev-parse", "branch-b"], cwd=tmp_path).returncode != 0:
        # Fallback: some git versions default to "master" on init.
        _run(["git", "checkout", "-q", "-b", "branch-b", "master"], cwd=tmp_path)
    _add_commit(tmp_path, "b.txt", "branch-b", "branch-b commit")

    ver = _verify_lock(tmp_path, "sess-branch")
    assert ver.returncode == 1
    assert "DRIFT: head" in (ver.stdout + ver.stderr)


def test_intent_lock_verify_detects_plan_drift_after_forward_head(tmp_path: Path) -> None:
    """Plan-hash drift is detected even after legitimate HEAD advancement."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan v1", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    cap = _capture_lock(tmp_path, "sess-plan-drift-fwd", plan, audit)
    assert cap.returncode == 0

    _add_commit(tmp_path, "impl.txt", "implementation", "implement")
    plan.write_text("plan v2 (mutated)", encoding="utf-8")

    ver = _verify_lock(tmp_path, "sess-plan-drift-fwd")
    assert ver.returncode == 1
    assert "DRIFT: plan" in (ver.stdout + ver.stderr)


def test_intent_lock_verify_detects_audit_drift_after_forward_head(tmp_path: Path) -> None:
    """Audit-hash drift is detected even after legitimate HEAD advancement."""
    _init_git_repo(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("plan", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("Verdict: PASS", encoding="utf-8")

    cap = _capture_lock(tmp_path, "sess-audit-drift-fwd", plan, audit)
    assert cap.returncode == 0

    _add_commit(tmp_path, "impl.txt", "implementation", "implement")
    audit.write_text("Verdict: PASS\n(amended notes)", encoding="utf-8")

    ver = _verify_lock(tmp_path, "sess-audit-drift-fwd")
    assert ver.returncode == 1
    assert "DRIFT: audit" in (ver.stdout + ver.stderr)


def test_intent_lock_verify_ancestry_uses_subprocess_list_argv() -> None:
    """Structural lint: verify() must use list-form subprocess.run for the ancestry check.

    Guards against shell=True regression that would open A03 injection vectors via
    a tampered head_commit value in the fingerprint JSON.
    """
    src = INTENT_LOCK.read_text(encoding="utf-8")
    # The ancestry call must exist as a list (square-bracket argv) and must NOT pass shell=True.
    assert "merge-base" in src and "is-ancestor" in src, "ancestry check missing"
    # No shell=True anywhere in the module.
    assert "shell=True" not in src, "shell=True forbidden"
    # The ancestry check must be invoked with list-form argv: search for the literal pattern.
    pattern = re.compile(r'\[\s*"git"\s*,\s*"merge-base"\s*,\s*"--is-ancestor"', re.MULTILINE)
    assert pattern.search(src), "merge-base --is-ancestor must be invoked via list-form argv"


# ---- Track 2: skill-admission (3 tests) ----


def test_skill_admission_admits_registered_skill() -> None:
    """Real registered skill qor-implement should be admitted."""
    result = _run([sys.executable, str(SKILL_ADMISSION), "qor-implement"])
    assert result.returncode == 0, result.stderr
    assert "ADMITTED: qor-implement" in result.stdout


def test_skill_admission_rejects_unregistered() -> None:
    """Bogus name not in registry should be rejected."""
    result = _run(
        [sys.executable, str(SKILL_ADMISSION), "qor-bogus-nonexistent"],
    )
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "NOT-ADMITTED" in combined
    assert "reason=unregistered" in combined


def test_skill_admission_rejects_missing_frontmatter_key(tmp_path: Path) -> None:
    """Fixture skill dir with SKILL.md missing 'phase' key rejects."""
    # Build a fake skills root with one skill missing the `phase` frontmatter key.
    fake_skills = tmp_path / "qor" / "skills" / "fake-cat" / "qor-fixture"
    fake_skills.mkdir(parents=True)
    skill_file = fake_skills / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: qor-fixture\n"
        "description: test fixture skill\n"
        "---\n"
        "# body\n",
        encoding="utf-8",
    )
    # Point the script at the fake root via env var SKILLS_ROOT.
    env = os.environ.copy()
    env["SKILLS_ROOT"] = str(tmp_path / "qor" / "skills")

    result = subprocess.run(
        [sys.executable, str(SKILL_ADMISSION), "qor-fixture"],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "reason=missing-frontmatter:phase" in combined


# ---- Track 3: gate-skill-matrix (3 tests) ----


def test_gate_skill_matrix_runs_clean_on_current_repo() -> None:
    """Real repo should show Broken: 0 and exit 0."""
    result = _run([sys.executable, str(GATE_SKILL_MATRIX)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Broken: 0" in result.stdout


def test_gate_skill_matrix_detects_broken_handoff(tmp_path: Path) -> None:
    """Fixture skill with a reference to /qor-nonexistent exits 1."""
    fake_root = tmp_path / "qor" / "skills" / "cat-a" / "qor-alpha"
    fake_root.mkdir(parents=True)
    (fake_root / "SKILL.md").write_text(
        "---\nname: qor-alpha\n---\n"
        "# body\n"
        "Handoff: /qor-nonexistent for cleanup.\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SKILLS_ROOT"] = str(tmp_path / "qor" / "skills")

    result = subprocess.run(
        [sys.executable, str(GATE_SKILL_MATRIX)],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 1
    assert "qor-nonexistent" in result.stdout


def test_gate_skill_matrix_ignores_self_references(tmp_path: Path) -> None:
    """A skill referencing its own trigger is not counted as broken."""
    fake_root = tmp_path / "qor" / "skills" / "cat-s" / "qor-selfy"
    fake_root.mkdir(parents=True)
    (fake_root / "SKILL.md").write_text(
        "---\nname: qor-selfy\n---\n"
        "Trigger: /qor-selfy\n"
        "Pure self-ref test.\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SKILLS_ROOT"] = str(tmp_path / "qor" / "skills")

    result = subprocess.run(
        [sys.executable, str(GATE_SKILL_MATRIX)],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Broken: 0" in result.stdout


# ---- Track 4: skill-edit verification (1 test, SG-035 proximity-anchored) ----


def test_reliability_unwired_in_skills() -> None:
    """Both skills invoke the reliability scripts at their respective step headers."""
    implement = (REPO_ROOT / "qor" / "skills" / "sdlc"
                 / "qor-implement" / "SKILL.md").read_text(encoding="utf-8")
    substantiate = (REPO_ROOT / "qor" / "skills" / "governance"
                    / "qor-substantiate" / "SKILL.md").read_text(encoding="utf-8")

    # Proximity-anchored (SG-035): step header within 500 chars of invocation path.
    impl_pattern = re.compile(
        r"Step 5\.5.{0,1500}(?:qor\.reliability\.intent_lock|qor-logic reliability intent_lock)", re.DOTALL,
    )
    assert impl_pattern.search(implement), (
        "qor-implement must invoke qor.reliability.intent_lock near Step 5.5"
    )

    sub_pattern_lock = re.compile(
        r"Step 4\.6.{0,2000}(?:qor\.reliability\.intent_lock|qor-logic reliability intent_lock)", re.DOTALL,
    )
    sub_pattern_admit = re.compile(
        r"Step 4\.6.{0,2000}(?:qor\.reliability\.skill_admission|qor-logic reliability skill_admission)", re.DOTALL,
    )
    sub_pattern_matrix = re.compile(
        r"Step 4\.6.{0,2000}(?:qor\.reliability\.gate_skill_matrix|qor-logic reliability gate_skill_matrix)", re.DOTALL,
    )
    assert sub_pattern_lock.search(substantiate), (
        "qor-substantiate must invoke qor.reliability.intent_lock near Step 4.6"
    )
    assert sub_pattern_admit.search(substantiate), (
        "qor-substantiate must invoke qor.reliability.skill_admission near Step 4.6"
    )
    assert sub_pattern_matrix.search(substantiate), (
        "qor-substantiate must invoke qor.reliability.gate_skill_matrix near Step 4.6"
    )
