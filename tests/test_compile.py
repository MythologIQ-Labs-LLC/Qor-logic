"""Tests for Phase 2 compile pipeline + drift check."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from qor.scripts import compile as compile_mod
from qor.scripts import check_variant_drift as drift_mod


@pytest.fixture
def fake_tree(tmp_path, monkeypatch):
    """Build a minimal qor/skills/ + qor/agents/ fixture and point compile_mod at it."""
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "test-skill").mkdir(parents=True)
    (skills / "governance" / "test-skill" / "SKILL.md").write_text("# test-skill\n", encoding="utf-8")
    (skills / "governance" / "test-skill" / "references").mkdir()
    (skills / "governance" / "test-skill" / "references" / "notes.md").write_text("ref\n", encoding="utf-8")
    (skills / "memory" / "loose.md").parent.mkdir(parents=True)
    (skills / "memory" / "loose.md").write_text("loose skill\n", encoding="utf-8")
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "test-agent.md").write_text("# agent\n", encoding="utf-8")

    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)
    return tmp_path


def test_compile_emits_claude_variant(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    skill_md = out / "variants" / "claude" / "skills" / "test-skill" / "SKILL.md"
    assert skill_md.exists()
    assert skill_md.read_text(encoding="utf-8") == "# test-skill\n"


def test_compile_emits_kilocode_variant(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    skill_md = out / "variants" / "kilo-code" / "skills" / "test-skill" / "SKILL.md"
    assert skill_md.exists()


def test_compile_copies_skill_references(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    ref = out / "variants" / "claude" / "skills" / "test-skill" / "references" / "notes.md"
    assert ref.exists()
    assert ref.read_text(encoding="utf-8") == "ref\n"


def test_compile_emits_loose_skill(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    loose = out / "variants" / "claude" / "skills" / "loose.md"
    assert loose.exists()
    assert loose.read_text(encoding="utf-8") == "loose skill\n"


def test_compile_flattens_agents(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    # Agent lands flat, not under a category subdir in dist
    agent = out / "variants" / "claude" / "agents" / "test-agent.md"
    assert agent.exists()
    # No category subdir
    assert not (out / "variants" / "claude" / "agents" / "governance").exists()


def test_codex_stub_writes_gitkeep_only(fake_tree):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    codex = out / "variants" / "codex"
    children = list(codex.iterdir())
    assert len(children) == 1
    assert children[0].name == ".gitkeep"


def test_compile_cleans_stale_outputs(fake_tree):
    out = fake_tree / "dist"
    # Pre-populate a stale file
    stale = out / "variants" / "claude" / "skills" / "stale-skill" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")
    assert stale.exists()

    compile_mod.compile_all(out)
    assert not stale.exists()


def test_drift_detector_clean_after_compile(fake_tree, monkeypatch):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    # Point drift at this dist
    monkeypatch.setattr(drift_mod, "COMMITTED_DIST", out)
    # Run main with default args
    import sys as _s
    _s.argv = ["drift", "--committed", str(out)]
    rc = drift_mod.main()
    assert rc == 0


def test_drift_detector_flags_manual_edit(fake_tree, monkeypatch, capsys):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    # Tamper a dist file
    skill_md = out / "variants" / "claude" / "skills" / "test-skill" / "SKILL.md"
    skill_md.write_text("# TAMPERED\n", encoding="utf-8")

    monkeypatch.setattr(drift_mod, "COMMITTED_DIST", out)
    import sys as _s
    _s.argv = ["drift", "--committed", str(out)]
    rc = drift_mod.main()
    assert rc == 1
    captured = capsys.readouterr()
    assert "DRIFT DETECTED" in captured.out


def test_drift_detector_flags_stale_file(fake_tree, monkeypatch, capsys):
    out = fake_tree / "dist"
    compile_mod.compile_all(out)
    # Add a file that compile wouldn't produce
    extra = out / "variants" / "claude" / "skills" / "extra-file.md"
    extra.write_text("extra\n", encoding="utf-8")

    monkeypatch.setattr(drift_mod, "COMMITTED_DIST", out)
    import sys as _s
    _s.argv = ["drift", "--committed", str(out)]
    rc = drift_mod.main()
    assert rc == 1
    captured = capsys.readouterr()
    assert "only in committed" in captured.out  # extra-file.md is in committed but not regenerated


def test_dry_run_does_not_write(fake_tree):
    out = fake_tree / "dist"
    summary = compile_mod.compile_all(out, dry_run=True)
    assert summary["skill_dirs"] >= 1
    assert not out.exists()  # dry-run never touched disk
