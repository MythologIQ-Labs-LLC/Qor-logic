#!/usr/bin/env python3
"""Intent Lock — fingerprint implementer intent before implementation.

Captures SHA-256 of plan + audit + git HEAD at capture time; re-verifies on
substantiation. Any drift interdicts downstream phases (SG-032/SG-036 spirit:
prevent silent plan drift between audit PASS and final seal).

Usage:
    intent-lock.py capture --session <sid> --plan <path> --audit <path> [--repo <dir>]
    intent-lock.py verify  --session <sid> [--repo <dir>]

Repo defaults to the current working directory. Writes to <repo>/.qor/intent-lock/<sid>.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from qor.scripts import verdict_dialect
except ImportError:  # pragma: no cover - taken only outside an installed tree
    # This module is executed as a bare script by path, both by its own tests
    # and by operators (`python qor/reliability/intent_lock.py capture ...`).
    # In that mode `qor` resolves to whatever is installed in site-packages,
    # which may predate this file. Extending sys.path does not help: `qor` is
    # already in sys.modules by then, so the retry finds the same stale package.
    # Load the sibling source directly instead, so the gate runs from the tree
    # it lives in rather than requiring a reinstall.
    import importlib.util

    _dialect_path = Path(__file__).resolve().parents[1] / "scripts" / "verdict_dialect.py"
    _spec = importlib.util.spec_from_file_location("_qor_verdict_dialect", _dialect_path)
    verdict_dialect = importlib.util.module_from_spec(_spec)
    # Register before exec: @dataclass resolves annotations through
    # sys.modules[cls.__module__], which is None for an unregistered module.
    sys.modules[_spec.name] = verdict_dialect
    _spec.loader.exec_module(verdict_dialect)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _hash_file(path: Path) -> str:
    """SHA256 of the file's bytes with line endings normalized to LF.

    GAP-GOV-03, applied here in Phase 218 (GH #318). `ledger_hash.content_hash`
    has normalized since that lesson; this hasher did not, so git's autocrlf --
    or an editor, or `Path.write_text` on Windows -- read as plan/audit drift
    and ABORTed a correct seal.

    Only line endings are normalized. Indentation and trailing whitespace still
    change the digest, because those are edits.
    """
    return _sha256_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def _head_commit(repo: Path) -> str:
    """Return current git HEAD short-ish commit (full SHA). No network."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _audit_has_pass(audit_path: Path) -> bool:
    """Return True if the audit file declares a canonical PASS verdict line.

    Phase 53 (LOW-4): anchored multiline regex, rejecting substring "PASS"
    inside narrative prose. Phase 183 (GH #263): markdown-heading forms
    accepted. Phase 275 (GH #424): the decision moved to ``verdict_dialect``,
    shared with ``verdict_reconcile`` so the two gates reading this same file
    stop disagreeing about what a PASS is.

    The behaviour change is that a PASS-shaped line no longer authorizes on its
    own. Every verdict-labeled line in the report must be readable and state the
    same value. A report quoting the canonical form while carrying a VETO used
    to authorize `capture`; it now refuses.
    """
    body = audit_path.read_text(encoding="utf-8", errors="replace")
    return verdict_dialect.is_pass(verdict_dialect.read_verdict(body))


def _verdict_hint(audit_path: Path) -> str:
    """Say which of the three ways a report failed to declare a PASS.

    Phase 183 (GH #263) distinguished 'non-canonical' from 'not PASS'. Phase 275
    adds the third: a report stating two different verdicts is neither, and
    reporting it as "audit not PASS" is true but unactionable -- the operator
    cannot see that the file contradicts itself, or where.
    """
    body = audit_path.read_text(encoding="utf-8", errors="replace")
    verdict = verdict_dialect.read_verdict(body)
    if verdict.unreadable:
        bad = verdict_dialect.unreadable_lines(verdict)
        return (
            "ERROR: audit verdict line found but not in a canonical form; "
            "expected 'Verdict: PASS' (bold or #-heading forms accepted) "
            "on its own line; unreadable: "
            + "; ".join(line.strip() for line in bad[:3])
        )
    if verdict.conflict:
        return (
            "ERROR: audit states more than one verdict: "
            + ", ".join(sorted(set(verdict.values)))
            + "; lines: "
            + "; ".join(line.strip() for line in verdict.lines[:4])
        )
    return "ERROR: audit not PASS"


def _fingerprint_path(repo: Path, session: str) -> Path:
    return repo / ".qor" / "intent-lock" / f"{session}.json"


def _snapshot_path(repo: Path, session: str, kind: str) -> Path:
    return repo / ".qor" / "intent-lock" / f"{session}.{kind}.snapshot"


def _normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


_DIFF_LINE_BOUND = 40


def _drift_report(kind: str, repo: Path, session: str, live: Path) -> None:
    """Print the drift line, plus the decidable delta when the snapshot exists.

    Phase 231 (GH #332 Direction 3): the referent used to be unrecoverable --
    the lock held a hash of bytes that may never have been committed, so every
    override rested on testimony. With the capture-time snapshot the reviewer
    sees exactly what changed. Both sides diff over the same LF normalization
    (audit O2); legacy records without snapshots keep the bare report.
    """
    import difflib

    print(f"DRIFT: {kind}", file=sys.stderr)
    snapshot = _snapshot_path(repo, session, kind)
    if not snapshot.is_file():
        return
    captured = _normalized(snapshot).decode("utf-8", errors="replace").splitlines()
    current = _normalized(live).decode("utf-8", errors="replace").splitlines() if live.is_file() else []
    diff = list(difflib.unified_diff(captured, current, "captured", "current", lineterm=""))
    for line in diff[:_DIFF_LINE_BOUND]:
        print(line, file=sys.stderr)
    if len(diff) > _DIFF_LINE_BOUND:
        print(f"... diff truncated ({len(diff) - _DIFF_LINE_BOUND} more lines)", file=sys.stderr)


def _head_is_ancestor(repo: Path, captured_head: str) -> bool:
    """Phase 43 ancestry check, extracted (audit O1): the captured HEAD must
    remain reachable from current HEAD -- forward progress passes, rewrites,
    hard resets, and divergent branch switches fail."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", captured_head, "HEAD"],
        cwd=str(repo), capture_output=True, text=True, check=False,
    )
    return result.returncode == 0


def capture(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    plan = Path(args.plan).resolve()
    audit = Path(args.audit).resolve()

    if not plan.is_file():
        print(f"ERROR: plan not found: {plan}", file=sys.stderr)
        return 1
    if not audit.is_file():
        print(f"ERROR: audit not found: {audit}", file=sys.stderr)
        return 1
    if not _audit_has_pass(audit):
        print(_verdict_hint(audit), file=sys.stderr)
        return 1

    def _relativize(p: Path) -> str:
        # Phase 172 (publication boundary): store repo-relative paths so lock
        # records never reveal the local workspace layout.
        try:
            return p.relative_to(repo).as_posix()
        except ValueError:
            return p.name  # outside the repo: keep only the leaf name

    fingerprint = {
        "session": args.session,
        "plan_path": _relativize(plan),
        "plan_hash": _hash_file(plan),
        "audit_path": _relativize(audit),
        "audit_hash": _hash_file(audit),
        "head_commit": _head_commit(repo),
        "captured_ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    out = _fingerprint_path(repo, args.session)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    # Phase 231 (GH #332): keep the audited bytes the hashes were computed
    # over, so a later drift is decidable instead of testimonial. Snapshots
    # are the hasher's own normalization -- sha256(snapshot) equals the
    # recorded hash by construction.
    _snapshot_path(repo, args.session, "plan").write_bytes(_normalized(plan))
    _snapshot_path(repo, args.session, "audit").write_bytes(_normalized(audit))
    print(f"LOCKED: {args.session}")
    return 0


def verify(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    fp_path = _fingerprint_path(repo, args.session)
    if not fp_path.is_file():
        print(f"NO LOCK: {args.session}", file=sys.stderr)
        return 1

    data = json.loads(fp_path.read_text(encoding="utf-8"))

    def _resolve(recorded: str) -> Path:
        # Phase 172: records are repo-relative; legacy absolute records
        # (pre-172 grandfather) resolve as-is.
        p = Path(recorded)
        return p if p.is_absolute() else repo / p

    plan = _resolve(data["plan_path"])
    if not plan.is_file() or _hash_file(plan) != data["plan_hash"]:
        _drift_report("plan", repo, args.session, plan)
        return 1

    audit = _resolve(data["audit_path"])
    if not audit.is_file() or _hash_file(audit) != data["audit_hash"]:
        _drift_report("audit", repo, args.session, audit)
        return 1

    if not _head_is_ancestor(repo, data["head_commit"]):
        print("DRIFT: head", file=sys.stderr)
        return 1

    print(f"VERIFIED: {args.session}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Intent lock capture/verify.")
    sub = p.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser("capture", help="Capture intent fingerprint.")
    cap.add_argument("--session", required=True)
    cap.add_argument("--plan", required=True)
    cap.add_argument("--audit", required=True)
    cap.add_argument("--repo", default=".")
    cap.set_defaults(func=capture)

    ver = sub.add_parser("verify", help="Verify intent fingerprint.")
    ver.add_argument("--session", required=True)
    ver.add_argument("--repo", default=".")
    ver.set_defaults(func=verify)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
