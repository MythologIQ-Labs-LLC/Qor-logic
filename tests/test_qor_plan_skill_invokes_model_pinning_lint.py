"""Phase 240: retired model pins stay absent while the compatibility lint remains wired.

The active skill corpus must contain no `model_compatibility` or
`min_model_capability` admission metadata. The historical command name
`model_pinning_lint` remains temporarily wired from a plan-phase skill because
it now surfaces execution-context inspection and fabrication-risk checks.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"


def _read_frontmatter(path: Path) -> str | None:
    body = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    return match.group(1) if match else None


def _skills_with_pinning_keys() -> list[Path]:
    matches: list[Path] = []
    for skill in SKILLS_DIR.rglob("SKILL.md"):
        fm = _read_frontmatter(skill)
        if not fm:
            continue
        if "model_compatibility:" in fm and "min_model_capability:" in fm:
            matches.append(skill)
    return matches


def _plan_phase_skills() -> list[Path]:
    matches: list[Path] = []
    for skill in SKILLS_DIR.rglob("SKILL.md"):
        fm = _read_frontmatter(skill)
        if not fm:
            continue
        if re.search(r"^phase\s*:\s*plan\s*$", fm, re.MULTILINE):
            matches.append(skill)
    return matches


def test_active_skills_have_no_retired_pins_and_plan_keeps_compatibility_lint():
    pinning_skills = _skills_with_pinning_keys()
    assert not pinning_skills, (
        "retired model admission metadata remains in active skills: "
        f"{[str(path.relative_to(REPO_ROOT)) for path in pinning_skills]}"
    )

    plan_skills = _plan_phase_skills()
    assert plan_skills, "expected >=1 skill with phase: plan"

    invokers = [
        s for s in plan_skills
        if any(
            form in s.read_text(encoding="utf-8")
            for form in (
                "python -m qor.scripts.model_pinning_lint",
                "qor-logic scripts model_pinning_lint",
            )
        )
    ]
    assert invokers, (
        "At least one phase: plan skill MUST retain the compatibility lint "
        "while it owns execution-context inspection and fabrication-risk checks."
    )


def test_lint_catches_synthetic_violator(tmp_path):
    """Negative-path: a fixture with pinning skills but no plan-phase invoker fails."""
    pinning_dir = tmp_path / "skills" / "pinning"
    pinning_dir.mkdir(parents=True)
    (pinning_dir / "SKILL.md").write_text(textwrap.dedent("""
        ---
        name: pinning
        phase: implement
        model_compatibility: [claude-opus-4-7]
        min_model_capability: opus
        ---
        body
    """).strip(), encoding="utf-8")

    plan_dir = tmp_path / "skills" / "plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "SKILL.md").write_text(textwrap.dedent("""
        ---
        name: plan
        phase: plan
        ---
        # body without lint invocation
    """).strip(), encoding="utf-8")

    plan_body = (plan_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "python -m qor.scripts.model_pinning_lint" not in plan_body


def test_lint_passes_when_phase_plan_skill_invokes_lint(tmp_path):
    """Positive-path: synthetic plan-phase skill containing the invocation passes."""
    plan_dir = tmp_path / "skills" / "plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "SKILL.md").write_text(textwrap.dedent("""
        ---
        name: plan
        phase: plan
        ---
        ## Step 0.3
        python -m qor.scripts.model_pinning_lint --repo-root .
    """).strip(), encoding="utf-8")

    body = (plan_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "python -m qor.scripts.model_pinning_lint" in body  # prose-lint: ok=prompt-contract: synthetic fixture round-trip
