"""Phase 109 D-109.3: /qor-status routes on governance health before lifecycle.

Exercises the health-gate routing helper (`recommended_next`) that /qor-status
consults before its existence-only decision tree, so a damaged or incomplete
artifact surfaces repair/completion rather than /qor-plan or /qor-implement.
"""
from __future__ import annotations

from qor.scripts.governance_health import (
    ArtifactStatus,
    check_governance_health,
    recommended_next,
)


def _docs(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    return d


def test_status_reports_damaged_before_lifecycle_next(tmp_path):
    docs = _docs(tmp_path)
    (docs / "META_LEDGER.md").write_text("%%% not a ledger %%%\ngarbage\n", encoding="utf-8")
    findings = check_governance_health(tmp_path)
    state, next_action = recommended_next(findings)
    assert state == "DAMAGED"
    assert "/qor-remediate" in next_action
    assert "/qor-plan" not in next_action
    assert "/qor-implement" not in next_action


def test_status_reports_incomplete_seeded_artifact(tmp_path):
    docs = _docs(tmp_path)
    (docs / "META_LEDGER.md").write_text(
        "# QoreLogic Meta Ledger\n\n### Entry #1: SEAL\nsealed.\n", encoding="utf-8"
    )
    (docs / "ARCHITECTURE_PLAN.md").write_text(
        "# Architecture Plan\n\nTODO: select a risk grade.\n", encoding="utf-8"
    )
    findings = check_governance_health(tmp_path)
    arch = next(f for f in findings if f.path.endswith("ARCHITECTURE_PLAN.md"))
    assert arch.status is ArtifactStatus.INCOMPLETE
    state, next_action = recommended_next(findings)
    assert state == "INCOMPLETE"
    assert "complete" in next_action.lower()
    assert "ready" not in next_action.lower()
