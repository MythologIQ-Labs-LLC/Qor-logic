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
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# GAP-SEC-07: single canonical path-safety validator lives in session.py;
# re-exported here for backward compatibility with existing callers.
from qor.scripts.session import validate_session_id  # noqa: E402,F401

from qor.scripts import shadow_process

from qor import workdir as _workdir

MARKER_PATH = _workdir.root() / ".qor" / "remediate-pending"

THRESHOLD = 10
STALE_DAYS = 90
ESCALATION_EVENT = "aged_high_severity_unremediated"


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def sweep(events: list[dict], now: datetime) -> tuple[list[dict], list[dict], int]:
    """Apply stale expiry + self-escalation; return (updated_events, new_escalations, breach_sum).

    Pure function — no I/O. Caller is responsible for writing results.
    Escalation events are always UPSTREAM (infrastructure-generated).
    """
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
    # Phase 253 (GH #410): collapse recurrence and honor enforcer-backed pending
    # proposals, so the sum measures process debt rather than phase count.
    sum_unaddressed = collapsed_severity(combined)
    return events, new_escalations, sum_unaddressed



def _signature(event: dict) -> tuple:
    """The identity a recurring disclosed event shares across occurrences.

    Phase 254: collapse requires positive evidence that two events describe the
    same condition. A shared ``gate``, ``capability`` or ``pattern`` is that
    evidence; absent all three, identical details are. Differing details mean we
    do not know the events are the same, so they are not merged.

    Phase 253 keyed only on ``gate``/``capability``, so events carrying neither
    collapsed by ``event_type`` alone and two unrelated ``degradation`` defects
    counted as one. That direction is the more dangerous one: a rule that hides
    real debt produces a number that looks better.

    ``gate`` resolves before the digest, so an event whose details carry a
    varying field such as ``phase`` still collapses.
    """
    import hashlib
    import json

    details = event.get("details") or {}
    key = details.get("gate") or details.get("capability") or details.get("pattern")
    if key is None:
        blob = json.dumps(details, sort_keys=True, default=str).encode("utf-8")
        key = "details:" + hashlib.sha256(blob).hexdigest()[:12]
    return (event.get("event_type"), key)


def _pending_discount_applies(event: dict) -> bool:
    """True when a pending proposal has bought its discount with real evidence.

    GH #410 fix 4. Excluding `addressed_pending` unconditionally would let a bare
    proposal silence the signal -- the closing-on-prose failure this repository
    rejects elsewhere. Requiring a `closure_enforcer` that validates means the
    discount costs the same evidence stage 2 demands; stage 2 still requires the
    review-pass attestation before `addressed` becomes true.
    """
    if not event.get("addressed_pending"):
        return False
    enforcer = event.get("closure_enforcer")
    if not enforcer:
        return False
    from qor.scripts.remediate_mark_addressed import (
        ClosureEnforcerError,
        _validate_closure_enforcer,
    )

    try:
        _validate_closure_enforcer(enforcer)
    except (ClosureEnforcerError, Exception):
        return False
    return True


def collapsed_severity(events: list[dict]) -> int:
    """Severity sum with recurrence collapsed (GH #410 fix 6).

    A disclosed event repeating with the same signature contributes its severity
    ONCE. Every occurrence stays in the log as history; only the sum changes.

    Without this the threshold measured how many phases had been sealed rather
    than accumulated process debt: `data_api_acl_lint` skips every seal because
    a repository has no SQL migrations -- a permanent, correct property of it --
    and each seal added severity that nothing could ever remediate, because
    nothing was wrong.

    A genuinely new gate skipping, or a new capability falling short, still adds
    its severity, which is what keeps the threshold a signal rather than merely
    quieter.
    """
    seen: set[tuple] = set()
    total = 0
    for event in events:
        if event.get("addressed"):
            continue
        if _pending_discount_applies(event):
            continue
        sig = _signature(event)
        if sig in seen:
            continue
        seen.add(sig)
        total += event.get("severity", 0)
    return total


def every_unaddressed_event_has_a_pending_proposal(events: list[dict]) -> bool:
    """True when no unaddressed event is missing a remediation proposal.

    GH #410 fix 5: a routing escape that clears the marker even when the sum
    stays at or above threshold. With fix 4 in place this is usually
    unreachable; it exists so a future phase judging that discount too permissive
    can revert it without reintroducing the deadlock the issue reported.
    """
    unaddressed = [e for e in events if not e.get("addressed")]
    if not unaddressed:
        return True
    return all(e.get("addressed_pending") for e in unaddressed)


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
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--now", type=str, help="ISO-8601 UTC override for testing")
    ap.add_argument("--dry-run", action="store_true", help="Don't write changes back")
    args = ap.parse_args()

    single_file = args.log is not None
    if single_file:
        events = shadow_process.read_events(args.log)
    else:
        events = shadow_process.read_all_events()
    if not events:
        print("No events in log; nothing to check.")
        remove_marker()
        return 0

    now = parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    updated, new_escalations, sum_unaddr = sweep(events, now)

    unaddr_ids = [e["id"] for e in (updated + new_escalations) if not e["addressed"]]

    if not args.dry_run:
        if new_escalations or any(e.get("addressed_reason") == "stale" for e in updated):
            if single_file:
                shadow_process.write_events(updated + new_escalations, args.log)
            else:
                src_map = shadow_process.id_source_map()
                for esc in new_escalations:
                    src_map[esc["id"]] = shadow_process.UPSTREAM_LOG_PATH
                shadow_process.write_events_per_source(
                    updated + new_escalations, src_map,
                )
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
