"""Phase 240: qor-audit execution-context admission behavior."""
from __future__ import annotations

import pytest

from qor.scripts import qor_audit_runtime as runtime


def _inspection(*, missing=None, unverified=None, model="gpt-family") -> dict:
    return {
        "rendering_recipe": "conservative",
        "context": {
            "declared_model_family": model,
            "responder_model_family": "unknown",
        },
        "missing_hard_requirements": missing or [],
        "unverified_hard_requirements": unverified or [],
    }


def test_non_claude_model_is_not_an_audit_blocker(monkeypatch):
    monkeypatch.setattr(
        runtime.execution_context,
        "inspect_skill",
        lambda *_args, **_kwargs: _inspection(model="gpt-5.6-sol"),
    )
    result = runtime.audit_execution_context()
    assert result["context"]["declared_model_family"] == "gpt-5.6-sol"


def test_unverified_capability_is_visible_but_not_blocking(monkeypatch):
    monkeypatch.setattr(
        runtime.execution_context,
        "inspect_skill",
        lambda *_args, **_kwargs: _inspection(unverified=["repo-search"]),
    )
    assert runtime.audit_execution_context()["unverified_hard_requirements"] == [
        "repo-search"
    ]


def test_proven_missing_hard_capability_blocks_audit(monkeypatch):
    monkeypatch.setattr(
        runtime.execution_context,
        "inspect_skill",
        lambda *_args, **_kwargs: _inspection(missing=["repo-search"]),
    )
    with pytest.raises(RuntimeError, match="missing declared hard requirements"):
        runtime.audit_execution_context()


def test_real_seam_inspects_the_live_qor_audit_contract():
    """Phase 247 remediation (independent-audit V-6): the three tests above
    stub inspect_skill, so a silent break in load_contract, _find_skill, or
    recipe selection -- or deletion of qor-audit's contract frontmatter --
    passed unnoticed. Drive the REAL seam end to end against the live corpus
    with a controlled context: no monkeypatching of any qor function."""
    from pathlib import Path

    from qor.scripts import execution_context

    repo_root = Path(__file__).resolve().parents[1]
    ctx = execution_context.ExecutionContext(
        host="test-host",
        declared_model_family="any-model",
        responder_model_family="any-model",
        reasoning_mode="unknown",
        capabilities=(),
        capabilities_complete=False,
        rendering_hint=None,
    )
    result = execution_context.inspect_skill(repo_root, "qor-audit", ctx)

    # the live qor-audit contract must load and select an admitted recipe
    assert result["skill"] == "qor-audit"
    assert result["rendering_recipe"] in execution_context.RENDER_RECIPES
    assert result["rendering_directives"], "selected recipe must carry directives"
    # incomplete telemetry must never promote to a blocking 'missing'
    assert result["missing_hard_requirements"] == []
    # model identity flows through as provenance, never altering the result set
    assert result["context"]["declared_model_family"] == "any-model"


def test_real_seam_rejects_a_skill_without_a_contract(tmp_path):
    """The seam's own failure path, unstubbed: a corpus whose skill carries no
    execution-context frontmatter raises rather than fabricating a contract."""
    import pytest as _pytest

    from qor.scripts import execution_context

    d = tmp_path / "qor" / "skills" / "test" / "bare"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: bare\n---\nbody\n", encoding="utf-8")
    with _pytest.raises(ValueError, match="no execution-context contract"):
        execution_context.inspect_skill(tmp_path, "bare")
