"""Phase 240: retired model pins stay absent while the compatibility lint remains wired.

The active skill corpus must contain no `model_compatibility` or
`min_model_capability` admission metadata. The historical command name
`model_pinning_lint` remains temporarily wired from a plan-phase skill because
it now surfaces execution-context inspection and fabrication-risk checks.

Phase 247 remediation (independent-audit V-4/V-5): the retired-field detector
flags EITHER field alone (the shipped AND conjunction let a single-field
reintroduction pass), and the synthetic fixtures now drive the shared
detection helpers instead of asserting substrings against files the tests
authored themselves (which could never fail).
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"

_RETIRED_KEYS = ("model_compatibility:", "min_model_capability:")


def _read_frontmatter(path: Path) -> str | None:
    body = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    return match.group(1) if match else None


def _skills_with_pinning_keys(root: Path = SKILLS_DIR) -> list[Path]:
    matches: list[Path] = []
    for skill in root.rglob("SKILL.md"):
        fm = _read_frontmatter(skill)
        if not fm:
            continue
        # V-4: either retired field alone is a violation.
        if any(key in fm for key in _RETIRED_KEYS):
            matches.append(skill)
    return matches


def _plan_phase_skills(root: Path = SKILLS_DIR) -> list[Path]:
    matches: list[Path] = []
    for skill in root.rglob("SKILL.md"):
        fm = _read_frontmatter(skill)
        if not fm:
            continue
        if re.search(r"^phase\s*:\s*plan\s*$", fm, re.MULTILINE):
            matches.append(skill)
    return matches


_LINT_FORMS = (
    "python -m qor.scripts.model_pinning_lint",
    "qor-logic scripts model_pinning_lint",
)


def _plan_skill_invokes_lint(root: Path = SKILLS_DIR) -> bool:
    return any(
        any(form in s.read_text(encoding="utf-8") for form in _LINT_FORMS)
        for s in _plan_phase_skills(root)
    )


def test_active_skills_have_no_retired_pins_and_plan_keeps_compatibility_lint():
    pinning_skills = _skills_with_pinning_keys()
    assert not pinning_skills, (
        "retired model admission metadata remains in active skills: "
        f"{[str(path.relative_to(REPO_ROOT)) for path in pinning_skills]}"
    )

    assert _plan_phase_skills(), "expected >=1 skill with phase: plan"
    assert _plan_skill_invokes_lint(), (
        "At least one phase: plan skill MUST retain the compatibility lint "
        "while it owns execution-context inspection and fabrication-risk checks."
    )


def _write_skill(root: Path, name: str, frontmatter: str, body: str = "body") -> None:
    d = root / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\n{frontmatter}\n---\n{body}\n", encoding="utf-8"
    )


def test_detector_flags_either_retired_field_alone(tmp_path):
    """V-4 regression: a skill reintroducing exactly ONE retired field must be
    flagged by the same detector the live-corpus test uses."""
    root = tmp_path / "one"
    _write_skill(root, "compat-only", "phase: implement\nmodel_compatibility: [legacy-model]")
    assert [p.parent.name for p in _skills_with_pinning_keys(root)] == ["compat-only"]

    root = tmp_path / "two"
    _write_skill(root, "cap-only", "phase: implement\nmin_model_capability: legacy-tier")
    assert [p.parent.name for p in _skills_with_pinning_keys(root)] == ["cap-only"]


def test_lint_catches_synthetic_violator(tmp_path):
    """V-5 regression: the negative-path fixture now drives the shared
    detection helpers -- a corpus with a pinning skill and no plan-phase
    invoker must FAIL both checks, via the same functions the live test
    runs, not via substring assertions on self-authored files."""
    root = tmp_path
    _write_skill(
        root, "pinning",
        "phase: implement\nmodel_compatibility: [legacy-model]\nmin_model_capability: legacy-tier",
    )
    _write_skill(root, "plan", "phase: plan", body="# body without lint invocation")

    assert _skills_with_pinning_keys(root), "detector must flag the pinning fixture"
    assert not _plan_skill_invokes_lint(root), (
        "invoker check must report the missing lint invocation"
    )


def test_lint_passes_when_phase_plan_skill_invokes_lint(tmp_path):
    """Positive-path: the same helpers pass on a clean corpus whose plan-phase
    skill carries the invocation."""
    _write_skill(
        tmp_path, "plan", "phase: plan",
        body=textwrap.dedent("""\
            ## Step 0.3
            python -m qor.scripts.model_pinning_lint --repo-root .
        """),
    )
    assert not _skills_with_pinning_keys(tmp_path)
    assert _plan_skill_invokes_lint(tmp_path)
