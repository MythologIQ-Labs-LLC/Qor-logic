"""Behavioral tests for early version-applicability validation (GH #282).

Every test invokes validate() and asserts on the returned verdict or the raised
error. _list_tags is monkeypatched so there is no live-tag coupling.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import version_applicability as va
from qor.scripts import governance_helpers as gh


def _repo(tmp_path: Path, change_class: str, version: str = "0.132.0") -> Path:
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "x"\nversion = "{version}"\n', encoding="utf-8"
    )
    plan = tmp_path / "docs" / "plan-x.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(f"# plan\n\n**change_class**: {change_class}\n", encoding="utf-8")
    return plan


def test_feature_target_above_tag_passes(tmp_path, monkeypatch):
    plan = _repo(tmp_path, "feature", "0.132.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.132.0"])
    verdict = va.validate(plan, tmp_path)
    assert verdict.ok
    assert verdict.classification == "release"
    assert verdict.target == (0, 133, 0)


def test_feature_target_not_above_tag_fails(tmp_path, monkeypatch):
    plan = _repo(tmp_path, "feature", "0.132.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.140.0"])
    verdict = va.validate(plan, tmp_path)
    assert not verdict.ok
    assert verdict.classification == "release"


def test_missing_change_class_raises(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.132.0"\n', encoding="utf-8"
    )
    plan = tmp_path / "docs" / "plan-x.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("# plan\n\nno class here\n", encoding="utf-8")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.132.0"])
    with pytest.raises(ValueError):
        va.validate(plan, tmp_path)


def test_governance_class_is_version_not_applicable(tmp_path, monkeypatch):
    plan = _repo(tmp_path, "governance", "0.132.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.132.0"])
    verdict = va.validate(plan, tmp_path)
    assert verdict.ok
    assert verdict.classification == "version-not-applicable"
    assert verdict.target is None


def test_is_release_class_forward_and_inverse():
    for c in ("hotfix", "feature", "breaking"):
        assert va.is_release_class(c)
    assert not va.is_release_class("governance")
