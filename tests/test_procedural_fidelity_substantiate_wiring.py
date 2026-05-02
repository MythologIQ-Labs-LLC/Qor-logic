"""Phase 58: substantiate skill wiring (Phase 50 co-occurrence behavior invariant)."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"


def _frontmatter(p: Path) -> str | None:
    body = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    return m.group(1) if m else None


def _substantiate_skills() -> list[Path]:
    matches: list[Path] = []
    for skill in SKILLS_DIR.rglob("SKILL.md"):
        fm = _frontmatter(skill)
        if not fm:
            continue
        if re.search(r"^phase\s*:\s*substantiate\s*$", fm, re.MULTILINE):
            matches.append(skill)
    return matches


def test_substantiate_skill_invokes_procedural_fidelity_at_step_4_6_6():
    """Phase 50 co-occurrence rule: any SKILL.md whose `phase: substantiate`
    MUST invoke `python -m qor.scripts.procedural_fidelity --session`."""
    subs = _substantiate_skills()
    assert subs, "expected >=1 substantiate-phase skill"
    invokers = [
        s for s in subs
        if "python -m qor.scripts.procedural_fidelity --session" in s.read_text(encoding="utf-8")
    ]
    assert invokers, (
        "At least one phase: substantiate skill MUST invoke procedural_fidelity; "
        f"none of {len(subs)} substantiate skills do."
    )


def test_step_4_6_6_uses_warn_not_abort_semantics():
    """The procedural_fidelity invocation must NOT be followed by `|| ABORT`
    (matches Phase 55 pre-audit-lint WARN idiom; distinct from Phase 56
    secret-scan which IS followed by `|| ABORT`).
    """
    subs = _substantiate_skills()
    for skill in subs:
        body = skill.read_text(encoding="utf-8")
        idx = body.find("python -m qor.scripts.procedural_fidelity --session")
        if idx == -1:
            continue
        window = body[idx:idx + 250]
        assert "|| ABORT" not in window, (
            f"{skill}: procedural_fidelity invocation must NOT use `|| ABORT` "
            f"(WARN-only per Open Question 1 default). Window: {window[:200]!r}"
        )
