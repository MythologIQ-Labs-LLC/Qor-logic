"""Phase 54: skill-prose co-occurrence invariant for OverrideFrictionRequired.

For any SKILL.md whose body invokes ``gate_chain.emit_gate_override(``, the
same body must reference ``OverrideFrictionRequired`` AND describe a re-call
with ``justification=``. The conditional on actual override-emission
behavior makes this a behavior invariant rather than substring-presence.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"

_EMIT_TOKEN = "gate_chain.emit_gate_override("
_FRICTION_TOKEN = "OverrideFrictionRequired"
_JUSTIFICATION_TOKEN = "justification="


def _override_emitting_skills() -> list[Path]:
    matches: list[Path] = []
    for skill in SKILLS_DIR.rglob("SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        if _EMIT_TOKEN in body:
            matches.append(skill)
    return matches


def test_skills_emitting_gate_overrides_handle_friction_exception():
    violators: list[str] = []
    for skill in _override_emitting_skills():
        body = skill.read_text(encoding="utf-8")
        problems: list[str] = []
        if _FRICTION_TOKEN not in body:
            problems.append("missing OverrideFrictionRequired reference")
        if _JUSTIFICATION_TOKEN not in body:
            problems.append("missing justification= re-call description")
        if problems:
            violators.append(
                f"{skill.relative_to(REPO_ROOT)}: " + "; ".join(problems)
            )
    assert not violators, (
        f"skills calling {_EMIT_TOKEN} must reference {_FRICTION_TOKEN} and "
        f"describe re-call with {_JUSTIFICATION_TOKEN}; violators: {violators}"
    )


def test_lint_finds_at_least_five_override_emitting_skills():
    """Sanity: walk discovered the gate-checking skill set."""
    found = _override_emitting_skills()
    assert len(found) >= 5, (
        f"expected >=5 SKILL.md files invoking emit_gate_override; got {len(found)}"
    )


def test_lint_catches_synthetic_violator(tmp_path):
    """Negative-path: skill calling emit_gate_override but not referencing friction handling."""
    fake_skills = tmp_path / "qor" / "skills" / "fake"
    fake_skills.mkdir(parents=True)
    skill_path = fake_skills / "SKILL.md"
    skill_path.write_text(textwrap.dedent("""
        # /qor-fake

        ### Step 0
        gate_chain.emit_gate_override(current_phase="fake", session_id=sid)
    """).strip(), encoding="utf-8")

    body = skill_path.read_text(encoding="utf-8")
    assert _EMIT_TOKEN in body
    assert _FRICTION_TOKEN not in body
    assert _JUSTIFICATION_TOKEN not in body
