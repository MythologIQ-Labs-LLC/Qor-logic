# AUDIT REPORT — plan-qor-phase14-v2-shadow-attribution.md

**Tribunal Date**: 2026-04-15
**Target**: `docs/plan-qor-phase14-v2-shadow-attribution.md`
**Risk Grade**: L1 (spec-level defects; no security concerns)
**Auditor**: The QorLogic Judge

---

## VERDICT: **VETO**

---

### Executive Summary

Plan v2 closes all 5 Entry #31 violations and correctly expands scope to 7 writer call sites (good grounding work). VETO issued for 2 substantive defects: (1) the proposed `id_source_map()` write-back pattern silently drops newly-created events (escalation events in `check_shadow_threshold.py` and new events from any future caller), and (2) the signature change from `append_event(event, log_path=None)` to keyword-only `(event, *, attribution=None, log_path=None)` breaks 2 existing test call sites that pass `log_path` positionally. Both are fixable without redesign.

### Audit Results

#### Security Pass
**Result**: PASS. No credentials, auth stubs, or security bypasses. Plan is governance/process infrastructure only.

#### Ghost UI Pass
**Result**: PASS. No UI elements proposed.

#### Section 4 Razor Pass
**Result**: CONDITIONAL PASS — see V-3.

| Check | Limit | Blueprint Proposes | Status |
|---|---|---|---|
| Max function lines | 40 | All proposed functions <20 lines | OK |
| Max file lines | 250 | `create_shadow_issue.py`: 227 + ~25 est. = ~252 | MARGINAL |
| Max nesting depth | 3 | Max 2 (conditional in collector) | OK |
| Nested ternaries | 0 | 0 | OK |

`shadow_process.py` (121 + ~24 = ~145): OK. `check_shadow_threshold.py` (150 + ~20 = ~170): OK. `create_shadow_issue.py` (227 + ~25 = ~252): borderline.

#### Dependency Pass
**Result**: PASS. No new dependencies.

#### Orphan Pass
**Result**: PASS. All proposed files connect to existing import chains. `doctrine-shadow-attribution.md` is referenced by 4 skills + test. `PROCESS_SHADOW_GENOME_UPSTREAM.md` is read by collector + shadow_process constants. `test_shadow_attribution.py` is discovered by pytest.

#### Macro-Level Architecture Pass
**Result**: FAIL — see V-1 (silent data loss in write-back pattern).

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-1 | Data loss (silent drop) | Track E, `check_shadow_threshold.py` write-back | `id_source_map()` is built from existing events on disk. New escalation events created by `sweep()` (line 64-83 of `check_shadow_threshold.py`) have IDs not yet in either file. The plan's write-back pattern `src_map.get(e["id"]) == LOCAL_LOG_PATH` returns `None` for these new IDs — they match neither `local` nor `upstream` filter and are silently dropped from both files. Same exposure in `create_shadow_issue.py` if any new events are ever appended during a read-modify-write cycle. |
| V-2 | Breaking change (unaccounted) | Track C, `append_event` signature | Current signature: `append_event(event: dict, log_path: Path \| None = None)` — `log_path` is a regular parameter, passable positionally. Plan proposes: `append_event(event: dict, *, attribution=None, log_path=None)` — the `*` makes `log_path` keyword-only. Two existing test call sites pass `log_path` positionally: `tests/test_shadow.py:329` (`shadow_process.append_event(e, log)`) and `tests/test_shadow.py:341` (`shadow_process.append_event(e, log)`). Both raise `TypeError` under the new signature. Plan says "existing body unchanged" but does not account for this positional-to-keyword breakage. |
| V-3 | Section 4 Razor (marginal) | Track E, `create_shadow_issue.py` | File is 227 lines today. Dual-file changes to `flip_events_only`, `mark_resolved`, and main flow add ~25 lines → ~252, exceeding the 250-line Razor limit. Plan does not estimate or address. |
| V-4 | Plan-internal inconsistency | Affected Files summary, line 240 | Header reads "Modified — scripts (5)" but enumerates 6 files (`shadow_process.py`, `collect_shadow_genomes.py`, `gate_chain.py`, `qor_audit_runtime.py`, `check_shadow_threshold.py`, `create_shadow_issue.py`). |

### Required Remediation

1. **V-1**: New events created during a read-modify-write cycle must not be lost. Prescribed fix: extend `id_source_map()` to accept an `extras` parameter (or return a builder), OR — simpler — classify new escalation events at creation time. In `check_shadow_threshold.py`, escalation events are infrastructure-generated → UPSTREAM. The sweep function should assign new events to a file explicitly (e.g., `new_event["_target_path"] = shadow_process.UPSTREAM_LOG_PATH`), and the write-back pattern should handle events with no map entry by checking `_target_path`. Alternatively, rewrite `sweep()` to call `shadow_process.append_event(new_event, attribution="UPSTREAM")` immediately instead of batching, eliminating the need for a post-hoc split. This second option is simpler (no `_target_path` metadata) but changes the write-back flow from batch-rewrite to incremental-append-then-rewrite-originals. Pick one; add test `test_escalation_events_not_dropped_during_sweep`.
2. **V-2**: Explicitly update `tests/test_shadow.py:329` and `tests/test_shadow.py:341` from `shadow_process.append_event(e, log)` to `shadow_process.append_event(e, log_path=log)`. Add these 2 files to Track F "Modified — tests" with the change note. Also grep for any other positional callers in tests (the 2 found are from `test_append_event_atomic` and its multi-event variant; verify no others exist in `test_e2e.py`, `test_gates.py`, `test_qor_audit_runtime.py`).
3. **V-3**: Either (a) extract a `write_events_per_source(events, src_map)` helper into `shadow_process.py` (keeps `create_shadow_issue.py` thin — callers shrink by ~10 lines each), or (b) state an explicit estimate showing the file stays at or under 250 lines. Option (a) also de-duplicates the pattern between `check_shadow_threshold.py` and `create_shadow_issue.py`.
4. **V-4**: Correct header to "Modified — scripts (6)".

### Verdict Hash

**Content Hash**: `80f2ad9af6a36720ac3fa3a27cc2c02224bc9e29bb53616b4576e6819a9efe9b`
**Previous Hash**: `54ef6a4281b361dea2f5c704d5b962caf4d278a87272ba87654b3317674a7d1b`
**Chain Hash**: `4d23775ffea278cb176dc1560066d14f7692c05b4ad5ac73033bb3ad0f46e17b`
(sealed as Entry #32)

---
_This verdict is binding._
