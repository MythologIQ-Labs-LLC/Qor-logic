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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.governance_index")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    findings = check_index_drift(Path(args.repo_root))
    for f in findings:
        print(f"WARN [governance-index/{f.kind}]: {f.path} -- {f.reason}", file=sys.stderr)
    return 1 if findings else 0  # WARN-only V1: non-zero signals drift, callers wrap with `|| true`


if __name__ == "__main__":
    raise SystemExit(main())
