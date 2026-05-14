"""Seal entry check — verify substantiate appended a SESSION SEAL ledger entry.

Closes SG-AdjacentState-A: a class of bookkeeping gaps where /qor-substantiate
runs to completion (commit, tag, push) without appending the mandatory
SESSION SEAL entry to docs/META_LEDGER.md. Phase 46's first substantiate
sealed at v0.33.0 without writing entries #150-#152; intent-lock and the
existing reliability gates did not catch it.

Pure-function helper. The CLI wrapper resolves phase number from the plan
path via governance_helpers and delegates to ``check()`` which reads the
ledger and verifies the latest entry is a SESSION SEAL for the given phase
with internally-consistent chain hash.

Usage:
    seal_entry_check.py --ledger <path> --plan <path>

Exit 0 on PASS, 1 on FAIL with error message on stderr.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from qor.scripts import ledger_hash
from qor.scripts.governance_helpers import derive_phase_metadata


_ENTRY_HEADER_RE = re.compile(
    r"^### Entry #(\d+):\s*"
    r"(GATE TRIBUNAL|IMPLEMENTATION|SESSION SEAL)"
    r"[^\n]*?Phase\s*(\d+)",
    re.MULTILINE,
)
_HASH_FIELD_RE = re.compile(
    r"\*\*(?:Content Hash|Previous Hash|Chain Hash)(?:\s*\([^)]+\))?\*\*:\s*`([0-9a-fA-F]{64})`"
)


@dataclass
class SealEntryResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


def _parse_latest_entry(text: str) -> dict | None:
    """Return the latest entry's parsed fields, or None if no entries found."""
    matches = list(_ENTRY_HEADER_RE.finditer(text))
    if not matches:
        return None
    last = matches[-1]
    block = text[last.start():]
    hashes = _HASH_FIELD_RE.findall(block)
    if len(hashes) < 3:
        return None
    return {
        "entry_num": int(last.group(1)),
        "kind": last.group(2),
        "phase_num": int(last.group(3)),
        "content_hash": hashes[0],
        "previous_hash": hashes[1],
        "chain_hash": hashes[2],
    }


def check(ledger_path: Path, phase_num: int) -> SealEntryResult:
    """Verify the latest ledger entry is a SESSION SEAL for ``phase_num`` with
    internally-consistent chain hash, and that full chain verification passes."""
    text = Path(ledger_path).read_text(encoding="utf-8")
    latest = _parse_latest_entry(text)
    errors: list[str] = []

    if latest is None:
        errors.append(f"no parseable entries in {ledger_path}")
        return SealEntryResult(ok=False, errors=errors)

    if latest["kind"] != "SESSION SEAL":
        errors.append(
            f"latest entry #{latest['entry_num']} is {latest['kind']}, "
            f"expected SESSION SEAL for phase {phase_num}"
        )

    if latest["phase_num"] != phase_num:
        errors.append(
            f"phase mismatch: expected {phase_num}, found {latest['phase_num']} "
            f"on entry #{latest['entry_num']}"
        )

    expected = ledger_hash.chain_hash(latest["content_hash"], latest["previous_hash"])
    if latest["chain_hash"] != expected:
        errors.append(
            f"chain_hash inconsistent on entry #{latest['entry_num']}: "
            f"recorded {latest['chain_hash'][:8]}..., recomputed {expected[:8]}..."
        )

    if not errors:
        rc = ledger_hash.verify(Path(ledger_path))
        if rc != 0:
            errors.append(f"full chain verification failed (ledger_hash.verify rc={rc})")

    return SealEntryResult(ok=not errors, errors=errors)


def check_previous_hash_uniqueness(ledger_path: Path, min_entry_num: int = 207) -> SealEntryResult:
    """Phase 76 wiring (GH #51): detect concurrent federation race signature.

    Walks all entries in the ledger from ``min_entry_num`` onward (default 207,
    the entry that introduced the check at Phase 76 seal), groups by
    ``previous_hash`` value, and reports any value claimed by more than one
    entry. Two entries claiming the same predecessor hash is the signature
    of a concurrent append race.

    Forward-only by design (per SG-ConcurrentLedgerRace-A): pre-Phase-76
    entries are grandfathered to preserve chain immutability. Past duplicate
    instances (e.g., META_LEDGER #109/#111/#113 from earlier federation
    activity) remain in the ledger as documented residual; V2 operator-
    authorized reconciliation is the only path that may change them.

    Returns ``SealEntryResult(ok=True, errors=[])`` when all in-scope
    previous_hash values are unique. Returns ``SealEntryResult(ok=False,
    errors=[...])`` naming the duplicate entry numbers and shared hash prefix.
    """
    text = Path(ledger_path).read_text(encoding="utf-8")
    seen: dict[str, list[int]] = {}
    for match in _ENTRY_HEADER_RE.finditer(text):
        entry_num = int(match.group(1))
        if entry_num < min_entry_num:
            continue
        block_end = text.find("\n### Entry #", match.end())
        block = text[match.start(): block_end if block_end != -1 else len(text)]
        prev_match = re.search(
            r"\*\*Previous Hash(?:\s*\([^)]+\))?\*\*:\s*`([0-9a-fA-F]{64})`",
            block,
        )
        if not prev_match:
            continue
        prev_hash = prev_match.group(1).lower()
        seen.setdefault(prev_hash, []).append(entry_num)
    errors: list[str] = []
    for prev_hash, nums in sorted(seen.items()):
        if len(nums) > 1:
            num_list = ", ".join(f"#{n}" for n in sorted(nums))
            errors.append(
                f"concurrent-ledger-race: entries {num_list} all claim previous_hash "
                f"prefix {prev_hash[:8]}... (full: {prev_hash})"
            )
    return SealEntryResult(ok=not errors, errors=errors)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify SESSION SEAL ledger entry")
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        phase_num, _slug = derive_phase_metadata(args.plan)
    except (ValueError, FileNotFoundError) as e:
        print(f"plan path resolution failed: {e}", file=sys.stderr)
        return 1

    result = check(ledger_path=args.ledger, phase_num=phase_num)
    if result.ok:
        print(f"OK seal entry verified for phase {phase_num}")
        return 0
    for err in result.errors:
        print(f"FAIL: {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
