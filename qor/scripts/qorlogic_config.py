"""The one tolerant reader for `.qorlogic/config.json` (Phase 210).

Several controls resolve operator declarations from this file -- attribution
policy (Phase 207) and badge-layout resolution (Phase 210) so far. Each having
its own parse would let them degrade differently under identical malformed
input, a defect that only surfaces when someone relies on their agreement.

Reading is tolerant and total: an absent file, an unreadable path, invalid
JSON, a non-object document, and a non-object section all yield the empty
mapping. Nothing here raises, because a broken operator config must never break
a gate -- each consumer decides what its own defaults are, and an empty mapping
means "declared nothing".
"""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_RELPATH = Path(".qorlogic") / "config.json"


def load_section(repo_root: Path | None, name: str) -> dict:
    """Return the named top-level object from the config, or `{}`."""
    root = Path.cwd() if repo_root is None else Path(repo_root)
    config_path = root / CONFIG_RELPATH
    try:
        if not config_path.is_file():
            return {}
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    section = data.get(name)
    return section if isinstance(section, dict) else {}
