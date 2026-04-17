"""Phase 24: Gemini CLI host registration."""
from __future__ import annotations

from pathlib import Path


def test_gemini_repo_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.hosts import resolve
    target = resolve("gemini", scope="repo")
    assert target.base == tmp_path / ".gemini"
    assert target.install_map == {"commands/": tmp_path / ".gemini" / "commands"}


def test_gemini_global_scope():
    from qor.hosts import resolve
    target = resolve("gemini", scope="global")
    assert target.base == Path.home() / ".gemini"
    assert target.install_map["commands/"] == Path.home() / ".gemini" / "commands"


def test_gemini_no_skills_or_agents_prefix():
    from qor.hosts import resolve
    target = resolve("gemini", scope="global")
    assert "skills/" not in target.install_map
    assert "agents/" not in target.install_map


def test_gemini_target_override(tmp_path):
    from qor.hosts import resolve
    target = resolve("gemini", target_override=tmp_path)
    assert target.base == tmp_path
    assert target.install_map["commands/"] == tmp_path / "commands"
