"""Behavioral tests for the conveyance conformance verifier (Phase 141).

The live test (`test_every_seeded_control_is_satisfied`) is the CI gate: it fails
when any seeded control is missing, posture-downgraded, or absent from a conveyed
variant. The synthetic tests invoke `verify_control` on constructed inputs and
assert on the returned failure reasons.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import compliance_conformance as cc
from qor.scripts.compliance_matrix import Control

REPO = Path(__file__).resolve().parents[1]


def test_every_seeded_control_is_satisfied():
    failures = cc.verify_all(REPO)
    assert failures == {}, "conformance failures:\n" + "\n".join(
        f"  {cid}: {reasons}" for cid, reasons in failures.items()
    )


def _skill(root, rel, body):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def _ctl(**over):
    base = dict(
        id="demo", framework="F", control="c", enforcing_module="qor.scripts.x",
        posture="ABORT", detection="skill-marker",
        wired_into={"skill": "qor/skills/governance/qor-demo/SKILL.md", "step": "9.9"},
        variants=(), invocation="x --flag",
    )
    base.update(over)
    return Control(**base)


def test_skill_marker_detects_posture_downgrade(tmp_path):
    _skill(tmp_path, "qor/skills/governance/qor-demo/SKILL.md",
           "### Step 9.9: demo\n\n`qor-logic scripts x --flag || true`\n\n### Step 9.10: next\n")
    reasons = cc.verify_control(_ctl(posture="ABORT"), tmp_path)
    assert reasons, "expected a downgrade reason"
    assert any("|| true" in r or "downgrad" in r.lower() for r in reasons), reasons


def test_skill_marker_detects_missing_in_variant(tmp_path):
    _skill(tmp_path, "qor/skills/governance/qor-demo/SKILL.md",
           "### Step 9.9: demo\n\n`x --flag || ABORT`\n\n### Step 9.10: next\n")
    _skill(tmp_path, "qor/dist/variants/claude/skills/qor-demo/SKILL.md",
           "### Step 9.9: demo\n\n(gate was dropped during compile)\n")
    reasons = cc.verify_control(_ctl(variants=("claude",)), tmp_path)
    assert reasons
    assert any("variant" in r.lower() and "claude" in r for r in reasons), reasons


def test_skill_marker_passes_when_source_and_variant_carry_gate(tmp_path):
    good = "### Step 9.9: demo\n\n`x --flag || ABORT`\n\n### Step 9.10: next\n"
    _skill(tmp_path, "qor/skills/governance/qor-demo/SKILL.md", good)
    _skill(tmp_path, "qor/dist/variants/claude/skills/qor-demo/SKILL.md", good)
    assert cc.verify_control(_ctl(variants=("claude",)), tmp_path) == []


def test_test_detection_flags_vanished_test(tmp_path):
    ctl = _ctl(detection="test", invocation="",
               wired_into={"test": "tests/test_nope.py::test_gone"}, variants=())
    reasons = cc.verify_control(ctl, tmp_path)
    assert reasons
    assert any("test" in r.lower() for r in reasons), reasons
