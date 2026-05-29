"""Phase 46 (#40): parse FEATURE_INDEX.md markdown table, tally by status, and
detect outside-scope regressions vs a prior-seal snapshot.

V1 surfaces row counts and the list of entries that flipped from `verified`
to `unverified` since the prior snapshot. Deep verification (does the test
actually exercise this feature?) remains operator judgment per the SG-035
acceptance question; this helper only counts what FEATURE_INDEX claims.

Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

STATUS_VALUES = ("verified", "unverified", "n/a")
_TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
_SEPARATOR = re.compile(r"^\|\s*[:-]+\s*(\|\s*[:-]+\s*)+\|\s*$")


@dataclass(frozen=True)
class IndexSummary:
    total: int = 0
    verified: int = 0
    unverified: int = 0
    n_a: int = 0
    newly_unverified: tuple[str, ...] = ()
    missing_index: bool = False


def parse_index_rows(text: str) -> list[dict[str, str]]:
    """Parse a FEATURE_INDEX markdown table into row dicts.

    Expects column order: ID | Name | Source-of-truth | Doc citation | Test path | Verification status
    Tolerates extra columns at the end; trims whitespace.
    """
    rows: list[dict[str, str]] = []
    in_table = False
    header: list[str] = []
    for line in text.splitlines():
        line_stripped = line.rstrip()
        if not _TABLE_ROW.match(line_stripped):
            in_table = False
            continue
        if _SEPARATOR.match(line_stripped):
            in_table = bool(header)
            continue
        cells = [c.strip() for c in line_stripped.strip("|").split("|")]
        if not header:
            header = [c.lower().strip() for c in cells]
            continue
        if not in_table:
            continue
        if len(cells) < len(header):
            continue
        row = dict(zip(header, cells[: len(header)]))
        status = _normalize_status(row.get("verification status", ""))
        if status is None:
            continue
        row["status"] = status
        row["id"] = row.get("id", "")
        rows.append(row)
    return rows


def _normalize_status(text: str) -> str | None:
    cleaned = text.strip().lower()
    if cleaned in STATUS_VALUES:
        return cleaned
    return None


def tally(
    repo_root: str | Path,
    index_path: str = "docs/FEATURE_INDEX.md",
    prior_snapshot: dict[str, str] | None = None,
) -> IndexSummary:
    path = Path(repo_root) / index_path
    if not path.exists():
        return IndexSummary(missing_index=True)
    rows = parse_index_rows(path.read_text(encoding="utf-8"))
    counts = {"verified": 0, "unverified": 0, "n/a": 0}
    for row in rows:
        counts[row["status"]] += 1
    newly: list[str] = []
    if prior_snapshot:
        current = {row["id"]: row["status"] for row in rows if row["id"]}
        for entry_id, prior_status in prior_snapshot.items():
            if prior_status != "verified":
                continue
            cur = current.get(entry_id)
            if cur == "unverified":
                newly.append(entry_id)
    return IndexSummary(
        total=len(rows),
        verified=counts["verified"],
        unverified=counts["unverified"],
        n_a=counts["n/a"],
        newly_unverified=tuple(newly),
    )


def write_seal_snapshot(
    repo_root: str | Path,
    sid: str,
    rows: list[dict[str, str]],
) -> Path:
    """Write a session-scoped snapshot for the next seal to diff against."""
    snap_dir = Path(repo_root) / ".qor" / "feature_index_snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"{sid}.json"
    snap = {row["id"]: row["status"] for row in rows if row.get("id")}
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return path


def read_seal_snapshot(repo_root: str | Path, sid: str) -> dict[str, str]:
    path = Path(repo_root) / ".qor" / "feature_index_snapshots" / f"{sid}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    """FEATURE_INDEX regression ABORT (Phase 114; GH #155/#40).

    Exits non-zero when an outside-scope ``verified -> unverified`` regression is
    detected against the prior-seal snapshot. ``--warn-only`` downgrades to a
    print-and-pass (the graduated-rollout escape, mirroring the WARN-only
    convention of dod_check / ci_coverage_lint). A missing FEATURE_INDEX is a
    skip (rc 0), never a crash.
    """
    parser = argparse.ArgumentParser(prog="qor.scripts.feature_index_verify")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--index-path", default="docs/FEATURE_INDEX.md")
    parser.add_argument("--snapshot", default=None,
                        help="session id of a prior-seal snapshot to diff against")
    parser.add_argument("--warn-only", action="store_true",
                        help="print regressions but exit 0 (graduated rollout)")
    args = parser.parse_args(argv)

    prior = read_seal_snapshot(args.repo_root, args.snapshot) if args.snapshot else None
    summary = tally(args.repo_root, args.index_path, prior)

    if summary.missing_index:
        print(f"feature_index: skip (no {args.index_path})")
        return 0

    print(
        f"feature_index: total={summary.total} verified={summary.verified} "
        f"unverified={summary.unverified} n/a={summary.n_a}"
    )
    if summary.newly_unverified:
        for fid in summary.newly_unverified:
            print(f"  REGRESSION [verified->unverified] {fid}")
        if args.warn_only:
            print("feature_index: WARN-only; not aborting")
            return 0
        print("feature_index: ABORT (outside-scope regression)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
