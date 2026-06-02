"""Progressive-disclosure lint (Phase 132; GH #162 / SG-SkillCorpusGrowth-A V2).

Flags SKILL.md heading sections whose inline prose (fenced code excluded) exceeds
a per-section budget while not pointing to a `references/` file — candidates to
extract into a references/ file per the progressive-disclosure discipline. The
corpus-growth counterweight's detection half. Advisory (no auto-refactor).
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

SECTION_PROSE_BUDGET = 2200  # chars of non-code prose per heading section
_HEADING_RE = re.compile(r"^#{2,6}\s+.*$", re.MULTILINE)
_FENCED_RE = re.compile(r"```.*?```", re.DOTALL)
_REFERENCES_RE = re.compile(r"references/[\w./-]+\.md")
_ESCAPE = "qor:inline-prose-ok"


@dataclass(frozen=True)
class DisclosureFinding:
    skill: str
    section: str
    prose_chars: int


def _sections(text: str) -> list[tuple[str, str]]:
    """(heading_text, body) per heading; body runs to the next heading."""
    matches = list(_HEADING_RE.finditer(text))
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        heading = m.group(0).lstrip("#").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((heading, text[start:end]))
    return out


def _inline_prose_chars(body: str) -> int:
    return len(_FENCED_RE.sub("", body))


def scan_text(skill: str, text: str) -> list[DisclosureFinding]:
    findings: list[DisclosureFinding] = []
    for heading, body in _sections(text):
        if _ESCAPE in body or _REFERENCES_RE.search(body):
            continue
        prose = _inline_prose_chars(body)
        if prose >= SECTION_PROSE_BUDGET:
            findings.append(DisclosureFinding(skill=skill, section=heading, prose_chars=prose))
    return findings


def scan_skills(skills_root: Path) -> list[DisclosureFinding]:
    findings: list[DisclosureFinding] = []
    for skill_md in sorted(skills_root.glob("**/SKILL.md")):
        skill = skill_md.parent.name
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings.extend(scan_text(skill, text))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="progressive_disclosure_lint")
    parser.add_argument("--skills-root", default="qor/skills")
    args = parser.parse_args(argv)
    findings = scan_skills(Path(args.skills_root))
    if not findings:
        return 0
    for f in findings:
        print(f"[inline-prose-extractable] {f.skill} :: {f.section} "
              f"({f.prose_chars} prose chars >= {SECTION_PROSE_BUDGET}) -- "
              f"extract to a references/ file")
    print(f"progressive_disclosure_lint: {len(findings)} extraction candidate(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
