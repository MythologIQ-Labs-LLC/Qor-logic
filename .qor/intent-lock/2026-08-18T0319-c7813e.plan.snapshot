# Plan: The lock's guarantee stops depending on the person it constrains

**iteration**: 1

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Sessions sealed before phase 231 have no committed evidence and are grandfathered by the boundary constant, exactly like the sibling gate's phase-52 boundary. The audit report's committed referent cannot be matched (its path is reused every phase); its snapshot self-consistency is the whole check, stated in the module docstring.
- non_goals: No change to `intent_lock` capture/verify, `seal_stage`, or the local ladder. No verdict-authorized deltas (GH #351 stays evidence-gated).
- exclusions: GH #351, GH #320, GH #286.

## Open Questions

None. Every reused surface is cited; the two committed-evidence sessions are the live fixtures.

## Locked Decisions

**LD-1: The SEAL-entry walker is reused, not reimplemented.**

```
git show v0.153.0:qor/reliability/gate_chain_completeness.py | grep -nE '^def _extract_seal_sessions' -> 33:def _extract_seal_sessions(text: str, phase_min: int) -> dict[int, str]:
```

**LD-2: The CI step joins the job that already verifies sealed-state invariants, directly after its completeness step.**

```
git show v0.153.0:.github/workflows/ci.yml | grep -nE 'python -m qor.reliability.gate_chain_completeness' -> 95:        run: python -m qor.reliability.gate_chain_completeness --phase-min 52
```

**LD-3: Three checks per sealed session at or above phase 231**: the record and both snapshots exist in the checkout; each snapshot's LF-normalized sha256 equals its recorded hash (importing `intent_lock`'s hashers -- self-consistency, the binding the #344 incident broke); the recorded `plan_hash` equals the hash of the committed file at the recorded `plan_path` (the plan referent persists; the audit referent does not, so its snapshot IS the preserved referent). Any failure exits 1 with the session, check, and paths named.

**LD-4: The live repo is its own fixture**: a test walks the real `docs/META_LEDGER.md` at phase_min 231 and asserts a clean result -- environment-honest (the evidence is tracked, full checkouts carry it) and the anti-recurrence binding in the veto-pattern ledger-test spirit.

## Phase 1: Bind the verification contract (tests first)

### Affected Files

- `tests/test_intent_lock_committed.py` - NEW.

### Unit Tests

- `test_valid_session_verifies_clean` - a tmp repo with a synthetic SEAL entry (phase 300) and a coherent lock family (record whose hashes match the snapshots, snapshot matching the committed plan) returns no failures.
- `test_tampered_snapshot_is_named` - the same fixture with one snapshot byte-flipped returns a failure naming the session and the snapshot check.
- `test_missing_family_is_named` - the record deleted returns a presence failure.
- `test_plan_referent_mismatch_is_named` - the committed plan edited after capture returns a referent failure distinct from self-consistency.
- `test_grandfather_boundary_skips_old_sessions` - a phase-200 SEAL entry with no lock family returns no failures at the default boundary.
- `test_the_real_ledger_verifies_clean_at_the_boundary` - LD-4, over the repo's own ledger and committed evidence.

All red at v0.153.0 (module absent; ImportError at collection).

## Phase 2: The checker and the CI step

### Affected Files

- `qor/reliability/intent_lock_committed.py` - NEW; `check(repo_root, ledger_path, phase_min=231) -> list[Failure]` implementing LD-3 over LD-1's walker; argparse `main` (`--repo-root`, `--ledger`, `--phase-min`) exiting 1 on failures.
- `.github/workflows/ci.yml` - one step after the LD-2 anchor: `python -m qor.reliability.intent_lock_committed --phase-min 231`, with a two-line comment citing GH #352 and the #16798 asymmetry it closes.

### Changes

Phase 1's six tests go green; the existing gate-chain-completeness job semantics are untouched (additive step); the CI-coverage lint's view of workflows is checked in the sweep.

### Unit Tests

- Phase 1's six tests observed red-then-green.
- `python -m qor.reliability.intent_lock_committed --phase-min 231` observed exit 0 locally in the substantiate sweep (the same invocation CI will run).

## Feature Inventory Touches

None. Reliability tooling, one CI step, tests.

## Definition of Done

### Deliverable 1: CI sees the lock

- **D1**: A sealed session whose lock evidence is missing, tampered, or referent-drifted fails CI on the merge that carries it -- the #16798 asymmetry closed for every future session; the gate no longer depends on the person it constrains.
- **D2**: `intent_lock_committed.check` per LD-3; the CI step per LD-2.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file; this phase's own PR is the first to run the step against two live sessions' evidence.
- **D4**: `test_tampered_snapshot_is_named` and `test_the_real_ledger_verifies_clean_at_the_boundary` observed red at v0.153.0 and green after Phase 2.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase233-ci-lock-verify.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase233-ci-lock-verify.md --repo-root .` -- citation truth check.
