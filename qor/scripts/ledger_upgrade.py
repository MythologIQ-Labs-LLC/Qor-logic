#!/usr/bin/env python3
"""Phase 179 (GH #271 V1 slice): one-command ledger recovery + versioned format.

A consumer ledger that goes format-DAMAGED after a toolkit update previously
required a two-step manual migrate (never in-place) plus a separate verify.
``upgrade`` orchestrates the Phase 170 migrator (`ledger_migrate.migrate`:
markup moves, math does not) and the post-anchor acceptance verifier
(`ledger_hash.verify_post_anchor`: disclosed pre-anchor failures are a legal
healthy state per GH #199) under a swap-on-success-only contract:

- migrate into a sibling temp file,
- stamp the schema-version marker,
- verify the TEMP,
- atomically replace the original only when acceptance passes;
  any residual failure leaves the original byte-untouched and exits 1.

The marker (``<!-- qor:meta-ledger-schema=1 -->``) makes the format
machine-detectable; an absent marker reads as version 0 (legacy). Stdlib +
in-repo reuse only.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1
_MARKER_RE = re.compile(r"<!--\s*qor:meta-ledger-schema=(\d+)\s*-->")
_MARKER_LINE = f"<!-- qor:meta-ledger-schema={SCHEMA_VERSION} -->"


def schema_version(text: str) -> int:
    """The ledger's declared schema version; 0 when no marker (legacy)."""
    match = _MARKER_RE.search(text)
    return int(match.group(1)) if match else 0


def ensure_marker(text: str) -> str:
    """Insert the version marker after the first line; idempotent."""
    if _MARKER_RE.search(text):
        return text
    head, sep, rest = text.partition("\n")
    return f"{head}{sep}{_MARKER_LINE}\n{rest}"


@dataclass(frozen=True)
class UpgradeReport:
    stats: dict
    verify_rc: int
    swapped: bool


def upgrade(ledger_path: Path, dry_run: bool = False) -> UpgradeReport:
    """Migrate + verify + swap-on-success-only. Original untouched on failure."""
    from qor.scripts import ledger_hash, ledger_migrate

    ledger_path = Path(ledger_path)
    text = ledger_path.read_text(encoding="utf-8")
    migrated, stats = ledger_migrate.migrate(text)
    migrated = ensure_marker(migrated)

    temp = ledger_path.with_suffix(ledger_path.suffix + ".upgrade.tmp")
    try:
        temp.write_text(migrated, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            verify_rc = ledger_hash.verify_post_anchor(temp)
        if verify_rc == 0 and not dry_run and migrated != text:
            os.replace(temp, ledger_path)
            return UpgradeReport(stats, verify_rc, swapped=True)
        return UpgradeReport(stats, verify_rc, swapped=False)
    finally:
        temp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ledger", type=Path, default=Path("docs/META_LEDGER.md"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    report = upgrade(args.ledger, dry_run=args.dry_run)
    counts = " ".join(f"{k}={v}" for k, v in sorted(report.stats.items()))
    if report.verify_rc != 0:
        print(f"FAIL: post-anchor verification rejected the upgraded form; "
              f"original untouched ({counts})")
        return 1
    state = "dry-run (nothing written)" if args.dry_run else (
        "upgraded" if report.swapped else "already canonical")
    print(f"OK: {state}; schema={SCHEMA_VERSION} ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
