#!/usr/bin/env python3
"""Gate-to-skill handoff matrix validator.

Walks qor/skills/**/SKILL.md (or SKILLS_ROOT env override); for each skill,
extracts /qor-* references and verifies the target skill exists. Self-
references are dropped. Reports broken handoffs and exits non-zero if any.

Usage: gate-skill-matrix.py

Exit 0 if no broken handoffs. Exit 1 otherwise.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SKILLS_ROOT = REPO_ROOT / "qor" / "skills"
# /qor-<name> handoff. Exclude reference-file basenames (those live in
# references/<name>.md, not as standalone skills).
HANDOFF_RE = re.compile(r"/qor-([a-z][\w-]*)")
_REFERENCE_SUFFIXES = ("-templates", "-patterns", "-examples", "-reports")


def _is_reference_doc_name(name: str) -> bool:
    """True if the matched name is clearly a reference-file basename."""
    return any(name.endswith(suffix) for suffix in _REFERENCE_SUFFIXES)


def _skills_root() -> Path:
    return Path(os.environ.get("SKILLS_ROOT", str(DEFAULT_SKILLS_ROOT)))


def collect_skills(root: Path) -> dict[str, Path]:
    """Map skill trigger (dir basename) -> SKILL.md path."""
    skills: dict[str, Path] = {}
    if not root.is_dir():
        return skills
    for skill_md in sorted(root.rglob("SKILL.md")):
        skills[skill_md.parent.name] = skill_md
    return skills


def extract_references(filepath: Path) -> list[str]:
    """All /qor-<name> references in the file, as trigger names.

    Excludes matches that are reference-file basenames (suffixes like
    -templates, -patterns) since those live in references/<name>.md and
    are not standalone skills.
    """
    body = filepath.read_text(encoding="utf-8", errors="replace")
    return [
        f"qor-{m}" for m in HANDOFF_RE.findall(body)
        if not _is_reference_doc_name(m)
    ]


def build_matrix(
    skills: dict[str, Path],
) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """Return (matrix: name -> [resolved refs], broken: [(src, ref)])."""
    matrix: dict[str, list[str]] = {}
    broken: list[tuple[str, str]] = []

    for name, filepath in skills.items():
        refs = sorted(set(extract_references(filepath)))
        refs = [r for r in refs if r != name]  # drop self-refs
        matrix[name] = refs
        for ref in refs:
            if ref not in skills:
                broken.append((name, ref))

    return matrix, broken


def print_report(
    matrix: dict[str, list[str]],
    broken: list[tuple[str, str]],
) -> None:
    print("Gate-to-Skill Handoff Matrix")
    print("=" * 40)
    for skill, refs in sorted(matrix.items()):
        label = ", ".join(refs) if refs else "(no handoffs)"
        print(f"  {skill} -> {label}")

    total_refs = sum(len(r) for r in matrix.values())
    print()
    print(
        f"Skills: {len(matrix)} | "
        f"Handoffs: {total_refs} | "
        f"Broken: {len(broken)}"
    )

    if broken:
        print()
        print("--- BROKEN REFERENCES ---")
        for source, target in broken:
            print(f"  [X] {source} -> {target} (not found)")


def main(argv: list[str] | None = None) -> int:
    root = _skills_root()
    skills = collect_skills(root)
    if not skills:
        print(f"No SKILL.md files found under {root}", file=sys.stderr)
        return 1

    matrix, broken = build_matrix(skills)
    print_report(matrix, broken)
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
