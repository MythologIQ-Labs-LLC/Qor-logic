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
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import shadow_process  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKER_PATH = REPO_ROOT / ".qor" / "remediate-pending"
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


def load_marker() -> dict:
    if not MARKER_PATH.exists():
        raise SystemExit(f"No marker at {MARKER_PATH}. Run check_shadow_threshold.py first.")
    return json.loads(MARKER_PATH.read_text(encoding="utf-8"))


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
    ap.add_argument("--log", type=Path, default=shadow_process.LOG_PATH)
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

    # Mark-resolved mode: no gh, no URL, manual resolution
    if args.mark_resolved:
        if not args.events:
            print("ERROR: --mark-resolved requires --events <ids>", file=sys.stderr)
            return 2
        target_ids = set(args.events.split(","))
        flipped = mark_resolved(args.log, target_ids)
        print(f"Marked {flipped} event(s) resolved in {args.log}")
        return 0

    # Flip-only mode: no gh call, no marker load
    if args.flip_only:
        if not args.events:
            print("ERROR: --flip-only requires --events <ids>", file=sys.stderr)
            return 2
        target_ids = set(args.events.split(","))
        flipped = flip_events_only(args.log, target_ids, args.flip_only)
        print(f"Flipped {flipped} event(s) in {args.log}")
        if MARKER_PATH.exists():
            MARKER_PATH.unlink()
        return 0

    if not args.skip_auth and not args.dry_run:
        ensure_gh_auth()

    if args.events:
        target_ids = set(args.events.split(","))
        marker = {"breach_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "threshold": 10}
    else:
        marker = load_marker()
        target_ids = set(marker["event_ids"])

    all_events = shadow_process.read_events(args.log)
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
    shadow_process.write_events(updated, args.log)
    print(f"Updated {len(target_ids)} event(s) in {args.log}")

    if MARKER_PATH.exists() and not args.events:
        MARKER_PATH.unlink()
        print(f"Removed marker: {MARKER_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
