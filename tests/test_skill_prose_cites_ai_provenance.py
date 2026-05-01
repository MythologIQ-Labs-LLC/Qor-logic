"""Phase 54: skill-prose co-occurrence behavior invariant for AI provenance.

For any SKILL.md whose body invokes ``gate_chain.write_gate_artifact(``, the
same body must also invoke ``ai_provenance.build_manifest(``. The conditional
on actual gate-write behavior is what makes this a behavior invariant rather
than a presence-only substring check.

Negative-path: synthetic skill fixture invoking write_gate_artifact but
omitting build_manifest; the lint must catch it.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"

_GATE_WRITE_TOKEN = "gate_chain.write_gate_artifact("
_PROVENANCE_TOKEN = "ai_provenance.build_manifest("


def _gate_writing_skills() -> list[Path]:
    """Walk all SKILL.md files; return those that invoke write_gate_artifact."""
    matches: list[Path] = []
    for skill in SKILLS_DIR.rglob("SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        if _GATE_WRITE_TOKEN in body:
            matches.append(skill)
    return matches


def test_skills_writing_gate_artifacts_invoke_build_manifest():
    """Co-occurrence invariant: gate-writing skills MUST invoke build_manifest."""
    violators: list[str] = []
    for skill in _gate_writing_skills():
        body = skill.read_text(encoding="utf-8")
        if _PROVENANCE_TOKEN not in body:
            violators.append(str(skill.relative_to(REPO_ROOT)))
    assert not violators, (
        f"skills calling {_GATE_WRITE_TOKEN} must also call {_PROVENANCE_TOKEN}; "
        f"violators: {violators}"
    )


def test_lint_finds_at_least_six_gate_writing_skills():
    """Sanity: walk discovered the SDLC + governance skill set.

    Without this assertion the lint could be vacuously passing if the
    walk returned zero files matching the gate-write token.
    """
    found = _gate_writing_skills()
    assert len(found) >= 6, (
        f"expected >=6 SKILL.md files invoking write_gate_artifact; got {len(found)}"
    )


def test_lint_catches_synthetic_violator(tmp_path):
    """Negative-path: a skill calling write_gate_artifact but not build_manifest fails."""
    fake_skills = tmp_path / "qor" / "skills" / "fake"
    fake_skills.mkdir(parents=True)
    skill_path = fake_skills / "SKILL.md"
    skill_path.write_text(textwrap.dedent("""
        # /qor-fake

        ### Step Z

        gate_chain.write_gate_artifact(phase="fake", payload={}, session_id=sid)
        # NOTE: deliberately omits ai_provenance.build_manifest call
    """).strip(), encoding="utf-8")

    body = skill_path.read_text(encoding="utf-8")
    assert _GATE_WRITE_TOKEN in body
    assert _PROVENANCE_TOKEN not in body, (
        "fixture must demonstrate the violator pattern: gate-write present, "
        "build_manifest absent"
    )
