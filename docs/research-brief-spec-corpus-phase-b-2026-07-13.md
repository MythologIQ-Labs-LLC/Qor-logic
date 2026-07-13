# Research Brief

**Date**: 2026-07-13T16:44:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #277 -- spec corpus Phase B (gate-chain wiring) + Phase C (per-requirement verify)
**Scope**: delta lifecycle conventions; the three near-cap skill seams; qa_evidence coverage producer

---

## Executive Summary

Phase A (v0.130.0) shipped the tools; #277 gives them chain authority. All
wiring seams verified live: plan.schema.json takes an additive `spec_deltas`
property; the two big governance skills have ~400 bytes of headroom each
(qor-audit 39,536 / qor-substantiate 39,502 vs the 39,936 lock), so wiring
steps must be two-line pointers into references/ files; qa_evidence's
coverage pillar is explicitly "deferred" (qa_evidence.py:30) and is Phase C's
designed home. The delta needs a lifecycle convention Phase A did not define:
where delta documents live, when they fold, and what consumes them.

## Findings

### Delta lifecycle (the design gap Phase A left open)
- Phase A defined delta GRAMMAR (spec-grammar.md) but not delta LOCATION or
  consumption. Convention decided by composition with existing seams:
  `qor/specs/<capability>/deltas/<session-id>.md`, authored at plan time,
  declared in the plan artifact's `spec_deltas` array, linted at audit,
  FOLDED into `qor/specs/<capability>/spec.md` inside substantiate after
  PASS, then deleted (git history preserves the delta; the fold is the
  surviving state - mirrors how plans are point-in-time while the corpus is
  current-truth).
- Fold evidence: the folded spec's LF-normalized sha256 lands in the seal
  entry as a `**Spec Corpus Hash**:` field and in substantiate.json as an
  optional `spec_corpus_hash` property (additive edit to an EXISTING schema;
  the freeze lint governs new schema files only -- gate_schema_freeze_lint
  compares directory names against the registry).

### Verified seams
- qor/gates/schema/plan.schema.json:71 (`new_ceremony_artifacts` precedent
  for optional structured arrays); no `spec_deltas` today.
- qor/skills/governance/qor-audit/SKILL.md = 39,536 B; qor-substantiate =
  39,502 B; headroom lock 39,936 (tests/test_substantiate_staging_gates.py).
  Pointer-steps of ~120 bytes each fit; prose goes to
  `references/spec-delta-pre-pass.md` (audit) and the seal-gate-ladder
  reference (substantiate).
- qor/scripts/qa_evidence.py:24,30 -- PILLARS includes "coverage" with the
  skip note "deferred: coverage-posture pillar follow-on"; build_payload
  accepts a coverage dict. Phase C produces it.
- audit.schema.json:40 `specification-drift` -- the pre-pass's VETO category
  (no schema change).

### Phase C shape (honest V1)
- Per-requirement verify at seal time over the session's deltas: every
  ADDED/MODIFIED requirement must (a) pass the grammar lint, (b) name at
  least one scenario, and (c) carry grep-evidence that the requirement's
  declared surface exists (the `spec_deltas` array gains optional
  `evidence` (a repo path) per entry). Results render as the qa_evidence
  coverage pillar payload {{checked, verified, unverified[]}} -- partial
  coverage stays explicit per the module's anti-half-measure docstring.
- Scenario-intent-vs-implementation (full correctness) stays a Judge duty
  documented in the pre-pass reference; V1 verifies structure + existence,
  not semantics (no fabricated verification).

### Self-application (the acceptance demo)
- This cycle authors the FIRST live capability spec: qor/specs/spec-corpus/
  with a delta describing the fold behavior itself; this session's seal
  performs the first real fold and records the first Spec Corpus Hash.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| #277: audit pre-pass routes into specification-drift | category live at audit.schema.json:40 | MATCH |
| #277: fold runs inside substantiate after PASS only | substantiate flow + seal entry are the seams; additive schema property suffices | MATCH |
| #277: Phase C maps onto the qa coverage pillar | qa_evidence.py:30 marks it deferred by design | MATCH |

## Recommendations

1. (P1) `spec_lint --delta` mode (section structure + inner blocks reuse
   check()); `spec_fold.py` (fold_session_deltas: read plan artifact
   spec_deltas, apply spec_merge per capability, write spec, delete delta,
   return {{capability: sha256}}).
2. (P1) plan.schema.json additive `spec_deltas` (capability, delta_path,
   ops[], evidence?); substantiate.schema.json additive `spec_corpus_hash`.
3. (P1) Pointer-steps in qor-plan (Step 3b: author delta when behavior
   changes), qor-audit (Step 0.7: delta lint pre-pass || VETO
   specification-drift), qor-substantiate (Step 7.9: fold after gates,
   record hash) -- prose in references/.
4. (P2) `spec_requirement_verify.py` producing the qa coverage payload.
5. (P2) Self-apply: first spec + delta folded by this session's own seal.

## Updated Knowledge

Deltas are consumables: authored at plan, gated at audit, folded and deleted
at seal -- the corpus is current-truth, git history is the delta archive.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
