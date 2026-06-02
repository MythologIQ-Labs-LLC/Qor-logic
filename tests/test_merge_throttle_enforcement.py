"""Behavioral tests for Phase 129 (GH #153 + #154): merge-velocity enforcement
+ workspace-fragility contract restore + plan/implement wiring.

merge_velocity grades are mocked (no live git) to avoid the known
test_merge_velocity_check flake and keep these deterministic.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import merge_velocity_check as mvc
from qor.scripts import workspace_fragility_check as wfc


def _fake_va(capacity: str) -> mvc.VelocityAssessment:
    return mvc.VelocityAssessment(
        prs_merged_in_window=30, additions_total=9999, repair_density=0.3,
        shared_core_touch_count=5, stabilization_capacity=capacity,
        recommended_action="branch_only", evidence=("synthetic",), window_days=7,
    )


# --- #153 enforcement ---

def test_main_aborts_on_exceeded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mvc, "assess_merge_velocity", lambda *a, **k: _fake_va("exceeded"))
    assert mvc.main(["--repo-root", str(tmp_path)]) == 1


def test_main_override_exits_0_and_logs_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mvc, "assess_merge_velocity", lambda *a, **k: _fake_va("exceeded"))
    events: list[dict] = []
    monkeypatch.setattr(mvc.shadow_process, "append_event",
                        lambda e, **k: events.append(e) or "id")
    rc = mvc.main(["--repo-root", str(tmp_path), "--override"])
    assert rc == 0
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_override"
    assert events[0]["details"]["gate"] == "merge_velocity_check"


def test_main_healthy_returns_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mvc, "assess_merge_velocity", lambda *a, **k: _fake_va("healthy"))
    assert mvc.main(["--repo-root", str(tmp_path)]) == 0


# --- #154 fragility contract + wiring ---

def test_fragility_has_capacity_and_shared_surface_fields(tmp_path: Path) -> None:
    a = wfc.assess_workspace_fragility(tmp_path)
    assert hasattr(a, "stabilization_capacity")
    assert hasattr(a, "shared_surface_risk")


def test_capacity_mirrors_grade() -> None:
    assert wfc._capacity_for("high") == "exceeded"
    assert wfc._capacity_for("medium") == "strained"
    assert wfc._capacity_for("low") == "healthy"


def test_branch_only_when_shared_surface_high() -> None:
    assert wfc._recommended_action("low", "high") == "branch_only"
    # without high shared-surface risk, the grade-based action stands
    assert wfc._recommended_action("low", "low") == wfc._ACTION_FROM_GRADE["low"]


def test_shared_surface_risk_high_on_many_branches() -> None:
    assert wfc._shared_surface_risk(active_branch_count=50, recent_commit_diff_lines=10) == "high"
    assert wfc._shared_surface_risk(active_branch_count=1, recent_commit_diff_lines=10) == "low"


def test_qor_plan_wires_fragility_check() -> None:
    text = Path("qor/skills/sdlc/qor-plan/SKILL.md").read_text(encoding="utf-8")
    assert "workspace_fragility_check" in text  # prose-lint: ok=prompt-contract


def test_qor_implement_wires_fragility_check() -> None:
    text = Path("qor/skills/sdlc/qor-implement/SKILL.md").read_text(encoding="utf-8")
    assert "workspace_fragility_check" in text  # prose-lint: ok=prompt-contract
