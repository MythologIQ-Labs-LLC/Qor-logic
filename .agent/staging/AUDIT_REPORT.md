# AUDIT REPORT — plan-qor-phase19-packaging-foundation.md

**Tribunal Date**: 2026-04-16
**Target**: `docs/plan-qor-phase19-packaging-foundation.md`
**Risk Grade**: L1 (documentation-level defects in a still-unimplemented plan)
**Auditor**: The QorLogic Judge (cross-referencing `qor/references/doctrine-shadow-genome-countermeasures.md`)

---

## VERDICT: **VETO**

---

### Executive Summary

Plan is substantively sound — 4 tracks map cleanly to the brief's Sprint 1, inline grounding present throughout, SG-036 honored, version math correct (263→272, 0.9.0→0.10.0). VETO issued for 2 **SG-038 recurrences** (prose-code mismatch) and 1 SG-016 grounding error (off-by-one). V-1: header claims "Closes gaps: PKG-01/02/03, CI-01/02 (5 of 18)" but Track A Changes explicitly closes PKG-04 + PKG-05 too, and Track D tests cover all 7 IDs — triple-surface mismatch. V-2: Out-of-scope section says "Sprint 4 (Phase 22): PyPI metadata polish" but Track A proposes exactly that metadata polish (classifiers, keywords, urls, authors). Self-contradicting scope boundaries. V-3: plan states `pyproject.toml` is 21 lines; `wc -l` → 20.

### Audit Results

#### Security Pass
**Result**: PASS. Stub dispatcher has no auth surface. Release workflow uses OIDC trusted publisher (no API token in-repo).

#### Ghost UI Pass
**Result**: PASS. No UI.

#### Section 4 Razor Pass
**Result**: PASS.

| Check | Limit | Proposed | Status |
|---|---|---|---|
| Max function lines | 40 | `main()` ~20; `_not_implemented()` ~3 | OK |
| Max file lines | 250 | `pyproject.toml` ~70; `qor/cli.py` ~40; `ci.yml` ~20; `release.yml` ~20 | OK |
| Max nesting depth | 3 | ≤2 | OK |
| Nested ternaries | 0 | 0 | OK |

#### Dependency Pass
**Result**: PASS. No new runtime deps. Tests use stdlib `tomllib` (3.11+, repo requires 3.11+) and pytest `capsys`. CI uses standard actions.

#### Orphan Pass
**Result**: PASS. `qor/cli.py` wired via `[project.scripts].qorlogic`; tests follow pytest discovery; workflows triggered by GitHub events.

#### Macro-Level Architecture Pass
**Result**: PASS. Clean module boundaries between packaging config, CLI stub, CI. No cross-track couplings.

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-1 | SG-038 recurrence (prose-code gap-count mismatch) | Plan header vs Track A Changes vs Track D tests | Header reads "**Closes gaps**: GAP-PKG-01, GAP-PKG-02, GAP-PKG-03, GAP-CI-01, GAP-CI-02 (5 of 18)". Track A Changes ends with "Closes GAP-PKG-01, GAP-PKG-02, GAP-PKG-03 (scripts entry), **GAP-PKG-04 (readme), GAP-PKG-05 (metadata)**." Track D tests include `test_pyproject_declares_readme` (PKG-04) and `test_pyproject_declares_classifiers` (PKG-05). Actual scope: 5 PKG + 2 CI = **7 gaps closed**, not 5. Triple-surface inconsistency — exact SG-038 pattern. |
| V-2 | Self-contradiction (scope boundary) | Out-of-scope section vs Track A | Out-of-scope states "Sprint 4 (Phase 22): PyPI metadata polish, `.gitignore` build artifacts, `compile.py` → `dist_compile.py` rename, drift/ledger CI wiring, TestPyPI rehearsal." Track A proposes exactly the PyPI metadata (classifiers, keywords, urls, authors, BSL-1.1 license) that is declared out-of-scope. Pick one. |
| V-3 | SG-016 grounding error (off-by-one) | Grounded state section, "`pyproject.toml`: 21 lines" | Judge-verified via `wc -l pyproject.toml` → **20 lines**. Minor, substantive harm nil (post-edit still under Razor), but SG-016 discipline says cite verified exact values. |

### Required Remediation

1. **V-1**: Pick one scope and propagate everywhere. Recommended: **keep PKG-04 + PKG-05 in Phase 19** (trivial, tests already present). Update header to "Closes gaps: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, CI-01, CI-02 (7 of 18)". Alternative (tighter Sprint 1): remove readme/classifiers/keywords/urls/authors from Track A, drop `test_pyproject_declares_readme` + `test_pyproject_declares_classifiers`, update to +7 tests (263 → 270). Pick and reconcile prose, Track A code, test list, success criteria, and CI Commands section.
2. **V-2**: After V-1 resolution, update Out-of-scope section to match. If PKG-04/05 stay in Phase 19, remove "PyPI metadata polish" from Sprint 4 list. If they move, remove metadata keys from Track A's pyproject.toml block.
3. **V-3**: Update grounded-state bullet from "21 lines" to "20 lines". Add the command used (`wc -l pyproject.toml` → 20) for SG-016 provenance.

### Verdict Hash

**Content Hash**: `23642d7110e82b64435321e68c547a881e2f560dc79398c89a9fa215f3046f31`
**Previous Hash**: `44d5991e33a5907ee0b9e21b4aed63976c01c98a4749cd603af0057727481530`
**Chain Hash**: `31e4e93101df6aef1c16eb1271b20b27f705be0cd9e4dd281d900d9d05b1a4b7`
(sealed as Entry #56)

---
_This verdict is binding._
