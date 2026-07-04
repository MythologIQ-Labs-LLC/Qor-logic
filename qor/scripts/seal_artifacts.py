"""Seal-artifact generators: README badges + SYSTEM_STATE header (Phase 164).

Generate-not-assert (research entry #378, rec 2): substantiate Step 6 runs
`--write` to regenerate the presentation artifacts deterministically; Step 6.5
and CI run `--check` to gate on currency. Pure renderers; atomic writes
(tmp + os.replace, same discipline as changelog_stamp.apply_stamp). Counting
and badge parsing are reused from badge_currency -- check and write stay
un-complected across modules.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import tempfile
from pathlib import Path

from qor.scripts import badge_currency

# (url_pattern, url_replacement_fmt, alt_pattern, alt_replacement_fmt) per badge
_BADGE_FORMS: dict[str, tuple[str, str, str, str]] = {
    "tests": (
        r"badge/Tests-\d+%20passing", "badge/Tests-{n}%20passing",
        r'alt="Tests: \d+ passing"', 'alt="Tests: {n} passing"',
    ),
    "skills": (
        r"badge/Skills-\d+", "badge/Skills-{n}",
        r'alt="Skills: \d+"', 'alt="Skills: {n}"',
    ),
    "agents": (
        r"badge/Agents-\d+", "badge/Agents-{n}",
        r'alt="Agents: \d+"', 'alt="Agents: {n}"',
    ),
    "doctrines": (
        r"badge/Doctrines-\d+", "badge/Doctrines-{n}",
        r'alt="Doctrines: \d+"', 'alt="Doctrines: {n}"',
    ),
    "ledger": (
        r"badge/Ledger-\d+%20entries%20sealed", "badge/Ledger-{n}%20entries%20sealed",
        r'alt="Ledger: \d+ entries sealed"', 'alt="Ledger: {n} entries sealed"',
    ),
}

_SEAL_RE = re.compile(r"^### Entry #\d+: SESSION SEAL -- Phase (\d+)", re.MULTILINE)
_HEADER_PHASE_RE = re.compile(r"^(\*\*Phase\*\*:\s*Phase )(\d+)", re.MULTILINE)
_SNAPSHOT_RE = re.compile(r"^(\*\*Snapshot\*\*:\s*)(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def render_readme_badges(text: str, counts: dict[str, int]) -> str:
    """Substitute badge counts into README text; unknown badges pass through."""
    for key, n in counts.items():
        forms = _BADGE_FORMS.get(key)
        if forms is None:
            continue
        url_re, url_fmt, alt_re, alt_fmt = forms
        text = re.sub(url_re, url_fmt.format(n=n), text)
        text = re.sub(alt_re, alt_fmt.format(n=n), text)
    return text


def render_system_state_header(text: str, phase: int, snapshot: str) -> str:
    """Rewrite the Snapshot date and the Phase number; preserve all narrative."""
    _dt.date.fromisoformat(snapshot)
    if not _HEADER_PHASE_RE.search(text) or not _SNAPSHOT_RE.search(text):
        raise ValueError(
            "SYSTEM_STATE header markers missing: need '**Snapshot**: YYYY-MM-DD' "
            "and '**Phase**: Phase N' lines"
        )
    text = _SNAPSHOT_RE.sub(lambda m: f"{m.group(1)}{snapshot}", text, count=1)
    text = _HEADER_PHASE_RE.sub(lambda m: f"{m.group(1)}{phase}", text, count=1)
    return text


def collect_counts(repo_root: Path, skip_tests: bool = False) -> dict[str, int]:
    """Current-truth counts via badge_currency counters."""
    counts = {
        "skills": badge_currency.count_skills(repo_root),
        "agents": badge_currency.count_agents(repo_root),
        "doctrines": badge_currency.count_doctrines(repo_root),
        "ledger": badge_currency.count_ledger_entries(repo_root / "docs" / "META_LEDGER.md"),
    }
    if not skip_tests:
        counts["tests"] = badge_currency.count_tests(repo_root)
    return counts


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, path)


def update_files(
    repo_root: Path, phase: int, snapshot: str, counts: dict[str, int] | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Regenerate README badges + SYSTEM_STATE header; return paths that changed
    (or, with dry_run, that WOULD change -- rendering runs, writes are suppressed)."""
    if counts is None:
        counts = collect_counts(repo_root)
    changed: list[str] = []
    readme = repo_root / "README.md"
    before = readme.read_text(encoding="utf-8")
    after = render_readme_badges(before, counts)
    if after != before:
        if not dry_run:
            _write_atomic(readme, after)
        changed.append(str(readme))
    state = repo_root / "docs" / "SYSTEM_STATE.md"
    before = state.read_text(encoding="utf-8")
    after = render_system_state_header(before, phase=phase, snapshot=snapshot)
    if after != before:
        if not dry_run:
            _write_atomic(state, after)
        changed.append(str(state))
    return changed


def _check_header(repo_root: Path) -> list[str]:
    text = (repo_root / "docs" / "SYSTEM_STATE.md").read_text(encoding="utf-8")
    ledger = (repo_root / "docs" / "META_LEDGER.md").read_text(encoding="utf-8")
    out: list[str] = []
    sealed = [int(m) for m in _SEAL_RE.findall(ledger)]
    header = _HEADER_PHASE_RE.search(text)
    snapshot = _SNAPSHOT_RE.search(text)
    if header is None or snapshot is None:
        return ["header: SYSTEM_STATE Snapshot/Phase markers missing"]
    if sealed:
        latest = max(sealed)
        got = int(header.group(2))
        # mid-seal --write legitimately sets header to latest+1 (seal entry lands after)
        if not latest <= got <= latest + 1:
            out.append(f"header: SYSTEM_STATE records Phase {got}, latest seal is Phase {latest}")
    try:
        _dt.date.fromisoformat(snapshot.group(2))
    except ValueError:
        out.append(f"header: snapshot date {snapshot.group(2)!r} is not a valid ISO date")
    return out


def check_files(repo_root: Path, skip_tests: bool = False) -> list[str]:
    """Mismatch descriptions for badges + header; empty list == current."""
    ledger = repo_root / "docs" / "META_LEDGER.md"
    mismatches = badge_currency.check_currency(repo_root, ledger, skip_tests=skip_tests)
    mismatches.extend(_check_header(repo_root))
    return mismatches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--phase", type=int, help="phase number for --write")
    ap.add_argument("--snapshot", help="YYYY-MM-DD snapshot date for --write")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--skip-tests", action="store_true",
                    help="skip the pytest --collect-only Tests count (unit tests / fast paths)")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --write: render everything, preview the write set, mutate nothing")
    args = ap.parse_args(argv)
    if args.write:
        if args.phase is None or args.snapshot is None:
            ap.error("--write requires --phase and --snapshot")
        counts = collect_counts(args.repo_root, skip_tests=args.skip_tests)
        changed = update_files(args.repo_root, args.phase, args.snapshot,
                               counts=counts, dry_run=args.dry_run)
        for c in changed:
            print(f"[dry] would write {c}" if args.dry_run else f"regenerated: {c}")
        if not changed:
            print("OK: seal artifacts already current")
        return 0
    mismatches = check_files(args.repo_root, skip_tests=args.skip_tests)
    if mismatches:
        print("FAIL: seal-artifact currency mismatch:")
        for m in mismatches:
            print(f"  {m}")
        return 1
    print("OK: seal artifacts current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
