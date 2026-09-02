"""Declared badge-count repository topology.

One immutable value naming the roots and relative glob patterns the badge
counters walk, plus the CLI plumbing that builds it. Owning this here keeps
`badge_currency` about counting and `seal_artifacts` about writing, and keeps
the layout one value rather than six loose parameters threaded through every
signature (Phase 206; audit entry #502 Ground 1).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, fields, replace
from pathlib import Path

from qor.scripts.qorlogic_config import load_section


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
    # Phase 250 (GH #406): the glossary is layout-bound the same way the three
    # counted roots are -- doc_integrity and doc_integrity_strict resolved it as
    # a literal, so the strict tier was unreachable in any workspace that keeps
    # its glossary elsewhere. Declared here rather than in a second resolver so
    # one module owns the `layout` section.
    glossary_path: Path = Path("qor/references/glossary.md")


DEFAULT_LAYOUT = BadgeLayout()


def add_layout_args(parser: argparse.ArgumentParser) -> None:
    """Declare the six layout flags on any CLI that counts badge kinds.

    Every default is `None` so an UNSET flag stays distinguishable from one set
    to the default value. While the defaults were the real layout values, a
    flag always arrived populated and no lower-precedence source could ever
    win, which would have made the config channel inert (Phase 210, GH #299).
    """
    for name in ("skills", "agents", "doctrines"):
        parser.add_argument(f"--{name}-root", type=Path, default=None)
        parser.add_argument(f"--{name}-pattern", default=None)
    parser.add_argument("--glossary-path", type=Path, default=None)


def _declared(section: dict, key: str, cast=None):
    """Return a usable config value for `key`, or None to fall through."""
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return cast(value) if cast else value


def layout_from_args(args: argparse.Namespace) -> BadgeLayout:
    """Resolve one layout as flag > `.qorlogic/config.json` > `qor/` default.

    Resolution is per key: a config declaring only `skills_root` leaves the
    other five at their defaults. Every malformed shape degrades to the default
    rather than raising -- a broken operator config must not break a gate.

    Declaring a root is not trusting it. Values resolved here are candidates;
    repository containment, pattern traversal, and symlink rejection remain in
    `badge_currency._resolve_count_root` / `_count_matching`.
    """
    section = load_section(getattr(args, "repo_root", None), "layout")
    resolved = {}
    for field in fields(BadgeLayout):
        flag = getattr(args, field.name, None)
        if flag is not None:
            resolved[field.name] = flag
            continue
        cast = Path if field.name.endswith(("_root", "_path")) else None
        declared = _declared(section, field.name, cast)
        if declared is not None:
            resolved[field.name] = declared
    return replace(DEFAULT_LAYOUT, **resolved)
