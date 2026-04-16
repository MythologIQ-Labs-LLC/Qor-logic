#!/usr/bin/env python3
"""Cross-repo Shadow Genome collector.

For each enabled repo in ~/.qor/repos.json:
  1. subprocess `check_shadow_threshold.py` in that repo (applies stale expiry
     + aged-high-severity self-escalation; delegated state mutation).
  2. Read the updated PROCESS_SHADOW_GENOME.md; pool unaddressed events
     tagged with source_repo.
  3. If pooled severity sum >= threshold: build consolidated issue body,
     `gh issue create` against meta_repo, capture URL.
  4. For each source_repo with events in the issue: subprocess
     `create_shadow_issue.py --flip-only <URL> --events <ids>` with cwd=repo
     (each repo's own tool flips its own state).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

from qor.scripts import shadow_process

from qor import resources as _resources

SCHEMA_PATH = Path(str(_resources.schema("repos_config.schema.json")))
DEFAULT_CONFIG = Path.home() / ".qor" / "repos.json"

CHECK_SCRIPT = [sys.executable, "-m", "qor.scripts.check_shadow_threshold"]
ISSUE_SCRIPT = [sys.executable, "-m", "qor.scripts.create_shadow_issue"]
UPSTREAM_LOG_REL = "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md"
LEGACY_LOG_REL = "docs/PROCESS_SHADOW_GENOME.md"

def load_config(path: Path | None = None) -> dict:
    """Load config from $QOR_CONFIG, explicit path, or ~/.qor/repos.json."""
    if path is None:
        env_path = os.environ.get("QOR_CONFIG")
        path = Path(env_path) if env_path else DEFAULT_CONFIG
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)
    return data

def read_repo_shadow(repo_path: Path) -> list[dict]:
    """Read shadow events: upstream-first, legacy fallback with warning."""
    upstream = repo_path / UPSTREAM_LOG_REL
    legacy = repo_path / LEGACY_LOG_REL
    if upstream.exists():
        return shadow_process.read_events(upstream)
    events = shadow_process.read_events(legacy) if legacy.exists() else []
    if events:
        print(f"WARN: {repo_path.name}: only legacy log present; "
              f"events pending classification to upstream doctrine.", file=sys.stderr)
    return events


def sweep_one(repo: dict) -> list[dict]:
    """Run per-repo threshold check; return unaddressed events tagged with source_repo."""
    repo_path = Path(repo["path"])
    if not repo_path.exists():
        print(f"WARN: repo path not found: {repo_path}", file=sys.stderr)
        return []
    if not repo.get("enabled", True):
        return []

    result = subprocess.run(
        CHECK_SCRIPT,
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode not in (0, 10):
        print(f"WARN: {repo['name']} check failed rc={result.returncode}: {result.stderr}",
              file=sys.stderr)
        return []

    events = read_repo_shadow(repo_path)
    unaddressed = [e for e in events if not e.get("addressed", False)]
    for e in unaddressed:
        e["source_repo"] = repo["name"]
    return unaddressed


def sweep_all(config: dict) -> list[dict]:
    """Iterate enabled repos; return pooled unaddressed events."""
    pooled: list[dict] = []
    for repo in config["repos"]:
        pooled.extend(sweep_one(repo))
    return pooled


def build_issue_body(events: list[dict], threshold: int) -> str:
    by_repo: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_repo[e.get("source_repo", "<unknown>")].append(e)

    total_sev = sum(e["severity"] for e in events)
    lines = [
        "## Cross-repo Process Shadow Genome — pooled threshold breach",
        "",
        f"Severity sum: **{total_sev}** (threshold {threshold})",
        f"Total events: {len(events)}",
        f"Repos affected: {len(by_repo)}",
        f"Sweep ts: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
    ]

    for repo_name in sorted(by_repo):
        repo_events = by_repo[repo_name]
        repo_sev = sum(e["severity"] for e in repo_events)
        lines.append(f"### {repo_name} — {len(repo_events)} events, sev {repo_sev}")
        lines.append("")
        etype_counts = Counter(e["event_type"] for e in repo_events)
        for etype, n in etype_counts.most_common():
            lines.append(f"- `{etype}`: {n}")
        lines.append("")
        for e in repo_events:
            lines.append(
                f"  - `{e['id'][:12]}...` {e['ts']} `{e['skill']}` / "
                f"`{e['event_type']}` / sev {e['severity']}"
            )
        lines.append("")

    lines.append("### Next action")
    lines.append("")
    lines.append(
        "Run `/qor-remediate` in the originating repo(s). Events will be flipped "
        "`addressed=true` with this issue URL automatically after issue creation "
        "(via `create_shadow_issue.py --flip-only`)."
    )
    return "\n".join(lines)


def dispatch(body: str, meta_repo: str, event_count: int, sev_sum: int, dry_run: bool = False) -> str | None:
    title = (f"[qor-shadow] Cross-repo threshold breach — "
             f"{event_count} events, sev {sev_sum}")
    if dry_run:
        print(f"--- DRY RUN ---\nTitle: {title}\nRepo: {meta_repo}\n\n{body}")
        return None
    result = subprocess.run(
        ["gh", "issue", "create",
         "--repo", meta_repo,
         "--title", title,
         "--body-file", "-",
         "--label", "qor-shadow"],
        input=body,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise SystemExit(f"gh issue create failed:\n{result.stderr}")
    return result.stdout.strip().splitlines()[-1]


def flip_per_repo(url: str, events: list[dict], config: dict) -> dict:
    """For each source_repo, subprocess create_shadow_issue.py --flip-only.

    Returns {repo_name: flipped_count} summary.
    """
    by_repo: dict[str, list[str]] = defaultdict(list)
    for e in events:
        by_repo[e["source_repo"]].append(e["id"])

    repo_lookup = {r["name"]: r for r in config["repos"]}
    summary: dict[str, int] = {}

    for repo_name, ids in by_repo.items():
        repo = repo_lookup.get(repo_name)
        if not repo:
            print(f"WARN: no config entry for source_repo {repo_name}", file=sys.stderr)
            continue
        result = subprocess.run(
            [*ISSUE_SCRIPT,
             "--flip-only", url,
             "--events", ",".join(ids)],
            cwd=str(repo["path"]),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"WARN: flip failed for {repo_name}: {result.stderr}", file=sys.stderr)
            summary[repo_name] = 0
        else:
            # Parse "Flipped N event(s)..." from stdout
            first = result.stdout.strip().splitlines()[0] if result.stdout else ""
            try:
                n = int(first.split()[1])
            except (IndexError, ValueError):
                n = len(ids)
            summary[repo_name] = n
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--config", type=Path, help="Override config path")
    ap.add_argument("--dry-run", action="store_true",
                    help="Sweep + pool; print summary; no issue, no flip")
    ap.add_argument("--config-show", action="store_true",
                    help="Print resolved config and exit")
    args = ap.parse_args()

    config = load_config(args.config)

    if args.config_show:
        print(json.dumps(config, indent=2))
        return 0

    pooled = sweep_all(config)
    if not pooled:
        print("No unaddressed events across any repo.")
        return 0

    sev_sum = sum(e["severity"] for e in pooled)
    threshold = config["threshold"]

    print(f"Pooled: {len(pooled)} events, severity sum {sev_sum} (threshold {threshold})")

    if sev_sum < threshold:
        print("Below threshold; no action.")
        return 0

    body = build_issue_body(pooled, threshold)
    url = dispatch(body, config["meta_repo"], len(pooled), sev_sum, dry_run=args.dry_run)

    if args.dry_run:
        return 0

    print(f"Consolidated issue created: {url}")
    summary = flip_per_repo(url, pooled, config)
    for name, n in summary.items():
        print(f"  {name}: flipped {n} event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
