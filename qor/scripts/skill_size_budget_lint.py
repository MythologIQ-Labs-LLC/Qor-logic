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



class LayoutUndeclaredError(RuntimeError):
    """A layout-bound path does not resolve and the operator declared nothing.

    Phase 250 (GH #406). A silent pass on an unresolvable path is the
    vacuous-gate shape; declaring the key absent turns the skip into evidence.
    """


def resolve_skills_root(args, *, require: bool = False) -> Path | None:
    """Resolve the skills root as flag > `.qorlogic/config.json` > `qor/skills`.

    ``require=True`` applies the typed-skip contract: an unresolvable root whose
    key the operator explicitly declared absent returns ``None`` (a typed skip);
    an unresolvable root with no declaration at all raises
    ``LayoutUndeclaredError`` naming the key the operator must declare.
    """
    from qor.scripts import badge_layout
    from qor.scripts.qorlogic_config import load_section

    repo_root = Path(getattr(args, "repo_root", None) or ".")
    flag = getattr(args, "skills_root", None)
    if flag is not None:
        return repo_root / flag
    section = load_section(repo_root, "layout")
    declared_absent = "skills_root" in section and section["skills_root"] is None
    resolved = repo_root / badge_layout.layout_from_args(args).skills_root
    if resolved.is_dir() or not require:
        return resolved
    if declared_absent:
        return None
    raise LayoutUndeclaredError(
        "skills_root does not resolve and is not declared in .qorlogic/config.json; "
        "declare layout.skills_root, or set it to null to record a typed skip"
    )


def layout_skip_event(layout_key: str, session: str) -> dict:
    """A groupable typed skip naming the layout key the gate needed.

    Phase 250 (GH #406): the shadow genome previously accumulated free-text
    reasons nobody could group.
    """
    from qor.scripts import shadow_process

    return {
        "ts": shadow_process.now_iso(),
        "skill": "qor-substantiate",
        "session_id": session,
        "event_type": "gate_skipped_prerequisite_absent",
        "severity": 1,
        "details": {"gate": "skill_size_budget_lint", "layout_key": layout_key},
        "addressed": False, "issue_url": None, "addressed_ts": None,
        "addressed_reason": None, "source_entry_id": None,
    }


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


def scan(skills_root: Path | None) -> list[SizeFinding]:
    """Findings for one resolved skills root; empty for a typed-skip (None)."""
    if skills_root is None:
        return []
    return check_skills(skills_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.skill_size_budget_lint")
    parser.add_argument(
        "--skills-root", type=Path, default=None,
        help="root directory holding SKILL.md files (default qor/skills)",
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    # Phase 250 (GH #406): resolve flag > config > default rather than reading a
    # constant, so a consumer workspace's declared layout is honored.
    findings = scan(resolve_skills_root(args))
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
