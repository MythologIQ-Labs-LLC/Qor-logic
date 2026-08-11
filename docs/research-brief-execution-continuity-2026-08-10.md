# Research Brief

**Date**: 2026-08-10
**Analyst**: The Qor-logic Analyst
**Target**: GH #285 — provider-neutral execution-continuity semantics for the lifecycle gates
**Scope**: What exists, what must be built, what must not be duplicated, and whether this fits one phase

---

## Executive Summary

#285 is buildable now: its upstream dependency is closed and a reviewed contract version exists. But it **cannot ship as one phase**, and the blocker is not scope judgement — it is a measured size lock. Two of the seven skills it must modify have 520 and 360 bytes of headroom against a test-enforced 39,936-byte cap.

The most useful finding is that the hardest-sounding requirement is already half-built. `intent_lock` performs exact-revision binding today; continuity is its cross-provider generalisation, not a new mechanism. Building a parallel one would be the significant error available here.

## Findings

### 1. The upstream contract is pinnable, but only from prose

The upstream line's `ADR-0015` (provider-neutral execution control plane) declares `**Contract version:** 1.0`. Two schemas shipped alongside it: an execution-continuity contract and an execution-admission contract.

Neither schema carries a version field. Their `$id` is a bare URL with no version segment; top-level keys are `$schema`, `$id`, `title`, `type`, `$defs`, `oneOf`. So a downstream pin can cite "ADR-0015 contract version 1.0" but **nothing in the artifact would contradict a stale pin**. The pin is assertable, not mechanically verifiable.

This satisfies #285's requirement ("implementation must pin a reviewed compatibility version") and simultaneously weakens it. Worth raising upstream; it does not block.

### 2. `intent_lock` already does exact-revision binding

`qor/reliability/intent_lock.py` (199 lines) captures SHA-256 of plan + audit + git HEAD at capture and re-verifies on drift (`_head_commit` at line 34, `git rev-parse HEAD`).

#285 asks that plans "bind continuation and verification to exact revisions" and that "revision mismatch prevents continuation". That is what intent-lock does, scoped to one session. Continuity generalises it across providers: a successor reads a predecessor's checkpoint and must verify the same revision.

**The seam is to extend intent-lock's contract, not to invent a second revision-binding mechanism.** Two mechanisms disagreeing about what "same revision" means is the failure this project has repeatedly catalogued — one concept with two authorities.

### 3. `inconclusive` is genuinely new

`grep -rln "inconclusive" qor/scripts/ qor/reliability/ qor/gates/schema/` returns nothing. Today every gate is binary: PASS/VETO, verified/rejected, exit 0/1. #285 requires a third outcome that is neither success nor product rejection, routed differently by validate and remediate.

This is the conceptually deepest change in the issue. It touches verdict handling in audit, substantiate, validate, and remediate, and it cannot be expressed by reusing an existing enum.

### 4. `plan.schema.json` has no contract-pin property

21 properties; the nearest analogue is `spec_deltas`. A new additive property is required. Precedent is good — `required_gate_artifacts` (Phase 168) and `spec_deltas` (Phase 192) were both added additively without breaking prior sessions.

### 5. The size lock forces a split, and the split is not optional

| Skill | bytes | slack to 39936 | lock |
|---|---|---|---|
| research | 9,712 | +30,224 | no |
| plan | 24,920 | +15,016 | no |
| **audit** | **39,416** | **+520** | **enforced** |
| implement | 19,034 | +20,902 | no |
| **substantiate** | **39,576** | **+360** | **enforced** |
| validate | 9,890 | +30,046 | enforced |
| remediate | 7,543 | +32,393 | no |

Phase 207 needed two trims for a three-line edit to `qor-substantiate`. #285 adds audit classifications, fail-closed checks, and substantiation evidence requirements to exactly these two files. It will not fit.

Both already carry `references/` directories (6 and 3 files), so the disclosure *pattern* is precedented.

**But the operation is not mechanical, and an earlier draft of this brief said it was.** 49 test
files assert content inside these two skills. The two highest-yield disclosure candidates are
guarded directly: `findings_categories` by 14 files and `Step Prerequisites` by 3. Every line moved
to `references/` must be checked against those assertions, because a wiring test that pins an exact
token in `SKILL.md` fails the moment the token moves. Phase A is bounded and precedented; it is not
cheap, and planning it as cheap would repeat the estimation error this brief otherwise warns about.

### 6. The four cross-authorities are settled

#39, #51, #108, #139 are all CLOSED. They must be referenced as boundaries, not reopened. #51 matters most concretely: checkpoints must reference stable ledger identity (`entry_id`, 26 lines, content-addressable) rather than sequential entry numbers.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Upstream dependency shipped | Plus #65 closed; ADR-0015 v1.0; schemas present | MATCH |
| "pin a reviewed compatibility version" | Version exists in ADR prose only, not in the schema artifact | DRIFT — assertable, not verifiable |
| Continuity needs new revision binding | `intent_lock` already binds plan+audit+HEAD | DRIFT — extend, do not duplicate |
| `inconclusive` is a routing change | Concept absent from the codebase entirely | MATCH (larger than it reads) |
| Ships in one governed phase | Two target skills have 520/360 bytes of headroom | DRIFT — split required |

## Recommendations

1. **Two phases, in this order.**
   - **A — headroom.** Progressive-disclosure pass on `qor-audit` and `qor-substantiate` into their
     existing `references/` dirs. Independently valuable and unblocks everything, but guarded by 49
     test files (14 on `findings_categories` alone) -- budget for per-token verification, not a
     quick move.
   - **B — the continuity contract.** Schema property + lint, glossary, doctrine, the semantics across all seven skills, and the 13 behavioural tests.
2. **B must be atomic.** #285's acceptance criteria require documentation, glossary, schema/lint, and behavioural tests to ship in the same governed phase. B cannot be split further without violating the issue. It will be a large phase and that is the issue's design, not drift.
3. **Extend `intent_lock`; do not build a parallel checkpoint verifier.**
4. **Reference `entry_id` for checkpoint identity**, per #51.
5. **Raise the unversioned-schema gap upstream** — a contract that cannot be mechanically pinned invites silent staleness downstream.
6. Do not start B in the same session as A. A changes the two files B then edits heavily; sequencing them apart keeps each seal's diff legible.

## Updated Knowledge

Nothing in `docs/SHADOW_GENOME.md` requires amendment. The size-lock constraint is already recorded as the GH #266 closure holding, and this brief is its first use as a *planning input* rather than a warning — the lock did its job by making the split visible before a plan committed to one phase.

---

_Research complete. Findings are advisory — implementation decisions remain with the Governor._
