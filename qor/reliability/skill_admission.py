#!/usr/bin/env python3
"""Skill admission gate — verify a skill invocation is registered and well-formed.

Discovers skills by walking qor/skills/**/SKILL.md (or the directory given via
the SKILLS_ROOT env var). Admits if the skill is registered and its frontmatter
contains required keys (name, description, phase) and the name matches the
requested skill trigger.

Usage: skill-admission.py <skill-name>

Exit 0 on ADMITTED. Exit 1 on NOT-ADMITTED with reason printed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SKILLS_ROOT = REPO_ROOT / "qor" / "skills"
REQUIRED_KEYS = ("name", "description", "phase")


def _skills_root() -> Path:
    return Path(os.environ.get("SKILLS_ROOT", str(DEFAULT_SKILLS_ROOT)))


def discover_skills(root: Path) -> dict[str, Path]:
    """Map skill trigger name (dir basename) -> SKILL.md path."""
    skills: dict[str, Path] = {}
    if not root.is_dir():
        return skills
    for skill_md in root.rglob("SKILL.md"):
        name = skill_md.parent.name
        skills[name] = skill_md
    return skills


def parse_frontmatter(body: str) -> dict[str, str] | None:
    """Parse the leading --- ... --- block. Return {key: value} or None."""
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        return None

    result: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.startswith(" "):
            # Skip blank lines and nested YAML (e.g. metadata subkeys).
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        result[key.strip()] = value.strip()
    return result


def check_admission(name: str, skills: dict[str, Path]) -> tuple[bool, str]:
    """Return (admitted, message)."""
    if name not in skills:
        return False, f"NOT-ADMITTED: {name} reason=unregistered"

    body = skills[name].read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(body)
    if fm is None:
        return False, f"NOT-ADMITTED: {name} reason=missing-frontmatter:(none)"

    for key in REQUIRED_KEYS:
        if key not in fm:
            return False, f"NOT-ADMITTED: {name} reason=missing-frontmatter:{key}"

    if fm["name"] != name:
        return False, f"NOT-ADMITTED: {name} reason=name-mismatch"

    return True, f"ADMITTED: {name}"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: skill-admission.py <skill-name>", file=sys.stderr)
        return 2

    name = args[0]
    skills = discover_skills(_skills_root())
    admitted, message = check_admission(name, skills)
    print(message)
    return 0 if admitted else 1


if __name__ == "__main__":
    raise SystemExit(main())
