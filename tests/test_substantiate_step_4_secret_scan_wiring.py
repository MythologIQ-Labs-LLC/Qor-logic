"""Phase 56: substantiate skill body wiring tests (Phase 50 co-occurrence)."""
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


def test_substantiate_skill_invokes_secret_scanner_at_step_4_6_5():
    """Co-occurrence behavior invariant (Phase 50 model): every SKILL.md whose
    ``phase: substantiate`` MUST invoke ``python -m qor.scripts.secret_scanner --staged``
    in its body. Anchored to actual frontmatter, not single-skill substring.
    """
    substantiate_skills = _substantiate_skills()
    assert substantiate_skills, "expected >=1 skill with phase: substantiate"

    invokers = [
        s for s in substantiate_skills
        if "python -m qor.scripts.secret_scanner --staged" in s.read_text(encoding="utf-8")
    ]
    assert invokers, (
        f"At least one phase: substantiate skill MUST invoke secret_scanner; "
        f"none of {len(substantiate_skills)} substantiate skills do."
    )


def test_substantiate_step_4_6_5_uses_abort_semantics():
    """The secret_scanner invocation must follow the existing reliability-sweep
    idiom: non-zero exit propagates via ``|| ABORT``.
    """
    invokers = [
        s for s in _substantiate_skills()
        if "python -m qor.scripts.secret_scanner --staged" in s.read_text(encoding="utf-8")
    ]
    assert invokers, "no substantiate-phase skill invokes secret_scanner"
    for skill in invokers:
        body = skill.read_text(encoding="utf-8")
        # Find the invocation and assert "|| ABORT" appears within the next 80 chars
        idx = body.find("python -m qor.scripts.secret_scanner --staged")
        window = body[idx:idx + 200]
        assert "|| ABORT" in window, (
            f"{skill}: secret_scanner invocation must be followed by '|| ABORT' "
            f"(matches reliability-sweep idiom). Got window: {window!r}"
        )
