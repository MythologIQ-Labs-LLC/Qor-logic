#!/usr/bin/env python3
"""remediate: flip matched events to addressed=true in their origin file.

Step 4 of the /qor-remediate skill protocol. Uses shadow_process's dual-file
API to preserve LOCAL/UPSTREAM attribution on write-back.

SG-032 guard: unknown IDs (not present in id_source_map) are surfaced as a
list instead of silently dropped. Caller decides whether to abort or warn.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Make shadow_process importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

import shadow_process  # noqa: E402


def mark_addressed(
    event_ids: list[str],
    session_id: str,
) -> tuple[int, list[str]]:
    """Flip the given events to addressed=true; route write-back to origin file.

    Returns (flipped_count, missing_ids). Missing IDs are event_ids that did
    not match any record in either shadow log (LOCAL or UPSTREAM). They are
    surfaced rather than silently dropped per SG-032.

    session_id is recorded in the event details but addressed_reason is
    constrained by the schema enum to one of {issue_created, remediated,
    stale, null}; we use "remediated".
    """
    events = shadow_process.read_all_events()
    src_map = shadow_process.id_source_map()
    target = set(event_ids)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    flipped = 0
    for e in events:
        if e["id"] in target and not e["addressed"]:
            e["addressed"] = True
            e["addressed_ts"] = now
            e["addressed_reason"] = "remediated"
            flipped += 1

    known_ids = set(src_map.keys())
    missing_ids = [eid for eid in event_ids if eid not in known_ids]

    if flipped:
        shadow_process.write_events_per_source(events, src_map)
    return flipped, missing_ids
