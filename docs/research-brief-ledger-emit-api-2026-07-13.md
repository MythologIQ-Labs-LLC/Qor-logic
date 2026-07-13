# Research Brief

**Date**: 2026-07-13T18:05:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #278 -- canonical ledger emit API + structured health output + retroactive normalization
**Scope**: verify parser contract; the 32-skip band's actual shape; emission sites; health output seam

---

## Executive Summary

All three remainders verified against source. The 32 perpetually-skipped
entries are pre-convention bodies carrying NO hash markup at all --
_resolve_recorded returns None and verify grandfathers everything below
markup_required_cutoff into the skip summary (ledger_hash.py:306-323,
:376-436). Retro-hashing them into the live chain is IMPOSSIBLE without
editing post-anchor hash fields (the first verifiable entry's recorded
Previous Hash would no longer link), so the operator-directed retroactive
fix takes the issue's sanctioned second path: an explicit migration-
attestation entry, emitted through the new typed renderer (self-application),
after which verify reports the legacy band as attested -- zero skips.

## Findings

### Why the 32 skip, precisely
- ledger_hash.py:306-323 -- _resolve_recorded needs canonical
  Content/Previous/Chain markup (or the Session-Seal fallback); the legacy
  band has neither.
- :392-405 -- below markup_required_cutoff an unresolved entry increments
  `skipped` (the GAP-GOV-09 modern-entry FAIL applies only at/after the
  cutoff); :434-435 prints the standing "Skipped N" line every run.
- Chain-preservation constraint: the first verifiable entry's recorded
  Previous Hash is a historical value; threading a recomputed retro-chain
  underneath it would require editing that field -- forbidden by the
  operator's acceptance ("hash fields of post-anchor entries stay
  byte-untouched"). The attestation path is the only chain-preserving one.

### Attestation precedent already exists in the verifier
- :293-304 `_attested_reconciled` -- RECONCILIATION entries already attest
  other entries by number, tolerated by verify under a security gate
  (duplicate-previous_hash membership). The migration entry is the same
  mechanism with a stronger claim: per-entry BODY DIGESTS, so any later
  edit of a legacy body breaks its attestation.

### Emission today is hand-assembly
- Every ledger entry this repo writes (skills prose + this session's own
  ceremony) hand-builds markdown and hand-computes hashes; drift between
  emit shape and parse shape is caught only by seal_entry_check after the
  fact. ledger_hash exposes the primitives (content_hash :25, chain_hash
  :39, normalize/assert_sealable_text :65/:77) but no Entry model or
  renderer. entry_id.derive_entry_id exists separately.

### Structured health seam
- governance_health prints prose findings; status_json wraps it at the
  check level; the Phase 191 snapshot embeds the LADDER but not
  governance_health's own findings detail. A `--format json` on
  governance_health (findings as objects: path/reason/legal_next/state)
  composes with, and does not duplicate, the snapshot contract (the
  snapshot's health section stays ladder-level).

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| #278: retroactive fix must not touch post-anchor hash fields | retro-chaining would break the first verifiable link; attestation preserves all bytes | MATCH (attestation path selected) |
| #278: one canonical emit API | zero renderer exists; hand-assembly everywhere | MATCH (gap confirmed) |
| #278: structured health composes with the snapshot | snapshot embeds ladder verdicts only | MATCH |

## Recommendations

1. (P1) `qor/scripts/ledger_emit.py`: typed `LedgerEntry` (number, title,
   fields ordered dict, body, hash trio) + `render()` producing exactly the
   markup _resolve_recorded parses (round-trip test: render -> resolve ->
   verify) + `append()` computing content/chain via ledger_hash primitives
   and entry_id.
2. (P1) `ledger_attest_legacy` (module or ledger_upgrade extension): find
   entries verify would skip; compute LF-normalized body digests; emit ONE
   `MIGRATION ATTESTATION` entry THROUGH ledger_emit listing
   `#<n>=<digest12>` per entry; extend verify to print
   `OK Entry #N: attested by migration entry #M` (digest re-checked) and
   drop them from the skip count. Acceptance: `ledger_hash verify
   docs/META_LEDGER.md` reports ZERO skipped on the live ledger.
3. (P2) `governance_health --format json` (findings as structured objects;
   exit semantics unchanged).
4. (P2) Self-application: the live migration entry for the real 32-entry
   band is emitted by the new API inside this cycle's seal.

## Updated Knowledge

Legacy bands are normalized by ATTESTATION, not by rewriting history: the
migration entry binds each pre-convention body to a digest inside the live
chain, so the band becomes tamper-evident without a single historical byte
changing.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
