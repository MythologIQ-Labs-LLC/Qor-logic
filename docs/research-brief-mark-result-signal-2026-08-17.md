# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: GH #341 (`mark_addressed` returns `(0, [])` indistinguishably for already-addressed batches)
**Scope**: caller surface; result-type design; per-operation semantics of the third signal

---

## Executive Summary

The flip helpers silently skip events whose addressed-state makes them ineligible, so a caller cannot distinguish "nothing matched" (unknown ids, surfaced in `missing` per SG-032) from "nothing to do" (all already addressed) -- both read `(0, [])`. Eight unpack sites exist (seven in tests, one prose snippet in the qor-remediate skill at 8.1 KB, far from any size band). Design: a `MarkResult` NamedTuple `(changed, missing, skipped)` returned by `mark_addressed`, `mark_addressed_pending`, and `correct_closure_enforcers`, where `skipped` carries the ids that were known but excluded by the operation's own eligibility guard -- already-addressed for the mark path, not-remediated or citation-already-equal for the corrective path. Tuple growth breaks two-element unpacking by design; all eight sites update deliberately, which is the honest cost of making the signal impossible to ignore.

## Findings

### 1. The silent-skip sites (verified at v0.150.0)

- `_flip_event_fields` (line 50): mutates only `event["id"] in target and not event["addressed"]`; addressed ids in the target vanish from every output.
- `_flip_event_fields_per_event` (line 73): non-corrective path `if event.get("addressed"): continue` (line 101); corrective path skips not-remediated events and equal-citation no-ops -- three skip classes, none surfaced.
- Return sites: `mark_addressed_pending` line 119, `mark_addressed` line 150 (legacy branch; mapping branch above it), `correct_closure_enforcers` line 169.

### 2. Caller surface

Seven test unpack sites (`tests/test_remediate.py:446`, `test_remediate_enforcer_edges.py:92,123`, `test_remediate_per_event_enforcers.py:52,112,133`, `test_sg_closure_enforcement.py:63`) and one prose snippet (`qor/skills/sdlc/qor-remediate/SKILL.md:130`). The qor-audit Step 4.2 snippet calls without unpacking. No production importer unpacks the result (the remediation flow is skill-driven).

### 3. Semantics of `skipped`

One concept covers all three operations without braiding: ids that were present and known but excluded by the operation's eligibility guard. For `mark_addressed`/`mark_addressed_pending` that is "already addressed" (the #341 case); for `correct_closure_enforcers` it is "not remediated" or "citation already equal". A caller distinguishing outcomes needs exactly (mutated, unknown, ineligible); finer sub-classification would encode per-operation branches into the shared type for no consumer.

### 4. Compatibility posture

A three-field NamedTuple deliberately breaks `a, b = ...` unpacking -- the alternative (a 2-iterating tuple subclass) would preserve the very ignorability the issue exists to remove. All eight sites are governed surfaces in this repo; deliberate update is cheap and declared.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #341: zero reads as failure when it means already-done | Verified: both flip helpers drop ineligible ids from all outputs | MATCH |
| #341: keep all-or-nothing validation order and SG-032 surface | Design touches only the return shape; validation/attestation order and `missing` untouched | MATCH |

## Recommendations

1. Phase 230 (feature): `MarkResult(changed, missing, skipped)` across the three public functions, helpers threaded, eight call sites updated deliberately, behavioral tests for both skip classes red-first.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
