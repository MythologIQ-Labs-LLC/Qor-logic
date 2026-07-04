# Plan: Phase 166 - SG closure enforcement (GH #249)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: The corpus lint is WARN-only in V1 (the audit Step 0.6 ladder wraps `|| true`); the fail-closed layer is the `mark_addressed` contract. Existing doctrine entries are not backfilled in this phase; the lint's finding list is the backfill worklist.
- non_goals: No change to the stage-1 `mark_addressed_pending` contract; no new `addressed_reason` enum values; no `qor/cli.py` change (generic runner invocation); no backfill of the ~8 prose-only doctrine entries.
- exclusions: Doctrine/glossary edits only via /qor-document at seal (doctrine-governance-enforcement closure rule; no glossary terms).

## Open Questions

(none)

## Origin

Research brief docs/research-brief-sg-closure-enforcement-2026-07-04.md (ledger entry #386, session `2026-07-04T0803-3fde29`); GH #249 (perspective-reset rec 3, umbrella #247). Root evidence: prose codification went 0-for-4 against SG-038 recurrence; only executable checks have stuck.

## Locked Decisions

- **LD-1: schema seam is a new property + a second `allOf` if-then rule.**
  `git show HEAD:qor/gates/schema/shadow_event.schema.json | grep -nE 'additionalProperties|allOf|addressed_pending' -> 7:additionalProperties: false, 91:addressed_pending (optional, Phase 36), 101:allOf with one if-then (addressed+remediated => addressed_pending required)`. The new `closure_enforcer` property must be added under `properties` (else `additionalProperties: false` rejects it) and the new if-then mirrors the existing Phase 36 rule shape.
- **LD-2: contract seam is `mark_addressed` stage 2 only.**
  `git show HEAD:qor/scripts/remediate_mark_addressed.py | grep -nE 'def mark_addressed|ReviewAttestationError' -> 37:class ReviewAttestationError, 64:def mark_addressed_pending, 112:def mark_addressed(event_ids, session_id, review_pass_artifact_path, remediate_gate_path)`. Stage 2 verifies audit PASS via `_verify_review_pass_artifact` (72-109) and flips fields at 126-134; the enforcer validation slots before the flip.
- **LD-3: test fixture pattern exists.**
  `grep -nE 'mock.patch.object\(shadow_process, .LOCAL_LOG_PATH' tests/test_remediate.py -> 208` -- events seeded to tmp files with `LOCAL_LOG_PATH`/`UPSTREAM_LOG_PATH` patched; new tests reuse `make_event`/`_seed` from `tests/test_remediate.py`.
- **LD-4: corpus shape for the lint.**
  `grep -cE '^## SG-' qor/references/doctrine-shadow-genome-countermeasures.md -> 40` entries; ~32 cite an enforcer inline (test path / module / gate step), ~8 prose-only (research entry #386 sampling).
- **LD-5: audit ladder wiring point.**
  `grep -n 'plan_feature_tdd_lint' qor/skills/governance/qor-audit/SKILL.md -> Step 0.6 bash ladder (all `|| true`)`; qor-audit SKILL.md is 39.6 KB (WARN, under the 40 KB EXCEEDED cap; the one-line ladder addition keeps it under).
- **LD-6: no CI workflow change.**
  The lint runs in the audit ladder (skill-time), not in .github/workflows -- no Phase 89 CI-surface registry row required this phase.
- **LD-7: complete caller enumeration for the `mark_addressed` signature change (SG-AffectedFilesContract-A).**
  `grep -rn 'mark_addressed(' qor/ tests/ -> tests/test_remediate.py:349,372,395,420,442 (5 call sites; updated in this plan); qor/skills/sdlc/qor-remediate/SKILL.md:130 + qor/skills/governance/qor-audit/SKILL.md Step 4.2 code examples (updated in Phase 2); qor/references/doctrine-governance-enforcement.md:214 names the signature (updated via /qor-document at seal); qor/dist/** (recompiled); qor/scripts/create_shadow_issue.py:113 defines an UNRELATED same-named function for the issue_created path -- exempt (not a caller of remediate_mark_addressed.mark_addressed).`

## Phase 1: Closure-enforcer contract (TDD first)

### Affected Files

- tests/test_sg_closure_enforcement.py - NEW; behavioral tests for validation, flip stamping, schema rule, and the corpus lint
- tests/test_remediate.py - the 5 existing `mark_addressed` call sites (LD-7) gain the `closure_enforcer` argument
- qor/gates/schema/shadow_event.schema.json - `closure_enforcer` property + if-then rule (LD-1)
- qor/scripts/remediate_mark_addressed.py - `closure_enforcer` required parameter on stage 2, validated fail-closed (LD-2)
- qor/scripts/sg_closure_lint.py - NEW; WARN-only corpus lint over the `## SG-` entries

### Changes

`shadow_event.schema.json`: add `closure_enforcer: {"type": ["string", "null"]}` with description; add `allOf` rule: if `addressed==true` and `addressed_reason=="remediated"` then `closure_enforcer` is required with `{"type": "string", "minLength": 8}`.

`remediate_mark_addressed.py`:
- New `ClosureEnforcerError(Exception)`.
- `_validate_closure_enforcer(value: str, repo_root: Path) -> None` -- accepts exactly four forms: (1) an existing `tests/test_*.py` path; (2) a module matching `^qor\.(scripts|reliability)\.[a-z0-9_]+$` that `importlib.util.find_spec` resolves; (3) a gate-step reference matching `^/qor-[a-z-]+ Step [0-9]+(\.[0-9]+)*$`; (4) `cannot-automate: <justification>` with justification >= 50 chars. Anything else raises `ClosureEnforcerError`; no event is mutated.
- `mark_addressed(..., closure_enforcer: str, repo_root: Path | None = None)` -- validates before `_verify_review_pass_artifact`, then includes `"closure_enforcer": closure_enforcer` in the stage-2 field flip.

`sg_closure_lint.py` (<150 lines): `parse_entries(text) -> list[(name, body)]` splitting on `^## SG-`; `entry_cites_enforcer(body) -> bool` matching any of: `tests/test_[a-z0-9_]+\.py`, `qor\.(scripts|reliability)\.[a-z0-9_]+`, `qor/(scripts|reliability)/[a-z0-9_]+\.py`, `/qor-[a-z-]+` + `Step`, or a `cannot-automate` marker; `main(argv)` with `--doctrine <path>` (default the countermeasure doctrine) printing `WARN [sg-closure] <name>: no executable enforcer cited` per finding and a summary line; exit 1 when findings exist (ladder wraps `|| true`; V2 removes the wrap).

### Unit Tests

- tests/test_sg_closure_enforcement.py::test_validate_accepts_all_four_forms - existing test path, importable module, gate-step ref, and a >=50-char cannot-automate all validate without raising
- tests/test_sg_closure_enforcement.py::test_validate_rejects_bad_forms - missing test path, non-importable module, malformed gate ref, short cannot-automate justification, and empty string each raise ClosureEnforcerError
- tests/test_sg_closure_enforcement.py::test_mark_addressed_stamps_closure_enforcer - happy path (seeded tmp log + PASS review artifact): event flips addressed=true AND carries the closure_enforcer value
- tests/test_sg_closure_enforcement.py::test_mark_addressed_invalid_enforcer_mutates_nothing - invalid enforcer raises before any flip; event remains addressed=false
- tests/test_sg_closure_enforcement.py::test_schema_requires_enforcer_on_remediated_close - jsonschema validation: a remediated+addressed event WITHOUT closure_enforcer fails; WITH it passes; an unaddressed event without it still passes (grandfather)
- tests/test_sg_closure_enforcement.py::test_lint_flags_only_prose_only_entries - synthetic doctrine with one enforcer-citing and one prose-only entry: exactly the prose-only entry is flagged; exit 1 with findings, 0 without

## Phase 2: Wiring + prose

### Affected Files

- qor/skills/governance/qor-audit/SKILL.md - Step 0.6 ladder gains `qor-logic scripts sg_closure_lint || true` (LD-5); the Step 4.2 `rma.mark_addressed(...)` code example gains the `closure_enforcer` argument (LD-7)
- qor/skills/sdlc/qor-remediate/SKILL.md - Step 4/6 prose documents the required `closure_enforcer` argument and its four accepted forms; the Step 6 call example updated (LD-7)
- qor/dist/ - recompiled
- tests/test_sg_closure_wiring.py - NEW; single wiring lock

### Unit Tests

- tests/test_sg_closure_wiring.py::test_audit_ladder_and_remediate_document_closure_enforcer - audit SKILL.md Step 0.6 invokes `sg_closure_lint`; remediate SKILL.md names `closure_enforcer` and the `cannot-automate:` form. Carries `# prose-lint: ok=wiring regression lock; skill prose has no invokable unit`.

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: closure-enforcer contract

- **D1**: An SG event can only close as `remediated` when an executable enforcer (or an explicit cannot-automate decision) is recorded on the event (GH #249 core rule).
- **D2**: Schema property + if-then rule; `mark_addressed` required parameter validated against the four forms; fail-closed with `ClosureEnforcerError`.
- **D3**: doctrine-governance-enforcement gains the closure rule (via /qor-document); seal entry cites this plan; GH #249 closes with the contract documented.
- **D4**: `test_mark_addressed_invalid_enforcer_mutates_nothing` observes the raise-without-mutation behavior; `test_schema_requires_enforcer_on_remediated_close` observes the schema rejection.

### Deliverable: corpus lint

- **D1**: Prose-only countermeasure entries are visible at every audit (the backfill worklist can never silently grow).
- **D2**: `qor/scripts/sg_closure_lint.py` <150 lines, stdlib; exit 1 on findings for the V2 flip.
- **D3**: Wired into the audit Step 0.6 ladder WARN-only; dist recompiled.
- **D4**: `test_lint_flags_only_prose_only_entries` observes correct discrimination on a synthetic corpus.

## CI Commands

- `python -m pytest tests/test_sg_closure_enforcement.py tests/test_sg_closure_wiring.py -q` -- new-test determinism (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts sg_closure_lint` -- live corpus WARN inventory (expected ~8 findings; exit 1 wrapped by the ladder)
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase166-sg-closure-enforcement.md` -- plan-text consistency
