# Research Brief

**Date**: 2026-07-13T14:08:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #239 -- living behavioral spec corpus with delta-fold (Phase A)
**Scope**: spec grammar + deterministic merge module; gate-chain integration deferral analysis

---

## Executive Summary

GH #239 is fully unimplemented (no PR; no qor/specs/ tree; no spec_lint or
spec_merge modules; plan.schema.json carries no spec_deltas). The issue itself
structures the work as three phases and marks Phase A "small, shippable
first" -- the deterministic grammar + merge module with tests, no gate-chain
wiring. Phase B (schema + skill wiring + fold-inside-substantiate) and Phase C
(requirement-level verify) carry the cycle's real risks (seal-gate timing,
term-drift, skill-size budgets on two near-cap SKILL.md files) and are
correctly a separate, later cycle. This cycle ships Phase A per the issue's
own sequencing.

## Findings

### Nothing exists yet; the named analogues are style precedents only
- No qor/specs/ directory (glob verified); no spec_lint.py / spec_merge.py.
- qor/gates/schema/plan.schema.json declares feature_inventory_touches but no
  spec_deltas array.
- qor/scripts/feature_index_verify.py and qor/scripts/check_variant_drift.py
  are the house style for pure stdlib check modules with CLI mains.

### The audit taxonomy is already ready for Phase B
- qor/gates/schema/audit.schema.json:40 -- `specification-drift` is a live
  findings category; Phase B's delta lint can route into it without a schema
  change.

### Registration surfaces for Phase A are minimal
- qor/scripts/governance_index.py:54-63 -- the fail-closed `unregistered`
  scan covers root *.md and docs/*.md ONLY; a grammar reference at
  qor/references/spec-grammar.md needs no registration (registered anyway as
  a curated Tier 2 row for discoverability).
- The README doctrine-inventory test locks doctrine-*.md names only; naming
  the grammar file spec-grammar.md (it is a format reference, not a doctrine)
  keeps that lock untouched.

### Grammar and merge semantics (from the issue, made precise)
- Spec file: `qor/specs/<capability>/spec.md`; `### Requirement: <name>`
  headings; each requirement body carries exactly one RFC-2119 SHALL/MUST
  statement and >= 1 nested `#### Scenario: <name>` in GIVEN/WHEN/THEN
  bullets; observable behavior only.
- Delta file: `## ADDED Requirements` / `## MODIFIED Requirements` /
  `## REMOVED Requirements` sections; ADDED and MODIFIED carry complete
  requirement blocks (MODIFIED restates whole -- heading-keyed
  match-and-replace is what makes the merge deterministic); REMOVED lists
  requirement headings.
- Merge failure semantics: MODIFIED/REMOVED naming an absent heading is an
  ERROR (fail loudly), never a silent skip -- the concurrency conflict
  surface identified in the dossier.

### Phase B/C deferral grounds (recorded, not hand-waved)
- Fold-inside-substantiate needs a new seal-gate step + ledger field +
  substantiate.schema change; the delta lint belongs at audit as a pre-pass
  (late Step-6 failure would burn re-audit cycles).
- /qor-plan and /qor-audit SKILL.md are at 25.2 KB and 38.6 KB -- wiring
  prose must go through progressive disclosure; qor-audit has ~1.3 KB
  headroom under the lock.
- Phase C's per-requirement verify maps onto qa_evidence's deferred coverage
  pillar (qor/scripts/qa_evidence.py) -- a natural later home.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| Issue: "specification-drift VETO category" exists for Phase B | audit.schema.json:40 | MATCH |
| Issue: FEATURE_INDEX is an index, not behavior | docs/FEATURE_INDEX.md row shape | MATCH |
| Issue: nothing spec-shaped exists | zero spec surfaces corpus-wide | MATCH (gap confirmed) |

## Recommendations

1. (P1) Ship Phase A: `qor/scripts/spec_lint.py` (`check(text, strict=True)`
   -> findings list; CLI exit 0/1) + `qor/scripts/spec_merge.py`
   (`apply(spec_text, delta_text) -> str`; heading-keyed; error on absent
   MODIFIED/REMOVED targets; idempotent for ADDED-only re-application is NOT
   claimed -- re-adding an existing heading is an error too, preserving
   determinism) + `qor/specs/` scaffold with a README signpost +
   `qor/references/spec-grammar.md` (the format contract, quotable by B).
2. (P1) TDD: grammar pass/fail quadrants; merge ADDED/MODIFIED/REMOVED;
   error-on-absent-target; error-on-duplicate-ADDED; order preservation;
   round-trip determinism (same inputs -> byte-identical output).
3. (P2) Record Phase B/C as the deferral roadmap in the seal entry and the
   final handoff (schema wiring, audit pre-pass, fold-after-PASS with ledger
   hash, qa_evidence coverage-pillar mapping).

## Updated Knowledge

The spec corpus rides UNDER the gate chain (the issue's non-goal explicitly
rejects enabler-style ungated specs); Phase A therefore ships pure tools with
no chain authority -- authority arrives only with Phase B's wiring.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
