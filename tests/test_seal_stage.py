"""Phase 229 (GH #337): the seal stages what a seal commits, by executable.

The documented Step 9.5 enumeration drifted from reality for nine ceremony
families and could not even run verbatim (it staged a `src/` that does not
exist). The list is now a module constant exercised by these tests; the
document invokes the mechanism instead of restating it.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import seal_stage


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / ".agent" / "staging").mkdir(parents=True)
    (tmp_path / ".qor" / "gates" / "sess-a").mkdir(parents=True)
    (tmp_path / ".qor" / "gates" / "sess-b").mkdir(parents=True)
    return tmp_path


def _staged(repo: Path) -> set[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                         cwd=repo, capture_output=True, text=True, check=True)
    return set(out.stdout.split())


def test_ceremony_files_are_staged(tmp_path):
    repo = _repo(tmp_path)
    for f in ("CHANGELOG.md", "README.md", "pyproject.toml",
              "docs/META_LEDGER.md", "docs/plan-qor-phase999-x.md",
              "docs/research-brief-x-2026-01-01.md",
              ".agent/staging/AUDIT_REPORT.md",
              ".qor/gates/sess-a/plan.json"):
        (repo / f).write_text("x", encoding="utf-8")

    staged_paths = seal_stage.stage("sess-a", repo)

    staged = _staged(repo)
    for f in ("CHANGELOG.md", "README.md", "pyproject.toml",
              "docs/META_LEDGER.md", "docs/plan-qor-phase999-x.md",
              "docs/research-brief-x-2026-01-01.md",
              ".agent/staging/AUDIT_REPORT.md",
              ".qor/gates/sess-a/plan.json"):
        assert f in staged, f
    assert staged_paths, "stage() must report what it staged"


def test_noise_is_not_staged(tmp_path):
    repo = _repo(tmp_path)
    (repo / "CHANGELOG.md").write_text("x", encoding="utf-8")
    (repo / "scratch.txt").write_text("noise", encoding="utf-8")
    (repo / "docs" / "notes.md").write_text("noise", encoding="utf-8")

    seal_stage.stage("sess-a", repo)

    staged = _staged(repo)
    assert "CHANGELOG.md" in staged
    assert "scratch.txt" not in staged
    assert "docs/notes.md" not in staged


def test_missing_families_are_harmless(tmp_path):
    """A repo lacking optional families stages what exists and raises nothing."""
    repo = _repo(tmp_path)
    (repo / "CHANGELOG.md").write_text("x", encoding="utf-8")

    staged_paths = seal_stage.stage("sess-a", repo)

    assert _staged(repo) == {"CHANGELOG.md"}
    assert staged_paths == ["CHANGELOG.md"]


def test_intent_lock_family_is_force_added_for_the_session(tmp_path):
    """Phase 231 (GH #332): the sealed session's lock record and snapshots are
    committed evidence, force-added past the directory's gitignore; another
    session's stay local."""
    repo = _repo(tmp_path)
    (repo / ".gitignore").write_text(".qor/intent-lock/\n", encoding="utf-8")
    lock_dir = repo / ".qor" / "intent-lock"
    lock_dir.mkdir(parents=True)
    for name in ("sess-a.json", "sess-a.plan.snapshot", "sess-a.audit.snapshot",
                 "sess-b.json"):
        (lock_dir / name).write_text("x", encoding="utf-8")

    seal_stage.stage("sess-a", repo)

    staged = _staged(repo)
    assert ".qor/intent-lock/sess-a.json" in staged
    assert ".qor/intent-lock/sess-a.plan.snapshot" in staged
    assert ".qor/intent-lock/sess-a.audit.snapshot" in staged
    assert ".qor/intent-lock/sess-b.json" not in staged


def test_gate_directory_is_staged_for_the_session(tmp_path):
    """The Phase 176 guarantee, now behavioral: the named session's gate dir is
    staged; another session's is untouched."""
    repo = _repo(tmp_path)
    (repo / ".qor" / "gates" / "sess-a" / "audit.json").write_text("{}", encoding="utf-8")
    (repo / ".qor" / "gates" / "sess-b" / "audit.json").write_text("{}", encoding="utf-8")

    seal_stage.stage("sess-a", repo)

    staged = _staged(repo)
    assert ".qor/gates/sess-a/audit.json" in staged
    assert ".qor/gates/sess-b/audit.json" not in staged
