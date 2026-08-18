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
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.reliability.gate_chain_completeness import _extract_seal_sessions
from qor.reliability.intent_lock import _hash_file, _normalized, _sha256_bytes

#: Sessions sealed before Phase 231 have no committed evidence (the lock
#: directory was fully operator-local); grandfathered like the sibling
#: gate's phase-52 boundary.
DEFAULT_PHASE_MIN = 231


@dataclass(frozen=True)
class Failure:
    phase: int
    session: str
    kind: str  # missing-evidence | snapshot-mismatch | plan-referent-mismatch
    detail: str


def _check_session(repo: Path, phase: int, session: str) -> list[Failure]:
    lock_dir = repo / ".qor" / "intent-lock"
    record_path = lock_dir / f"{session}.json"
    snaps = {kind: lock_dir / f"{session}.{kind}.snapshot" for kind in ("plan", "audit")}

    missing = [p for p in (record_path, *snaps.values()) if not p.is_file()]
    if missing:
        names = ", ".join(p.name for p in missing)
        return [Failure(phase, session, "missing-evidence", f"{session}: absent: {names}")]

    record = json.loads(record_path.read_text(encoding="utf-8"))
    failures: list[Failure] = []
    for kind, snap in snaps.items():
        if _sha256_bytes(_normalized(snap)) != record[f"{kind}_hash"]:
            failures.append(Failure(
                phase, session, "snapshot-mismatch",
                f"{session}: {snap.name} does not match recorded {kind}_hash"))

    plan_path = record["plan_path"]
    plan_file = (repo / plan_path) if not Path(plan_path).is_absolute() else Path(plan_path)
    if not plan_file.is_file() or _hash_file(plan_file) != record["plan_hash"]:
        failures.append(Failure(
            phase, session, "plan-referent-mismatch",
            f"{session}: committed {plan_path} does not match recorded plan_hash"))
    return failures


def check(repo_root: Path, ledger_path: Path | None = None,
          phase_min: int = DEFAULT_PHASE_MIN) -> list[Failure]:
    ledger = ledger_path or repo_root / "docs" / "META_LEDGER.md"
    sessions = _extract_seal_sessions(ledger.read_text(encoding="utf-8"), phase_min)
    failures: list[Failure] = []
    for phase in sorted(sessions):
        failures.extend(_check_session(repo_root, phase, sessions[phase]))
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
