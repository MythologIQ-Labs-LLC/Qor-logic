"""Phase 119 (GH #148): forward-only META_LEDGER reconciliation.

Real fix superseding the Phase 91 `--tolerate-known-grandfathered` read-only
stopgap. `reconcile` appends an operator-authorized RECONCILIATION entry that
enumerates the duplicate-`previous_hash` residual (SG-ConcurrentLedgerRace-A);
`ledger_hash.verify` then reports DISCLOSED_RECONCILED for exactly that
attested set without the CLI flag. Forward-only: sealed entries are never
renumbered, rewritten, or deleted -- the entry is appended.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import entry_id, ledger_fragment
from qor.scripts.ledger_hash import (
    CHAIN_HASH_RE,
    ENTRY_RE,
    PREV_HASH_RE,
    SESSION_SEAL_RE,
    chain_hash,
)

RECONCILIATION_TITLE = "RECONCILIATION"


def _entries(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    parts = ENTRY_RE.split(text)
    for i in range(1, len(parts), 2):
        out.append((int(parts[i]), parts[i + 1] if i + 1 < len(parts) else ""))
    return out


def detect_residual(ledger_text: str) -> dict[str, list[int]]:
    """Group entry numbers by shared previous_hash; return only groups with
    2+ members (the reconcilable duplicate-previous_hash residual). No cutoff:
    consumer ledgers may carry the residual at any entry number."""
    by_prev: dict[str, list[int]] = {}
    for num, body in _entries(ledger_text):
        ph = PREV_HASH_RE.search(body)
        if not ph:
            continue
        by_prev.setdefault(ph.group(1) or ph.group(2), []).append(num)
    return {prev: sorted(nums) for prev, nums in by_prev.items() if len(nums) >= 2}


def build_proposal(ledger_path: Path, *, ts: str) -> dict:
    """Pending reconciliation proposal. Reads the ledger; never mutates it.
    `ts` is supplied by the caller so the proposal id is deterministic and
    free of hidden wall-clock coupling."""
    text = Path(ledger_path).read_text(encoding="utf-8")
    groups = detect_residual(text)
    residual = sorted(n for nums in groups.values() for n in nums)
    prev_hashes = sorted(groups.keys())
    proposal_id = hashlib.sha256(
        f"{residual}|{prev_hashes}|{ts}".encode("utf-8")
    ).hexdigest()[:12]
    return {
        "status": "pending",
        "ledger": str(ledger_path),
        "residual_entry_nums": residual,
        "previous_hashes": prev_hashes,
        "ts": ts,
        "proposal_id": proposal_id,
    }


def _recorded_chain_hash(body: str) -> str | None:
    """The entry's recorded chain hash / session seal, or None when absent."""
    xh = CHAIN_HASH_RE.search(body)
    if xh:
        return xh.group(1) or xh.group(2)
    seal = SESSION_SEAL_RE.search(body)
    if seal:
        return seal.group(1)
    return None


def _last_chain_hash(text: str) -> str:
    """Chain hash to link the new entry off: the LAST entry carrying recorded
    hash markup. Phase 180 (GH #234): a deferred-Merkle tail (no-fabrication
    entries with no hash markup) is a legal state -- the exact state reconcile
    exists to repair -- so walk backward past it to the last validly
    chain-hashed entry instead of rejecting the ledger. Only recorded hashes
    are ever selected; nothing is fabricated."""
    entries = _entries(text)
    if not entries:
        # Genesis: no prior entry -> all-zeros previous (verify() exempts it).
        return "0" * 64
    for _, body in reversed(entries):
        recorded = _recorded_chain_hash(body)
        if recorded:
            return recorded
    raise ValueError("no validly chain-hashed entry found to link off")


def append_reconciliation_entry(
    ledger_path: Path, proposal: dict, *, ts: str, dry_run: bool = False,
) -> dict:
    """Append a forward-only RECONCILIATION entry attesting the proposal's
    residual set. Pre-existing ledger bytes are preserved verbatim. With
    dry_run the full entry is computed (numbers, hashes, entry id) but the
    ledger is not touched (Phase 167; GH #250)."""
    path = Path(ledger_path)
    text = path.read_text(encoding="utf-8")
    residual = sorted(int(n) for n in proposal["residual_entry_nums"])
    if not residual:
        raise ValueError("nothing to reconcile: proposal residual set is empty")

    next_num = ledger_fragment.next_entry_number(text)
    previous = _last_chain_hash(text)
    reconciled_line = ", ".join(f"#{n}" for n in residual)
    prev_hashes_line = ", ".join(proposal.get("previous_hashes", []))
    scope = (
        f"Operator-authorized forward-only reconciliation of {len(residual)} "
        f"duplicate-previous_hash residual entries ({reconciled_line}) per "
        f"SG-ConcurrentLedgerRace-A. No sealed entries renumbered or rewritten. "
        f"proposal_id={proposal.get('proposal_id')} ts={ts}"
    )
    content = hashlib.sha256(scope.encode("utf-8")).hexdigest()
    chain = chain_hash(content, previous)
    eid = entry_id.derive_entry_id(ts, "RECONCILE", content)

    entry = (
        f"\n\n### Entry #{next_num}: {RECONCILIATION_TITLE}\n\n"
        f"**Timestamp**: {ts}\n"
        f"**Phase**: RECONCILE\n"
        f"**Author**: Operator\n"
        f"**Reconciled Entries**: {reconciled_line}\n"
        f"**Reconciled Previous-Hashes**: {prev_hashes_line}\n"
        f"**Proposal ID**: `{proposal.get('proposal_id')}`\n"
        f"**Entry ID**: `{eid}`\n\n"
        f"**Scope**: {scope}\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{previous}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n"
    )
    if not dry_run:
        path.write_text(text + entry, encoding="utf-8")
    return {
        "entry_num": next_num,
        "content_hash": content,
        "previous_hash": previous,
        "chain_hash": chain,
        "entry_id": eid,
        "reconciled_entry_nums": residual,
    }
