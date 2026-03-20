#!/usr/bin/env python3
"""Compile processed S.H.I.E.L.D. skills into Agent Workflow format."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "processed"
WORKFLOW_DIR = REPO_ROOT / "compiled" / ".agent" / "workflows"

TAG_PATTERNS = {
    "trigger": re.compile(r"<trigger>(.*?)</trigger>", re.DOTALL),
    "phase": re.compile(r"<phase>(.*?)</phase>", re.DOTALL),
    "persona": re.compile(r"<persona>(.*?)</persona>", re.DOTALL),
}


def extract_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Split YAML frontmatter from body. Returns (metadata, body)."""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, content[match.end():]


def extract_skill_tags(content: str) -> dict[str, str]:
    """Extract trigger, phase, persona from <skill> block."""
    tags: dict[str, str] = {}
    for tag, pattern in TAG_PATTERNS.items():
        m = pattern.search(content)
        tags[tag] = m.group(1).strip() if m else "unknown"
    return tags


def compile_workflow(source: Path, dest: Path) -> bool:
    """Compile a single skill file into workflow format."""
    content = source.read_text(encoding="utf-8", errors="replace")
    meta, body = extract_frontmatter(content)
    name = meta.get("name", source.stem)
    tags = extract_skill_tags(content)

    header = (
        f"# Workflow: {name}\n"
        f"# Phase: {tags['phase']}\n"
        f"# Persona: {tags['persona']}\n"
        f"# Trigger: {tags['trigger']}\n"
        f"\n---\n"
    )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(header + body, encoding="utf-8")
    return True


def main() -> int:
    """Compile all processed skills into agent workflows."""
    sources = sorted(PROCESSED_DIR.glob("*.md"))
    if not sources:
        print("No processed skill files found.")
        return 0

    compiled = 0
    for src in sources:
        meta, _ = extract_frontmatter(
            src.read_text(encoding="utf-8", errors="replace"),
        )
        name = meta.get("name", src.stem)
        dest = WORKFLOW_DIR / f"{name}.md"
        if compile_workflow(src, dest):
            print(f"  [OK] {src.name} -> workflows/{name}.md")
            compiled += 1

    print()
    print(f"Compiled {compiled}/{len(sources)} workflows to {WORKFLOW_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
