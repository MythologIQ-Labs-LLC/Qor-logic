#!/usr/bin/env python3
"""Phase 175 (GH #267): governance-DNA durability.

A consumer workspace lost its local-only governance DNA files to ``git clean``
and the loss went undetected for a month; the health gate classified the
result as UNINITIALIZED and routed toward bootstrap, which would have
destroyed the recoverable history. This module provides the durability layer:

- ``ensure_session_backup``: one snapshot of the five DNA files per session,
  triggered structurally from ``gate_chain.write_gate_artifact`` (fail-open;
  zero skill-prose bytes -- both big governance SKILL.md files sit within 70
  bytes of the 40 KB EXCEEDED budget).
- ``restore``: no-clobber copy-back (a restore must never silently destroy
  state NEWER than the snapshot; ``force=True`` overrides). Emits exactly one
  severity-3 ``governance-state-loss`` shadow event per restore.
- ``prior_initialization_evidence``: distinguishes "previously initialized,
  now missing" (git history or a populated backup dir) from a genuinely new
  workspace, so ``governance_health`` can route to restore-then-remediate
  instead of bootstrap.

The backup lives under the gitignored ``.agent/local-backup/governance/`` and
therefore does NOT survive ``git clean -fdx`` (documented in the doctrine);
it narrows the loss window, it does not eliminate it. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

DNA_FILES = (
    "docs/META_LEDGER.md",
    "docs/CONCEPT.md",
    "docs/ARCHITECTURE_PLAN.md",
    "docs/SYSTEM_STATE.md",
    "docs/SHADOW_GENOME.md",
)

_MARKER = ".complete"
_BACKUP_ROOT = Path(".agent") / "local-backup" / "governance"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup_dir(base: Path, session_id: str) -> Path:
    """Per-session backup directory (validates the session id path-safety)."""
    from qor.scripts import session as _session

    _session.validate_session_id(session_id)
    return Path(base) / _BACKUP_ROOT / session_id


def ensure_session_backup(base: Path, session_id: str) -> Path | None:
    """Snapshot the DNA files once per session; idempotent via a marker.

    Returns the backup dir, or None on failure (fail-open contract: the
    caller is the governed write path and must never abort on backup error).
    """
    base = Path(base)
    try:
        out = backup_dir(base, session_id)
        marker = out / _MARKER
        if marker.is_file():
            return out
        out.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, str] = {}
        for rel in DNA_FILES:
            source = base / rel
            if not source.is_file():
                continue
            shutil.copyfile(source, out / Path(rel).name)
            manifest[rel] = _sha256(source)
        marker.write_text(
            json.dumps({"session_id": session_id, "files": manifest}, indent=2),
            encoding="utf-8",
        )
        return out
    except (OSError, ValueError):
        return None


def restore(base: Path, source_dir: Path, force: bool = False) -> list[dict]:
    """Copy DNA files back from ``source_dir``; NO-CLOBBER by default.

    A destination that already exists is skipped (``action: skipped-exists``)
    unless ``force`` -- a restore must never silently destroy state newer than
    the snapshot. Emits ONE severity-3 governance-state-loss shadow event.
    """
    base = Path(base)
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"backup source not found: {source_dir}")
    report: list[dict] = []
    for rel in DNA_FILES:
        copied = source_dir / Path(rel).name
        if not copied.is_file():
            continue
        target = base / rel
        if target.exists() and not force:
            report.append({"path": rel, "action": "skipped-exists"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(copied, target)
        report.append({"path": rel, "sha256": _sha256(target), "action": "restored"})
    _emit_state_loss_event(source_dir, report)
    return report


def _emit_state_loss_event(source_dir: Path, report: list[dict]) -> None:
    from qor.scripts import shadow_process

    event = {
        "ts": shadow_process.now_iso(),
        "skill": "qor-governance-snapshot",
        "session_id": source_dir.name,
        "event_type": "governance-state-loss",
        "severity": 3,
        "details": {
            "restored": [r["path"] for r in report if r["action"] == "restored"],
            "skipped_exists": [r["path"] for r in report if r["action"] == "skipped-exists"],
            "source": str(source_dir),
        },
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    shadow_process.append_event(event, attribution="UPSTREAM")


def prior_initialization_evidence(base: Path) -> str | None:
    """Evidence that this workspace was governed before: a populated backup
    dir (no subprocess) or ledger history in git. None for a new workspace."""
    base = Path(base)
    backups = base / _BACKUP_ROOT
    if backups.is_dir() and any(backups.iterdir()):
        return f"local-backup snapshots present under {_BACKUP_ROOT.as_posix()}"
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", DNA_FILES[0]],
            cwd=base, capture_output=True, text=True, check=False, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    sha = result.stdout.strip()
    if result.returncode == 0 and sha:
        return f"git history contains {DNA_FILES[0]} (last commit {sha[:12]})"
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup", help="snapshot the DNA files for a session")
    b.add_argument("--session", required=True)
    b.add_argument("--base", type=Path, default=Path.cwd())
    r = sub.add_parser("restore", help="no-clobber restore from a backup dir")
    r.add_argument("--from", dest="source", required=True, type=Path)
    r.add_argument("--base", type=Path, default=Path.cwd())
    r.add_argument("--force", action="store_true")
    e = sub.add_parser("evidence", help="report prior-initialization evidence")
    e.add_argument("--base", type=Path, default=Path.cwd())
    args = ap.parse_args(argv)
    if args.cmd == "backup":
        out = ensure_session_backup(args.base, args.session)
        if out is None:
            print("FAIL: backup could not be written")
            return 1
        print(f"OK: DNA snapshot at {out}")
        return 0
    if args.cmd == "restore":
        try:
            report = restore(args.base, args.source, force=args.force)
        except FileNotFoundError as exc:
            print(f"FAIL: {exc}")
            return 1
        for row in report:
            print(f"{row['action']}: {row['path']}")
        return 0
    evidence = prior_initialization_evidence(args.base)
    print(evidence or "no prior-initialization evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
