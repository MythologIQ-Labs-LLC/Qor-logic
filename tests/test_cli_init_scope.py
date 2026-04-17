"""Phase 24: init subcommand respects --scope."""
from __future__ import annotations

import json
from pathlib import Path


def test_init_writes_scope_repo_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.cli import main
    rc = main(["init", "--host", "gemini"])
    assert rc == 0
    config = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert config["host"] == "gemini"
    assert config["scope"] == "repo"


def test_init_with_target_override(tmp_path):
    from qor.cli import main
    target = tmp_path / "my_project"
    rc = main(["init", "--host", "codex", "--scope", "repo", "--target", str(target)])
    assert rc == 0
    config = json.loads((target / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert config["host"] == "codex"
    assert config["scope"] == "repo"


def test_init_global_scope_writes_to_host_base(tmp_path, monkeypatch):
    # Redirect HOME so we don't touch real ~/.codex
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows analog
    from qor.cli import main
    rc = main(["init", "--host", "codex", "--scope", "global"])
    assert rc == 0
    expected = Path.home() / ".codex" / ".qorlogic" / "config.json"
    assert expected.exists()
    config = json.loads(expected.read_text(encoding="utf-8"))
    assert config["host"] == "codex"
    assert config["scope"] == "global"


def test_init_records_all_core_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("QORLOGIC_PROJECT_DIR", raising=False)
    from qor.cli import main
    rc = main(["init", "--host", "gemini", "--scope", "repo", "--profile", "sdlc"])
    assert rc == 0
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["host"] == "gemini"
    assert data["scope"] == "repo"
    assert data["profile"] == "sdlc"
    assert "governance_scope" in data
