"""Phase 188 (GH #244): cursor + cline host targets."""
from __future__ import annotations

from pathlib import Path

from qor import hosts


def test_cursor_repo_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    target = hosts.resolve("cursor")
    assert target.name == "cursor"
    assert target.base == tmp_path / ".cursor"
    assert target.skills_dir == tmp_path / ".cursor" / "skills"
    assert target.agents_dir == tmp_path / ".cursor" / "agents"


def test_cline_repo_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    target = hosts.resolve("cline")
    assert target.name == "cline"
    assert target.base == tmp_path / ".clinerules"
    assert target.install_map["workflows/"] == tmp_path / ".clinerules" / "workflows"


def test_cline_no_skills_prefix(tmp_path, monkeypatch):
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    target = hosts.resolve("cline")
    assert set(target.install_map) == {"workflows/"}


def test_cursor_global_scope(monkeypatch):
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    target = hosts.resolve("cursor", scope="global")
    assert target.base == Path.home() / ".cursor"
