"""Phase 218 (GH #313): the audit report and its gate artifact must agree.

`/qor-implement` Step 2 reads `.agent/staging/AUDIT_REPORT.md` and branches on
the verdict string alone. Nothing compares it to the audit gate artifact.

`.agent/staging/` is not session-scoped, so the stale window is unbounded rather
than a race. This session hit it three times: a Phase 206 report survived into
Phase 215, a Phase 215 report into Phase 216, and a stale VETO into Phase 217's
implement. Each time the interdiction would have passed on a PASS belonging to a
different phase -- passing for the wrong reason, which is worse than failing.

Both records already carry what is needed: the artifact has `target` and
`target_content_hash`.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import verdict_reconcile

REPO_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENT_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-implement" / "SKILL.md"

PLAN = "docs/plan-qor-phase218-unreconciled-record-cluster.md"
DIGEST = "a" * 64


def _report(tmp_path: Path, *, target: str, verdict: str = "PASS") -> Path:
    p = tmp_path / "AUDIT_REPORT.md"
    p.write_text(
        f"# AUDIT REPORT -- iteration 1\n\n"
        f"**Verdict**: {verdict}\n"
        f"**Target**: {target}\n",
        encoding="utf-8",
    )
    return p


def _artifact(tmp_path: Path, *, target: str, digest: str = DIGEST) -> Path:
    p = tmp_path / "audit.json"
    p.write_text(json.dumps({
        "phase": "audit", "verdict": "PASS",
        "target": target, "target_content_hash": digest,
    }), encoding="utf-8")
    return p


def test_mismatched_target_is_rejected(tmp_path: Path):
    """THE COUNTERFACTUAL. A PASS naming another phase's plan is not permission."""
    report = _report(tmp_path, target="docs/plan-qor-phase206-badge-layout-resolution.md")
    artifact = _artifact(tmp_path, target=PLAN)

    findings = verdict_reconcile.reconcile(report, artifact)

    assert findings, "a cross-phase report must not satisfy the interdiction"
    assert any(f.code == "target-mismatch" for f in findings), [f.code for f in findings]


def test_matching_target_and_digest_accepted(tmp_path: Path):
    """The good path: same plan, same digest, no findings."""
    report = _report(tmp_path, target=PLAN)
    artifact = _artifact(tmp_path, target=PLAN)

    assert verdict_reconcile.reconcile(report, artifact, plan_digest=DIGEST) == []


def test_stale_content_hash_is_rejected(tmp_path: Path):
    """Matching paths, but the plan was amended after the report was written.

    Comparing paths alone would accept this. The digest is why the check is
    worth having beyond the three occurrences that motivated it.
    """
    report = _report(tmp_path, target=PLAN)
    artifact = _artifact(tmp_path, target=PLAN, digest=DIGEST)

    findings = verdict_reconcile.reconcile(report, artifact, plan_digest="b" * 64)

    assert any(f.code == "digest-mismatch" for f in findings), [f.code for f in findings]


def test_absent_artifact_is_a_finding_not_permission(tmp_path: Path):
    """A missing gate artifact must not read as agreement."""
    report = _report(tmp_path, target=PLAN)

    findings = verdict_reconcile.reconcile(report, tmp_path / "nope.json")

    assert any(f.code == "artifact-missing" for f in findings), [f.code for f in findings]


def test_non_pass_verdict_is_reported(tmp_path: Path):
    """A stale VETO is caught here too, before Step 2's own interdiction."""
    report = _report(tmp_path, target=PLAN, verdict="VETO")
    artifact = _artifact(tmp_path, target=PLAN)

    findings = verdict_reconcile.reconcile(report, artifact, plan_digest=DIGEST)

    assert any(f.code == "verdict-not-pass" for f in findings), [f.code for f in findings]


def test_implement_step_invokes_the_reconciler():
    """The wiring coupling.

    Step 2 is prose: nothing mechanical fails if the call is dropped, and
    `verdict_reconcile` would sit in the tree looking like coverage. Precedent:
    Phase 217's `test_seal_step_invokes_the_check`, shipped for this reason.
    """
    body = IMPLEMENT_SKILL.read_text(encoding="utf-8")
    assert "verdict_reconcile" in body, "Step 2 must invoke the reconciler"  # prose-lint: ok=wiring-contract for a prompt-only unit


def test_cli_is_invocable_with_the_wired_flags(tmp_path: Path):
    """The CLI must accept exactly what the skill invokes.

    Phase 217 wired a seal step at `--scope auto` while the module's argparse
    rejected it, so the step exited 2 on every run. Same class: a module the
    skill cannot invoke is not wired, however complete it looks.
    """
    report = _report(tmp_path, target=PLAN)
    artifact = _artifact(tmp_path, target=PLAN)

    rc = verdict_reconcile.main([
        "--report", str(report), "--artifact", str(artifact), "--plan-digest", DIGEST])
    assert rc == 0

    stale = _report(tmp_path, target="docs/plan-qor-phase206-badge-layout-resolution.md")
    assert verdict_reconcile.main([
        "--report", str(stale), "--artifact", str(artifact)]) == 1


def test_path_separators_do_not_cause_a_false_mismatch(tmp_path: Path):
    """Windows artifacts record backslash paths; reports carry forward slashes.

    Found by running this module against its own phase's audit artifact. Left
    unfixed it would report `target-mismatch` on identical paths and ABORT
    every implement on Windows -- a false positive introduced by the fix for
    false negatives.
    """
    report = _report(tmp_path, target="docs/plan-qor-phase218-unreconciled-record-cluster.md")
    artifact = _artifact(
        tmp_path, target=r"docs\plan-qor-phase218-unreconciled-record-cluster.md")

    findings = verdict_reconcile.reconcile(report, artifact, plan_digest=DIGEST)

    assert findings == [], f"identical paths must not mismatch: {findings}"

