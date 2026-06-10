# Doctrine: Ledger Concurrency — linearize the hash chain at the trunk

Phase 162 (GH #231 Option 1). Defines how the `docs/META_LEDGER.md` hash chain
stays consistent when different agents / developers work on different branches of
a shared repo.

## The problem

The ledger is a **linear hash chain**: each entry binds to exactly one predecessor
via `Previous Hash = chain_hash(prev_content, prev_prev)` (`qor/scripts/ledger_hash.py`).
A linear chain assumes a single totally-ordered append sequence. Git gives a
**branch DAG** (a partial order). Two branches can each append "the next entry"
citing the same predecessor, forking the chain; on merge git text-merges the
ledger and can **auto-merge two non-conflicting appends silently** into a
valid-looking but forked history.

Integrity and coordination are orthogonal. The hash chain provides
**tamper-evidence**; it was never going to provide **concurrency control**. Git
already provides coordination (DAG + merge + conflict). The chain should lean on
the trunk, not assume a single writer.

## The contract: provisional-until-merge

`main` is the single linear source of truth. A **provisional seal entry** is a
seal entry sealed on a branch before that branch is up to date with `main`: its
`Previous Hash` reflects the branch's base at seal time, which may be stale. A
provisional entry becomes canonical only once its branch is rebased onto the
current `main` tip and (if the tip moved) re-anchored.

**Ledger base currency** is the property that a branch's first new-on-branch
entry's `Previous Hash` equals `origin/main`'s tip `Chain Hash` — i.e. the
branch's new sub-chain starts exactly where `main` ends. A base-current branch
merges into a still-linear chain.

## The gate (V1 WARN-first)

`qor.reliability.ledger_base_currency.check_base_currency(branch_text, base_text)` identifies the
first entry whose `Chain Hash` is not present in the base (new-on-branch entries
are identified by chain-hash set membership, robust to entry-number reuse) and
asserts its `Previous Hash` equals the base tip. The CLI
(`python -m qor.reliability.ledger_base_currency --base-ref origin/main`) is
**WARN-only in V1** (`--enforce` reserved for V2): it surfaces a stale-base fork
before merge without blocking. It is wired as a WARN-only CI step on the `test`
job. The V2 flip to a required, fail-closed check follows the same WARN->VETO ramp
prior gates used, after operator evidence on false-positive rate.

This is the forward-looking complement to the post-hoc detector
`seal_entry_check.check_previous_hash_uniqueness` (`SG-ConcurrentLedgerRace-A`),
which is retained: the gate catches a stale base *before* merge; the detector
catches a landed fork *after*.

## The fix: re-anchor at merge

When the gate WARNs, the operator rebases onto current `main` and re-anchors the
provisional sub-chain. `reanchor(base_tip_chain, new_entries)` is a pure fold:
for each new entry `{content_hash, ts, phase}` it recomputes
`Previous Hash = <running tip>`, `Chain Hash = chain_hash(content_hash, prev)`, and
`Entry ID = derive_entry_id(ts, phase, content_hash)`, starting from the live base
tip. It returns the corrected `(previous_hash, chain_hash, entry_id)` sequence; it
does **not** edit the ledger (the operator applies the values, keeping the seal
deliberate). Content hashes are unchanged — only the chain linkage is rebuilt — so
the GOV-01 `content_hash`<->plan binding is preserved.

## Why a single operator already sees this

Done one phase at a time and merged in order, the chain never forks — but that is
discipline, not construction (e.g. a phase branched off a sibling's seal commit
must be stacked, not branched from a stale `main`). The gate makes the
linearization the stacking discipline approximates explicit and checkable.

## V2 / alternatives (out of scope for V1)

- Promote the gate to required / fail-closed (the documented V2 flip).
- Per-entry content-addressed files + a derived chain index (eliminates the
  textual-merge fork surface).
- A Merkle tree + causal order via commit-DAG ancestry or Lamport clocks (true
  parallel sealing; CRDT direction).
- Explicit federation reconciliation that re-anchors divergent local appends at
  merge (the `--auto` re-verify + uniqueness detector are seeds of this).
