# Plan: META_LEDGER reconciliation tool — `qor-logic reconcile` + RECONCILIATION entry (real fix)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: RECONCILIATION entry
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: reconcile command
  home: qor/references/doctrine-governance-enforcement.md

**boundaries**:
- limitations: Reconciliation is **forward-only and attestation-based**: it appends a new `RECONCILIATION` ledger entry that enumerates the tolerated duplicate-`previous_hash` residual set; it never renumbers, rewrites, or deletes sealed entries. It tolerates only the exact entry set it attests — non-attested chain failures still FAIL. It does not repair a genuinely corrupt (non-duplicate-previous_hash) chain.
- non_goals: Touching the canonical `docs/META_LEDGER.md` (which verifies clean strict — reconcile targets consumer/synthetic ledgers via `--ledger`); removing the `--tolerate-known-grandfathered` CLI stopgap (retained; the RECONCILIATION entry is its permanent, in-chain successor); auto-authorizing reconciliation (operator must explicitly authorize stage 2).
- exclusions: Post-anchor re-genesis model (rejected in favor of attestation — narrower toleration, keeps strict verification of all non-residual entries); cross-workspace federation merge.

## Open Questions

None. Model resolved up-front: **attestation-anchor**. The RECONCILIATION entry records the reconciled entry numbers + their shared `previous_hash`; `verify-ledger` tolerates exactly those (DISCLOSED_RECONCILED — no error, no taint) when a valid in-chain RECONCILIATION entry attests them, and chains post-reconciliation entries normally off the RECONCILIATION entry. Two-stage operator authorization mirrors the Phase 36 B19 pending->authorized contract: `reconcile propose` writes a pending proposal artifact; `reconcile authorize --proposal <path>` (the explicit operator signal) appends the entry. Forward-only is structurally enforced — append-only, never rewrite (SG-ConcurrentLedgerRace-A "Forbidden interpretation").

## Context

GH #148 (umbrella #147; supersedes deferred V2 of #85 + #51). #85 asked for a real reconciliation tool; PR #106 shipped only option D (the `--tolerate-known-grandfathered` read-only stopgap). No `reconcile` subcommand exists in `qor/cli.py`; `RECONCILIATION` is deferred prose only (`doctrine-shadow-genome-countermeasures.md:285`). Consumer workspaces with pre-V1 duplicate-`previous_hash` interleave (an external QA exemplar's app per #85: #16a/b,#17a/b,#18a/b) still cannot ship a clean strict `verify-ledger`. This phase ships the forward-only RECONCILIATION entry + operator-authorized `reconcile` command so those ledgers verify clean without the CLI flag and without rewriting sealed entries.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_reconcile.py` · test_descriptor: `qor-logic reconcile propose --ledger <synthetic-dup-ledger> writes a pending proposal enumerating the duplicate-previous_hash residual set; ledger unchanged`
- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_reconcile.py` · test_descriptor: `qor-logic reconcile authorize --proposal <p> appends a RECONCILIATION entry; pre-existing entries byte-identical; strict verify-ledger then passes with DISCLOSED_RECONCILED`

## Phase 1: Reconciliation core (`qor/scripts/reconcile.py`)

### Affected Files

- `tests/test_reconcile.py` - NEW. Behavioral tests for residual detection, proposal build/round-trip, forward-only append, and two-stage authorization (see Unit Tests).
- `qor/scripts/reconcile.py` - NEW. Pure-logic core; no CLI/argparse here.

### Changes

`reconcile.py` exposes:

```python
RECONCILIATION_TITLE = "RECONCILIATION"

def detect_residual(ledger_text: str, cutoff: int = 207) -> list[ResidualGroup]:
    """Return groups of entries sharing a previous_hash (the reconcilable
    residual). Reuses the duplicate-previous_hash grouping that backs
    ledger_hash.find_grandfathered_entries (entry-num <= cutoff)."""

def build_proposal(ledger_path: Path, cutoff: int = 207) -> dict:
    """Pending proposal: {status: 'pending', ledger, residual_entry_nums,
    previous_hashes, ts, proposal_id}. Reads the ledger; does NOT mutate it."""

def append_reconciliation_entry(ledger_path: Path, proposal: dict) -> dict:
    """Append a forward-only RECONCILIATION entry. previous_hash = the chain
    hash of the current last entry; content_hash = SHA256 of the entry's
    canonical scope; chain_hash = chain_hash(content, previous); entry_id via
    entry_id.derive_entry_id; entry number via ledger_fragment.next_entry_number.
    The entry body carries a machine-parseable `**Reconciled Entries**: #a, #b, ...`
    line. Pre-existing ledger bytes are preserved verbatim (append-only)."""
```

The RECONCILIATION entry is the in-chain, operator-signed successor to `--tolerate-known-grandfathered`: it records the tolerated set permanently rather than re-asserting it per CLI invocation. De-complecting: detection (read-only) is separated from authorization (proposal artifact) and from the append (mutation); each is independently testable.

### Unit Tests

- `tests/test_reconcile.py::test_detect_residual_finds_duplicate_previous_hash_groups` - build a synthetic ledger with the #85 corpus shape (#16a/b,#17a/b,#18a/b each sharing a `previous_hash`); assert `detect_residual` returns exactly those entry numbers grouped by shared hash, and excludes unique-`previous_hash` entries and entries above cutoff.
- `::test_build_proposal_is_pending_and_nonmutating` - assert the returned proposal has `status=='pending'` and the enumerated residual; assert the ledger file bytes are unchanged after the call (read-before/after equality).
- `::test_append_reconciliation_entry_is_forward_only` - capture every `### Entry #N:` block before append; after `append_reconciliation_entry`, assert all prior blocks are byte-identical and exactly one new `### Entry #<next>:` RECONCILIATION entry was added with a valid (non-placeholder) 64-hex content/previous/chain hash and a `**Reconciled Entries**:` line listing the residual.
- `::test_reconciliation_entry_chain_hash_is_consistent` - assert `chain_hash(content, previous) == recorded chain hash` for the new entry (so `ledger_hash.verify` accepts it as a normal forward link).

## Phase 2: verify-ledger recognizes RECONCILIATION (`qor/scripts/ledger_hash.py`)

### Affected Files

- `tests/test_ledger_hash_reconciliation.py` - NEW. verify() behavior on reconciled ledgers (see Unit Tests).
- `qor/scripts/ledger_hash.py` - add RECONCILIATION recognition to `verify()`.

### Changes

Add `RECONCILED_ENTRIES_RE` matching the `**Reconciled Entries**: #a, #b, ...` line. In `verify()`, before the per-entry loop, collect the union of reconciled entry numbers from all RECONCILIATION entries into `reconciled: set[int]`. In the loop, an entry whose chain math fails but whose number is in `reconciled` emits `DISCLOSED_RECONCILED Entry #N: attested by RECONCILIATION entry` on stdout, does NOT increment `errors`, and does NOT set `last_failed` (no taint propagation) — mirroring the existing `DISCLOSED_GRANDFATHERED` path but gated on in-chain attestation rather than the `--tolerate-known-grandfathered` flag. The flag path is unchanged and still works.

This keeps strict verification for every non-attested entry: a duplicate-`previous_hash` failure NOT listed in any RECONCILIATION entry still FAILs.

### Unit Tests

- `tests/test_ledger_hash_reconciliation.py::test_strict_verify_passes_after_reconciliation` - synthetic ledger with the duplicate residual + an appended RECONCILIATION entry attesting it; `verify(..., tolerate_known_grandfathered=False)` returns 0 and emits `DISCLOSED_RECONCILED` for the residual (assert on stdout), no FAIL on stderr.
- `::test_verify_still_fails_on_unattested_duplicate` - residual present but the RECONCILIATION entry attests only a subset; `verify` (strict) still returns non-zero for the unattested duplicate entry (proves toleration is scoped to the attested set, not blanket).
- `::test_post_reconciliation_entries_chain_off_reconciliation_entry` - append a normal entry after the RECONCILIATION entry whose `previous_hash` is the RECONCILIATION chain hash; assert `verify` reports `OK` for it (no taint leaked from the pre-reconciliation duplicates).
- `::test_reconciliation_does_not_taint_downstream` - assert an entry after the residual but before any FAIL is not marked TAINTED once the residual is attested.

## Phase 3: CLI two-stage command + handler

### Affected Files

- `tests/test_cli_reconcile.py` - NEW. Subprocess tests for `reconcile propose` / `reconcile authorize` (see Unit Tests).
- `qor/cli_handlers/reconcile.py` - NEW. `register(sub)` adds `reconcile` parser with `propose` / `authorize` subcommands; `dispatch(args)` routes them.
- `qor/cli.py` - wire `reconcile` via the handler `register`/`dispatch` pattern (mirroring `compliance`/`release`).

### Changes

`reconcile propose --ledger <path> [--out <proposal.json>]` → `reconcile.build_proposal`, write pending proposal JSON, print the residual summary. Read-only.

`reconcile authorize --proposal <path> --ledger <path>` → load the proposal, re-verify its residual still matches the current ledger (raise on drift), call `reconcile.append_reconciliation_entry`, stamp the proposal `status='authorized'`. The explicit `--proposal <path>` arg is the sole operator-authorization signal (no heuristic proposal discovery — mirrors the Phase 36 B19 anti-pattern guard).

`cli.py`: `from qor.cli_handlers import reconcile as reconcile_handlers; sp_reconcile = reconcile_handlers.register(sub)`; in `main()`, route `args.command == "reconcile"` through `reconcile_handlers.dispatch(args)` then print help on no subcommand (exact `compliance`/`release` pattern).

### Unit Tests

- `tests/test_cli_reconcile.py::test_propose_writes_pending_proposal` - subprocess `qor-logic reconcile propose --ledger <synthetic> --out <p>` exits 0, the proposal file parses with `status=='pending'` and the residual entry numbers, and the synthetic ledger file is unchanged (byte equality before/after).
- `::test_authorize_appends_entry_and_strict_verify_passes` - subprocess `reconcile authorize --proposal <p> --ledger <synthetic>` exits 0; then subprocess `qor-logic verify-ledger --ledger <synthetic>` (strict, no flag) exits 0. Proves the end-to-end real fix.
- `::test_authorize_requires_proposal_arg` - `reconcile authorize --ledger <synthetic>` (no `--proposal`) exits non-zero (two-stage enforced; no heuristic discovery).
- `::test_authorize_rejects_stale_proposal` - mutate the ledger residual after proposing; `authorize` exits non-zero with a drift message (proposal must match current ledger).

## Phase 4: Doctrine

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - update SG-ConcurrentLedgerRace-A: note V2 (`reconcile`) availability, the attestation-anchor model, and that it produces a forward-only RECONCILIATION entry (never rewrites sealed entries); update the line ~285 "reserved for a future phase" prose to "shipped in Phase 119 (#148)".
- `qor/references/doctrine-governance-enforcement.md` - add a short subsection documenting the `reconcile` two-stage propose->authorize protocol and the RECONCILIATION entry shape.

### Changes

SG-ConcurrentLedgerRace-A gains: "V2 (Phase 119; GH #148): `qor-logic reconcile propose`/`authorize` appends an operator-authorized, forward-only RECONCILIATION entry enumerating the tolerated duplicate-`previous_hash` residual; `verify-ledger` recognizes it and reports `DISCLOSED_RECONCILED` for the attested set without the `--tolerate-known-grandfathered` flag. The forward-only rule is preserved: the RECONCILIATION entry is appended, never rewriting #1-#207." Keep the existing "Forbidden interpretation" (no renumbering) text intact.

### Unit Tests

- `tests/test_ledger_hash_reconciliation.py::test_doctrine_documents_reconcile_v2` - assert SG-ConcurrentLedgerRace-A text contains both `reconcile` and `RECONCILIATION` and still contains the forbidden-renumbering clause (so the V2 note does not delete the immutability guarantee). (Functional doc-contract assertion: reads the doctrine file and checks the co-occurrence the implementation depends on.)

## Definition of Done

### Deliverable: reconcile core + RECONCILIATION entry

- **D1**: `qor-logic reconcile` appends an operator-authorized, forward-only RECONCILIATION entry that lets a duplicate-`previous_hash` consumer ledger pass strict `verify-ledger`, without rewriting sealed entries.
- **D2**: `qor/scripts/reconcile.py` (`detect_residual`, `build_proposal`, `append_reconciliation_entry`); `qor/cli_handlers/reconcile.py` (`register`/`dispatch` with `propose`/`authorize`); `qor/cli.py` wiring.
- **D3**: SG-ConcurrentLedgerRace-A + governance-enforcement doctrine updated; version bumped (substantiate Step 7.5); META_LEDGER seal entry.
- **D4**: `tests/test_reconcile.py::test_append_reconciliation_entry_is_forward_only` (prior entries byte-identical) + `tests/test_cli_reconcile.py::test_authorize_appends_entry_and_strict_verify_passes` (end-to-end strict verify 0).

### Deliverable: verify-ledger RECONCILIATION recognition

- **D1**: strict `verify-ledger` tolerates exactly the attested residual; non-attested duplicates still FAIL.
- **D2**: `RECONCILED_ENTRIES_RE` + reconciled-set collection + `DISCLOSED_RECONCILED` path in `ledger_hash.verify()`.
- **D3**: doctrine documents the verify recognition.
- **D4**: `tests/test_ledger_hash_reconciliation.py::test_strict_verify_passes_after_reconciliation` + `::test_verify_still_fails_on_unattested_duplicate`.

## CI Commands

- `python -m pytest tests/test_reconcile.py tests/test_ledger_hash_reconciliation.py tests/test_cli_reconcile.py -q` — new reconcile behavior end-to-end.
- `python -m pytest tests/test_ledger_hash.py tests/test_ledger_hash_tolerate_grandfathered.py tests/test_seal_entry_check_previous_hash_uniqueness.py -q` — no regression in existing ledger verification + grandfathered tolerance.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — canonical ledger still verifies clean (reconcile must not touch it).
- `python -m pytest -q` — full suite green before substantiate.
