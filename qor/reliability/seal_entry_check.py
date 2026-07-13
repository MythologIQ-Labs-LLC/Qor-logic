"""Seal entry check -- verify substantiate appended a SESSION SEAL ledger entry.

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
from qor.scripts import ledger_dialect
from qor.scripts.governance_helpers import derive_phase_metadata


# GH #282: the header no longer needs to carry `Phase <N>` inline -- the shared
# ledger_dialect.entry_phase reads the phase from the header OR a separate
# `**Phase**:` line, and the shared hash regexes accept the fenced dialect too,
# so this consumer agrees with ledger_hash and governance_health.
_ENTRY_HEADER_RE = re.compile(
    r"^### Entry #(\d+):\s*"
    r"(GATE TRIBUNAL|IMPLEMENTATION|SESSION SEAL)"
    r"([^\n]*)",
    re.MULTILINE,
)
_PLAN_FIELD_RE = re.compile(r"^\*\*Plan\*\*:\s*(\S+)", re.MULTILINE)


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
    content = ledger_dialect.hash_value(ledger_dialect.CONTENT_HASH_RE.search(block))
    previous = ledger_dialect.hash_value(ledger_dialect.PREV_HASH_RE.search(block))
    chain = ledger_dialect.hash_value(ledger_dialect.CHAIN_HASH_RE.search(block))
    if not (content and previous and chain):
        return None
    phase = ledger_dialect.entry_phase(last.group(0), block)
    if phase is None:
        return None
    plan_match = _PLAN_FIELD_RE.search(block)
    return {
        "entry_num": int(last.group(1)),
        "kind": last.group(2),
        "phase_num": phase,
        "content_hash": content,
        "previous_hash": previous,
        "chain_hash": chain,
        "plan_path": plan_match.group(1) if plan_match else None,
        "block": block,
    }


def check(ledger_path: Path, phase_num: int, repo_root: Path | None = None) -> SealEntryResult:
    """Verify the latest ledger entry is a SESSION SEAL for ``phase_num`` with
    internally-consistent chain hash, that its recorded ``content_hash`` matches
    the bytes of the plan it cites (GAP-GOV-01: forward-only binding -- only the
    just-sealed latest entry is recomputed), and that post-anchor chain
    verification passes (GH #88: tolerates a re-anchored ledger's disclosed
    pre-anchor failures instead of tainting every entry after them)."""
    try:
        text = Path(ledger_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        # GH #201 follow-on: a seal that wrote invalid-UTF-8 bytes fails closed
        # here instead of raising an uncaught decode error.
        return SealEntryResult(ok=False, errors=[f"ledger is not valid UTF-8: {exc}"])
    latest = _parse_latest_entry(text)
    errors: list[str] = []

    if latest is None:
        errors.append(f"no parseable entries in {ledger_path}")
        return SealEntryResult(ok=False, errors=errors)

    # GH #201 follow-on: the actual seal path edits META_LEDGER directly (not via
    # ledger_fragment), so validate the just-sealed entry is ASCII here -- making
    # the seal fail-closed against the non-ASCII corruption class.
    try:
        ledger_hash.assert_sealable_text(latest["block"], label=f"entry #{latest['entry_num']} body")
    except ValueError as exc:
        errors.append(str(exc))

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

    # GAP-GOV-01: bind content_hash to the cited plan's bytes. Recompute the plan
    # digest and fail the seal if it does not match the recorded content_hash, so
    # the hash can no longer be an unverified free field. Forward-only: only this
    # latest (just-sealed) entry is recomputed; existing entries are grandfathered.
    plan_rel = latest.get("plan_path")
    if plan_rel:
        root = Path(repo_root) if repo_root is not None else Path(ledger_path).parent.parent
        plan_file = root / plan_rel
        if not plan_file.is_file():
            errors.append(
                f"entry #{latest['entry_num']} cites plan {plan_rel!r} but the plan "
                f"file is absent under {root}"
            )
        else:
            recomputed = ledger_hash.content_hash(plan_file)
            if recomputed != latest["content_hash"]:
                errors.append(
                    f"content_hash on entry #{latest['entry_num']} does not match its plan "
                    f"{plan_rel}: recorded {latest['content_hash'][:8]}..., "
                    f"recomputed {recomputed[:8]}..."
                )

    if not errors:
        rc = ledger_hash.verify_post_anchor(Path(ledger_path))
        if rc != 0:
            errors.append(
                f"full chain verification failed (ledger_hash.verify_post_anchor rc={rc})"
            )

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
        prev_match = ledger_dialect.PREV_HASH_RE.search(block)
        if not prev_match:
            continue
        prev_hash = ledger_dialect.hash_value(prev_match).lower()
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


def check_latest(ledger_path: Path, repo_root: Path | None = None) -> SealEntryResult:
    """GAP-GOV-03: re-verify the latest SESSION SEAL entry without an external
    plan argument -- derive the phase from the entry itself, then run ``check``
    (which recomputes content_hash from the entry's cited plan, the GOV-01
    binding). Used by CI to re-verify the COMMITTED seal's binding (the gates
    otherwise run only on the pre-commit working tree)."""
    try:
        text = Path(ledger_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return SealEntryResult(ok=False, errors=[f"ledger is not valid UTF-8: {exc}"])
    latest = _parse_latest_entry(text)
    if latest is None:
        return SealEntryResult(ok=False, errors=[f"no parseable latest entry in {ledger_path}"])
    return check(ledger_path, latest["phase_num"], repo_root=repo_root)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify SESSION SEAL ledger entry")
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument(
        "--auto", action="store_true",
        help="derive phase + plan from the latest entry (GAP-GOV-03 committed-seal re-verify)",
    )
    args = parser.parse_args(argv)

    if args.auto:
        result = check_latest(args.ledger)
        label: object = "latest"
    else:
        if args.plan is None:
            parser.error("--plan is required unless --auto is given")
        try:
            phase_num, _slug = derive_phase_metadata(args.plan)
        except (ValueError, FileNotFoundError) as e:
            # GH #223: the strict `plan-qor-phase<N>-<slug>.md` filename is a
            # qor-internal convention; downstream workspaces name plans
            # `plan-<slug>.md`. The filename only ever supplied the phase NUMBER
            # for the consistency check, so a non-conforming name must NOT hard-
            # block the seal (this gate is `|| ABORT` at substantiate Step 7.7).
            # Fall back to the ledger-derived phase (the `--auto` path), which
            # re-derives the phase from the latest entry and still runs the
            # identical GOV-01 content_hash<->cited-plan binding -- a WARN, not
            # rc=1. A real inconsistency still FAILs.
            print(
                f"WARN: plan filename not phase-tagged ({e}); deriving phase from "
                f"the latest ledger entry instead.",
                file=sys.stderr,
            )
            result = check_latest(args.ledger)
            label = "latest (plan-name fallback)"
        else:
            result = check(ledger_path=args.ledger, phase_num=phase_num)
            label = phase_num

    if result.ok:
        print(f"OK seal entry verified for phase {label}")
        return 0
    for err in result.errors:
        print(f"FAIL: {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
