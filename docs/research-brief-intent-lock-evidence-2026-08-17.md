# Research Brief

**Date**: 2026-08-17
**Analyst**: The Qor-logic Analyst
**Target**: GH #332 (audit carry-forward and the seal-time intent lock are in structural conflict)
**Scope**: the lock's storage and verify surface; why overrides are undecidable; the Direction 3 design; the CI-visibility asymmetry

---

## Executive Summary

The lock stores hashes and nothing else (`plan_hash`/`audit_hash`, LF-normalized, plus a HEAD-ancestry anchor), so when a verdict-directed correction changes the plan between capture and seal, `DRIFT: plan` fires with an unrecoverable referent -- the audited bytes were never committed, and the override rests on testimony. The issue's own analysis names Direction 3 (store enough to prove equivalence) as the smallest change that makes the recurring override decidable, and the repo state sharpens #16798's asymmetry into a measurement: 7 legacy lock records are tracked, the other 127 (every session since phase 59) sit under a `.gitignore` entry, so CI cannot see the lock at all. Phase 231: capture snapshots the audited bytes beside the record; verify on DRIFT emits the unified diff (testimony becomes evidence); the sealed session's lock family joins the executable staging ceremony via a deliberate force-add, making the referent recoverable and CI verification possible going forward. The larger contract change (Direction 1, verdict-authorized deltas) and the CI-side verify job are declared follow-ons, not this phase.

## Findings

### 1. The lock today (verified at v0.151.0, `qor/reliability/intent_lock.py`, 209 lines)

- `capture` stores `{session, plan_path, plan_hash, audit_path, audit_hash, head_commit, captured_ts}` at `.qor/intent-lock/<session>.json` (line 93-134); repo-relative paths since Phase 172; LF-normalized hasher since Phase 218 (GH #318).
- `verify` re-hashes the live files and prints bare `DRIFT: plan` / `DRIFT: audit` with no further information (lines 152-160); HEAD check is ancestry, not equality (Phase 43).
- On drift there is nothing to diff against: the audited bytes exist only if they happen to survive on disk or in history. In the Phase 223 incident they did not.

### 2. The CI-visibility asymmetry, measured

`.gitignore:18` lists `.qor/intent-lock/`; `git ls-files` shows exactly 7 tracked records (sessions through phase 59, tracked before the ignore landed) against 134 on disk. Every modern lock record is operator-local -- which is precisely why intent_lock is "the one gate in the ladder with no CI enforcement" (#16798): CI has no artifact to check. Legacy records are grandfathered with absolute paths (pre-172), so un-ignoring the whole directory would trip the publication-boundary lint; a per-session deliberate force-add of NEW records (relative paths, boundary-clean) is the safe path.

### 3. Direction 3 design

- Capture additionally writes `<session>.plan.snapshot` and `<session>.audit.snapshot`: the exact LF-normalized bytes the stored hashes are computed over (self-consistent by construction).
- Verify, on hash mismatch, loads the snapshot when present and prints a unified diff (bounded head) after the `DRIFT:` line -- the override reviewer sees exactly what changed since capture, the Phase 218 equivalence argument becomes mechanical, and a carried-correction delta is visibly the delta the verdict named.
- Legacy records without snapshots verify exactly as today (graceful degradation; no retroactive migration).
- `seal_stage`'s ceremony gains the sealed session's `.qor/intent-lock/<session>*` family via `git add -f` (the directory stays ignored so 127 legacy operator-local records stay local). The committed record+snapshot make the referent recoverable forever and give a future CI job something to verify.

### 4. Explicitly out of scope, with reasons

- Direction 1 (structured verdict-authorized deltas) changes the audit-report contract and the lock's verify semantics together -- a phase of its own once diffs have accumulated showing what authorized deltas look like in practice.
- Direction 2 (capture after corrections) narrows coverage and the issue itself notes it does not fix the general case.
- The CI-side verify job needs the committed artifacts this phase creates; follow-on once a few sealed sessions carry them.

## Blueprint Alignment

| Claim | Actual Finding | Status |
|---|---|---|
| #332: the lock's referent is unrecoverable on carry-forward | Verified: hashes only, no snapshot, bytes never committed | MATCH |
| #16798: no CI enforcement | Measured: 7 of 134 records tracked; dir gitignored | MATCH, quantified |
| #332: Direction 3 is the smallest decidability fix | Snapshot + diff-on-drift is additive, backward-tolerant, boundary-clean | MATCH |

## Recommendations

1. Phase 231 (feature): snapshots at capture, diff on DRIFT, ceremony force-add of the session lock family, legacy tolerance. Follow-ons filed at cycle end: Direction 1 as a design issue; the CI verify job.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
