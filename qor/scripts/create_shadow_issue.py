#!/usr/bin/env python3
"""Create a GitHub issue aggregating unaddressed process shadow events.

Flow:
  1. Validate gh auth status.
  2. Resolve event set: from .qor/remediate-pending marker (default) or explicit --events ids.
  3. Build issue body with severity breakdown + per-event details.
  4. gh issue create --repo MythologIQ-Labs-LLC/Qor-logic --label qor-shadow.
  5. Update events in PROCESS_SHADOW_GENOME: addressed=true, issue_url=<url>.
  6. Remove the marker file.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_EVENT_ID_RE = re.compile(r'^[a-f0-9]{64}$')


def validate_event_id(event_id: str) -> None:
    """Validate event ID matches ^[a-f0-9]{64}$. Raises ValueError on invalid.

    Phase 278 (GH #459): the type check is not decoration. ``_EVENT_ID_RE.match``
    raises ``TypeError`` on a non-string, so an integer id -- exactly what a
    hand-edited or machine-generated marker yields -- escaped this function as a
    type its own docstring does not name, and a caller obeying the documented
    contract would not catch it.
    """
    if not isinstance(event_id, str):
        raise ValueError(
            f"Invalid event ID: expected a string, got {type(event_id).__name__} "
            f"({event_id!r})"
        )
    if not _EVENT_ID_RE.match(event_id):
        raise ValueError(f"Invalid event ID: {event_id!r}")


class EventIdArgumentError(ValueError):
    """A ``--events`` argument that cannot be turned into a usable id set.

    Carried as one dedicated exception so the helper below does not choose the
    error *mechanism*: each argparse branch converts this to its own
    ``print`` + ``return 2``, which is that site's measured convention. A helper
    serving three branches must not impose a mechanism on callers whose
    convention it does not know.
    """


def parse_events_argument(raw: str) -> set[str]:
    """Turn a ``--events`` value into a validated set of event ids.

    Three ordered rules, deliberately distinct (Phase 278; GH #459):

    1. **normalize** -- split on ``,``, strip each element, drop empties. A
       trailing comma is an artifact of the separator, not an id the operator
       named, and ``--events "<id>,"`` works today.
    2. **require non-empty** -- ``--events ","`` names no ids at all. Without
       this rule normalization yields an empty target set, which matches no
       event and exits 0: the silent success this function exists to prevent,
       reintroduced through its own normalizer.
    3. **validate** each survivor.

    Conflating (1) and (2) is what makes the fix reopen the defect.
    """
    ids = {part.strip() for part in raw.split(",")}
    ids.discard("")
    if not ids:
        raise EventIdArgumentError(
            f"--events was given but names no event ids: {raw!r}"
        )
    for event_id in sorted(ids):
        try:
            validate_event_id(event_id)
        except ValueError as exc:
            raise EventIdArgumentError(str(exc)) from exc
    return ids

from qor.scripts import shadow_process

from qor import workdir as _workdir

MARKER_PATH = _workdir.root() / ".qor" / "remediate-pending"
DEFAULT_REPO = "MythologIQ-Labs-LLC/Qor-logic"


def ensure_gh_auth() -> None:
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise SystemExit("ERROR: gh CLI not installed. https://cli.github.com/")
    if result.returncode != 0:
        raise SystemExit(f"ERROR: gh not authenticated. Run 'gh auth login'.\n{result.stderr}")


_REGEN = "remove it and re-run check_shadow_threshold.py."


def load_marker() -> dict:
    """Load the remediate-pending marker, or exit naming what is wrong with it.

    Phase 273 (GH #454): the absent case was guarded and nothing else, so a
    truncated write raised JSONDecodeError, non-UTF-8 bytes raised
    UnicodeDecodeError, and valid-but-non-object JSON returned cleanly and
    failed later at the first subscript.

    Worst was a dict whose `event_ids` is a string: `set("evt-1")` is a set of
    CHARACTERS, so nothing matched and main returned 0 -- a breached governance
    threshold reporting success. That survives an isinstance(dict) guard, which
    is why the shape is checked and not just the type of the payload.

    This EXITS rather than degrading, which is the opposite of the remedy two
    earlier phases applied to other readers. Those sit in gate-writing paths
    with an established degraded value; this one already exits when the marker
    is absent, and its caller opens an issue rather than writing a gate
    artifact. Returning a degraded value here would move the failure one frame
    further from its cause -- the defect, not the cure.

    The fields checked are the ones this module dereferences, not the writer's
    full payload, so the guard cannot drift as that payload grows. Typing is
    asymmetric by consequence: a wrong-typed `event_ids` produces a wrong
    governance verdict, while `threshold` and `breach_ts` interpolate into an
    issue body and produce a visibly odd line nobody acts on.
    """
    if not MARKER_PATH.exists():
        raise SystemExit(f"No marker at {MARKER_PATH}. Run check_shadow_threshold.py first.")
    try:
        raw = MARKER_PATH.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Marker at {MARKER_PATH} is not UTF-8 ({exc}); {_REGEN}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Marker at {MARKER_PATH} is not readable JSON ({exc}); {_REGEN}")
    if not isinstance(data, dict):
        raise SystemExit(
            f"Marker at {MARKER_PATH} parsed as {type(data).__name__}, expected an object; {_REGEN}"
        )
    missing = [k for k in ("event_ids", "threshold", "breach_ts") if k not in data]
    if missing:
        raise SystemExit(f"Marker at {MARKER_PATH} is missing {', '.join(missing)}; {_REGEN}")
    if not isinstance(data["event_ids"], list):
        raise SystemExit(
            f"Marker at {MARKER_PATH} has event_ids as {type(data['event_ids']).__name__}, "
            f"expected a list; {_REGEN}"
        )
    # Phase 278 (GH #459): the type guard above was Phase 273's; it admits a
    # LIST of malformed elements, which then match no event, empty the
    # selection, and exit 0 on a breached threshold. SystemExit rather than the
    # validator's ValueError, because that is this loader's contract -- "exit
    # naming what is wrong with it" -- and a ValueError escaping here would be
    # an unhandled traceback one line below a clean named message.
    for event_id in data["event_ids"]:
        try:
            validate_event_id(event_id)
        except ValueError as exc:
            raise SystemExit(
                f"Marker at {MARKER_PATH} has an unusable event id ({exc}); {_REGEN}"
            ) from exc
    return data


def build_body(events: list[dict], marker: dict) -> str:
    counts = Counter(e["event_type"] for e in events)
    sev_sum = sum(e["severity"] for e in events)
    lines = [
        "## Process Shadow Genome — threshold breach",
        "",
        f"Severity sum: **{sev_sum}** (threshold {marker['threshold']})",
        f"Event count: {len(events)}",
        f"Detected: {marker['breach_ts']}",
        "",
        "### Event type distribution",
        "",
    ]
    for etype, n in counts.most_common():
        lines.append(f"- `{etype}`: {n}")
    lines.append("")
    lines.append("### Events")
    lines.append("")
    for e in events:
        lines.append(
            f"- **{e['ts']}** `{e['skill']}` / `{e['event_type']}` / sev {e['severity']}"
        )
        if e.get("details"):
            details_str = json.dumps(e["details"], indent=2)[:500]
            lines.append(f"  ```json\n  {details_str}\n  ```")
    lines.append("")
    lines.append(
        "### Next action\n\n"
        "Run `/qor-remediate` to propose a process change. Mark events `addressed=true` "
        "with `addressed_reason=remediated` after resolution."
    )
    return "\n".join(lines)


def create_issue(repo: str, title: str, body: str) -> str:
    result = subprocess.run(
        [
            "gh", "issue", "create",
            "--repo", repo,
            "--title", title,
            "--body-file", "-",
            "--label", "qor-shadow",
        ],
        input=body,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise SystemExit(f"gh issue create failed:\n{result.stderr}")
    url = result.stdout.strip().splitlines()[-1]
    return url


def mark_addressed(events_log: list[dict], target_ids: set[str], url: str) -> list[dict]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for e in events_log:
        if e["id"] in target_ids and not e["addressed"]:
            e["addressed"] = True
            e["addressed_ts"] = now
            e["addressed_reason"] = "issue_created"
            e["issue_url"] = url
    return events_log


def flip_events_only(log_path: Path, target_ids: set[str], url: str) -> int:
    """Update matching events to addressed=true with the given url. Returns count flipped.

    Used by the cross-repo collector (Phase 5) to apply a single consolidated
    issue URL across multiple repos without each repo opening its own issue.
    """
    all_events = shadow_process.read_events(log_path)
    before = sum(1 for e in all_events if e["id"] in target_ids and not e["addressed"])
    if before == 0:
        return 0
    updated = mark_addressed(all_events, target_ids, url)
    shadow_process.write_events(updated, log_path)
    return before


def mark_resolved(log_path: Path, target_ids: set[str], reason: str = "remediated") -> int:
    """Update matching events to addressed=true without an issue URL.

    For when an operator resolves a process issue via direct action and there's
    no GitHub issue to attach. addressed_reason='remediated'; issue_url remains null.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_events = shadow_process.read_events(log_path)
    flipped = 0
    for e in all_events:
        if e["id"] in target_ids and not e["addressed"]:
            e["addressed"] = True
            e["addressed_ts"] = now
            e["addressed_reason"] = reason
            flipped += 1
    if flipped:
        shadow_process.write_events(all_events, log_path)
    return flipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--events", help="Comma-separated event ids (overrides marker)")
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-auth", action="store_true", help="For testing only")
    ap.add_argument("--flip-only", metavar="URL",
                    help="Skip gh; just flip matching events to addressed=true with URL. "
                         "Used by cross-repo collector.")
    ap.add_argument("--mark-resolved", action="store_true",
                    help="Skip gh; flip events to addressed=true with "
                         "addressed_reason='remediated', no URL. For operator-driven "
                         "resolution when there's no GitHub issue to attach.")
    args = ap.parse_args()

    single_file = args.log is not None
    log = args.log or shadow_process.LOG_PATH

    if args.mark_resolved:
        if not args.events:
            print("ERROR: --mark-resolved requires --events <ids>", file=sys.stderr)
            return 2
        try:
            target_ids = parse_events_argument(args.events)
        except EventIdArgumentError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        flipped = mark_resolved(log, target_ids)
        print(f"Marked {flipped} event(s) resolved in {log}")
        return 0

    if args.flip_only:
        if not args.events:
            print("ERROR: --flip-only requires --events <ids>", file=sys.stderr)
            return 2
        try:
            target_ids = parse_events_argument(args.events)
        except EventIdArgumentError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        flipped = flip_events_only(log, target_ids, args.flip_only)
        print(f"Flipped {flipped} event(s) in {log}")
        if MARKER_PATH.exists():
            MARKER_PATH.unlink()
        return 0

    if not args.skip_auth and not args.dry_run:
        ensure_gh_auth()

    if args.events:
        try:
            target_ids = parse_events_argument(args.events)
        except EventIdArgumentError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        marker = {"breach_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "threshold": 10}
    else:
        marker = load_marker()
        target_ids = set(marker["event_ids"])

    if single_file:
        all_events = shadow_process.read_events(log)
    else:
        all_events = shadow_process.read_all_events()
    selected = [e for e in all_events if e["id"] in target_ids and not e["addressed"]]
    if not selected:
        print("No matching unaddressed events. Nothing to do.")
        return 0

    title = f"[qor-shadow] Process threshold breach — {len(selected)} events, sev {sum(e['severity'] for e in selected)}"
    body = build_body(selected, marker)

    if args.dry_run:
        print(f"--- DRY RUN ---\nTitle: {title}\n\n{body}")
        return 0

    url = create_issue(args.repo, title, body)
    print(f"Issue created: {url}")

    updated = mark_addressed(all_events, target_ids, url)
    if single_file:
        shadow_process.write_events(updated, log)
    else:
        src_map = shadow_process.id_source_map()
        shadow_process.write_events_per_source(updated, src_map)
    print(f"Updated {len(target_ids)} event(s)")

    if MARKER_PATH.exists() and not args.events:
        MARKER_PATH.unlink()
        print(f"Removed marker: {MARKER_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
