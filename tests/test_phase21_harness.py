"""Phase 21: CLI harness, host resolver, manifest, CI wiring, rename, gitignore."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest


# ---- Track A: Host resolver (tests 1-6) ----

def test_host_resolver_claude_global_scope():
    """Phase 24: global scope produces ~/.claude (was default pre-Phase 24)."""
    from qor.hosts import resolve
    target = resolve("claude", scope="global")
    assert target.name == "claude"
    assert target.skills_dir == Path.home() / ".claude" / "skills"
    assert target.agents_dir == Path.home() / ".claude" / "agents"


def test_host_resolver_kilo_global_scope():
    from qor.hosts import resolve
    target = resolve("kilo-code", scope="global")
    assert target.name == "kilo-code"
    assert target.skills_dir == Path.home() / ".kilo-code" / "skills"
    assert target.agents_dir == Path.home() / ".kilo-code" / "agents"


def test_host_resolver_codex_resolves():
    """Phase 22: codex resolves instead of raising."""
    from qor.hosts import resolve
    target = resolve("codex", scope="global")
    assert target.name == "codex"
    assert "codex" in str(target.skills_dir)


def test_host_resolver_target_override(tmp_path):
    from qor.hosts import resolve
    target = resolve("claude", target_override=tmp_path)
    assert target.skills_dir == tmp_path / "skills"
    assert target.agents_dir == tmp_path / "agents"


def test_host_resolver_qorlogic_project_dir_env(tmp_path, monkeypatch):
    """Phase 24: CLAUDE_PROJECT_DIR no longer consulted; QORLOGIC_PROJECT_DIR replaces it."""
    from qor.hosts import resolve
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    target = resolve("claude", scope="repo")
    assert target.skills_dir == tmp_path / ".claude" / "skills"
    assert target.agents_dir == tmp_path / ".claude" / "agents"


def test_host_resolver_unknown_host_raises():
    from qor.hosts import resolve
    with pytest.raises(ValueError, match="unknown"):
        resolve("unknown-host")


# ---- Track A: Manifest (tests 7-8) ----

def test_manifest_emission_format(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "test-agent.md").write_text(
        "# agent\n", encoding="utf-8"
    )
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    manifest_path = out / "manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1"
    assert "generated_ts" in data
    assert isinstance(data["files"], list)
    assert len(data["files"]) > 0
    for entry in data["files"]:
        assert "id" in entry
        assert "source_path" in entry
        assert "install_rel_path" in entry
        assert "sha256" in entry


def test_manifest_sha256_matches_content(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    data = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    # Verify at least one entry sha256 matches manual computation
    for entry in data["files"]:
        fpath = out / "variants" / "claude" / entry["install_rel_path"]
        if fpath.exists():
            expected = hashlib.sha256(fpath.read_bytes()).hexdigest()
            assert entry["sha256"] == expected
            break
    else:
        pytest.fail("No manifest entry matched a file on disk")


# ---- Track A: Install/Uninstall (tests 9-12) ----

def test_install_copies_files_to_target(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod
    from qor.cli import _do_install

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    target_dir = tmp_path / "install_target"
    _do_install("claude", target_override=target_dir, dist_root=out)

    assert (target_dir / "skills" / "test-skill" / "SKILL.md").exists()
    assert (target_dir / "agents" / "a.md").exists()


def test_install_writes_installed_record(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod
    from qor.cli import _do_install

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    target_dir = tmp_path / "install_target"
    _do_install("claude", target_override=target_dir, dist_root=out)

    record = target_dir / ".qorlogic-installed.json"
    assert record.exists()
    data = json.loads(record.read_text(encoding="utf-8"))
    assert isinstance(data["files"], list)
    assert len(data["files"]) > 0


def test_uninstall_removes_installed_files(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod
    from qor.cli import _do_install, _do_uninstall

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    target_dir = tmp_path / "install_target"
    _do_install("claude", target_override=target_dir, dist_root=out)
    assert (target_dir / "skills" / "test-skill" / "SKILL.md").exists()

    _do_uninstall(target_override=target_dir)
    assert not (target_dir / "skills" / "test-skill" / "SKILL.md").exists()
    assert not (target_dir / ".qorlogic-installed.json").exists()


def test_cli_install_integration(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod
    from qor.cli import main

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    target_dir = tmp_path / "install_target"
    monkeypatch.setattr("qor.cli._default_dist_root", lambda: out)
    rc = main(["install", "--host", "claude", "--target", str(target_dir)])
    assert rc == 0
    assert (target_dir / "skills" / "test-skill" / "SKILL.md").exists()


# ---- Track A: CLI compile + verify-ledger (tests 13-14) ----

def test_cli_compile_returns_zero(tmp_path, monkeypatch):
    from qor.scripts import dist_compile as compile_mod
    from qor.cli import main

    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text(
        "# test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "a.md").write_text("# a\n", encoding="utf-8")
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)
    monkeypatch.setattr(compile_mod, "DEFAULT_OUT", tmp_path / "dist")

    rc = main(["compile"])
    assert rc == 0


def test_cli_verify_ledger_returns_zero(monkeypatch):
    from qor.cli import main
    # Point at the real ledger
    rc = main(["verify-ledger"])
    assert rc == 0


# ---- Track B: CI wiring (tests 15-16) ----

def test_ci_yml_has_drift_step():
    ci_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    assert "check_variant_drift" in text


def test_ci_yml_has_ledger_step():
    ci_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    assert "ledger_hash.py verify" in text


# ---- Track C: Rename (tests 17-19) ----

def test_dist_compile_importable():
    from qor.scripts import dist_compile
    assert hasattr(dist_compile, "compile_all")


def test_no_old_compile_module():
    old_path = Path(__file__).resolve().parent.parent / "qor" / "scripts" / "compile.py"
    assert not old_path.exists(), "qor/scripts/compile.py should be renamed to dist_compile.py"


def test_drift_check_uses_dist_compile():
    drift_path = Path(__file__).resolve().parent.parent / "qor" / "scripts" / "check_variant_drift.py"
    text = drift_path.read_text(encoding="utf-8")
    assert "dist_compile" in text
    assert "import compile as" not in text


# ---- Track D: .gitignore (test 20) ----

def test_gitignore_has_build_patterns():
    gi_path = Path(__file__).resolve().parent.parent / ".gitignore"
    text = gi_path.read_text(encoding="utf-8")
    for pattern in ["build/", "/dist/", "*.egg-info/", "*.whl"]:
        assert pattern in text, f"Missing {pattern} in .gitignore"
