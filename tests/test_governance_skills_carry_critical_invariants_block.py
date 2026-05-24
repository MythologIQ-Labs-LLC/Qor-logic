"""Phase 100: structural countermeasure for F4 Critical Invariants summaries.

Each binding-gate governance skill must carry a top-level
`## Critical Invariants` section between `## Purpose` and
`## Environment`. The summary anchors operator/LLM reads of the file:
even with truncated context, the inviolable contracts are visible
without scanning step-level prose.

Forward-only sweep: any current or future qor/skills/governance/*/SKILL.md
whose step prose contains VETO or ABORT keywords MUST carry the block.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOVERNANCE_ROOT = REPO_ROOT / "qor" / "skills" / "governance"

QOR_AUDIT_SKILL = GOVERNANCE_ROOT / "qor-audit" / "SKILL.md"
QOR_SUBSTANTIATE_SKILL = GOVERNANCE_ROOT / "qor-substantiate" / "SKILL.md"
INVARIANTS_HEADING = "## Critical Invariants"
PURPOSE_HEADING = "## Purpose"
ENVIRONMENT_HEADING_PREFIX = "## Environment"
V2_RAMP_NOTE = "V2 ramp note"


def test_qor_audit_carries_critical_invariants_block():
    text = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert INVARIANTS_HEADING in text, (
        f"qor-audit SKILL.md must carry {INVARIANTS_HEADING!r} block"
    )
    assert V2_RAMP_NOTE in text, (
        f"qor-audit invariants block must include the Phase 99 V2 ramp framing note"
    )


def test_qor_substantiate_carries_critical_invariants_block():
    text = QOR_SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    assert INVARIANTS_HEADING in text, (
        f"qor-substantiate SKILL.md must carry {INVARIANTS_HEADING!r} block"
    )


def test_critical_invariants_block_positioned_before_environment():
    """The block must precede the Environment section so it anchors
    the read at the top of each skill body.
    """
    for skill in (QOR_AUDIT_SKILL, QOR_SUBSTANTIATE_SKILL):
        text = skill.read_text(encoding="utf-8")
        invariants_pos = text.find(INVARIANTS_HEADING)
        env_pos = text.find(ENVIRONMENT_HEADING_PREFIX)
        purpose_pos = text.find(PURPOSE_HEADING)
        assert invariants_pos != -1, f"{skill}: missing invariants block"
        assert env_pos != -1, f"{skill}: missing environment block"
        assert purpose_pos != -1 < invariants_pos, (
            f"{skill}: Critical Invariants must follow Purpose"
        )
        assert invariants_pos < env_pos, (
            f"{skill}: Critical Invariants must precede Environment "
            f"(got invariants at {invariants_pos}, environment at {env_pos})"
        )


_BINDING_GATE_PATTERNS = (
    "-> VETO",
    "-> ABORT",
    "|| ABORT",
    "**VETO**",
    "**ABORT**",
    "binding-VETO",
    "binding VETO",
)


def test_governance_skills_with_binding_gates_carry_invariants_block():
    """Forward-only sweep: any governance/*/SKILL.md whose step prose
    contains a binding-gate declaration (`-> VETO`, `-> ABORT`, `|| ABORT`,
    `**VETO**`, `**ABORT**`, or `binding-VETO`/`binding VETO`) MUST
    carry `## Critical Invariants`. Catches future drift where a new
    binding-gate skill ships without the summary block.

    Distinguishes binding-gate declarations from incidental keyword
    appearances (e.g., `ai_provenance.HumanOversight.VETO` enum
    references) by requiring the specific gate-syntax patterns.
    """
    failures: list[str] = []
    for skill_md in GOVERNANCE_ROOT.glob("*/SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        if not any(pattern in text for pattern in _BINDING_GATE_PATTERNS):
            continue
        if INVARIANTS_HEADING not in text:
            failures.append(str(skill_md.relative_to(REPO_ROOT)))
    assert not failures, (
        "Governance skills with binding-gate declarations must carry "
        f"'## Critical Invariants' block:\n  " + "\n  ".join(failures)
    )
