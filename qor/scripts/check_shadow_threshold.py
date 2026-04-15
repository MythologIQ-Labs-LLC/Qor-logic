#!/usr/bin/env python3
"""Check PROCESS_SHADOW_GENOME for threshold breach.

Steps per sweep:
  1. Stale expiry: sev 1-2 unaddressed > 90 days -> addressed=true, reason=stale.
  2. Aged self-escalation: sev >= 3 unaddressed > 90 days -> emit one
     aged_high_severity_unremediated (sev 5) per source. Idempotent.
  3. Threshold: sum severity of still-unaddressed events.
  4. If sum >= THRESHOLD: write .qor/remediate-pending marker; exit 10.
     Else: remove stale marker; exit 0.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make shadow_process importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

import shadow_process  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKER_PATH = REPO_ROOT / ".qor" / "remediate-pending"

THRESHOLD = 10
STALE_DAYS = 90
ESCALATION_EVENT = "aged_high_severity_unremediated"


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def sweep(events: list[dict], now: datetime) -> tuple[list[dict], list[dict], int]:
    """Apply stale expiry + self-escalation; return (updated_events, new_escalations, breach_sum)."""
    changed = False
    cutoff = now - timedelta(days=STALE_DAYS)

    # Index: source_entry_id -> escalation event (to check idempotence)
    existing_escalations: set[str] = {
        e["source_entry_id"]
        for e in events
        if e["event_type"] == ESCALATION_EVENT and e.get("source_entry_id")
    }

    new_escalations: list[dict] = []
    for e in events:
        if e["addressed"]:
            continue
        age = now - parse_ts(e["ts"])
        if age.days < STALE_DAYS:
            continue
        if e["severity"] in (1, 2):
            e["addressed"] = True
            e["addressed_ts"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            e["addressed_reason"] = "stale"
            changed = True
        elif e["severity"] >= 3 and e["id"] not in existing_escalations:
            new_event = {
                "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "skill": "qor-shadow-process",
                "session_id": "escalation-sweep",
                "event_type": ESCALATION_EVENT,
                "severity": 5,
                "details": {
                    "aged_entry_id": e["id"],
                    "aged_skill": e["skill"],
                    "age_days": age.days,
                },
                "addressed": False,
                "issue_url": None,
                "addressed_ts": None,
                "addressed_reason": None,
                "source_entry_id": e["id"],
            }
            new_event["id"] = shadow_process.compute_id(new_event)
            new_escalations.append(new_event)
            existing_escalations.add(e["id"])

    combined = events + new_escalations
    sum_unaddressed = sum(e["severity"] for e in combined if not e["addressed"])
    return combined, new_escalations, sum_unaddressed


def write_marker(sum_severity: int, unaddressed_ids: list[str]) -> None:
    MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "breach_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "threshold": THRESHOLD,
        "severity_sum": sum_severity,
        "event_count": len(unaddressed_ids),
        "event_ids": unaddressed_ids,
        "next_action": "Run /qor-remediate or python qor/scripts/create_shadow_issue.py",
    }
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=MARKER_PATH.parent, delete=False, suffix=".tmp"
    ) as tf:
        json.dump(payload, tf, indent=2)
        tmp = tf.name
    os.replace(tmp, MARKER_PATH)


def remove_marker() -> None:
    if MARKER_PATH.exists():
        MARKER_PATH.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--log", type=Path, default=shadow_process.LOG_PATH)
    ap.add_argument("--now", type=str, help="ISO-8601 UTC override for testing")
    ap.add_argument("--dry-run", action="store_true", help="Don't write changes back")
    args = ap.parse_args()

    events = shadow_process.read_events(args.log)
    if not events:
        print("No events in log; nothing to check.")
        remove_marker()
        return 0

    now = parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    updated, new_escalations, sum_unaddr = sweep(events, now)

    unaddr_ids = [e["id"] for e in updated if not e["addressed"]]

    if not args.dry_run:
        if new_escalations or any(e.get("addressed_reason") == "stale" for e in updated):
            shadow_process.write_events(updated, args.log)
            print(f"Sweep wrote {len(new_escalations)} new escalation(s) and stale-expired events.")

    if sum_unaddr >= THRESHOLD:
        print(f"BREACH: severity sum {sum_unaddr} >= threshold {THRESHOLD}")
        print(f"  {len(unaddr_ids)} unaddressed event(s)")
        if not args.dry_run:
            write_marker(sum_unaddr, unaddr_ids)
            print(f"  Marker written: {MARKER_PATH}")
        return 10
    print(f"OK: severity sum {sum_unaddr} < threshold {THRESHOLD}")
    if not args.dry_run:
        remove_marker()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
