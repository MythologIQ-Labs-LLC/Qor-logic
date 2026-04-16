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
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _hash_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


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
    """Return True if the audit file contains a PASS verdict line."""
    body = audit_path.read_text(encoding="utf-8", errors="replace")
    return "PASS" in body


def _fingerprint_path(repo: Path, session: str) -> Path:
    return repo / ".qor" / "intent-lock" / f"{session}.json"


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
        print("ERROR: audit not PASS", file=sys.stderr)
        return 1

    fingerprint = {
        "session": args.session,
        "plan_path": str(plan),
        "plan_hash": _hash_file(plan),
        "audit_path": str(audit),
        "audit_hash": _hash_file(audit),
        "head_commit": _head_commit(repo),
        "captured_ts": dt.datetime.utcnow().isoformat() + "Z",
    }

    out = _fingerprint_path(repo, args.session)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    print(f"LOCKED: {args.session}")
    return 0


def verify(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    fp_path = _fingerprint_path(repo, args.session)
    if not fp_path.is_file():
        print(f"NO LOCK: {args.session}", file=sys.stderr)
        return 1

    data = json.loads(fp_path.read_text(encoding="utf-8"))

    plan = Path(data["plan_path"])
    if not plan.is_file() or _hash_file(plan) != data["plan_hash"]:
        print("DRIFT: plan", file=sys.stderr)
        return 1

    audit = Path(data["audit_path"])
    if not audit.is_file() or _hash_file(audit) != data["audit_hash"]:
        print("DRIFT: audit", file=sys.stderr)
        return 1

    current_head = _head_commit(repo)
    if current_head != data["head_commit"]:
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
