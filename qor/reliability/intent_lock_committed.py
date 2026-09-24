"""CI-side intent-lock verification for sealed sessions (Phase 233; GH #352).

intent_lock was the one ladder gate with no CI enforcement: its ABORT was
always resolvable by the person it constrains (#16798), because CI had no
artifact to check -- lock records were operator-local. Sealed sessions commit
their record and snapshots since Phase 231; this checker walks SESSION SEAL
entries at or above that boundary and fails the merge that loses or tampers
with the evidence.

Checks per sealed session: the record and both snapshots exist in the
checkout; each snapshot's LF-normalized sha256 equals its recorded hash
(self-consistency -- the binding the #344 incident broke); and the recorded
``plan_hash`` equals the hash of the committed file at the recorded
``plan_path``. The audit report's committed referent is deliberately NOT
matched: ``.agent/staging/AUDIT_REPORT.md`` is overwritten by every later
phase (173 commits touch it), so the committed snapshot IS its preserved
referent and self-consistency is the whole check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.reliability.gate_chain_completeness import _extract_seal_sessions
from qor.reliability.intent_lock import _hash_file, _normalized, _sha256_bytes
from qor.scripts import ledger_commitment, ledger_hash

#: Sessions sealed before Phase 231 have no committed evidence (the lock
#: directory was fully operator-local); grandfathered like the sibling
#: gate's phase-52 boundary.
DEFAULT_PHASE_MIN = 231

#: Phase 296: a walked session's plan hash may be superseded by a contiguous,
#: ledger-committed chain of `<session>.reattest-<k>.json` records (intent-lock
#: re-attestation; qor/references/doctrine-publication-boundary.md). The audit
#: side is never superseded, and the lock record itself is never rewritten.
_REATTEST_RE = re.compile(r"^(?P<session>.+)\.reattest-(?P<index>[^.]*)\.json$")
_INDEX_RE = re.compile(r"[1-9][0-9]*")
_REATTEST_FIELDS = frozenset({"session", "supersedes_plan_hash", "plan_hash", "reason"})


@dataclass(frozen=True)
class Failure:
    phase: int
    session: str
    # missing-evidence | snapshot-mismatch | plan-referent-mismatch | reattestation-invalid
    kind: str
    detail: str


def _reattestations(lock_dir: Path) -> dict[str, list[tuple[str, Path]]]:
    """Group `<session>.reattest-<k>.json` files by session (unordered)."""
    found: dict[str, list[tuple[str, Path]]] = {}
    if not lock_dir.is_dir():
        return found
    for path in lock_dir.glob("*.reattest-*.json"):
        match = _REATTEST_RE.match(path.name)
        if match:
            found.setdefault(match["session"], []).append((match["index"], path))
    return found


def _load_reattestation(path: Path, session: str) -> tuple[dict | None, str]:
    """Return ``(record, "")``, or ``(None, why)`` when the file is unusable."""
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"unreadable ({exc.__class__.__name__})"
    if not isinstance(body, dict) or set(body) != _REATTEST_FIELDS:
        return None, "field set is not exactly " + ", ".join(sorted(_REATTEST_FIELDS))
    if not all(isinstance(value, str) for value in body.values()):
        return None, "fields must be strings"
    if body["session"] != session:
        return None, f"session field {body['session']!r} does not match its filename"
    return body, ""


def _effective_plan_hash(repo: Path, session: str, recorded: str,
                         files: list[tuple[str, Path]],
                         commitments: dict[str, str]) -> tuple[str, list[str]]:
    """Fold a session's re-attestation chain into its effective plan hash.

    Returns the hash and the problems found; folding stops at the first
    problem, so the hash is the last one a valid link established.
    """
    bad_index = [path.name for index, path in files if not _INDEX_RE.fullmatch(index)]
    if bad_index:
        return recorded, [f"{name}: index is not [1-9][0-9]*" for name in bad_index]
    effective = recorded
    for expected, (index, path) in enumerate(sorted(files, key=lambda f: int(f[0])), 1):
        if int(index) != expected:
            return effective, [f"{path.name}: chain is not contiguous from reattest-1"]
        body, why = _load_reattestation(path, session)
        if body is None:
            return effective, [f"{path.name}: {why}"]
        if body["supersedes_plan_hash"] != effective:
            return effective, [f"{path.name}: does not chain from the effective plan hash"]
        rel = path.relative_to(repo).as_posix()
        if commitments.get(rel) != ledger_hash.content_hash(path):
            return effective, [f"{path.name}: not committed by a ledger entry at its current bytes"]
        effective = body["plan_hash"]
    return effective, []


def _check_session(repo: Path, phase: int, session: str,
                   reattests: list[tuple[str, Path]] | None = None,
                   commitments: dict[str, str] | None = None) -> list[Failure]:
    lock_dir = repo / ".qor" / "intent-lock"
    record_path = lock_dir / f"{session}.json"
    snaps = {kind: lock_dir / f"{session}.{kind}.snapshot" for kind in ("plan", "audit")}

    missing = [p for p in (record_path, *snaps.values()) if not p.is_file()]
    if missing:
        names = ", ".join(p.name for p in missing)
        return [Failure(phase, session, "missing-evidence", f"{session}: absent: {names}")]

    record = json.loads(record_path.read_text(encoding="utf-8"))
    plan_hash, problems = _effective_plan_hash(
        repo, session, record["plan_hash"], reattests or [], commitments or {})
    failures = [Failure(phase, session, "reattestation-invalid", f"{session}: {problem}")
                for problem in problems]
    expected = {"plan": plan_hash, "audit": record["audit_hash"]}
    for kind, snap in snaps.items():
        if _sha256_bytes(_normalized(snap)) != expected[kind]:
            failures.append(Failure(
                phase, session, "snapshot-mismatch",
                f"{session}: {snap.name} does not match recorded {kind}_hash"))

    plan_path = record["plan_path"]
    plan_file = (repo / plan_path) if not Path(plan_path).is_absolute() else Path(plan_path)
    if not plan_file.is_file() or _hash_file(plan_file) != plan_hash:
        failures.append(Failure(
            phase, session, "plan-referent-mismatch",
            f"{session}: committed {plan_path} does not match recorded plan_hash"))
    return failures


def _load_commitments(ledger: Path) -> tuple[dict[str, str], list[Failure]]:
    """Ledger commitments, or none plus a failure when the ledger is malformed."""
    try:
        return ledger_commitment.latest_commitments(ledger), []
    except ledger_commitment.MalformedCommitmentError as exc:
        return {}, [Failure(0, "", "reattestation-invalid",
                            f"ledger commitments unreadable: {exc}")]


def check(repo_root: Path, ledger_path: Path | None = None,
          phase_min: int = DEFAULT_PHASE_MIN) -> list[Failure]:
    ledger = ledger_path or repo_root / "docs" / "META_LEDGER.md"
    sessions = _extract_seal_sessions(ledger.read_text(encoding="utf-8"), phase_min)
    reattests = _reattestations(repo_root / ".qor" / "intent-lock")
    commitments, failures = _load_commitments(ledger) if reattests else ({}, [])
    # "Walked" is the session set for this phase_min; a record nothing walks
    # would sit unverified, so it fails instead.
    for session in sorted(set(reattests) - set(sessions.values())):
        failures.append(Failure(
            0, session, "reattestation-invalid",
            f"{session}: re-attestation for a session not walked at phase_min {phase_min}"))
    for phase in sorted(sessions):
        session = sessions[phase]
        failures.extend(_check_session(
            repo_root, phase, session, reattests.get(session), commitments))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.reliability.intent_lock_committed")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--phase-min", type=int, default=DEFAULT_PHASE_MIN)
    args = parser.parse_args(argv)
    failures = check(args.repo_root.resolve(), args.ledger, args.phase_min)
    for f in failures:
        print(f"FAIL [intent-lock-committed] phase {f.phase} [{f.kind}] {f.detail}",
              file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} intent-lock evidence failure(s); the lock's "
              f"guarantee is checked here, not by the person it constrains (#352).",
              file=sys.stderr)
        return 1
    print(f"OK: intent-lock evidence verified for sealed phases >= {args.phase_min}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
