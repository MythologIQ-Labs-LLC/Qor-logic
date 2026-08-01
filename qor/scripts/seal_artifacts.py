"""Seal-artifact generators: README badges + SYSTEM_STATE header (Phase 164).

Generate-not-assert (research entry #378, rec 2): substantiate Step 6 runs
`--write` to regenerate the presentation artifacts deterministically; Step 6.5
and CI run `--check` to gate on currency. Pure renderers; atomic writes
(tmp + os.replace, same discipline as changelog_stamp.apply_stamp). Counting
and badge parsing are reused from badge_currency so check and write consume the
same declared repository layout.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import tempfile
from pathlib import Path

from qor.scripts import badge_currency

# Badge kind -> the trailing words the shields.io label carries after the count.
_BADGE_SUFFIXES = {
    "tests": "passing",
    "skills": "",
    "agents": "",
    "doctrines": "",
    "ledger": "entries sealed",
}


def _badge_forms(key: str, suffix: str) -> tuple[str, str, str, str]:
    """Return (url_pattern, url_template, alt_pattern, alt_template) for a kind."""
    label = key.capitalize()
    url_tail = "%20" + suffix.replace(" ", "%20") if suffix else ""
    alt_tail = " " + suffix if suffix else ""
    return (
        rf"badge/{label}-\d+{url_tail}",
        f"badge/{label}-{{n}}{url_tail}",
        rf'alt="{label}: \d+{alt_tail}"',
        f'alt="{label}: {{n}}{alt_tail}"',
    )


_BADGE_FORMS: dict[str, tuple[str, str, str, str]] = {
    key: _badge_forms(key, suffix) for key, suffix in _BADGE_SUFFIXES.items()
}

_SEAL_RE = re.compile(r"^### Entry #\d+: SESSION SEAL -- Phase (\d+)", re.MULTILINE)
_HEADER_PHASE_RE = re.compile(r"^(\*\*Phase\*\*:\s*Phase )(\d+)", re.MULTILINE)
_SNAPSHOT_RE = re.compile(
    r"^(\*\*Snapshot\*\*:\s*)(\d{4}-\d{2}-\d{2})", re.MULTILINE
)


def render_readme_badges(text: str, counts: dict[str, int]) -> str:
    """Substitute badge counts into README text; unknown badges pass through."""
    for key, count in counts.items():
        forms = _BADGE_FORMS.get(key)
        if forms is None:
            continue
        url_re, url_fmt, alt_re, alt_fmt = forms
        text = re.sub(url_re, url_fmt.format(n=count), text)
        text = re.sub(alt_re, alt_fmt.format(n=count), text)
    return text


def render_system_state_header(text: str, phase: int, snapshot: str) -> str:
    """Rewrite the Snapshot date and Phase number; preserve all narrative."""
    _dt.date.fromisoformat(snapshot)
    if not _HEADER_PHASE_RE.search(text) or not _SNAPSHOT_RE.search(text):
        raise ValueError(
            "SYSTEM_STATE header markers missing: need '**Snapshot**: YYYY-MM-DD' "
            "and '**Phase**: Phase N' lines"
        )
    text = _SNAPSHOT_RE.sub(
        lambda match: f"{match.group(1)}{snapshot}", text, count=1
    )
    text = _HEADER_PHASE_RE.sub(
        lambda match: f"{match.group(1)}{phase}", text, count=1
    )
    return text


def collect_counts(
    repo_root: Path,
    skip_tests: bool = False,
    *,
    layout: badge_currency.BadgeLayout = badge_currency.DEFAULT_LAYOUT,
) -> dict[str, int]:
    """Return current-truth counts via badge_currency counters."""
    counts = badge_currency.count_by_layout(repo_root, layout)
    counts["ledger"] = badge_currency.count_ledger_entries(
        repo_root / "docs" / "META_LEDGER.md"
    )
    if not skip_tests:
        counts["tests"] = badge_currency.count_tests(repo_root)
    return counts


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(tmp, path)


def update_files(
    repo_root: Path,
    phase: int,
    snapshot: str,
    counts: dict[str, int],
    dry_run: bool = False,
) -> list[str]:
    """Regenerate README badges and the SYSTEM_STATE header.

    `counts` is required: the writer renders truth its caller resolved under a
    declared layout, so it never re-derives a layout of its own.
    """
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
    sealed = [int(match) for match in _SEAL_RE.findall(ledger)]
    header = _HEADER_PHASE_RE.search(text)
    snapshot = _SNAPSHOT_RE.search(text)
    if header is None or snapshot is None:
        return ["header: SYSTEM_STATE Snapshot/Phase markers missing"]
    if sealed:
        latest = max(sealed)
        got = int(header.group(2))
        if not latest <= got <= latest + 1:
            out.append(
                f"header: SYSTEM_STATE records Phase {got}, latest seal is Phase {latest}"
            )
    try:
        _dt.date.fromisoformat(snapshot.group(2))
    except ValueError:
        out.append(
            f"header: snapshot date {snapshot.group(2)!r} is not a valid ISO date"
        )
    return out


def check_files(
    repo_root: Path,
    skip_tests: bool = False,
    *,
    layout: badge_currency.BadgeLayout = badge_currency.DEFAULT_LAYOUT,
) -> list[str]:
    """Return badge and header mismatches; an empty list means current."""
    ledger = repo_root / "docs" / "META_LEDGER.md"
    mismatches = badge_currency.check_currency(
        repo_root, ledger, skip_tests=skip_tests, layout=layout
    )
    mismatches.extend(_check_header(repo_root))
    return mismatches


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--phase", type=int, help="phase number for --write")
    parser.add_argument("--snapshot", help="YYYY-MM-DD snapshot date for --write")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="skip the pytest --collect-only Tests count",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --write: render everything, preview the write set, mutate nothing",
    )
    badge_currency.add_layout_args(parser)
    return parser


def _run_write(args: argparse.Namespace, layout: badge_currency.BadgeLayout) -> int:
    """Regenerate the seal artifacts and report the write set."""
    changed = update_files(
        args.repo_root,
        args.phase,
        args.snapshot,
        counts=collect_counts(
            args.repo_root, skip_tests=args.skip_tests, layout=layout
        ),
        dry_run=args.dry_run,
    )
    for changed_path in changed:
        print(
            f"[dry] would write {changed_path}"
            if args.dry_run
            else f"regenerated: {changed_path}"
        )
    if not changed:
        print("OK: seal artifacts already current")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.write and (args.phase is None or args.snapshot is None):
        parser.error("--write requires --phase and --snapshot")
    layout = badge_currency.layout_from_args(args)

    try:
        if args.write:
            return _run_write(args, layout)
        mismatches = check_files(
            args.repo_root, skip_tests=args.skip_tests, layout=layout
        )
    except (badge_currency.BadgeLayoutError, OSError, RuntimeError) as exc:
        print(f"FAIL: seal-artifact truth could not be resolved: {exc}")
        return 1

    if mismatches:
        print("FAIL: seal-artifact currency mismatch:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return 1
    print("OK: seal artifacts current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
