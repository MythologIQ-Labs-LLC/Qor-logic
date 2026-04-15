#!/usr/bin/env python3
"""Validate gate-to-skill handoff references across processed skills."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "processed"
HANDOFF_RE = re.compile(r"/qor-([a-z][\w-]*)")


def collect_skills() -> dict[str, Path]:
    """Map skill trigger names to their file paths."""
    skills: dict[str, Path] = {}
    for filepath in sorted(PROCESSED_DIR.glob("*.md")):
        trigger = filepath.stem  # e.g. "qor-implement"
        skills[trigger] = filepath
    return skills


def extract_references(filepath: Path) -> list[str]:
    """Extract all /qor-* handoff references from a skill file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    return [f"qor-{m}" for m in HANDOFF_RE.findall(content)]


def build_matrix(
    skills: dict[str, Path],
) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """Build reference matrix and collect broken references."""
    matrix: dict[str, list[str]] = {}
    broken: list[tuple[str, str]] = []

    for name, filepath in skills.items():
        refs = sorted(set(extract_references(filepath)))
        # Exclude self-references
        refs = [r for r in refs if r != name]
        matrix[name] = refs
        for ref in refs:
            if ref not in skills:
                broken.append((name, ref))

    return matrix, broken


def print_matrix(
    matrix: dict[str, list[str]],
    broken: list[tuple[str, str]],
) -> None:
    """Print the handoff matrix and any broken references."""
    print("=" * 60)
    print("Gate-to-Skill Handoff Matrix")
    print("=" * 60)
    print()

    for skill, refs in sorted(matrix.items()):
        if refs:
            print(f"  {skill} -> {', '.join(refs)}")
        else:
            print(f"  {skill} -> (no handoffs)")

    print()
    print(f"Skills: {len(matrix)}  |  "
          f"Handoffs: {sum(len(r) for r in matrix.values())}  |  "
          f"Broken: {len(broken)}")

    if broken:
        print()
        print("--- BROKEN REFERENCES ---")
        for source, target in broken:
            print(f"  [X] {source} -> {target} (not found)")


def main() -> int:
    if not PROCESSED_DIR.is_dir():
        print(f"processed/ directory not found at {PROCESSED_DIR}")
        return 1

    skills = collect_skills()
    if not skills:
        print("No processed skill files found.")
        return 1

    matrix, broken = build_matrix(skills)
    print_matrix(matrix, broken)
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
