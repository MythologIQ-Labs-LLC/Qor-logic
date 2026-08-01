"""Declared badge-count repository topology.

One immutable value naming the roots and relative glob patterns the badge
counters walk, plus the CLI plumbing that builds it. Owning this here keeps
`badge_currency` about counting and `seal_artifacts` about writing, and keeps
the layout one value rather than six loose parameters threaded through every
signature (Phase 206; audit entry #502 Ground 1).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


class BadgeLayoutError(ValueError):
    """Configured badge-count layout cannot be resolved safely."""


@dataclass(frozen=True)
class BadgeLayout:
    """Roots and relative glob patterns for the counted badge kinds.

    Field defaults are the canonical `qor/` topology, so a caller that declares
    nothing gets the layout this repository has always used.
    """

    skills_root: Path = Path("qor/skills")
    skills_pattern: str = "**/SKILL.md"
    agents_root: Path = Path("qor/agents")
    agents_pattern: str = "**/*.md"
    doctrines_root: Path = Path("qor/references")
    doctrines_pattern: str = "doctrine-*.md"


DEFAULT_LAYOUT = BadgeLayout()


def add_layout_args(parser: argparse.ArgumentParser) -> None:
    """Declare the six layout flags on any CLI that counts badge kinds."""
    parser.add_argument("--skills-root", type=Path, default=DEFAULT_LAYOUT.skills_root)
    parser.add_argument("--skills-pattern", default=DEFAULT_LAYOUT.skills_pattern)
    parser.add_argument("--agents-root", type=Path, default=DEFAULT_LAYOUT.agents_root)
    parser.add_argument("--agents-pattern", default=DEFAULT_LAYOUT.agents_pattern)
    parser.add_argument(
        "--doctrines-root", type=Path, default=DEFAULT_LAYOUT.doctrines_root
    )
    parser.add_argument(
        "--doctrines-pattern", default=DEFAULT_LAYOUT.doctrines_pattern
    )


def layout_from_args(args: argparse.Namespace) -> BadgeLayout:
    """Build one layout value from the flags declared by `add_layout_args`."""
    return BadgeLayout(
        skills_root=args.skills_root,
        skills_pattern=args.skills_pattern,
        agents_root=args.agents_root,
        agents_pattern=args.agents_pattern,
        doctrines_root=args.doctrines_root,
        doctrines_pattern=args.doctrines_pattern,
    )
