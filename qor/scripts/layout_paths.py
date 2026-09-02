"""Layout-resolved governance paths (Phase 250; GH #406).

`doc_integrity` and `doc_integrity_strict` resolved the glossary as a literal,
so the strict tier was unreachable in any workspace that keeps its glossary
outside the `qor/` topology. These resolvers read the same `layout` section
`badge_layout` already owns, with the same flag > config > default precedence,
so one module answers "where does this workspace keep X" for every gate.

Kept separate from `doc_integrity` to hold that module under its 250-line
Section 4 Razor cap, and separate from `badge_layout` because that module's
subject is badge counting rather than governance-document location.
"""
from __future__ import annotations

import argparse
from pathlib import Path


_TIERS = ("minimal", "standard", "system", "legacy")

_TIER_REQUIREMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "minimal": (("README.md", "README.md"),),
    "standard": (
        ("README.md", "README.md"),
        ("qor/references/glossary.md", "glossary"),
    ),
    "system": (
        ("README.md", "README.md"),
        ("qor/references/glossary.md", "glossary"),
        ("docs/architecture.md", "architecture.md"),
        ("docs/lifecycle.md", "lifecycle.md"),
        ("docs/operations.md", "operations.md"),
        ("docs/policies.md", "policies.md"),
    ),
    "legacy": (),
}

def _resolved_layout(repo_root: str | Path):
    from qor.scripts import badge_layout

    ns = argparse.Namespace(repo_root=Path(repo_root), glossary_path=None)
    return badge_layout.layout_from_args(ns)


def resolve_glossary_path(repo_root: str | Path) -> str:
    """Return the workspace's glossary path, config-resolved.

    Defaults to the `qor/` topology, so a workspace declaring nothing behaves
    exactly as before. A consumer keeping its glossary elsewhere declares
    `layout.glossary_path` in `.qorlogic/config.json`.
    """
    return str(Path(repo_root) / _resolved_layout(repo_root).glossary_path)


def tier_requirements(
    repo_root: str | Path,
) -> dict[str, tuple[tuple[str, str], ...]]:
    """Tier -> required docs, with the glossary row resolved from the layout."""
    glossary_rel = _resolved_layout(repo_root).glossary_path.as_posix()
    return {
        tier: tuple(
            (glossary_rel, label) if label == "glossary" else (rel, label)
            for rel, label in rows
        )
        for tier, rows in _TIER_REQUIREMENTS.items()
    }
