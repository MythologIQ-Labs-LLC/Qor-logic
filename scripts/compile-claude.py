#!/usr/bin/env python3
"""Compile processed S.H.I.E.L.D. skills into Claude Code SKILL.md format."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "processed"
COMPILED_DIR = REPO_ROOT / "compiled" / ".claude" / "skills"

ENHANCED_FIELDS = {
    "user-invocable": "true",
    "allowed-tools": "Read, Glob, Grep, Edit, Write, Bash",
}


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Split YAML frontmatter from body. Returns (metadata, body)."""
    if not content.startswith("---"):
        return {}, content
    end = content.index("---", 3)
    raw = content[3:end].strip()
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            meta[key.strip()] = value.strip()
    body = content[end + 3:]
    return meta, body


def build_frontmatter(meta: dict[str, str]) -> str:
    """Build enhanced YAML frontmatter string."""
    lines = ["---"]
    for key, value in meta.items():
        lines.append(f"{key}: {value}")
    for key, value in ENHANCED_FIELDS.items():
        if key not in meta:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def compile_skills() -> list[Path]:
    """Compile all top-level processed skills into SKILL.md files."""
    compiled: list[Path] = []
    for skill_file in sorted(PROCESSED_DIR.glob("*.md")):
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(content)
        name = meta.get("name", skill_file.stem)

        out_dir = COMPILED_DIR / name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "SKILL.md"
        out_path.write_text(
            build_frontmatter(meta) + body, encoding="utf-8",
        )
        compiled.append(out_path)
    return compiled


def main() -> int:
    compiled = compile_skills()
    print("=" * 60)
    print("Claude Code SKILL.md Compilation Report")
    print("=" * 60)
    print()
    print(f"Skills compiled: {len(compiled)}")
    print()
    for path in compiled:
        skill_name = path.parent.name
        print(f"  [OK] {skill_name} -> {path}")
    print()
    print(f"Output root: {COMPILED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
