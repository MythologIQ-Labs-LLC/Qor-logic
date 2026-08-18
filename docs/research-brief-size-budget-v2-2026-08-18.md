# Research Brief

**Date**: 2026-08-18
**Analyst**: The Qor-logic Analyst
**Target**: GH #320 (V2: enforce skill-corpus drift at seal, once V1 disclosure has produced drift data)
**Scope**: entry-condition assessment; the exact flip surface; safety and bindings

---

## Executive Summary

The entry condition is met on both halves. Value: V1 disclosure has produced the drift data it was waiting for -- three governance skills sit in the WARN band (qor-audit 38.8 KB, qor-substantiate 36.3 KB, qor-plan 25.4 KB), qor-audit's EXCEEDED headroom shrank from 1,273 to 1,191 bytes across two consecutive phases (228, 232) that each had to budget skill text against it, and two phases (222, 229) hit hard size constraints mid-implementation. Safety: nothing is over EXCEEDED, so flipping costs nothing today and structurally prevents the breach class tomorrow. The flip surface is exactly one ladder-table row: Step 4.6.9's command drops `|| true`, its Policy column reads ABORT, and its Notes state the V2 posture -- WARN-band findings remain advisory, only EXCEEDED aborts, which is already the only condition on which the CLI exits 1. The ladder parser accepts ABORT (`POLICY_VALUES` at `substantiate_gates.py:33`), and no existing test pins the row's WARN policy (the wiring tests bind invocation presence and order only), so the change is additive-safe with one new red test binding the ABORT posture.

## Findings

### 1. Entry condition, measured

- Current lint output: 3 WARN findings, 0 EXCEEDED, exit 0 -- the flip aborts nothing today.
- qor-audit trajectory: 39,687 bytes after Phase 228, 39,769 after Phase 232 -- 1,191-byte headroom and shrinking, with both phases' plans carrying explicit byte arithmetic against the bound. The Phase 222 slack-floor test and the Phase 229 27-byte budget are the same pressure observed at the substantiate skill.
- The V1 design note anticipated exactly this conversion: "CLI exits 1 when any EXCEEDED finding is present so V2 can convert to a hard ABORT by removing the `|| true`".

### 2. Flip surface and bindings

- One row in the Step 4.6 ladder table (SKILL.md line 246): command `... || true` -> `... || ABORT`, Policy WARN -> ABORT, Notes amended.
- Parser: `substantiate_gates.POLICY_VALUES` includes ABORT; row order untouched.
- Tests: `test_skill_size_budget_substantiate_wiring.py` binds invocation presence, row removal, and order -- all survive; nothing binds the WARN policy. The dogfooding anchor in `test_skill_size_budget_lint.py` (qor-audit categorized `skill-over-warn-threshold`) survives because WARN-band behavior is unchanged.
- Byte cost of the row edit is approximately zero net (true -> ABORT is +1 character; Notes rewording constrained by the substantiate skill's own 2,700-byte slack floor, currently 2,727).

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #320: flip once V1 has produced drift data | Three-skill WARN band, two-phase headroom shrinkage, two hard-constraint incidents | MATCH (condition met) |
| V1 note: exit-1-on-EXCEEDED enables the flip | Verified in the lint's contract and current exit-0 state | MATCH |

## Recommendations

1. Phase 234 (feature): the one-row flip plus a red-first wiring test binding the ABORT posture; #320 closes with the measured entry-condition record.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
