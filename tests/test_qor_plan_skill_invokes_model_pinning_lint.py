"""Phase 55: co-occurrence behavior invariant for model-pinning lint coverage.

Conditional rule: enumerate every SKILL.md whose frontmatter declares the
pinning pair (`model_compatibility` + `min_model_capability`). For each such
skill, assert at least one SKILL.md whose `phase:` is `plan` invokes
`python -m qor.scripts.model_pinning_lint`.

Anchored to actual frontmatter-declaration set, not a single-skill substring.
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


def test_skills_with_pinning_keys_are_covered_by_pinning_lint_invocation():
    pinning_skills = _skills_with_pinning_keys()
    assert pinning_skills, "expected >=1 skill declaring model-pinning frontmatter"

    plan_skills = _plan_phase_skills()
    assert plan_skills, "expected >=1 skill with phase: plan"

    invokers = [
        s for s in plan_skills
        if "python -m qor.scripts.model_pinning_lint" in s.read_text(encoding="utf-8")
    ]
    assert invokers, (
        f"At least one phase: plan skill MUST invoke model_pinning_lint to cover "
        f"the {len(pinning_skills)} skills declaring pinning frontmatter; "
        f"none of {len(plan_skills)} plan-phase skills do."
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
    assert "python -m qor.scripts.model_pinning_lint" in body
