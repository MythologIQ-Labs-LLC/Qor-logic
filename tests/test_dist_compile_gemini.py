"""Phase 24: Gemini variant compilation (TOML commands + safe_load)."""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
import yaml


SAMPLE_SKILL_WITH_FRONTMATTER = """---
name: sample
description: Short sample skill
trigger: /sample
phase: PLAN
persona: Governor
---
# /sample - Sample Skill

Body line one.
Body line two.
"""

SAMPLE_LOOSE_SKILL = """---
name: log-decision
description: Log a decision
---
# log-decision

Body.
"""

SAMPLE_AGENT = """---
name: agent-architect
description: Architect agent
---
# agent-architect

Pattern library.
"""

BODY_WITH_EDGE_CASES = '''---
name: edge
description: Edge cases
---
# edge

Path: C:\\\\Users\\\\x
Triple: """this is a triple quote"""
Trailing backslash\\
'''

UNSAFE_FRONTMATTER = """---
name: bad
x: !!python/object/apply:os.system
---
# bad
"""


def _stage_sources(tmp_path: Path) -> tuple[Path, Path]:
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "cat" / "sample").mkdir(parents=True)
    (skills / "cat" / "sample" / "SKILL.md").write_text(
        SAMPLE_SKILL_WITH_FRONTMATTER, encoding="utf-8",
    )
    (skills / "cat" / "log-decision.md").write_text(
        SAMPLE_LOOSE_SKILL, encoding="utf-8",
    )
    (agents / "cat").mkdir(parents=True)
    (agents / "cat" / "agent-architect.md").write_text(
        SAMPLE_AGENT, encoding="utf-8",
    )
    return skills, agents


def _compile(tmp_path: Path, monkeypatch) -> Path:
    from qor.scripts import dist_compile as compile_mod
    skills, agents = _stage_sources(tmp_path)
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)
    out = tmp_path / "dist"
    compile_mod.compile_all(out)
    return out


def test_gemini_emits_skill_dir_toml(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    toml_path = out / "variants" / "gemini" / "commands" / "sample.toml"
    assert toml_path.exists()
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    assert data["description"] == "Short sample skill"
    assert data["trigger"] == "/sample"
    assert data["phase"] == "PLAN"
    assert data["persona"] == "Governor"
    assert "Body line one." in data["prompt"]


def test_gemini_emits_loose_skill_toml(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    toml_path = out / "variants" / "gemini" / "commands" / "log-decision.toml"
    assert toml_path.exists()
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    assert data["description"] == "Log a decision"


def test_gemini_emits_agent_toml_with_prefix(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    toml_path = out / "variants" / "gemini" / "commands" / "agent-agent-architect.toml"
    assert toml_path.exists()
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    assert "description" in data
    assert data["description"]  # non-empty


def test_gemini_skips_optional_keys_when_absent(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    toml_path = out / "variants" / "gemini" / "commands" / "log-decision.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    assert "trigger" not in data
    assert "phase" not in data
    assert "persona" not in data


def test_gemini_variant_manifest_lists_commands(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    manifest_path = out / "variants" / "gemini" / "manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    rels = {e["install_rel_path"] for e in data["files"]}
    assert "commands/sample.toml" in rels
    assert "commands/log-decision.toml" in rels
    assert "commands/agent-agent-architect.toml" in rels
    for entry in data["files"]:
        assert entry["install_rel_path"].startswith("commands/")
        assert entry["sha256"]


def test_gemini_all_toml_parse_with_tomllib(tmp_path, monkeypatch):
    out = _compile(tmp_path, monkeypatch)
    commands_dir = out / "variants" / "gemini" / "commands"
    for toml_path in commands_dir.glob("*.toml"):
        tomllib.loads(toml_path.read_text(encoding="utf-8"))  # raises on parse error


def test_safe_loader_rejects_python_object_tag(tmp_path, monkeypatch):
    """Proves yaml.safe_load is wired (not yaml.load)."""
    from qor.scripts import dist_compile as compile_mod
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "cat" / "bad").mkdir(parents=True)
    (skills / "cat" / "bad" / "SKILL.md").write_text(
        UNSAFE_FRONTMATTER, encoding="utf-8",
    )
    (agents / "cat").mkdir(parents=True)
    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)
    with pytest.raises((yaml.YAMLError, yaml.constructor.ConstructorError)):
        compile_mod.compile_all(tmp_path / "dist")


def test_toml_round_trip_with_triple_quotes_and_backslashes(tmp_path, monkeypatch):
    from qor.scripts.gemini_variant import render_gemini_command
    rendered = render_gemini_command(
        "edge",
        "Edge cases",
        BODY_WITH_EDGE_CASES,
        extras={},
    )
    parsed = tomllib.loads(rendered)
    assert parsed["prompt"] == BODY_WITH_EDGE_CASES


def test_dependency_shape():
    """Locks declared runtime dependencies exactly; prevents silent dep creep."""
    import tomllib
    root = Path(__file__).resolve().parent.parent
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data["project"]["dependencies"]
    assert sorted(deps) == sorted(["jsonschema>=4", "PyYAML>=6"])
