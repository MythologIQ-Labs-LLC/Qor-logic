"""Phase 105: dependency-admission cooling-period lint.

Walks `requirements-release.txt` diff vs a base ref, queries the PyPI Warehouse
API for upload time, and reports any newly-added or version-bumped entry whose
upload is within the cooling-period window (default 14 days) absent a matching
override in `docs/META_LEDGER.md`.

Operator-invokable + CI-invokable (WARN-only in pr-dependency-review.yml at V1).
Doctrine: qor/references/doctrine-dependency-admission.md.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from qor.scripts import _dep_admit_common as common


DEFAULT_THRESHOLD_DAYS = 14
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
DEFAULT_TIMEOUT = 5
_USER_AGENT = "qor-logic/dependency-admission-lint"


@dataclasses.dataclass(frozen=True)
class BumpReport:
    name: str
    old_version: str | None
    new_version: str
    age_days: int
    status: str  # "clean", "violation", "override"


@dataclasses.dataclass(frozen=True)
class LintResult:
    exit_code: int
    bumps: list[BumpReport]
    violations: list[common.Bump]
    network_errors: list[str]


class NetworkError(RuntimeError):
    """Raised when PyPI Warehouse query fails after all retries."""


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _fetch_pypi_upload_time(
    name: str, version: str, retries: int = DEFAULT_RETRIES, delay: int = DEFAULT_RETRY_DELAY
) -> datetime:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                data = json.load(resp)
            upload = data["urls"][0]["upload_time_iso_8601"]
            return common._parse_iso_utc(upload)
        except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)
    raise NetworkError(f"PyPI query failed after {retries} attempts: {last_err}")


def run_lint(
    *,
    current_lockfile_text: str,
    base_lockfile_text: str | None,
    ledger_text: str,
    threshold_days: int = DEFAULT_THRESHOLD_DAYS,
) -> LintResult:
    """Pure function entry point: returns LintResult, no I/O beyond PyPI HTTP."""
    current = common.parse_lockfile_entries(current_lockfile_text)
    base = (
        common.parse_lockfile_entries(base_lockfile_text)
        if base_lockfile_text is not None
        else []
    )
    bumps = common.diff_lockfile_against_base(current, base)
    overrides = common.parse_override_entries(ledger_text)
    override_keys = {(o.package, o.version) for o in overrides}

    now = _now_utc()
    reports: list[BumpReport] = []
    violations: list[common.Bump] = []
    network_errors: list[str] = []

    for bump in bumps:
        try:
            upload_time = _fetch_pypi_upload_time(bump.name, bump.new_version)
        except NetworkError as e:
            network_errors.append(f"{bump.name}@{bump.new_version}: {e}")
            continue
        age_days = (now - upload_time).days
        if age_days >= threshold_days:
            status = "clean"
        elif (bump.name, bump.new_version) in override_keys:
            status = "override"
        else:
            status = "violation"
            violations.append(bump)
        reports.append(
            BumpReport(
                name=bump.name,
                old_version=bump.old_version,
                new_version=bump.new_version,
                age_days=age_days,
                status=status,
            )
        )

    if network_errors:
        exit_code = 2
    elif violations:
        exit_code = 1
    else:
        exit_code = 0

    return LintResult(
        exit_code=exit_code,
        bumps=reports,
        violations=violations,
        network_errors=network_errors,
    )


def _render_markdown(result: LintResult) -> str:
    if not result.bumps:
        return "_No lockfile bumps detected._\n"
    lines = ["| Package | Version | Age (days) | Status |", "|---|---|---|---|"]
    for r in result.bumps:
        lines.append(f"| {r.name} | {r.new_version} | {r.age_days} | {r.status} |")
    return "\n".join(lines) + "\n"


def _git_show(ref: str, path: str, repo_root: Path) -> str | None:
    """git show <ref>:<path>. Returns None if ref/path missing."""
    try:
        out = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout
    except subprocess.CalledProcessError:
        return None


def _resolve_base_ref(repo_root: Path) -> str:
    """Default base: merge-base origin/main HEAD."""
    out = subprocess.run(
        ["git", "merge-base", "origin/main", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", default=None)
    p.add_argument("--lockfile", default="requirements-release.txt")
    p.add_argument("--ledger", default="docs/META_LEDGER.md")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--threshold-days", type=int, default=DEFAULT_THRESHOLD_DAYS)
    args = p.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    current_path = repo_root / args.lockfile
    if not current_path.is_file():
        print(f"ERROR: lockfile not found at {current_path}", file=sys.stderr)
        return 2
    current_text = current_path.read_text(encoding="utf-8")
    base_ref = args.base or _resolve_base_ref(repo_root)
    base_text = _git_show(base_ref, args.lockfile, repo_root)
    ledger_path = repo_root / args.ledger
    ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.is_file() else ""

    result = run_lint(
        current_lockfile_text=current_text,
        base_lockfile_text=base_text,
        ledger_text=ledger_text,
        threshold_days=args.threshold_days,
    )

    for err in result.network_errors:
        print(f"ERROR: PyPI query for {err}", file=sys.stderr)
    for v in result.violations:
        report = next(b for b in result.bumps if b.name == v.name and b.new_version == v.new_version)
        print(
            f"WARN: {v.name}@{v.new_version} uploaded {report.age_days} days ago "
            f"(within {args.threshold_days}d window); override absent",
            file=sys.stderr,
        )
    print(_render_markdown(result))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
