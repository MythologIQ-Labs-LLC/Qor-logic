"""Phase 217 (GH #314): install-drift scope resolution.

The defect this covers is noise, not silence. `check()` defaults to
`scope="repo"`; when that directory does not exist it returns one
`missing install` finding per source skill -- 30 of them, every invocation,
all expected and none meaningful. Collapsed by `|| echo` into a single
warning, it trained the operator to ignore a control that was, at the scope
actually in use, reporting 27 real mismatches.

A control whose default output is guaranteed-irrelevant is trained around,
so noise and silence fail identically.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import install_drift_check as idc


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    """Global scope resolves through Path.home(); pin it away from the operator.

    Without this the suite reads the real ~/.claude/skills, so results depend
    on whether the machine running the tests happens to have skills installed.
    That is the same class of dishonesty this phase exists to fix.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))


def _repo_with_skills(tmp_path: Path, names: list[str]) -> Path:
    repo = tmp_path / "repo"
    for name in names:
        d = repo / "qor" / "skills" / "sdlc" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {name}\nbody\n", encoding="utf-8")
    return repo


def _install(base: Path, repo: Path, names: list[str]) -> Path:
    skills = base / ".claude" / "skills"
    for name in names:
        d = skills / name
        d.mkdir(parents=True)
        src = repo / "qor" / "skills" / "sdlc" / name / "SKILL.md"
        (d / "SKILL.md").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return skills


NAMES = ["qor-plan", "qor-audit", "qor-implement"]


def test_absent_scope_reports_once_not_per_skill(tmp_path: Path, monkeypatch):
    """The core regression: an absent scope is ONE fact, not N defects.

    Before this phase, pointing `check()` at a scope with no install returned
    one finding per source skill. Thirty guaranteed-irrelevant findings per
    run is how a correct control becomes decorative.
    """
    repo = _repo_with_skills(tmp_path, NAMES)
    monkeypatch.chdir(repo)

    findings = idc.check(host="claude", scope="repo")

    assert len(findings) == 1, (
        f"an absent scope must collapse to one finding, got {len(findings)}: {findings}"
    )
    assert "repo" in findings[0]
    assert "not installed" in findings[0].lower()


def test_auto_scope_finds_real_mismatch(tmp_path: Path, monkeypatch):
    """Auto scope inspects the scope that actually has an install."""
    repo = _repo_with_skills(tmp_path, NAMES)
    skills = _install(repo, repo, NAMES)
    monkeypatch.chdir(repo)

    (skills / "qor-audit" / "SKILL.md").write_text("# qor-audit\nDIVERGED\n", encoding="utf-8")

    findings = idc.check(host="claude", scope="auto")

    assert len(findings) == 1, findings
    assert "qor-audit" in findings[0]
    assert "mismatch" in findings[0].lower()


def test_auto_scope_clean_when_synced(tmp_path: Path, monkeypatch):
    """A byte-identical install yields no findings."""
    repo = _repo_with_skills(tmp_path, NAMES)
    _install(repo, repo, NAMES)
    monkeypatch.chdir(repo)

    assert idc.check(host="claude", scope="auto") == []


def test_installed_scopes_lists_only_present_installs(tmp_path: Path, monkeypatch):
    """Scope discovery reports where an install exists, not where one could."""
    repo = _repo_with_skills(tmp_path, NAMES)
    monkeypatch.chdir(repo)

    assert idc.installed_scopes("claude") == []

    _install(repo, repo, NAMES)
    assert idc.installed_scopes("claude") == ["repo"]


def test_auto_scope_with_no_install_anywhere_is_one_finding(tmp_path: Path, monkeypatch):
    """Auto scope with nothing installed still reports once, not per skill."""
    repo = _repo_with_skills(tmp_path, NAMES)
    monkeypatch.chdir(repo)

    findings = idc.check(host="claude", scope="auto")

    assert len(findings) == 1, findings
    assert "no install found" in findings[0].lower()


def test_cli_accepts_auto_scope(tmp_path: Path, monkeypatch, capsys):
    """The CLI must accept every scope `check()` supports.

    `auto` was added to the function and not to argparse's choices, so the
    seal step wired at `--scope auto` exited 2 on every invocation -- a fix
    for an inert control, itself wired so it could not fire. This test is the
    coupling between the function's contract and the surface that exposes it.
    """
    repo = _repo_with_skills(tmp_path, NAMES)
    _install(repo, repo, NAMES)
    monkeypatch.chdir(repo)

    assert idc.main(["--host", "claude", "--scope", "auto"]) == 0
