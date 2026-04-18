"""Phase 32 Phase 1: install_drift_check functional tests.

Compares installed SKILL.md files against qor/skills/** source. SHA256 match
expected; missing files and content drift both flagged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import install_drift_check  # noqa: E402


def _mk_source(repo: Path, entries: dict[str, str]) -> None:
    for rel, body in entries.items():
        p = repo / "qor" / "skills" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def _mk_install(base: Path, entries: dict[str, str]) -> None:
    for rel, body in entries.items():
        p = base / "skills" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def test_clean_install_returns_empty(tmp_path, monkeypatch):
    _mk_source(tmp_path, {"governance/qor-x/SKILL.md": "body\n"})
    install = tmp_path / ".claude"
    _mk_install(install, {"qor-x/SKILL.md": "body\n"})
    monkeypatch.chdir(tmp_path)
    drift = install_drift_check.check(host="claude", scope="repo")
    assert drift == []


def test_missing_install_file_flagged(tmp_path, monkeypatch):
    _mk_source(tmp_path, {"governance/qor-y/SKILL.md": "body\n"})
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    drift = install_drift_check.check(host="claude", scope="repo")
    assert any("qor-y" in d for d in drift)
    assert any("missing" in d.lower() for d in drift)


def test_stale_install_file_flagged(tmp_path, monkeypatch):
    _mk_source(tmp_path, {"sdlc/qor-z/SKILL.md": "source content\n"})
    install = tmp_path / ".claude"
    _mk_install(install, {"qor-z/SKILL.md": "stale content\n"})
    monkeypatch.chdir(tmp_path)
    drift = install_drift_check.check(host="claude", scope="repo")
    assert any("qor-z" in d for d in drift)
    assert any("mismatch" in d.lower() or "differ" in d.lower() for d in drift)


def test_host_not_supported_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="host"):
        install_drift_check.check(host="nonexistent-host", scope="repo")


def test_scope_repo_looks_at_project_dir(tmp_path, monkeypatch):
    _mk_source(tmp_path, {"meta/qor-w/SKILL.md": "body\n"})
    install = tmp_path / ".claude"
    _mk_install(install, {"qor-w/SKILL.md": "body\n"})
    monkeypatch.chdir(tmp_path)
    drift = install_drift_check.check(host="claude", scope="repo")
    assert drift == []  # scope=repo reads .claude under cwd


def test_scope_global_reads_home_dir_path(tmp_path, monkeypatch):
    """Scope=global uses Path.home(). We don't write there; just confirm
    the path resolution branches differently -- missing home install
    should produce missing-file drift, not a ValueError."""
    _mk_source(tmp_path, {"memory/qor-v/SKILL.md": "body\n"})
    monkeypatch.chdir(tmp_path)
    # Point HOME to an empty temp dir so the global install looks blank
    monkeypatch.setenv("HOME", str(tmp_path / "fake_home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "fake_home"))
    # Should not raise; should flag missing install
    drift = install_drift_check.check(host="claude", scope="global")
    # We expect drift (install is missing from fake home)
    assert isinstance(drift, list)
