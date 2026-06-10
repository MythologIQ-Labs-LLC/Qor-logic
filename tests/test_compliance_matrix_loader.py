"""Behavioral tests for the compliance control-matrix loader (Phase 141).

Each test invokes the loader/helpers and asserts on the returned objects or the
raised error -- not on file presence.
"""
from __future__ import annotations

import json

import pytest

from qor.scripts import compliance_matrix as cm

REPO = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_load_matrix_parses_seed_registry():
    controls = cm.load_matrix(REPO)
    assert len(controls) >= 1
    for c in controls:
        assert c.posture in cm.POSTURES, (c.id, c.posture)
        assert c.detection in cm.DETECTIONS, (c.id, c.detection)
        assert c.enforcing_module
        assert isinstance(c.variants, tuple)


def _write_matrix(tmp_path, controls, waivers=None):
    root = tmp_path
    (root / "qor" / "compliance").mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "1", "controls": controls, "waivers": waivers or []}
    (root / "qor" / "compliance" / "control_matrix.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return root


def _control(**over):
    base = {
        "id": "demo",
        "framework": "F",
        "control": "c",
        "enforcing_module": "qor.scripts.x",
        "invocation": "x --flag",
        "posture": "ABORT",
        "detection": "skill-marker",
        "wired_into": {"skill": "qor/skills/governance/qor-substantiate/SKILL.md", "step": "4.6.5"},
        "variants": ["claude"],
        "engagement": ["ci"],
    }
    base.update(over)
    return base


def test_load_matrix_rejects_bad_posture(tmp_path):
    root = _write_matrix(tmp_path, [_control(id="bad", posture="MAYBE")])
    with pytest.raises(ValueError) as exc:
        cm.load_matrix(root)
    assert "bad" in str(exc.value) or "MAYBE" in str(exc.value)


def test_schema_rejects_missing_required_field(tmp_path):
    bad = _control()
    del bad["enforcing_module"]
    root = _write_matrix(tmp_path, [bad])
    with pytest.raises(ValueError):
        cm.load_matrix(root)


def test_enforced_set_shape(tmp_path):
    root = _write_matrix(
        tmp_path,
        [_control(id="a", posture="ABORT"), _control(id="b", posture="WARN")],
    )
    controls = cm.load_matrix(root)
    assert cm.enforced_set(controls) == {("a", "ABORT"), ("b", "WARN")}


def test_engagement_and_runner_parsed():
    controls = cm.load_matrix(REPO)
    for c in controls:
        assert isinstance(c.engagement, tuple) and c.engagement, c.id
        for pt in c.engagement:
            assert pt in cm.ENGAGEMENTS, (c.id, pt)
        # A control engaging a runnable point must carry a runner dict.
        if set(c.engagement) & set(cm.RUNNABLE_POINTS):
            assert isinstance(c.runner, dict), c.id
            assert c.runner.get("module") and c.runner.get("entry"), c.id


def test_schema_rejects_unknown_engagement(tmp_path):
    root = _write_matrix(tmp_path, [_control(id="bad", engagement=["nope"])])
    with pytest.raises(ValueError):
        cm.load_matrix(root)


# Phase 148 (Sprint B, GH #211): ci/seal runners wired + the 2 non-CLI controls disclosed.


def _by_id(controls):
    return {c.id: c for c in controls}


def test_ci_seal_runnable_controls_have_runners():
    controls = _by_id(cm.load_matrix(REPO))
    for cid, mod in [
        ("prompt-injection", "qor.scripts.prompt_injection_canaries"),
        ("governance-index", "qor.scripts.governance_index"),
        ("gate-chain-completeness", "qor.reliability.gate_chain_completeness"),
    ]:
        c = controls[cid]
        assert c.runner is not None, f"{cid} must carry a runner"
        assert c.runner["module"] == mod
        assert isinstance(c.runner.get("requires"), list) and c.runner["requires"], (
            f"{cid} runner must declare a non-empty requires list (disclosed-skip)"
        )


def test_disclosed_controls_carry_reason():
    controls = _by_id(cm.load_matrix(REPO))
    for cid in ("ai-provenance", "dependency-review"):
        c = controls[cid]
        assert c.runner is None, f"{cid} is not CLI-runnable; runner must stay null"
        assert c.runner_unavailable_reason, f"{cid} must declare runner_unavailable_reason"
