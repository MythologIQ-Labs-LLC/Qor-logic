# Plan: Phase 192 - Spec corpus Phase B/C: gate-chain wiring + per-requirement verify (GH #277)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Spec delta
  home: qor/references/spec-grammar.md

**boundaries**:
- limitations: [Phase C verifies structure and declared-surface existence, never scenario semantics (correctness stays a Judge duty); the fold requires a PASS audit in the session]
- non_goals: [retroactive spec backfill (the brownfield accretion rule stands), semantic scenario verification, delta authoring automation]
- exclusions: [enterprise/federation concepts]

## Open Questions

(none)

## Origin

Research brief docs/research-brief-spec-corpus-phase-b-2026-07-13.md (ledger entry #486, session `2026-07-13T1640-229740`); GH #277 (follow-up carrying #239's Phases B and C). Phase A shipped in v0.130.0.

## Locked Decisions

- **LD-1: deltas are consumables with a fixed lifecycle.**
  Authored at plan time at `qor/specs/<capability>/deltas/<session-id>.md`; declared in the plan gate artifact's new `spec_deltas` array; linted at audit; folded into `qor/specs/<capability>/spec.md` inside substantiate AFTER the reliability gates; the delta file is deleted by the fold (git history is the archive; the corpus is current-truth). `grep -nE 'def apply' qor/scripts/spec_merge.py -> 57` (the fold engine exists; Phase B adds the runner).
- **LD-2: schema changes are additive to existing schemas.**
  plan.schema.json gains optional `spec_deltas`: array of {capability, delta_path, ops[], evidence?} (`grep -nE 'new_ceremony_artifacts' qor/gates/schema/plan.schema.json -> 71` is the structural precedent). substantiate.schema.json gains optional `spec_corpus_hash` (object: capability -> sha256). `grep -nE 'compares this list against the directory' qor/scripts/gate_schema_freeze_lint.py -> 8` -- the freeze lint governs new schema FILES; additive property edits are in-contract.
- **LD-3: skill wiring is pointer-steps only.**
  qor-audit at 39,536 B and qor-substantiate at 39,502 B against the 39,936 headroom lock (tests/test_substantiate_staging_gates.py:48-62) -> each gains a two-line step pointing at references/ prose: qor-plan Step 3b (author + declare the delta when the plan changes contracted behavior; reference in qor/skills/sdlc/qor-plan/references/), qor-audit Step 0.7 (delta grammar pre-pass, `python -m qor.scripts.spec_lint --delta --files <paths> || VETO` with category `specification-drift`; reference file), qor-substantiate Step 7.9 (fold + record hash; extend the existing references/seal-gate-ladder.md).
- **LD-4: the fold is deterministic, loud, and evidenced.**
  New `qor/scripts/spec_fold.py`: `fold_session_deltas(repo_root, session_id) -> dict[str, str]` reads the plan artifact's spec_deltas, applies spec_merge per capability (SpecMergeError propagates -- a conflicting delta aborts the seal loudly), lints the folded result (a fold that produces an invalid spec aborts), writes the spec, deletes the delta, returns {capability: LF-normalized sha256}. The seal entry records `**Spec Corpus Hash**: capability=hash` and substantiate.json carries `spec_corpus_hash`. No deltas declared -> returns {} (no-op; sessions without behavior changes are unaffected).
- **LD-5: Phase C verifies without fabricating.**
  New `qor/scripts/spec_requirement_verify.py`: for each declared delta, every ADDED/MODIFIED requirement must pass the grammar lint, carry >= 1 scenario, and (when the entry declares `evidence`) the evidence path must exist. Output feeds `qa_evidence.build_payload(coverage=...)` as {checked, verified, unverified: [names]} -- producing the pillar qa_evidence.py:30 explicitly defers. Scenario-intent semantics remain a Judge duty documented in the audit pre-pass reference.
- **LD-6: self-application is the acceptance test.**
  This cycle authors the first live capability spec delta (`qor/specs/spec-corpus/deltas/2026-07-13T1640-229740.md`, requirements describing the fold behavior itself), declares it in this plan's gate artifact, and THIS session's seal performs the first real fold -- the integration test then asserts the folded spec exists, lints clean, and the delta is gone.

## Phase 1: Schema + delta lint mode (TDD first)

### Affected Files

- tests/test_spec_delta_wiring.py - NEW (red first)
- qor/gates/schema/plan.schema.json - additive spec_deltas
- qor/gates/schema/substantiate.schema.json - additive spec_corpus_hash
- qor/scripts/spec_lint.py - `--delta` mode: section structure (only the three section heads, at least one), inner ADDED/MODIFIED blocks pass check(), REMOVED items are bare headings

### Unit Tests

- tests/test_spec_delta_wiring.py - test_plan_artifact_accepts_spec_deltas: write_gate_artifact with a valid spec_deltas array succeeds; malformed op rejected (red today)
- tests/test_spec_delta_wiring.py - test_substantiate_artifact_accepts_corpus_hash (red today)
- tests/test_spec_delta_wiring.py - test_delta_lint_valid_delta_passes / test_delta_lint_bad_section_flagged / test_delta_lint_bad_inner_block_flagged: CLI exit codes + finding codes (red today)

## Phase 2: Fold runner + requirement verify (TDD first)

### Affected Files

- tests/test_spec_fold.py - NEW (red first)
- qor/scripts/spec_fold.py - NEW per LD-4
- qor/scripts/spec_requirement_verify.py - NEW per LD-5

### Unit Tests

- tests/test_spec_fold.py - test_fold_applies_and_deletes_delta: fixture repo with a plan artifact declaring one delta -> spec updated, delta gone, returned hash equals the file's LF sha256 (red today)
- tests/test_spec_fold.py - test_fold_conflict_aborts_loudly: delta MODIFYing an absent requirement -> SpecMergeError propagates, spec unchanged, delta retained (red today)
- tests/test_spec_fold.py - test_fold_invalid_result_aborts: a delta that folds into a grammar-violating spec -> error, nothing written
- tests/test_spec_fold.py - test_fold_noop_without_deltas: no spec_deltas in the plan artifact -> {{}} and no filesystem change
- tests/test_spec_fold.py - test_requirement_verify_produces_coverage_payload: verified/unverified split over a fixture delta (missing evidence path -> unverified with the requirement named); payload accepted by qa_evidence.build_payload (red today)

## Phase 3: Skill wiring + self-application

### Affected Files

- qor/skills/sdlc/qor-plan/SKILL.md + references/spec-delta-authoring.md - Step 3b pointer + prose
- qor/skills/governance/qor-audit/SKILL.md + references/spec-delta-pre-pass.md - Step 0.7 pointer + prose (Judge semantics duty documented here)
- qor/skills/governance/qor-substantiate/SKILL.md + references/seal-gate-ladder.md - Step 7.9 pointer + fold prose
- qor/specs/spec-corpus/deltas/2026-07-13T1640-229740.md - the first live delta (LD-6)
- qor/references/glossary.md - "Spec delta" entry
- qor/dist/ - recompiled

### Unit Tests

- tests/test_spec_delta_wiring.py - test_skill_pointer_steps_present: the three SKILL.md files carry their step pointers and cited references exist; both big skills stay under the headroom lock (invokes os.path.getsize against the bound)
- tests/test_spec_delta_wiring.py - test_self_application_delta_lints: the live delta file passes `--delta` lint (the fold itself is exercised by this session's seal per LD-6)

## Feature Inventory Touches

(empty -- governance tooling)

## Definition of Done

### Deliverable: spec corpus with chain authority

- **D1**: A plan that changes contracted behavior declares and authors a spec delta; audit lints it (VETO into specification-drift); the seal folds it after PASS and records the folded hash -- deltas never merge on VETO'd or unsealed work (GH #277 / #239 acceptance).
- **D2**: spec_lint --delta, spec_fold.fold_session_deltas, spec_requirement_verify + qa coverage payload; additive schema properties; pointer-steps within the headroom lock.
- **D3**: Glossary entry; ledger entries for plan/audit/implement/seal; the seal entry carries the FIRST live Spec Corpus Hash (LD-6); CHANGELOG feature entry.
- **D4**: The twelve tests observe schema acceptance/rejection, delta lint codes, fold semantics (apply/delete, loud conflict, invalid-result abort, no-op), coverage payload production, wiring presence within budget, and the live delta's lint; red-then-green twice; the live fold lands in this session's own seal.

## CI Commands

- `python -m pytest tests/test_spec_delta_wiring.py tests/test_spec_fold.py tests/test_spec_lint.py tests/test_spec_merge.py -q` - focused suites (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
