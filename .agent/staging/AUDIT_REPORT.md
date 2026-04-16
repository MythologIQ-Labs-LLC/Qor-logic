# AUDIT REPORT — plan-qor-phase20-import-migration.md

**Tribunal Date**: 2026-04-16
**Target**: `docs/plan-qor-phase20-import-migration.md`
**Risk Grade**: L1
**Auditor**: The QorLogic Judge

---

## VERDICT: **VETO**

---

### Executive Summary

Design is sound: use-case-agnostic working-dir anchor, `importlib.resources` for packaged assets, install-smoke CI test, non-SDLC scope respected. Grounded counts (13 sibling imports, 13 REPO_ROOT sites, 9 sys.path.insert sites) verified via independent grep. VETO issued for 3 SG-038 arithmetic recurrences in the plan's own enumerations — the fourth time since SG-038 was codified (Phase 15 v1, Phase 17a v1, Phase 19 v1, now Phase 20 v1). V-1: Scripts header says "(12)" but enumerates 15. V-2: Modified header says "(14)" but section sums to 20 (15 scripts + 2 reliability + 2 tests + 1 CI). V-3: gap-remaining arithmetic — "11 open after this phase" conflates pre-phase with post-phase counts; actual post-Phase-20 remaining = 18 − 7 (Phase 19) − 4 (Phase 20) = **7**, not 11.

### Audit Results

#### Security Pass
**Result**: PASS. Subprocess calls in proposed `detect_git_root()` use list-form argv with static head; 5-second timeout bounded. No credential exposure.

#### Ghost UI Pass
**Result**: PASS. No UI.

#### Section 4 Razor Pass
**Result**: PASS.

| Check | Limit | Proposed | Status |
|---|---|---|---|
| Max function lines | 40 | `qor/resources.py` helpers ≤5 lines; `qor/workdir.py` `detect_git_root` ~12 lines | OK |
| Max file lines | 250 | `resources.py` ~25; `workdir.py` ~45; `test_packaging_install.py` ~40 | OK |
| Max nesting depth | 3 | ≤2 | OK |
| Nested ternaries | 0 | 0 | OK |

#### Dependency Pass
**Result**: PASS. Stdlib `importlib.resources`, `subprocess`, `os`, `pathlib`. No external deps.

#### Orphan Pass
**Result**: PASS. `qor/resources.py` + `qor/workdir.py` imported by Track C/D/E files; `tests/test_packaging_install.py` discovered by pytest; CI smoke job references the new test module by path.

#### Macro-Level Architecture Pass
**Result**: PASS. Clean module boundary: `qor.resources` owns packaged-asset lookup; `qor.workdir` owns consumer-state anchor; no cross-import. Non-SDLC scope preserved: default chain has no git dependency.

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-1 | SG-038 recurrence (scripts count) | "Affected Files (summary) → Modified → Scripts" | Header reads "Scripts (12):" followed by 15 enumerated paths (shadow_process, validate_gate_artifact, session, remediate_read_context, remediate_mark_addressed, remediate_emit_gate, qor_audit_runtime, qor_platform, gate_chain, create_shadow_issue, collect_shadow_genomes, compile, check_variant_drift, check_shadow_threshold, calculate-session-seal = 15). Verified via `sed -n '/Modified (14)/,/^## /p' \| grep -c "qor/scripts/"` → 15. Count is off by 3. |
| V-2 | SG-038 recurrence (total modified count) | "Affected Files (summary) → Modified (14)" | Section total header says "Modified (14)" but the sub-group counts sum to 15 scripts + 2 reliability + 2 tests + 1 CI = **20 files**. Off by 6. If V-1 were reconciled to "Scripts (15)", the total would be "Modified (20)". |
| V-3 | SG-038 recurrence (remaining-gap arithmetic) | Plan header "Closes gaps: ... (4 of 18; 11 open after this phase)" | 18 total gaps minus 7 closed in Phase 19 (PKG-01/02/03/04/05, CI-01/02) minus 4 closing now (IMP-01/02/03/05) = **7 open after Phase 20**, not 11. The "11 open" value matches pre-Phase-20 count (18 − 7 = 11), suggesting the author conflated "open before this phase" with "open after". |

### Required Remediation

1. **V-1**: Update header from "Scripts (12)" to "Scripts (15)". Verify the 15 paths match actual Track coverage (Tracks C + D + E should all reference files in the list; recount).
2. **V-2**: Update header from "Modified (14)" to "Modified (20)" (or whatever the corrected sub-group sum is after V-1 resolution).
3. **V-3**: Update the plan header claim from "11 open after this phase" to "7 open after this phase". Or — for clarity — rewrite as "(4 of 18; 11 currently open, 7 remaining after Phase 20)" to show both checkpoint values.

Also: this is the **4th SG-038 recurrence since codification** (Phase 15 v1 → Phase 17a v1 → Phase 19 v1 → Phase 20 v1). Doctrine-alone is not preventing the pattern. Consider adding to the Phase 20 remediation a tiny plan-linter test that asserts `header_count == len(enumerated_list)` for the `Scripts ()`/`Modified ()`/`Closes gaps ()` headers.

### Verdict Hash

**Content Hash**: `be37ddbcb054c36eefebeecf71a6788dde91399562e075a834b0255dcca3f191`
**Previous Hash**: `0f821248ed30b40da4d4f69b10ce010616f3e681fec93af6a1229542417a4cd0`
**Chain Hash**: `698d5c49cca5c27c15b6129fe6a3f103b3d11e17de65b54916780c2ba31942fd`
(sealed as Entry #60)

---
_This verdict is binding._
