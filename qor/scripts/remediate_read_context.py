#!/usr/bin/env python3
"""remediate: read dual-file shadow events, filter unaddressed, group by key.

Step 1 of the /qor-remediate skill protocol. Consumes the Phase 14 dual-file
shadow infrastructure (LOCAL + UPSTREAM) and returns unaddressed events grouped
by (event_type, skill, session_id) for downstream pattern classification.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make shadow_process importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

import shadow_process  # noqa: E402


GroupKey = tuple[str, str, str]


def load_unaddressed_groups() -> dict[GroupKey, list[dict]]:
    """Return unaddressed events grouped by (event_type, skill, session_id).

    Empty logs (or all-addressed logs) yield an empty dict.
    """
    events = shadow_process.read_all_events()
    groups: dict[GroupKey, list[dict]] = {}
    for e in events:
        if e.get("addressed"):
            continue
        key = (e["event_type"], e["skill"], e["session_id"])
        groups.setdefault(key, []).append(e)
    return groups
