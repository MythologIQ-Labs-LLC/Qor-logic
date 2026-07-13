# Research Brief

**Date**: 2026-07-13T08:59:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #264 -- reachability_probe 30s collect-only subprocess timeout flakes under full-suite load
**Scope**: the flake mechanism, the validated remedy, tunability

---

## Executive Summary

`reachability_probe.check_test_collection` spawns `pytest --collect-only` per
candidate with `timeout=30` and treats `TimeoutExpired` as "candidate failed
to collect" (`continue`, verified live at reachability_probe.py:132-135).
Under full-suite CPU load (~2600 tests, Windows) the child can exceed 30s, so
ALL candidates silently time out and the probe returns a false-negative
finding -- the reporter observed 2/2 full-suite failures vs 14/14 isolated
passes, and validated that 120s produces clean runs. The sibling
importability check uses 20s (line 70) and the CLI test harness uses 60s --
the 30s constant is the outlier on the heaviest subprocess.

## Findings

### F1. Mechanism (verified live)

- reachability_probe.py:128-135: per-candidate `subprocess.run(...,
  timeout=30)`; `except TimeoutExpired: continue`. A load-induced timeout is
  indistinguishable from a genuine collection failure, and the loop's
  exhaustion yields `reachability-test-collection-failed` -- a false negative
  under load, a true positive otherwise. The silent-continue design is
  correct for genuine per-candidate failures; only the budget is wrong.

### F2. Remedy shape

- Reporter-validated: 120s clean under full-suite load. Env-tunable
  (`QOR_REACHABILITY_COLLECTION_TIMEOUT`, default 120) lets slow CI go higher
  without code change. Alternatives rejected: inconclusive-WARN finding
  changes the probe contract (Phase 99 V2 consumers); in-process pytest.main
  changes the isolation model; session caching couples probe to test harness.

### F3. Test shape

- The timeout value must be test-locked without a real 120s wait: monkeypatch
  `subprocess.run` with a recorder and assert the timeout kwarg passed equals
  the module constant; a second test asserts the env override is honored.
  Existing behavioral tests (collection pass/fail) remain the functional net.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Probe verdicts reflect reachability, not machine load | 30s budget makes load a verdict input | DRIFT (the fix) |

## Recommendations

1. (P0) Module constant `COLLECTION_TIMEOUT = int(os.environ.get("QOR_REACHABILITY_COLLECTION_TIMEOUT", "120"))`; use at the collect-only call.
2. (P0) Tests: recorder-based timeout assertion + env-override assertion.

## Updated Knowledge

None; a budget correction with tunability.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
