"""Skill-corpus size-budget lint (Phase 95; GH #92).

Walks ``qor/skills/**/SKILL.md`` and emits a finding for each skill exceeding
the per-skill size threshold. Two thresholds (V1):

- ``WARN_BYTES = 25 KB`` -> ``skill-over-warn-threshold``
- ``EXCEEDED_BYTES = 40 KB`` -> ``skill-over-exceeded-threshold``

Invoked at ``/qor-substantiate`` Step 4.6.9 (between merge-velocity 4.6.8 and
doc-integrity 4.7). WARN-only V1; CLI exits 1 when any EXCEEDED finding is
present so V2 can convert to a hard ABORT by removing the ``|| true`` wrap.

Per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-SkillCorpusGrowth-A.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

WARN_BYTES = 25 * 1024
EXCEEDED_BYTES = 40 * 1024


@dataclass(frozen=True)
class SizeFinding:
    skill_path: str
    size_bytes: int
    category: str  # 'skill-over-warn-threshold' | 'skill-over-exceeded-threshold'
    severity: str  # 'warn' in V1


def check_skills(skills_root: Path) -> list[SizeFinding]:
    """Walk ``skills_root`` for ``SKILL.md`` files; emit a SizeFinding per
    file exceeding the per-skill size threshold. Returns the empty list
    when no skill is large."""
    if not skills_root.is_dir():
        return []
    findings: list[SizeFinding] = []
    for skill in sorted(skills_root.rglob("SKILL.md")):
        size = skill.stat().st_size
        if size >= EXCEEDED_BYTES:
            category = "skill-over-exceeded-threshold"
        elif size >= WARN_BYTES:
            category = "skill-over-warn-threshold"
        else:
            continue
        findings.append(SizeFinding(
            skill_path=str(skill.relative_to(skills_root.parent.parent)
                          if (skills_root.parent.parent / skill.relative_to(skills_root.parent.parent)) == skill
                          else skill),
            size_bytes=size,
            category=category,
            severity="warn",
        ))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.skill_size_budget_lint")
    parser.add_argument(
        "--skills-root", type=Path, default=Path("qor/skills"),
        help="root directory holding SKILL.md files (default qor/skills)",
    )
    args = parser.parse_args(argv)
    findings = check_skills(args.skills_root)
    if not findings:
        return 0
    print(f"skill_size_budget_lint: {len(findings)} finding(s)")
    any_exceeded = False
    for f in findings:
        kb = f.size_bytes / 1024
        suffix = "EXCEEDED" if f.category == "skill-over-exceeded-threshold" else "WARN"
        print(f"  [{suffix}] {f.skill_path} ({kb:.1f} KB)")
        if f.category == "skill-over-exceeded-threshold":
            any_exceeded = True
    return 1 if any_exceeded else 0


if __name__ == "__main__":
    sys.exit(main())
