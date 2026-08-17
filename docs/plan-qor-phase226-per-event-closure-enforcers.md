# Plan: Closure provenance names the enforcer that guards each finding

**iteration**: 2

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: The corrective path repairs only the `closure_enforcer` field of events already closed as `remediated`; it cannot reopen, retimestamp, or change the reason -- by design. A batch in which every event is already addressed still returns `(0, [])` indistinguishably from a miss.
- non_goals: No distinguishable already-done signal (filed as its own issue at cycle end). No skill-text changes: the `/qor-audit` Step 4.2 and `/qor-remediate` Step 6 snippets pass a single shared enforcer, which remains a valid form of the widened signature (backward-compatible wrapper rationale per SG-AffectedFilesContract-A). No execution of the historical repair of the three mis-cited Phase 223 events -- that is the follow-on `/qor-remediate` pass immediately after this seal, using the API this phase ships.
- exclusions: GH #332, GH #337, GH #320, GH #286. PR #338 close/repoint remains an operator decision.

## Iteration 2 disposition of the iteration-1 VETO (F1, F2)

- **F1**: the adopted test file is now described from the artifact, not from prose: `git show bd63317:tests/test_remediate_per_event_enforcers.py` holds exactly four test functions (`test_mark_addressed_preserves_per_event_enforcers`, `test_invalid_member_prevents_entire_batch_mutation`, `test_correct_closure_enforcers_repairs_only_citation`, `test_list_signature_remains_supported`). The three implemented-but-untested behaviors get a NEW companion test file in Phase 1, each test red against v0.147.0; the O1 sharpness assertion (repaired event's `addressed` stays true) joins that file. Phase 2's acceptance counts eight observed tests, not ten imagined ones.
- **F2**: LD-5 and the Phase 3 receives list now include `_MODULE_RE`, `_GATE_STEP_RE`, `_CANNOT_AUTOMATE_PREFIX` (adopted module lines 54-56), which `_validate_closure_enforcer` lexically requires and nothing staying behind uses. Landing estimates: `remediate_mark_addressed.py` near 173, `remediate_attestation.py` near 119.

## Open Questions

None. Adoption provenance is declared: the implementation and test pair originate on `fix/stabilization-286-332-333-336-337` (commits `57eb632` fix, `bd63317` tests), authored by Knapp-Kevin, verified green in PR #338's CI run 32024552666 on the identical file base (research brief docs/research-brief-gh333-salvage-2026-08-17.md); adoption is by cherry-pick to preserve authorship, tests first so the red/green sequence is observed on this branch.

## Locked Decisions

**LD-1: The shipped signature takes one enforcer per batch; the widened signature accepts an event-to-enforcer mapping while keeping the list-plus-shared-enforcer form valid.**

```
git show v0.147.0:qor/scripts/remediate_mark_addressed.py | grep -nE '^def mark_addressed\(' -> 157:def mark_addressed(
```

```
git show v0.147.0:qor/scripts/remediate_mark_addressed.py | grep -nE 'closure_enforcer: str,' -> 162:    closure_enforcer: str,
```

**LD-2: Every enforcer in a mapping validates against the existing four-form contract before attestation and before any durable mutation (all-or-nothing).**

```
git show v0.147.0:qor/scripts/remediate_mark_addressed.py | grep -nE '^def _validate_closure_enforcer' -> 52:def _validate_closure_enforcer(value: str, repo_root: Path | None = None) -> None:
```

**LD-3: The shipped flip guard makes a wrong historical citation permanent -- an addressed event is never mutated -- which is why the corrective path exists as a separately attested, addressed-only mutation of the citation field alone.**

```
git show v0.147.0:qor/scripts/remediate_mark_addressed.py | grep -nE 'in target and not event' -> 97:        if event["id"] in target and not event["addressed"]:
```

**LD-4: Findings-key and attestation contracts are unchanged: PASS audit artifact whose `reviews_remediate_gate` names the remediation gate file, exactly the Phase 166 two-stage flip.** (Contract decision; the adopted tests bind it behaviorally.)

**LD-5: Razor arithmetic, measured against the adopted module (276 lines).** The attestation concern moves to a NEW `qor/scripts/remediate_attestation.py`: the validator's three constants `_MODULE_RE`, `_GATE_STEP_RE`, `_CANNOT_AUTOMATE_PREFIX` (3 lines at 54-56, used by nothing that stays), `ReviewAttestationError` (2 lines at 46-47), `ClosureEnforcerError` (2 at 50-51), `_validate_closure_enforcer` (32 at 59-90), `_verify_review_pass_artifact` (38 at 165-202), `_normalized_enforcers` (22 at 205-226) -- 99 definition-and-constant lines plus separators out, ~4 import/re-export lines back: `remediate_mark_addressed.py` lands near 173 and `remediate_attestation.py` near 119 with docstring and imports. Both under 250; every function in the adopted module is already at or under 39 lines. No comment is deleted to reach any number.

## Phase 1: Adopt the behavioral contract (tests first)

### Affected Files

- `tests/test_remediate_per_event_enforcers.py` - NEW; cherry-pick of `bd63317`, verbatim: four behavioral tests -- `test_mark_addressed_preserves_per_event_enforcers`, `test_invalid_member_prevents_entire_batch_mutation`, `test_correct_closure_enforcers_repairs_only_citation`, `test_list_signature_remains_supported`.
- `tests/test_remediate_enforcer_edges.py` - NEW; companion coverage for the three implemented-but-untested behaviors plus the O1 sharpness assertion.

### Changes

Cherry-pick `bd63317`, then author the companion file. Against v0.147.0 all mapping-form and corrective-path tests fail (a `Mapping` bound to `event_ids` with no `closure_enforcer` raises `TypeError` on the missing positional; `correct_closure_enforcers` does not exist, raising `AttributeError`) and the mapping-plus-shared-enforcer test fails because v0.147.0 raises nothing where `ClosureEnforcerError` is expected. Red is observed and recorded before Phase 2. `test_list_signature_remains_supported` already passes at v0.147.0, stated as such.

### Unit Tests

- The four cherry-picked tests: each invokes `mark_addressed` / `correct_closure_enforcers` and asserts on returned counts and written event state via monkeypatched shadow-process boundaries -- no presence-only assertions.
- `tests/test_remediate_enforcer_edges.py::test_empty_mapping_is_rejected_before_any_mutation` - `mark_addressed({}, ...)` raises `ClosureEnforcerError` and no write occurs.
- `tests/test_remediate_enforcer_edges.py::test_mapping_plus_shared_enforcer_is_rejected` - a mapping together with a VALID `closure_enforcer=` (a form `_validate_closure_enforcer` accepts) raises `ClosureEnforcerError`; the two forms cannot be mixed. The enforcer must be valid so the red observation at v0.147.0 is "no error raised", not a wrong-reason `ClosureEnforcerError` from shared-enforcer validation.
- `tests/test_remediate_enforcer_edges.py::test_unknown_mapping_ids_surface_in_missing` - an unknown event id in the mapping appears in the returned `missing` list while known ids still flip (SG-032 at the mapping surface).
- `tests/test_remediate_enforcer_edges.py::test_corrective_repair_leaves_addressed_true` - after `correct_closure_enforcers`, the repaired event's `addressed` remains true and `addressed_ts` is unchanged (O1 sharpness).

## Phase 2: Adopt the implementation

### Affected Files

- `qor/scripts/remediate_mark_addressed.py` - cherry-pick of `57eb632`: `_normalized_enforcers` (shared-vs-mapping normalization, validation before attestation), `_flip_event_fields_per_event` (per-event enforcer application plus the `addressed_only` corrective mode), widened `mark_addressed`, new `correct_closure_enforcers`.
- `tests/test_sg_closure_enforcement.py` - caller sweep, no change expected (legacy signature intact); verified by running.

### Changes

Cherry-pick `57eb632`. Phase 1's suite goes green; the pre-existing closure-enforcement suite stays green unmodified, which is the backward-compatibility evidence.

### Unit Tests

- Phase 1's eight tests (four adopted, four companion) observed red-then-green, except `test_list_signature_remains_supported`, which is green at v0.147.0 by design (backward compatibility) and stays green.
- `tests/test_sg_closure_enforcement.py` observed green unmodified.

## Phase 3: Razor extraction and doctrine parity

### Affected Files

- `qor/scripts/remediate_attestation.py` - NEW; receives `_MODULE_RE`, `_GATE_STEP_RE`, `_CANNOT_AUTOMATE_PREFIX`, `ReviewAttestationError`, `ClosureEnforcerError`, `_validate_closure_enforcer`, `_verify_review_pass_artifact`, `_normalized_enforcers` per LD-5, unchanged.
- `qor/scripts/remediate_mark_addressed.py` - imports those names from `remediate_attestation` (exception classes re-exported so existing `except` sites and tests keep resolving them through the original module).
- `qor/references/doctrine-governance-enforcement.md` - section 10.1 Stage 2 paragraph amended: `mark_addressed` accepts either a list with one shared `closure_enforcer` or an `{event_id: closure_enforcer}` mapping validated per event; and a sentence naming `correct_closure_enforcers` as the narrow PASS-attested repair for a wrong historical citation (cannot reopen, retimestamp, or change the reason).

### Changes

Pure structural move plus the doctrine amendment, one step so the written contract and the shipped surface change together. No behavior change: the whole suite is the guard.

### Unit Tests

- Full suite green after the move (the ten Phase 1 tests and the legacy closure suite exercise every moved name through the `remediate_mark_addressed` namespace).

## Feature Inventory Touches

None. Governance tooling, tests, and one doctrine; no user-touchable feature surface.

## Definition of Done

### Deliverable 1: Per-event closure provenance

- **D1**: A multi-finding remediation closes each event citing the mechanism that guards that event's pattern.
- **D2**: `mark_addressed(event_ids: list[str] | Mapping[str, str], ..., closure_enforcer: str | None = None)` in `qor/scripts/remediate_mark_addressed.py`; mapping form validates every enforcer before attestation before mutation.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: `test_mark_addressed_preserves_per_event_enforcers` observed failing against v0.147.0 and passing after Phase 2.

### Deliverable 2: Corrective path for wrong historical citations

- **D1**: A mis-cited closed event is repairable without reopening it.
- **D2**: `correct_closure_enforcers(event_enforcers, session_id, review_pass_artifact_path, remediate_gate_path)`; addressed-only, citation-field-only.
- **D4**: the corrective-path tests observed red-then-green across the cherry-picks.

### Deliverable 3: Razor compliance

- **D1**: The adopted module is structurally reduced per the LD-5 arithmetic, not comment-stripped.
- **D2**: `remediate_mark_addressed.py` and `remediate_attestation.py` both at or under 250 lines; all functions at or under 40.
- **D4**: line counts observed in the substantiate sweep.

### Deliverable 4: Doctrine parity

- **D1**: Section 10.1's written Stage 2 contract matches the shipped signature and names the corrective path.
- **D2**: `qor/references/doctrine-governance-enforcement.md` amended in the same step as the extraction.
- **D4**: doc-integrity strict pass at substantiate; the amended paragraph names both accepted forms.

## CI Commands

- `python -m pytest tests/ -q` -- full suite including the ten adopted behavioral tests and the unchanged legacy closure suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase226-per-event-closure-enforcers.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase226-per-event-closure-enforcers.md --repo-root .` -- citation truth check (the Phase 225 enforcer, over this plan's own Locked Decisions).
