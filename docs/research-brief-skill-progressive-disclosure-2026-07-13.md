# Research Brief

**Date**: 2026-07-13T06:41:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #266 -- qor-audit + qor-substantiate SKILL.md within 1 KB of the 40 KB EXCEEDED budget
**Scope**: movable-prose inventory, guardrail-test constraints, safe reduction target

---

## Executive Summary

qor-audit sits at 40,890 bytes and qor-substantiate at 40,935 (verified live;
EXCEEDED at 40,960 per `qor/scripts/skill_size_budget_lint.py:24`) -- one more
wiring paragraph to either file blocks the next seal. A targeted
progressive-disclosure pass can move ~2-3 KB of rationale prose per skill into
their already-cited references/ files. The issue's deeper "comfortably under
30 KB" aspiration would require restructuring the binding spine itself and is
DEFERRED with rationale: 45+ tokens across both files are hard-locked by the
corpus-consolidation, tag-timing, seal-flow-ordering, capability-declaration,
and staging-gates guardrail tests, and every step header, command token, and
ABORT/VETO invariant must remain inline by contract.

## Findings

### F1. Sizes and thresholds (verified live)

- qor-audit/SKILL.md: 40,890 bytes (70 under EXCEEDED); qor-substantiate/SKILL.md:
  40,935 (25 under, after the Phase 176 amendment). WARN=25,600 / EXCEEDED=40,960.

### F2. Guardrail inventory (the binding constraint set)

- `tests/test_skill_corpus_consolidation.py`: parametrized spine locks --
  AUDIT_INVARIANTS (9 exact ABORT/VETO sentences), AUDIT_STEPS (13 step
  headers), AUDIT_COMMANDS (9 tokens), SUBST_INVARIANTS (4), SUBST_STEPS (12),
  SUBST_COMMANDS (12), plus relocated-rationale tests asserting specific
  sentences LIVE IN references/ and NOT inline.
- `tests/test_seal_flow_ordering.py` + `tests/test_substantiate_tag_timing_wired.py`:
  step-ordering + bump/tag token placement locks (Constraints section included).
- `tests/test_qor_substantiate_capability_declarations.py`: `## Step
  Prerequisites` header + all 12 step IDs + per-step "Phase 75"/"Prerequisite"
  cross-references.
- `tests/test_substantiate_staging_gates.py` (Phase 176): Step 9.5 gates
  argument + <40,960 budget invariant + variant equality.
- `tests/test_skill_doctrine.py`: every `references/X.md` citation must resolve.

### F3. Movable blocks (rationale prose, per-block estimates)

qor-audit (~2.1 KB safely movable): Step 1 adversarial-mode dispatch rationale
(-> references/adversarial-mode.md, already cited); Infrastructure Alignment
Phase 99 V2 ramp narrative (-> references/phase37-subpasses.md, already cited);
Environment-section Phase 75 tolerance narrative (shared boilerplate);
Self-Application origin narrative (-> adversarial-mode.md).

qor-substantiate (~2.2 KB safely movable): Step 6.5 phase-class rationale and
Step 6.8 no-override philosophy (-> references/seal-gate-ladder.md, already
cited); Step Prerequisites table annotations (condense, structure + 12 IDs
preserved); Step 4.6 / 4.7.5 operator-flow explanations (-> seal-gate-ladder.md).

Phase 135 precedent gotchas: new reference files must be registered in the
glossary's referenced_by when terms move; wiring tests lock exact tokens;
relocated sentences must appear in the target reference (the consolidation
tests assert both directions).

### F4. Scope decision evidence

The failure mode GH #266 names is "one more wiring paragraph crosses EXCEEDED
and blocks a seal". Restoring >= 2 KB headroom per skill removes that failure
mode for many phases of normal wiring growth; the 30 KB aspiration requires
spine restructuring against the F2 lock set (high regression risk, low
marginal benefit now). A new budget-invariant test at 39 KB per skill locks
the recovered headroom so growth is visible before it is critical.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Progressive-disclosure doctrine: rationale in references/, contract inline | ~4-5 KB of rationale currently inline across both skills | DRIFT (the pass) |
| Guardrail tests lock the spine | Verified inventory (F2) | MATCH (the constraint honored) |

## Recommendations

1. (P0) Move the F3 blocks into their already-cited references; keep every F2
   token inline byte-exact.
2. (P0) Extend the Phase 176 budget test: BOTH skills < 39,936 bytes (39 KB)
   -- locks the recovered headroom.
3. (P1) Record the 30 KB aspiration as deferred on GH #266 with the F4
   rationale.

## Updated Knowledge

None; the pass applies existing doctrine (progressive disclosure) to two files.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
