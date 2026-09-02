"""Phase 252 (GH #409, #411, #413): three governance signals that reported
something untrue, each teaching an operator to discount its channel.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import governance_helpers as gh
from qor.scripts import pr_citation_lint as pcl
from qor.scripts import qor_platform as qp

_SEAL = "c" * 63 + "1"


def _git_repo(tmp_path: Path, branch: str) -> Path:
    def run(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True, text=True)

    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@example.com")
    run("config", "user.name", "t")
    (tmp_path / "f.txt").write_text("x\n", encoding="utf-8")
    run("add", "f.txt")
    run("commit", "-qm", "init")
    if branch != "main":
        run("checkout", "-q", "-b", branch)
    return tmp_path


def test_isolation_satisfied_on_a_feature_branch(tmp_path):
    """GH #409: the phase branch exists to isolate, and a feature branch already does.

    Requiring branch *creation* rather than isolation forces an override on
    every orchestrated cycle, which then accrues severity carrying no
    information.
    """
    repo = _git_repo(tmp_path, "phase/99-demo")

    assert gh.branch_isolation_satisfied(repo) is True


def test_isolation_not_satisfied_on_the_default_branch(tmp_path):
    """The pair that keeps the precondition from being always-true."""
    repo = _git_repo(tmp_path, "main")

    assert gh.branch_isolation_satisfied(repo) is False


def test_availability_reports_satisfied_by_fallback(monkeypatch):
    """GH #411: absent but covered is not the same as missing."""
    monkeypatch.setattr(qp, "current", lambda *a, **k: {"detected": {}, "declared": {}})

    assert qp.availability("agent-teams") == "satisfied-by-fallback"


def test_availability_reports_missing_without_a_fallback(monkeypatch):
    """The guard that keeps `capability_shortfall` worth its severity.

    Reserve the event for capabilities with no viable substitute; a capability
    absent from FALLBACKS still reports missing.
    """
    monkeypatch.setattr(qp, "current", lambda *a, **k: {"detected": {}, "declared": {}})

    assert qp.availability("codex-plugin") == "missing"


def test_availability_reports_available_when_present(monkeypatch):
    monkeypatch.setattr(
        qp, "current", lambda *a, **k: {"detected": {"agent-teams": True}, "declared": {}}
    )

    assert qp.availability("agent-teams") == "available"


def test_is_available_contract_is_unchanged(monkeypatch):
    """Pins the declared non-goal: existing boolean callers keep working."""
    monkeypatch.setattr(qp, "current", lambda *a, **k: {"detected": {}, "declared": {}})

    assert qp.is_available("agent-teams") is False
    assert qp.is_available("codex-plugin") is False


_ENTRY = "ledger entry #700"
_PLAN = "docs/plan-qor-phase252-governance-signal-fidelity.md"
_BRIEF = "docs/research-brief-open-repository-issues-2026-09-02.md"


def test_seal_pr_still_requires_all_three_citations():
    """The guard against fix 3 becoming a way to skip citations where they matter."""
    files = [".qor/gates/s1/substantiate.json", "docs/META_LEDGER.md"]

    assert pcl.check_pr_body(f"{_PLAN} {_ENTRY} {_SEAL}", changed_files=files) == []
    missing = pcl.check_pr_body(f"{_PLAN} {_ENTRY}", changed_files=files)
    assert any("Merkle" in m for m in missing)


def test_research_pr_requires_brief_and_entry_not_a_seal():
    """The PR #412 case: a research record could satisfy exactly one of three."""
    files = [".qor/gates/s1/research.json", "docs/META_LEDGER.md", _BRIEF]

    assert pcl.check_pr_body(f"{_BRIEF} {_ENTRY}", changed_files=files) == []
    missing = pcl.check_pr_body("no citations here", changed_files=files)
    assert missing, "a research PR must still cite its brief and ledger entry"


def test_pr_with_no_gate_artifacts_requires_the_full_triple():
    """A code PR cannot opt out by shipping no artifacts."""
    missing = pcl.check_pr_body(f"{_PLAN} {_ENTRY}", changed_files=["qor/scripts/x.py"])

    assert any("Merkle" in m for m in missing)


def test_source_changing_pr_requires_the_full_triple_despite_a_research_artifact():
    """Tribunal ground V-2 (entry #699): the lenient rule must not be reachable
    by addition.

    Deriving requirements from the artifact set alone makes that set the
    settable label -- the same hazard the phase-label approach was rejected for.
    """
    files = [".qor/gates/s1/research.json", "qor/scripts/x.py"]

    missing = pcl.check_pr_body(f"{_BRIEF} {_ENTRY}", changed_files=files)

    assert any("Merkle" in m for m in missing), (
        "a source-changing PR must not be judged under the research rule"
    )


def test_work_named_plan_path_is_accepted():
    """GH #407's family on the PR surface: the phase-number convention is this
    repository's own and never described what a governance plan is."""
    body = f"docs/plan-sprint1-install.md {_ENTRY} {_SEAL}"

    assert pcl.check_pr_body(body, changed_files=[".qor/gates/s1/substantiate.json"]) == []


def test_backward_compatible_default_without_changed_files():
    """Callers that pass no file list keep today's strict behavior."""
    assert pcl.check_pr_body(f"{_PLAN} {_ENTRY} {_SEAL}") == []
    assert pcl.check_pr_body("nothing") != []
