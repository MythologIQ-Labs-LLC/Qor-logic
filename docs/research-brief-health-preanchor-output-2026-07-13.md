# Research Brief

**Date**: 2026-07-13T08:18:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #268 -- governance-health emits unqualified FAIL/TAINTED lines for tolerated pre-anchor diagnostics
**Scope**: where the confusing output escapes, what is already tolerated, minimal classification shape

---

## Executive Summary

The VERDICT is already correct: `governance_health._ledger_damage` falls back
to the post-anchor verifier (GH #199 tolerance), so a re-anchored ledger with
disclosed pre-anchor failures classifies OK / exit 0. The CONFUSION is an
output asymmetry: `_ledger_damage` redirects stdout only (verified live at
governance_health.py:134,142) while `ledger_hash.verify` writes its FAIL and
TAINTED lines to STDERR (ledger_hash.py:417,429) -- so operators, the
status_json aggregator (which captures both streams), and the nightly-health
step summary see raw failure lines directly contradicting the OK verdict.
Minimal fix: suppress stderr alongside stdout in the two verification calls,
and surface the tolerance POSITIVELY -- the OK finding's reason names the
disclosed pre-anchor state instead of the generic "passes health checks".

## Findings

### F1. The bleed (verified live)

- `qor/scripts/governance_health.py:134,142`: `contextlib.redirect_stdout`
  only, around `_verify_ledger_chain` and `_verify_post_anchor`.
- `qor/scripts/ledger_hash.py:417,429` (+520,529 in verify_post_anchor):
  FAIL/TAINTED go to `sys.stderr`. Consumers seeing the bleed: the
  `governance-health` CLI, `status_json` (captures stdout+stderr), the
  nightly-health workflow step summary.

### F2. Already tolerated at the verdict level

- `_ledger_damage` (line 127): strict rc != 0 -> post-anchor fallback ->
  DAMAGED only when the post-anchor band genuinely fails. GH #268's AC items
  "OK classification + exit 0" already hold; the issue is presentation.

### F3. Minimal classification shape

- Suppress stderr in both redirected calls; thread a positive note: when
  strict verify failed but post-anchor passed, the OK finding's reason reads
  "passes health checks (disclosed pre-anchor residuals tolerated; post-anchor
  band clean)" -- satisfying the "output identifies the disclosed boundary"
  acceptance without new output formats. The structured/JSON output AC is
  GH #271 Phase-3 territory (typed model), deferred with that roadmap.
- Existing fixture reuse: tests/test_governance_health_post_anchor_tolerance.py
  builds exactly the re-anchored synthetic ledger; new tests capture BOTH
  streams and assert absence of FAIL/TAINTED plus the reason note. Genuine
  post-anchor failure stays DAMAGED (regression lock).

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| GH #199: tolerated pre-anchor -> OK verdict | Holds (verdict level) | MATCH |
| Diagnostics match the verdict | stderr bleed contradicts OK | DRIFT (the fix) |

## Recommendations

1. (P0) `redirect_stderr` beside `redirect_stdout` at both call sites; the
   tolerated branch returns a positive note for the OK finding's reason.
2. (P0) Capture-both-streams tests on the existing re-anchored fixture; the
   genuine post-anchor failure path regression-locked.
3. Structured output: defer to the GH #271 typed-model roadmap (recorded).

## Updated Knowledge

None; presentation alignment with an already-correct verdict.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
