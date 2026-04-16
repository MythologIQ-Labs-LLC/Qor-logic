# AUDIT REPORT — plan-qor-phase20-v2-import-migration.md

**Tribunal Date**: 2026-04-16
**Target**: `docs/plan-qor-phase20-v2-import-migration.md`
**Risk Grade**: L1
**Auditor**: The QorLogic Judge

---

## VERDICT: **VETO**

---

### Executive Summary

All 3 Entry #60 violations closed cleanly: "Scripts (15)" matches 15 enumerated, "Modified (20)" matches 15+2+2+1, "7 open after this phase" matches 18−7−4. Old values (12 / 14 / 11) appear only in historical closure-note quotes. Grounded counts re-verified independently (9 sys.path sites, 13 REPO_ROOT, 13 sibling imports). VETO issued for 1 fresh finding: V-1 — plan's Track F claims "Default target: 278 passed + 4 skipped" but provides no mechanism for integration tests to skip under default `pytest tests/` invocation. `@pytest.mark.integration` is merely declared in pyproject.toml markers (documentation only), not auto-skip; no `addopts = "-m 'not integration'"` configured; no module-level `pytest.skip(..., allow_module_level=True)` proposed. Under default pytest, the 4 new tests would run and fail (no installed wheel).

### Audit Results

#### Security Pass
**Result**: PASS.

#### Ghost UI Pass
**Result**: PASS.

#### Section 4 Razor Pass
**Result**: PASS. `qor/resources.py` ~25 lines; `qor/workdir.py` ~45 lines; `test_packaging_install.py` ~40 lines. All under 250.

#### Dependency Pass
**Result**: PASS. Stdlib only.

#### Orphan Pass
**Result**: PASS. `qor/resources.py` + `qor/workdir.py` imported by 14 Track C/D/E files.

#### Macro-Level Architecture Pass
**Result**: PASS. Clean `resources` vs `workdir` boundary; no cyclic deps.

### Entry #60 Closure Verification

| ID | Status | Re-Verification |
|---|---|---|
| V-1 (Scripts count) | CLOSED | Grep: "Scripts (15):" header; `sed -n '/### Modified (20)/,/^##/p' \| grep -c "qor/scripts/"` → 15. |
| V-2 (Modified total) | CLOSED | Header "Modified (20)"; sub-groups 15+2+2+1=20. |
| V-3 (remaining count) | CLOSED | "7 open after this phase" 2×; old "11" only in quoted historical note. |

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-1 | Spec gap (test-skip mechanism unspecified) | Track F + Track G | Plan states "Default target: 278 → 278 passed + 4 skipped" and "Tests integration: 282 passing in CI smoke". Relies on `@pytest.mark.integration` causing the 4 tests to skip under default `pytest tests/`. Judge-verified: (a) no existing `@pytest.mark.integration` tests in repo (grep returned empty), (b) pyproject.toml's `[tool.pytest.ini_options].markers` only DECLARES the marker; it does not configure auto-skip, (c) no `addopts = "-m 'not integration'"` exists in pyproject. Under standard pytest, declared markers do not auto-skip; the 4 tests would RUN under default `pytest tests/` and likely fail (no installed wheel). The plan's "+4 skipped default" target is unachievable without an explicit skip mechanism. Also: the existing `test` CI job (ci.yml) runs `python -m pytest tests/ -v` with no marker filter, so it too would run and fail on the new integration tests, before the install-smoke job has a chance to exercise them correctly. |

### Required Remediation

1. **V-1**: Pick one of:
   - **(a) `addopts = "-m 'not integration'"` in pyproject.toml `[tool.pytest.ini_options]`** — global default excludes integration; CI install-smoke job opt-ins via `-m integration` explicitly. Cleanest.
   - **(b) Module-level skip** in `tests/test_packaging_install.py`:
     ```python
     import os, pytest
     if not os.environ.get("QOR_RUN_INTEGRATION"):
         pytest.skip("Opt-in via QOR_RUN_INTEGRATION=1", allow_module_level=True)
     ```
     Env-var-gated; CI install-smoke sets `QOR_RUN_INTEGRATION=1`.
   - **(c) Per-test conditional skip** via `@pytest.mark.skipif(...)` decorator on each of the 4 tests.

   Recommend (a) — one line in pyproject, matches pytest convention, implicit for operators running `pytest tests/`. Also update the existing ci.yml `test` job prose to note that integration tests are excluded by default (no CI change needed since `addopts` is picked up automatically). Update Track F to describe the chosen mechanism explicitly.

### Verdict Hash

**Content Hash**: `2fd64ce359e139670c2f0daa1e5604290316fac4d56f729e9a2e8b03eaed7289`
**Previous Hash**: `698d5c49cca5c27c15b6129fe6a3f103b3d11e17de65b54916780c2ba31942fd`
**Chain Hash**: `02c379b80148a5a43800d01c901579fb68cdf55a15e36e981271b481be36eed3`
(sealed as Entry #61)

---
_This verdict is binding._
