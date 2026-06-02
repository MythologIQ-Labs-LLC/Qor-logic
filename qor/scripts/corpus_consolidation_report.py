"""Corpus consolidation report (Phase 132; GH #162 / SG-SkillCorpusGrowth-A V2).

Periodic counterweight to additive corpus growth: aggregates current-state corpus
signals — total SKILL.md bytes, per-skill size-budget findings, and
progressive-disclosure extraction candidates — into a ranked consolidation
worklist. Wired into /qor-process-review-cycle as the corpus-weight sweep.
Advisory: it surfaces candidates, never auto-refactors. Current-state only (no
git history -> deterministic).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import progressive_disclosure_lint as pdl
from qor.scripts import skill_size_budget_lint as ssb


@dataclass(frozen=True)
class ConsolidationReport:
    total_bytes: int
    oversized_skills: tuple
    extractable_sections: tuple
    candidates: tuple[str, ...]


def _total_bytes(skills_root: Path) -> int:
    return sum(p.stat().st_size for p in skills_root.glob("**/SKILL.md") if p.is_file())


def build_report(skills_root: Path) -> ConsolidationReport:
    size_findings = tuple(ssb.check_skills(skills_root))
    sections = tuple(pdl.scan_skills(skills_root))

    exceeded = [f for f in size_findings if f.category == "skill-over-exceeded-threshold"]
    warn = [f for f in size_findings if f.category == "skill-over-warn-threshold"]

    candidates: list[str] = []
    for f in exceeded:
        candidates.append(f"EXCEEDED skill: {f.skill_path} ({f.size_bytes} bytes) -- consolidate / split")
    for f in warn:
        candidates.append(f"WARN skill: {f.skill_path} ({f.size_bytes} bytes) -- watch / trim")
    for s in sections:
        candidates.append(f"extractable section: {s.skill} :: {s.section} "
                          f"({s.prose_chars} prose chars) -- move to references/")

    return ConsolidationReport(
        total_bytes=_total_bytes(skills_root),
        oversized_skills=size_findings,
        extractable_sections=sections,
        candidates=tuple(candidates),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="corpus_consolidation_report")
    parser.add_argument("--skills-root", default="qor/skills")
    args = parser.parse_args(argv)
    report = build_report(Path(args.skills_root))
    print(f"corpus_consolidation_report: total SKILL.md corpus = {report.total_bytes} bytes")
    print(f"  oversized skills: {len(report.oversized_skills)}; "
          f"extractable sections: {len(report.extractable_sections)}")
    if not report.candidates:
        print("  no consolidation candidates (corpus lean)")
        return 0
    print("  consolidation worklist (ranked):")
    for i, c in enumerate(report.candidates, 1):
        print(f"    {i}. {c}")
    return 0  # advisory periodic tool; never blocks


if __name__ == "__main__":
    raise SystemExit(main())
