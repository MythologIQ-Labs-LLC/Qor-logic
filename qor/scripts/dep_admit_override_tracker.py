"""Phase 105: dep-admit-override re-evaluation tracker.

Scans META_LEDGER for `**Dependency admission override**:` lines and emits a
markdown (or CSV) table showing which overrides are due for 30-day re-check.

Operator-invokable only (no CI wiring). Companion to dependency_admission_lint.py.
Doctrine: qor/references/doctrine-dependency-admission.md.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

from qor.scripts import _dep_admit_common as common


DEFAULT_FOLLOW_UP_DAYS = 30


@dataclasses.dataclass(frozen=True)
class TrackerRow:
    package: str
    version: str
    entry_ts: datetime
    age_days: int
    status: str  # "due" | "pending"
    justification: str


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def build_rows(
    ledger_text: str, follow_up_days: int = DEFAULT_FOLLOW_UP_DAYS
) -> list[TrackerRow]:
    """Parse overrides + compute status. Pure function."""
    overrides = common.parse_override_entries(ledger_text)
    now = _now_utc()
    rows: list[TrackerRow] = []
    for o in overrides:
        age_days = (now - o.entry_ts).days
        status = "due" if age_days >= follow_up_days else "pending"
        rows.append(
            TrackerRow(
                package=o.package,
                version=o.version,
                entry_ts=o.entry_ts,
                age_days=age_days,
                status=status,
                justification=o.justification,
            )
        )
    return rows


def apply_filter(rows: list[TrackerRow], filter_state: str) -> list[TrackerRow]:
    """Filter rows by status. filter_state in {'all', 'due', 'pending'}."""
    if filter_state == "all":
        return list(rows)
    return [r for r in rows if r.status == filter_state]


def render_markdown(rows: list[TrackerRow]) -> str:
    headers = ["Package", "Version", "Entry timestamp", "Age (days)", "Status", "Justification"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        ts = r.entry_ts.isoformat().replace("+00:00", "Z")
        lines.append(
            f"| {r.package} | {r.version} | {ts} | {r.age_days} | {r.status} | {r.justification} |"
        )
    return "\n".join(lines) + "\n"


def render_csv(rows: list[TrackerRow]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["package", "version", "entry_ts", "age_days", "status", "justification"])
    for r in rows:
        writer.writerow([
            r.package,
            r.version,
            r.entry_ts.isoformat().replace("+00:00", "Z"),
            r.age_days,
            r.status,
            r.justification,
        ])
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", default="docs/META_LEDGER.md")
    p.add_argument("--format", choices=["markdown", "csv"], default="markdown")
    p.add_argument("--filter", dest="filter_state", choices=["all", "due", "pending"], default="all")
    p.add_argument("--since", default=None, help="YYYY-MM-DD; only entries newer than this")
    p.add_argument("--follow-up-days", type=int, default=DEFAULT_FOLLOW_UP_DAYS)
    args = p.parse_args(argv)

    ledger_path = Path(args.ledger).resolve()
    if not ledger_path.is_file():
        print(f"ERROR: ledger not found at {ledger_path}", file=sys.stderr)
        return 2
    text = ledger_path.read_text(encoding="utf-8")

    rows = build_rows(text, follow_up_days=args.follow_up_days)
    if args.since:
        since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        rows = [r for r in rows if r.entry_ts >= since_dt]
    rows = apply_filter(rows, args.filter_state)

    output = render_csv(rows) if args.format == "csv" else render_markdown(rows)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
