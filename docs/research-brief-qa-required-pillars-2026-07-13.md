# Research Brief

**Date**: 2026-07-13T06:18:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #269 -- qa_evidence: required pillars so skipped security/stability/coverage cannot yield a production-grade PASS
**Scope**: verdict logic, artifact schema, consumers, backward compatibility

---

## Executive Summary

The issue's premise is true today and verified live: `qa_evidence.build_payload`
computes `verdict = "FAIL" iff any pillar status == "fail"` -- a payload whose
security, stability, and coverage pillars are ALL `skip` yields `PASS`
(`qor/scripts/qa_evidence.py:70`), and a consumer of `qa.json` cannot distinguish
"ran everything, all green" from "ran only regression". The skip-visible design is
deliberate (anti-half-measure transparency per the verification-closure doctrine),
so the fix is an OPT-IN policy layer: an adoption-mode default that preserves
current behavior byte-for-byte, plus a production posture where declared required
pillars must be `pass` -- a required `skip` fails the verdict.

## Findings

### F1. Verdict logic (verified live)

- `qor/scripts/qa_evidence.py:70`: `verdict = "FAIL" if any(p["status"] == "fail"
  for p in pillars.values()) else "PASS"`. Deferred pillars default to
  `{"status": "skip", "note": ...}` (lines 62-68); regression is the only pillar
  derived from real evidence (`_regression_pillar`, feature-index tally).
- Doctrine records the posture as intentional transparency, not a verdict rule:
  `qor/references/doctrine-verification-closure-integrity.md` ("skip is visible
  per-pillar but does not fail the verdict").

### F2. Schema and freeze posture

- `qor/gates/schema/qa.schema.json`: `verdict` enum `["PASS","FAIL"]` (strict);
  pillar `status` enum `["pass","fail","skip"]`; `additionalProperties: true`.
- `qa` is REGISTERED (`qor/gates/SCHEMA_REGISTRY.json:14`); modifying a registered
  schema is not a net-new schema, so `gate_schema_freeze_lint` (presence-based)
  is not tripped. Adding optional `policy` / `required_pillars` fields is
  additive; adding a THIRD verdict value would break the strict enum for
  existing consumers -- keep PASS/FAIL and encode the posture in fields.

### F3. Consumers and blast radius

- `qor/scripts/ac_close_guard.py:96-97`: reads `verdict` via
  `gate_chain.read_phase_artifact("qa", ...)` and WARNs (never blocks) when not
  PASS -- V1 WARN-first, `--enforce` reserved. A production-policy FAIL flows
  through this existing seam with zero close-guard changes (the verdict itself
  carries the policy's outcome).
- `/qor-substantiate` invokes the close guard with `--qa-session` (skill prose);
  no other verdict consumers found.

### F4. Backward compatibility

- Old `qa.json` artifacts carry no `policy` field; consumers treating absence as
  adoption-mode need no change. `build_payload` keeps its exact current output
  when the new keywords are omitted (adoption default) -- locked by regression
  test. Existing tests: `tests/test_qa_evidence.py` (pillar shapes, verdict
  rules, skip notes).

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| doctrine-verification-closure-integrity: skip visible, not failing | True at qa_evidence.py:70 | MATCH (by design; the gap is the missing opt-in strict posture) |
| Release/compliance consumers can require evidence | No mechanism exists | DRIFT (the issue's ask) |

## Recommendations

1. (P0) `build_payload(..., policy="adoption", required_pillars=None)`:
   production policy + declared required set -> a required pillar with status
   `skip` (or missing) fails the verdict; `fail` fails under both policies.
   Artifact records `policy` and `required_pillars` when provided.
2. (P0) Schema: optional `policy` enum `["adoption","production"]` and
   `required_pillars` array (items from the closed pillar set); `verdict` enum
   unchanged.
3. (P1) Doctrine paragraph: the two postures and when to use each.
4. (P1) CLI passthrough if qa_evidence has a CLI entry (verify at plan time).

## Updated Knowledge

None; the transparency posture stays documented, gaining the opt-in strict mode.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
