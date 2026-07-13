# Research Brief

**Date**: 2026-07-13T07:40:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #234 -- reconcile authorize fails on deferred-Merkle tail
**Scope**: the tail-parse defect, deferred-tail legality, minimal fix shape

---

## Executive Summary

`reconcile._last_chain_hash` (qor/scripts/reconcile.py:69-82, verified live)
inspects ONLY the literal final entry for a chain hash or session seal and
raises "final ledger entry has no parseable chain hash to link off" otherwise.
A deferred-Merkle tail -- entries that legally carry NO fabricated hash after
the chain goes DIRTY (the exact no-fabrication discipline reconcile exists to
repair) -- therefore blocks the very reconciliation that would fix it. A prior
scout run reproduced the failure synthetically on this code (build_proposal
succeeds and even computes the correct link-off ancestor; authorize then dies
in `_last_chain_hash`). Minimal fix: when the tail lacks parseable markup,
walk BACKWARD through prior entries for the last validly chain-hashed one;
raise only when none exists anywhere.

## Findings

### F1. Defect site (verified live this session)

- `qor/scripts/reconcile.py:69-82`: `entries[-1]` only; CHAIN_HASH_RE then
  SESSION_SEAL_RE; raise at line 82. Caller `append_reconciliation_entry`
  (line 99 area: `previous = _last_chain_hash(text)`) is the authorize path.
- The proposal already carries `previous_hashes` (the valid ancestors), proving
  the correct link-off value is derivable -- the tail-only parse is the bug,
  not missing information.

### F2. Deferred tails are legal state

- The no-fabrication discipline (no hash is ever invented) produces tails whose
  entries record prose like "Merkle Seal: DEFERRED to the reconciliation
  backfill batch". Reconcile's whole purpose is repairing exactly this state;
  the RECONCILIATION entry must link off the LAST VALIDLY HASHED entry, which
  is precisely what a backward walk yields.

### F3. Fix shape and test gap

- Backward-walk fallback inside `_last_chain_hash` is self-contained (no
  signature change, no caller updates -- SG-AffectedFilesContract trivially
  satisfied) and keeps the genesis (`"0"*64`) and no-hash-anywhere (raise)
  behaviors. 365 lines of existing reconcile tests cover only valid-tail
  ledgers; zero deferred-tail coverage (tests/test_reconcile.py,
  tests/test_cli_reconcile.py, tests/test_ledger_hash_reconciliation.py).
- Overlap: #271's typed parser would eventually subsume this, but the V1 slice
  just sealed (Phase 179) deliberately excluded emission/parse rework; this
  targeted fix is independently shippable (recorded in entry #434).

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Reconcile repairs no-fabrication residuals | The authorize path rejects the no-fabrication tail shape | DRIFT (the defect) |
| Forward-only, no rewrite | Unchanged by the fix (link-off selection only) | MATCH |

## Recommendations

1. (P0) Backward-walk fallback in `_last_chain_hash`; error message names the
   true condition ("no validly chain-hashed entry found to link off").
2. (P0) Deferred-tail regression tests: build_proposal + authorize succeed on
   a synthetic DIRTY-tail ledger; the RECONCILIATION entry links off the last
   valid ancestor; strict/post-anchor verify accepts the result.

## Updated Knowledge

None beyond the fix; #271 Phase-3 parser work will absorb the regex family later.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
