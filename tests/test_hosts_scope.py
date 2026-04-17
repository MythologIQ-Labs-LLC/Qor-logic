"""Phase 24: uniform repo/global scope model for host resolution."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_claude_repo_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.hosts import resolve
    target = resolve("claude", scope="repo")
    assert target.base == tmp_path / ".claude"


def test_claude_global_scope():
    from qor.hosts import resolve
    target = resolve("claude", scope="global")
    assert target.base == Path.home() / ".claude"


def test_codex_repo_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.hosts import resolve
    target = resolve("codex", scope="repo")
    assert target.base == tmp_path / ".codex"


def test_kilo_repo_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.hosts import resolve
    target = resolve("kilo-code", scope="repo")
    assert target.base == tmp_path / ".kilo-code"


def test_target_override_wins(tmp_path):
    from qor.hosts import resolve
    target = resolve("claude", scope="repo", target_override=tmp_path)
    assert target.base == tmp_path
    assert target.install_map["skills/"] == tmp_path / "skills"


def test_qorlogic_project_dir_env(tmp_path, monkeypatch):
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    from qor.hosts import resolve
    target = resolve("claude", scope="repo")
    assert target.base == tmp_path / ".claude"


def test_default_scope_is_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.hosts import resolve
    target = resolve("claude")
    assert target.base == tmp_path / ".claude"


def test_unknown_host_raises():
    from qor.hosts import resolve
    with pytest.raises(ValueError, match="unknown"):
        resolve("not-a-host", scope="repo")


def test_invalid_scope_raises():
    from qor.hosts import resolve
    with pytest.raises(ValueError):
        resolve("claude", scope="nonsense")


def test_install_map_prefixes_for_skills_agents_hosts(tmp_path):
    from qor.hosts import resolve
    target = resolve("claude", scope="repo", target_override=tmp_path)
    assert "skills/" in target.install_map
    assert "agents/" in target.install_map
    assert target.install_map["skills/"] == tmp_path / "skills"
    assert target.install_map["agents/"] == tmp_path / "agents"
