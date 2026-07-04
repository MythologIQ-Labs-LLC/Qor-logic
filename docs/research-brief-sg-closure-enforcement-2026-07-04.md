# Research Brief: SG Closure Enforcement (GH #249)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #249 -- a Shadow Genome pattern may only close with an executable check or a recorded can't-automate decision
**Scope**: current closure machinery, enforcement precedent in the countermeasure corpus, smallest enforcement seam, backfill burden

---

## Executive Summary

Closure is currently implicit: the structured event schema (`addressed`/`addressed_reason` with enum `issue_created|remediated|stale`) carries no field naming an enforcer, the two-stage `mark_addressed` flow verifies a PASS audit but never verifies that anything executable now guards the pattern, and the countermeasure doctrine cites enforcers only by convention (32 of 40 entries do; 8 are prose-only). The local structured log has never closed an event (0 of 3 addressed). Smallest seam: (1) a `closure_enforcer` schema field required when an event flips to `addressed=true` via `remediated`, validated by `mark_addressed` (test path, `qor.scripts.*`/`qor.reliability.*` module, gate step reference, or `cannot-automate: <justification>`); (2) a WARN-only doctrine lint over the countermeasure corpus flagging entries without an enforcer citation. Zero backfill required (grandfather: field mandatory only on new closures; lint WARN-only over existing entries).

## Findings

1. **Schema gap**: `qor/gates/schema/shadow_event.schema.json:67-84` -- `addressed: bool`, `addressed_ts`, `addressed_reason` enum `issue_created|remediated|stale`, `addressed_pending` (Phase 36 two-stage flip). No enforcer field; `remediated` does not distinguish executable-check closure from operator fiat.
2. **Contract gap**: `qor/scripts/remediate_mark_addressed.py:64-69` (stage 1 `mark_addressed_pending`) and `:112-134` (stage 2 `mark_addressed`) -- stage 2 re-verifies the audit artifact (PASS + `reviews_remediate_gate` match) but accepts closure with no evidence that an enforcer exists.
3. **Corpus precedent**: `qor/references/doctrine-shadow-genome-countermeasures.md` -- 40 `## SG-` entries; ~32 cite executable enforcement inline (e.g., SG-033 names `tests/test_shadow_genome_doctrine.py::test_no_positional_calls_to_keyword_only_functions`; SG-SkillProtocolBypass names `qor.reliability.gate_chain_completeness` + the CI job; SG-SecretLeakAtSeal-A names `qor.scripts.secret_scanner` at Step 4.6.5); ~8 are prose-only or deferred (SG-016/017/019/020/021 manual verification hints, SG-037 deferred test, SG-DoDImplicit-A V1 WARN-only).
4. **Never-exercised closure**: `docs/PROCESS_SHADOW_GENOME.md` -- 3 events, all `addressed: false`. The enforcement lands before the closure path has accumulated bad precedent.
5. **Prior art for the lint shape**: Phase 164's "generate-not-assert" and the pre-audit lint ladder (audit Step 0.6) give the wiring point; accountable-os `lint-migration-rls.mjs` gives the allowlist-with-reasons model (here: `cannot-automate:` justifications are the allowlist).

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| SG closure is governed | Only the audit-PASS half is governed; enforcer existence is unverified | DRIFT |
| Doctrine entries document countermeasures | True, but by convention only -- 20% lack an executable enforcer citation | PARTIAL |
| Enforcement needs heavy backfill | No -- 0 events closed to date; grandfathering costs nothing | MATCH (cheap) |

## Recommendations

1. **Schema + contract (fail-closed)**: add `closure_enforcer: string|null` to `shadow_event.schema.json` with an `if-then` rule (required non-null when `addressed==true` AND `addressed_reason=='remediated'`); `mark_addressed` gains a required `closure_enforcer` parameter validated against four accepted forms: existing `tests/test_*.py` path, importable `qor.scripts.*`/`qor.reliability.*` module, `/qor-<skill> Step N` gate reference, or `cannot-automate: <justification >=50 chars>`. Invalid or missing -> raise, no closure.
2. **Doctrine corpus lint (WARN-only)**: new `qor/scripts/sg_closure_lint.py` walking `## SG-` entries in the countermeasure doctrine and flagging entries whose body cites no test path, module, gate step, or explicit cannot-automate marker; wire into audit Step 0.6 ladder (`|| true`) and expose via the generic runner for the nightly ladder later.
3. **Skill prose**: /qor-remediate Step 4/6 documents the new parameter; doctrine-governance-enforcement gains the closure rule via /qor-document.
4. **Grandfather**: existing 3 unaddressed events unaffected; existing doctrine entries surface as WARN counts only (8 expected), with the lint's finding list doubling as the backfill worklist.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
