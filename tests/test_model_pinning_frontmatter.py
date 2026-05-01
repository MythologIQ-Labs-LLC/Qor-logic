"""Phase 55: model-pinning frontmatter + lint tests."""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from qor.scripts.model_pinning_lint import (
    _CAPABILITY_ORDER,
    check,
    extract_capability_tier,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

_EIGHT_SCOPED_SKILLS = (
    "qor/skills/sdlc/qor-research/SKILL.md",
    "qor/skills/sdlc/qor-plan/SKILL.md",
    "qor/skills/sdlc/qor-implement/SKILL.md",
    "qor/skills/sdlc/qor-refactor/SKILL.md",
    "qor/skills/governance/qor-audit/SKILL.md",
    "qor/skills/governance/qor-substantiate/SKILL.md",
    "qor/skills/governance/qor-validate/SKILL.md",
    "qor/skills/meta/qor-repo-audit/SKILL.md",
)


def _frontmatter(path: Path) -> str:
    body = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    assert match, f"missing YAML frontmatter in {path}"
    return match.group(1)


def test_eight_skills_declare_model_pinning_keys():
    violators: list[str] = []
    for rel in _EIGHT_SCOPED_SKILLS:
        path = REPO_ROOT / rel
        fm = _frontmatter(path)
        if "model_compatibility:" not in fm:
            violators.append(f"{rel}: missing model_compatibility")
        if "min_model_capability:" not in fm:
            violators.append(f"{rel}: missing min_model_capability")
    assert not violators, "scoped skills must declare model-pinning frontmatter; " + str(violators)


def _make_repo(tmp_path: Path, frontmatter: str) -> Path:
    skill = tmp_path / "qor" / "skills" / "test" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"---\n{frontmatter}\n---\nbody", encoding="utf-8")
    return tmp_path


def test_lint_warns_when_min_capability_exceeds_current_model(tmp_path):
    repo = _make_repo(tmp_path, "min_model_capability: opus")
    warnings = check(repo, current_model="claude-haiku-4-5-20251001")
    assert len(warnings) == 1
    assert "opus" in warnings[0].reason


def test_lint_passes_when_current_model_meets_minimum(tmp_path):
    repo = _make_repo(tmp_path, "min_model_capability: sonnet")
    warnings = check(repo, current_model="claude-sonnet-4-6")
    assert warnings == []


def test_lint_passes_when_current_model_exceeds_minimum(tmp_path):
    repo = _make_repo(tmp_path, "min_model_capability: sonnet")
    warnings = check(repo, current_model="claude-opus-4-7")
    assert warnings == []


def test_lint_warns_when_current_model_not_in_compatibility_list(tmp_path):
    repo = _make_repo(tmp_path, "model_compatibility: [claude-opus-4-7]")
    warnings = check(repo, current_model="claude-sonnet-4-6")
    assert len(warnings) == 1
    assert "compatibility list" in warnings[0].reason


def test_lint_skips_skills_without_pinning_keys(tmp_path):
    repo = _make_repo(tmp_path, "name: x")
    warnings = check(repo, current_model="claude-opus-4-7")
    assert warnings == []


def test_capability_tier_extraction_from_model_family_string():
    assert extract_capability_tier("claude-opus-4-7") == "opus"
    assert extract_capability_tier("claude-haiku-4-5-20251001") == "haiku"
    assert extract_capability_tier("claude-sonnet-4-6") == "sonnet"
    assert extract_capability_tier("unknown") is None
    assert extract_capability_tier(None) is None


def test_lint_handles_unset_qor_model_family_env(tmp_path, monkeypatch):
    monkeypatch.delenv("QOR_MODEL_FAMILY", raising=False)
    repo = _make_repo(tmp_path, "min_model_capability: opus")
    warnings = check(repo, current_model=None)
    assert warnings == []  # no warning without known model


def test_capability_order_is_haiku_sonnet_opus():
    assert _CAPABILITY_ORDER == ("haiku", "sonnet", "opus")
