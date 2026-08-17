# Plan: The repeated-VETO detector reads the ledger that exists

**iteration**: 1

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: The in-flight condition sees only what the ledger holds; an audit pass not yet written as a GATE TRIBUNAL entry is invisible until it lands. Session-scoped VETO escalation remains `cycle_count_escalator`'s domain; this detector's window is ledger-historical plus the one in-flight phase.
- non_goals: No change to the advisory wording contract, the emission payload shape, or `/qor-audit` Step 7 wiring (the `check(ledger_path, session_id)` signature is unchanged). No per-category counting in `cycle_count_escalator` (remains with GH #342). No repointment of event `7b2ed33a` (its mechanism is still unshipped; GH #342).
- exclusions: GH #332, GH #337, GH #320, GH #286, GH #341.

## Open Questions

None. Expected post-fix behavior on the live ledger is declared, not discovered: phases 225 and 226 each sealed after more than one audit pass, so the repaired detector will truthfully fire on the current window and the next `/qor-audit` Step 7 will emit a severity-3 `repeated_veto_pattern` event recommending `/qor-remediate`. That is the detector working, not a defect; the advisory is non-blocking by contract, and the ledger-binding test asserts parseability, never non-detection.

## Locked Decisions

**LD-1: The stale comparison is the whole recognition defect; the fix widens it to accept the current convention while keeping the grandfathered one.**

```
git show v0.148.0:qor/scripts/veto_pattern.py | grep -nE 'elif entry_type == "AUDIT"' -> 50:        elif entry_type == "AUDIT":
```

**LD-2: The sealed-only restriction is why the detector is one phase late even after recognition is fixed; the in-flight condition joins the newest unsealed multi-pass phase to the window instead of loosening this filter.**

```
git show v0.148.0:qor/scripts/veto_pattern.py | grep -nE 'return \{p: c for p, c in audits' -> 52:    return {p: c for p, c in audits.items() if p in sealed}
```

**LD-3: The window constant stays 2; the in-flight phase substitutes as the newest member rather than widening the window.**

```
git show v0.148.0:qor/scripts/veto_pattern.py | grep -nE '^_PATTERN_WINDOW' -> 24:_PATTERN_WINDOW = 2
```

**LD-4: The ledger-binding test asserts a structural property of the repo's own tracked artifact (non-empty parse above phase 200), never specific values, hashes, or non-detection -- the deliberate opposite of the synthetic-only suite that concealed this defect, and not the live-state-hardcoding pattern (no operator-local paths, no pinned entry contents).**

**LD-5: The held GH #333 repointment (`8f9c5c6e` -> `tests/test_veto_pattern_detector.py`) executes in this phase via `correct_closure_enforcers` under a reviews-remediate PASS attestation, per ledger #597's Required Next Action -- the citation becomes true in the same change that makes the test real.**

## Phase 1: Bind the tests to the ledger that exists

### Affected Files

- `tests/test_veto_pattern_detector.py` - extended with four tests (below); existing synthetic tests unchanged.

### Changes

Author the tests first; all four new ones fail against v0.148.0 (GATE TRIBUNAL fixtures parse to empty; `detect_repeated_veto_pattern` has no in-flight parameter, so those tests fail on TypeError; the real-ledger test fails because the live parse above phase 200 is empty).

### Unit Tests

- `test_gate_tribunal_entries_are_counted` - a synthetic ledger written in the current convention (`### Entry #N: GATE TRIBUNAL -- Phase 300 ...` plus `### Entry #M: SESSION SEAL -- Phase 300 ...`) parses to `{300: k}`.
- `test_audit_entries_still_counted` - the grandfathered `AUDIT` convention keeps parsing (entries 1-85 and the existing fixtures).
- `test_in_flight_phase_joins_the_window` - one sealed multi-pass phase plus an unsealed newer phase with two audit entries fires the pattern; the in-flight phase appears in `recent_phases`.
- `test_in_flight_single_pass_does_not_fire` - the same shape with a single in-flight audit does not fire (guards the inverse).
- `test_the_real_ledger_parses_to_nonempty_counts_above_phase_200` - `parse_phase_audit_counts` over `docs/META_LEDGER.md` returns at least one sealed phase above 200 (the anti-recurrence binding; red today by the defect itself).

## Phase 2: Recognize the convention and see the live cycle

### Affected Files

- `qor/scripts/veto_pattern.py` - recognition at line 50 becomes membership in `("AUDIT", "GATE TRIBUNAL")`; NEW `parse_in_flight_audit_count(ledger_text) -> tuple[int, int] | None` returns the newest unsealed phase carrying audit entries and its count; `detect_repeated_veto_pattern` gains optional `in_flight: tuple[int, int] | None = None` treated as the newest window member when its count exceeds 1; `check` wires the parse into the detect call. Signature of `check` unchanged.
- `tests/test_veto_pattern_event.py`, `tests/test_audit_language_doctrine.py`, `tests/test_audit_smoke_integration.py` - caller sweep, no change expected; verified by running.

### Changes

Phase 1's four new tests go green; every existing synthetic test stays green (recognition widened, never narrowed; `detect` default keeps legacy behavior when `in_flight` is None).

### Unit Tests

- Phase 1's five listed tests observed red-then-green (the grandfathered-convention test is green at v0.148.0 by design and stays green).

## Phase 3: Repoint the held closure citation

### Affected Files

- `docs/PROCESS_SHADOW_GENOME.md` - event `8f9c5c6e...` closure_enforcer repointed from `qor.scripts.cycle_count_escalator` to `tests/test_veto_pattern_detector.py` via `correct_closure_enforcers` under a reviews-remediate PASS attestation (proposal + attestation artifacts in this session's gate directory).

### Changes

Executed only after Phases 1-2 are green, so the recorded enforcer names a file that genuinely binds the detector to the ledger at the moment of recording. `addressed` and `addressed_ts` untouched (corrective-path contract).

### Unit Tests

- `tests/test_remediate_enforcer_edges.py::test_corrective_repair_leaves_addressed_true` - existing, unmodified; the shipped contract this step relies on.

## Feature Inventory Touches

None. Governance tooling, tests, and a shadow-log provenance correction.

## Definition of Done

### Deliverable 1: Convention recognition

- **D1**: The detector counts the audit entries the ledger actually writes.
- **D2**: `veto_pattern.py` recognition accepts `AUDIT` and `GATE TRIBUNAL`.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: `test_gate_tribunal_entries_are_counted` and `test_the_real_ledger_parses_to_nonempty_counts_above_phase_200` observed red at v0.148.0 and green after Phase 2.

### Deliverable 2: In-flight visibility

- **D1**: The live cycle's own multi-pass run is visible before its seal.
- **D2**: `parse_in_flight_audit_count` plus the optional `in_flight` window member; `check` signature unchanged.
- **D4**: `test_in_flight_phase_joins_the_window` and its inverse observed red-then-green.

### Deliverable 3: Truthful repointment (GH #333/#342 held item one)

- **D1**: The closure citation for `8f9c5c6e` names a mechanism that guards its pattern on the day it is recorded.
- **D2**: `correct_closure_enforcers` execution under PASS attestation, this session.
- **D4**: post-flip event state observed: `closure_enforcer == "tests/test_veto_pattern_detector.py"`, `addressed` true, `addressed_ts` unchanged.

## CI Commands

- `python -m pytest tests/ -q` -- full suite; the extended detector suite and every consumer green.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase227-veto-pattern-gate-tribunal.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase227-veto-pattern-gate-tribunal.md --repo-root .` -- citation truth check over this plan's Locked Decisions.
