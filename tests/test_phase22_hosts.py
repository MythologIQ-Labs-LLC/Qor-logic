"""Phase 22 Track C: Host expansion + init CLI tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_codex_host_resolves():
    """Codex no longer raises NotImplementedError."""
    from qor.hosts import resolve
    target = resolve("codex", scope="global")
    assert target.name == "codex"
    assert "codex" in str(target.skills_dir)


def test_register_host_custom():
    """register_host adds a new host factory."""
    from qor.hosts import HostTarget, register_host, resolve
    def _custom(scope: str = "repo") -> HostTarget:
        base = Path("/tmp/cursor")
        return HostTarget(
            name="cursor",
            base=base,
            install_map={"skills/": base / "skills", "agents/": base / "agents"},
        )
    register_host("cursor", _custom)
    target = resolve("cursor", scope="global")
    assert target.name == "cursor"
    assert target.skills_dir == Path("/tmp/cursor/skills")


def test_register_host_overrides_builtin():
    """register_host can override a built-in host."""
    from qor.hosts import HostTarget, register_host, resolve
    original = resolve("codex", scope="global")
    def _custom_codex(scope: str = "repo") -> HostTarget:
        base = Path("/tmp/codex-custom")
        return HostTarget(
            name="codex-custom",
            base=base,
            install_map={"skills/": base / "skills", "agents/": base / "agents"},
        )
    register_host("codex", _custom_codex)
    overridden = resolve("codex", scope="global")
    assert overridden.name == "codex-custom"
    # Restore original
    from qor.hosts import _codex_target
    register_host("codex", _codex_target)


def test_init_writes_config(tmp_path, monkeypatch):
    """qorlogic init writes .qorlogic/config.json."""
    monkeypatch.chdir(tmp_path)
    from qor.cli import main
    rc = main(["init", "--host", "claude", "--profile", "sdlc"])
    assert rc == 0
    config_path = tmp_path / ".qorlogic" / "config.json"
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["host"] == "claude"
    assert data["profile"] == "sdlc"


def test_init_sdlc_profile(tmp_path, monkeypatch):
    """SDLC profile sets governance_scope to git_root."""
    monkeypatch.chdir(tmp_path)
    from qor.cli import main
    main(["init", "--profile", "sdlc"])
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["governance_scope"] == "git_root"


def test_init_filesystem_profile(tmp_path, monkeypatch):
    """Non-SDLC profile sets governance_scope to cwd."""
    monkeypatch.chdir(tmp_path)
    from qor.cli import main
    main(["init", "--profile", "filesystem"])
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["governance_scope"] == "cwd"
    assert data["profile"] == "filesystem"


def test_install_reads_config(tmp_path, monkeypatch):
    """Config file is valid JSON with expected keys."""
    monkeypatch.chdir(tmp_path)
    from qor.cli import main
    main(["init", "--host", "kilo-code", "--profile", "research"])
    data = json.loads((tmp_path / ".qorlogic" / "config.json").read_text(encoding="utf-8"))
    assert data["host"] == "kilo-code"
    assert data["profile"] == "research"
    assert data["target"] is None


def test_policy_check_cli(tmp_path):
    """qorlogic policy check evaluates a request JSON."""
    request_data = {
        "principal": {"type": "Skill", "id": "qor-implement"},
        "action": {"type": "Action", "id": "implement"},
        "resource": {"type": "Gate", "id": "plan"},
        "entities": {
            'Gate::"plan"': {"verdict": "PASS"},
        },
    }
    req_file = tmp_path / "request.json"
    req_file.write_text(json.dumps(request_data), encoding="utf-8")
    from qor.cli import main
    rc = main(["policy", "check", str(req_file)])
    # Should return 0 (ALLOW) because gate_enforcement.cedar permits verdict==PASS
    assert rc == 0
