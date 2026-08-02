"""Repository-declared attribution policy (Phase 207).

`qor/scripts/attribution.py` is declared pure by its own doctrine contract, so
the filesystem read that resolves an operator's declaration lives here and
reaches the pure helper only as an already-resolved keyword.

The `Authored via [Qor-logic SDLC]` line is never optional. What is declarable
is whether the model `Co-Authored-By:` line is REQUIRED: the doctrine's stated
rationale for it is GitHub contributor-stats reporting, a convenience rather
than a governance guarantee, and some operators forbid AI co-author trailers
outright. Provenance is carried by the Merkle chain and the gate artifacts.

Resolution is tolerant and fails CLOSED: an absent file, an absent key, a
malformed document, or a non-boolean value all yield the strict default, so a
corrupt config demands more attribution rather than less.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_RELPATH = Path(".qorlogic") / "config.json"


@dataclass(frozen=True)
class AttributionPolicy:
    """What a repository requires of its commit attribution.

    `model_coauthor` True (the default) preserves the historical contract: a
    seal commit must carry both the framework line and a `Co-Authored-By:`
    line.
    """

    model_coauthor: bool = True


DEFAULT_POLICY = AttributionPolicy()


def resolve_policy(repo_root: Path | None = None) -> AttributionPolicy:
    """Read `.qorlogic/config.json` -> `attribution.model_coauthor`.

    Returns `DEFAULT_POLICY` unless the file exists, parses, and declares the
    key as a genuine boolean.
    """
    root = Path.cwd() if repo_root is None else Path(repo_root)
    config_path = root / CONFIG_RELPATH
    if not config_path.is_file():
        return DEFAULT_POLICY
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAULT_POLICY
    if not isinstance(data, dict):
        return DEFAULT_POLICY
    section = data.get("attribution")
    if not isinstance(section, dict):
        return DEFAULT_POLICY
    declared = section.get("model_coauthor")
    if not isinstance(declared, bool):
        return DEFAULT_POLICY
    return AttributionPolicy(model_coauthor=declared)
