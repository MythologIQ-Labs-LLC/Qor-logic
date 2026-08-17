# Plan: The intent lock keeps the evidence it will be asked about

**iteration**: 1

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: The diff makes an override decidable; it does not authorize any delta -- DRIFT still ABORTs and the operator still decides. Legacy records without snapshots verify exactly as today and their drifts remain testimony-resolved.
- non_goals: No verdict-authorized-delta contract (GH #332 Direction 1; follow-on issue at cycle end). No CI-side verify job (needs the committed artifacts this phase creates; follow-on issue). No bulk un-ignore of `.qor/intent-lock/` (127 legacy records include pre-172 absolute paths that would trip the publication boundary); the directory stays ignored and only the sealed session's family is force-added.
- exclusions: GH #320, GH #286, GH #349.

## Open Questions

None. Direction 3 is the issue's own stated preference and the design is additive.

## Locked Decisions

**LD-1: The capture record's hash fields stay exactly as they are; the snapshots are the bytes those hashes are computed over, so record and snapshot are self-consistent by construction.**

```
git show v0.151.0:qor/reliability/intent_lock.py | grep -nE '"plan_hash": _hash_file\(plan\)' -> 123:        "plan_hash": _hash_file(plan),
```

**LD-2: The bare two-word drift report is the decidability gap; on mismatch with a snapshot present, verify appends a bounded unified diff (first 40 lines) to stderr and still exits 1.**

```
git show v0.151.0:qor/reliability/intent_lock.py | grep -nE 'print\("DRIFT: plan"' -> 154:        print("DRIFT: plan", file=sys.stderr)
```

**LD-3: Snapshots live beside the record** (`.qor/intent-lock/<session>.plan.snapshot`, `<session>.audit.snapshot`), written LF-normalized at capture -- the same normalization the hasher applies, so `sha256(snapshot) == recorded hash` always holds for records this phase writes.

**LD-4: The sealed session's lock family joins the executable ceremony by deliberate force-add.**

```
git show v0.151.0:qor/scripts/seal_stage.py | grep -nE 'gate_dir = repo_root' -> 58:    gate_dir = repo_root / ".qor" / "gates" / session_id
```

`seal_stage.stage` additionally stages `.qor/intent-lock/<session>.json` and both snapshots when present, via a separate `git add -f --` invocation (the directory is gitignored; plain `git add` refuses ignored paths). Only the named session's files are ever force-added; the 127 legacy operator-local records stay local.

**LD-5: Legacy tolerance is verify-side only**: a record without snapshots verifies exactly as today (no diff, same exit codes, same messages); no retroactive snapshot generation (the referent for old sessions is already gone -- fabricating one would be worse than absence).

## Phase 1: Bind the evidence contract (tests first)

### Affected Files

- `tests/test_intent_lock_evidence.py` - NEW; behavioral coverage in tmp git repos.
- `tests/test_seal_stage.py` - extended with one test.

### Unit Tests

- `tests/test_intent_lock_evidence.py::test_capture_writes_selfconsistent_snapshots` - after capture, both snapshot files exist and `sha256` of each (LF-normalized content) equals the recorded hash.
- `tests/test_intent_lock_evidence.py::test_drift_prints_the_delta` - edit the plan after capture; verify exits 1 and stderr contains `DRIFT: plan` plus a unified-diff hunk showing the edited line.
- `tests/test_intent_lock_evidence.py::test_diff_is_bounded` - a drift of 200 lines emits no more than the bounded head (40 diff lines) plus a truncation note.
- `tests/test_intent_lock_evidence.py::test_legacy_record_without_snapshot_verifies_as_today` - a hand-written record with no snapshot files: clean verify exits 0; drifted verify exits 1 with exactly the bare two-word report.
- `tests/test_intent_lock_evidence.py::test_clean_verify_is_silent_about_snapshots` - no diff output on a clean verify.
- `tests/test_seal_stage.py::test_intent_lock_family_is_force_added_for_the_session` - in a tmp repo whose `.gitignore` covers `.qor/intent-lock/`, the named session's record and snapshots are staged after `stage()`; another session's are not.

All red at v0.151.0 (no snapshot files are written; no diff output exists; `seal_stage` stages nothing under an ignored path).

## Phase 2: Capture keeps, verify shows, ceremony carries

### Affected Files

- `qor/reliability/intent_lock.py` - capture writes the two snapshots (LF-normalized bytes); verify's two drift branches load the matching snapshot when present and append the bounded diff via `difflib.unified_diff`; a `_drift_report(kind, snapshot, live)` helper keeps both branches under the razor.
- `qor/scripts/seal_stage.py` - `stage()` force-adds the session's intent-lock family per LD-4; `CEREMONY` constants untouched (the family is session-derived, like the gate dir).

### Changes

Phase 1's six tests go green; the four existing intent-lock test files stay green (capture record fields unchanged per LD-1; verify's clean path and exit codes unchanged; the anchored-PASS and LF-invariance contracts untouched).

### Unit Tests

- Phase 1's six tests observed red-then-green.
- `tests/test_intent_lock_anchored_pass_check.py`, `tests/test_intent_lock_lf_invariance.py`, `tests/test_seal_intent_lock_state.py`, `tests/test_seal_flow_ordering.py` - caller sweep, green unmodified.

## Feature Inventory Touches

None. Reliability tooling, staging ceremony, tests.

## Definition of Done

### Deliverable 1: The referent is recoverable

- **D1**: A drift override is a decidable question -- the reviewer sees exactly what changed since capture instead of relying on testimony (GH #332's stated bar).
- **D2**: Snapshots at capture, self-consistent with the recorded hashes; bounded unified diff on DRIFT; legacy tolerance.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file; this phase's own seal commits its session's lock family -- the first committed lock record since phase 59.
- **D4**: `test_drift_prints_the_delta` and `test_capture_writes_selfconsistent_snapshots` observed red at v0.151.0 and green after Phase 2.

### Deliverable 2: CI can finally see the lock

- **D1**: Sealed sessions' lock records and snapshots are committed artifacts, making a CI-side verify job possible (follow-on).
- **D2**: `seal_stage` force-adds the session family; only the named session, never the legacy set.
- **D4**: `test_intent_lock_family_is_force_added_for_the_session` observed red-then-green; the boundary lint observed clean over the staged family in the substantiate sweep.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase231-intent-lock-evidence.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase231-intent-lock-evidence.md --repo-root .` -- citation truth check.
