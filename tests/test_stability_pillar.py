"""Behavioral tests for the qa.json stability pillar via runtime re-walk (Phase 116, #169)."""
from __future__ import annotations

from qor.scripts import qa_evidence
from qor.scripts import runtime_contract_walk


def test_pass_on_no_findings(tmp_path, monkeypatch):
    plan = tmp_path / "plan-qor-phase999-x.md"
    plan.write_text("# plan\n", encoding="utf-8")
    monkeypatch.setattr(runtime_contract_walk, "walk_plan", lambda p, r: [])
    p = qa_evidence.run_stability(str(plan), repo_root=str(tmp_path))
    assert p["status"] == "pass"


def test_fail_on_findings(tmp_path, monkeypatch):
    plan = tmp_path / "plan-qor-phase999-x.md"
    plan.write_text("# plan\n", encoding="utf-8")
    monkeypatch.setattr(runtime_contract_walk, "walk_plan", lambda p, r: ["a finding"])
    p = qa_evidence.run_stability(str(plan), repo_root=str(tmp_path))
    assert p["status"] == "fail"
    assert p["metric"] == 1


def test_skip_when_plan_absent(tmp_path):
    p = qa_evidence.run_stability(str(tmp_path / "nope.md"), repo_root=str(tmp_path))
    assert p["status"] == "skip"
