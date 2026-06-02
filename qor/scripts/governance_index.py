"""Governance Index drift checker (Phase 112, #140).

Parses the hand-edited `docs/GOVERNANCE_INDEX.md` 6-tier map and surfaces drift,
WARN-only in V1:

- ``stale-tier1``: the index's ``Last Reviewed`` date predates the newest sealed
  META_LEDGER entry (Tier-1 freshness contract).
- ``unregistered``: a governance doc present on disk is not named in any tier
  table.
- ``missing-index``: the index file itself is absent (legal next: ``qor-logic seed``).

Full Tier 3->6 / Tier 4->6 archival enforcement, the ``/qor-validate`` ledger
cross-check, and a hard ``/qor-implement`` block on stale Tier 1 are deferred to
V2. Per ``qor/references/doctrine-governance-index.md``.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_INDEX_REL = "docs/GOVERNANCE_INDEX.md"
_LAST_REVIEWED_RE = re.compile(r"\*\*Last Reviewed\*\*:\s*(\d{4}-\d{2}-\d{2})")
_SEAL_DATE_RE = re.compile(r"### Entry #\d+: SESSION SEAL.*?\*\*Timestamp\*\*:\s*(\d{4}-\d{2}-\d{2})", re.DOTALL)
_BACKTICK_PATH_RE = re.compile(r"`([^`]+\.md)`")
# Governance docs not required to carry their own index row.
_INDEX_SCAN_EXEMPT = {"docs/GOVERNANCE_INDEX.md"}


@dataclass(frozen=True)
class IndexFinding:
    kind: str
    path: str
    reason: str


def _last_reviewed(text: str) -> date | None:
    m = _LAST_REVIEWED_RE.search(text)
    return date.fromisoformat(m.group(1)) if m else None


def _latest_seal_date(ledger_text: str) -> date | None:
    dates = [date.fromisoformat(d) for d in _SEAL_DATE_RE.findall(ledger_text)]
    return max(dates) if dates else None


def _registered_paths(index_text: str) -> set[str]:
    return set(_BACKTICK_PATH_RE.findall(index_text))


def _governance_docs(base: Path) -> set[str]:
    """Repo-relative governance docs: root-level *.md plus docs/*.md (non-recursive)."""
    found: set[str] = set()
    for rel_dir in (".", "docs"):
        d = base / rel_dir
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            found.add(p.relative_to(base).as_posix())
    return found


def _is_registered(rel: str, registered: set[str]) -> bool:
    """A doc is registered if its path (or a glob row covering it) appears."""
    if rel in registered:
        return True
    name = Path(rel).name
    for reg in registered:
        if "*" in reg and re.fullmatch(reg.replace("*", ".*"), rel):
            return True
        if reg.endswith(name):
            return True
    return False


def check_index_drift(base: Path) -> list[IndexFinding]:
    base = Path(base)
    index_path = base / _INDEX_REL
    if not index_path.is_file():
        return [IndexFinding("missing-index", _INDEX_REL, "governance index absent; run `qor-logic seed`")]
    index_text = index_path.read_text(encoding="utf-8", errors="replace")
    findings: list[IndexFinding] = []

    reviewed = _last_reviewed(index_text)
    ledger = base / "docs" / "META_LEDGER.md"
    seal_date = _latest_seal_date(ledger.read_text(encoding="utf-8", errors="replace")) if ledger.is_file() else None
    if seal_date is not None and (reviewed is None or reviewed < seal_date):
        findings.append(IndexFinding("stale-tier1", _INDEX_REL, f"Last Reviewed {reviewed} predates latest seal {seal_date}"))

    registered = _registered_paths(index_text)
    for rel in sorted(_governance_docs(base)):
        if rel in _INDEX_SCAN_EXEMPT:
            continue
        if not _is_registered(rel, registered):
            findings.append(IndexFinding("unregistered", rel, "governance doc not named in any tier table"))
    return findings


_ADVANCE_RE = re.compile(r"(\*\*Last Reviewed\*\*:\s*)\d{4}-\d{2}-\d{2}")
_TIER3_HEADING_RE = re.compile(r"^##\s+Tier\s*3\b.*$", re.MULTILINE)
_NEXT_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
_PHASE_TOKEN_RE = re.compile(r"phase\s*(\d+)", re.IGNORECASE)


def advance_last_reviewed(base: Path, date_str: str) -> bool:
    """Rewrite every `**Last Reviewed**: <date>` line to date_str. The only
    index mutation. Returns True iff the file content changed."""
    index_path = Path(base) / _INDEX_REL
    if not index_path.is_file():
        return False
    text = index_path.read_text(encoding="utf-8", errors="replace")
    new = _ADVANCE_RE.sub(rf"\g<1>{date_str}", text)
    if new == text:
        return False
    index_path.write_text(new, encoding="utf-8")
    return True


def _tier3_region(index_text: str) -> str:
    """The text between the `## Tier 3` heading and the next `## ` heading."""
    m = _TIER3_HEADING_RE.search(index_text)
    if not m:
        return ""
    rest = index_text[m.end():]
    nxt = _NEXT_HEADING_RE.search(rest)
    return rest[: nxt.start()] if nxt else rest


def _tier3_unarchived(index_text: str, ledger_text: str) -> list[IndexFinding]:
    """A Tier 3 'Active Initiative' row that names a `phase <N>` already sealed
    in the ledger should have been archived to Tier 6 (forward guard; no
    auto-mutation)."""
    region = _tier3_region(index_text)
    findings: list[IndexFinding] = []
    for n in sorted({int(x) for x in _PHASE_TOKEN_RE.findall(region)}):
        if re.search(rf"SESSION SEAL\s*--\s*Phase\s*{n}\b", ledger_text):
            findings.append(IndexFinding(
                "tier3-unarchived", _INDEX_REL,
                f"Tier 3 names phase {n} but it is already SESSION-SEALed; archive to Tier 6",
            ))
    return findings


def _ledger_text(base: Path) -> str:
    ledger = Path(base) / "docs" / "META_LEDGER.md"
    return ledger.read_text(encoding="utf-8", errors="replace") if ledger.is_file() else ""


def enforce_at_seal(base: Path, seal_date: str) -> list[IndexFinding]:
    """Substantiate-time enforcement: advance Last Reviewed to the seal date,
    then return the residual drift that must FAIL-CLOSE the seal (`unregistered`
    + forward-guard `tier3-unarchived`). Absent index returns `missing-index`
    so the caller records a Phase 75 disclosed-skip rather than aborting."""
    base = Path(base)
    if not (base / _INDEX_REL).is_file():
        return [IndexFinding("missing-index", _INDEX_REL, "governance index absent; run `qor-logic seed`")]
    advance_last_reviewed(base, seal_date)
    index_text = (base / _INDEX_REL).read_text(encoding="utf-8", errors="replace")
    residual = [f for f in check_index_drift(base) if f.kind != "stale-tier1"]
    residual.extend(_tier3_unarchived(index_text, _ledger_text(base)))
    return residual


def cross_check_index_against_ledger(base: Path) -> list[IndexFinding]:
    """Validate-time read-only cross-check: `stale-tier1` (Last Reviewed vs
    latest sealed entry) + `tier3-unarchived` (Tier 3 row naming a sealed
    phase). No mutation. Absent index returns `missing-index`."""
    base = Path(base)
    if not (base / _INDEX_REL).is_file():
        return [IndexFinding("missing-index", _INDEX_REL, "governance index absent; run `qor-logic seed`")]
    index_text = (base / _INDEX_REL).read_text(encoding="utf-8", errors="replace")
    findings = [f for f in check_index_drift(base) if f.kind == "stale-tier1"]
    findings.extend(_tier3_unarchived(index_text, _ledger_text(base)))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.governance_index")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--advance-last-reviewed", metavar="DATE", default=None,
                        help="rewrite Last Reviewed to DATE (YYYY-MM-DD)")
    parser.add_argument("--enforce", action="store_true",
                        help="fail-closed substantiate enforcement (requires --advance-last-reviewed)")
    parser.add_argument("--cross-check-ledger", action="store_true",
                        help="read-only validate cross-check (stale-tier1 + tier3-unarchived)")
    args = parser.parse_args(argv)
    root = Path(args.repo_root)

    if args.cross_check_ledger:
        findings = cross_check_index_against_ledger(root)
        return _emit(findings, fail_closed=True)
    if args.enforce:
        seal_date = args.advance_last_reviewed
        if not seal_date:
            print("ERROR: --enforce requires --advance-last-reviewed <date>", file=sys.stderr)
            return 2
        findings = enforce_at_seal(root, seal_date)
        return _emit(findings, fail_closed=True)
    if args.advance_last_reviewed:
        advance_last_reviewed(root, args.advance_last_reviewed)
        return 0
    findings = check_index_drift(root)
    return _emit(findings, fail_closed=False)


def _emit(findings: list[IndexFinding], *, fail_closed: bool) -> int:
    """Print findings; return exit code. A sole `missing-index` is a Phase 75
    disclosed-skip (exit 0) so absent-index hosts don't abort the seal."""
    if findings and all(f.kind == "missing-index" for f in findings):
        print("SKIP [governance-index]: index absent; recording gate_skipped_prerequisite_absent (Phase 75)")
        return 0
    for f in findings:
        label = "FAIL" if fail_closed else "WARN"
        print(f"{label} [governance-index/{f.kind}]: {f.path} -- {f.reason}", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
