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
