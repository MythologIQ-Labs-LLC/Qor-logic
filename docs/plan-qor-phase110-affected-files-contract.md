# Plan: Phase 110 - SG-AffectedFilesContract-A countermeasure suite

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Affected Files Contract
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: Signature-Widening Cascade
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: Persistence Cascade
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations: The two new lints and the three new audit_risk_score signals are heuristic and WARN-only (advisory) in V1; they enumerate likely caller/persistence cascade gaps but do not block. Conversion to hard VETO is a deferred V2.
- non_goals: No change to the binding Step 3 audit passes; no &dyn-trait vtable cascade analysis; no macro-built or string-concatenated SQL parsing.
- exclusions: No retroactive application to sealed plans.

## Open Questions

None. Issues #133, #134, #135, #136, #137 carry detailed specifications, proposed implementations, test lists, and acceptance criteria. This plan transcribes and sequences them.

## Context

COREFORGE Phase 399 produced four same-family defects in one audit cycle: prose promises whose implementing files were not enumerated in any phase's `### Affected Files` block are by construction unfulfilled. The family lacks a named countermeasure entry, so each sub-leaf (call-graph cascade, persistence cascade) is rediscovered independently. This phase anchors the family doctrine (#136) and ships the auditor-side + author-side countermeasures (#133, #134, #135, #137).

## Feature Inventory Touches

Empty. Governance tooling + doctrine + skill-prompt enforcement only; no `src/` user-touchable product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: SG-AffectedFilesContract-A doctrine anchor (#136)

### Affected Files

- `tests/test_affected_files_contract_doctrine.py` - NEW. Behavioral check that the doctrine defines the entry and that the three sibling cross-references are bidirectional.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - AMENDED. Add `SG-AffectedFilesContract-A` entry (text from #136) after `SG-AuthorAuditMomentum-A`; add the new SG id to the cross-reference lines of the two sibling entries that exist in this repo: `SG-CitationDrift-A` and `SG-AuthorAuditMomentum-A`. `SG-EnumerationVerificationGap-A` is a COREFORGE consumer-repo entry (Phase 373) not present in qor-logic; it remains a one-way prose cross-reference in the new entry body with no back-edit (no such entry to edit here).

### Changes

Insert the `SG-AffectedFilesContract-A` section (pattern definition, originating recurrence, countermeasures, cross-references) per #136. Update the two in-repo sibling entries' cross-reference lines (`SG-CitationDrift-A`, `SG-AuthorAuditMomentum-A`) to name `SG-AffectedFilesContract-A`.

### Unit Tests

- `tests/test_affected_files_contract_doctrine.py::test_entry_defined_with_required_sections` - invokes a parser over the doctrine file; asserts the `SG-AffectedFilesContract-A` heading exists and its body names both the call-graph and persistence-cascade sub-leaves. Fails if the entry is absent or missing a sub-leaf.
- `tests/test_affected_files_contract_doctrine.py::test_sibling_cross_references_are_bidirectional` - invokes the parser; asserts each in-repo sibling (`SG-CitationDrift-A`, `SG-AuthorAuditMomentum-A`) names `SG-AffectedFilesContract-A` in its body. Fails if any back-reference is missing.

## Phase 2: plan_signature_widening_caller_lint (#133)

### Affected Files

- `tests/test_plan_signature_widening_caller_lint.py` - NEW. Behavioral tests for caller-enumeration completeness.
- `qor/scripts/_lint_utils.py` - NEW. Shared `find_callers(name, repo_root)` helper (consumed by this lint and by Phase 4's audit_risk_score signal, per #135 de-duplication note).
- `qor/scripts/plan_signature_widening_caller_lint.py` - NEW. Parses signature-change grammar, greps callers, cross-checks Affected Files, emits WARN per unenumerated caller file.
- `qor/skills/governance/qor-audit/SKILL.md` - AMENDED. Wire into the Step 0.6 lint ladder (`|| true` WARN-only).

### Changes

Per #133: signature-change regex set (`widen \`fn\`(...) to`, `change \`fn\` signature`, `add ... parameter to \`fn\``, `replace \`fn\` body`); for each function, grep `\b<fn>\s*\(` over `*.rs|*.py|*.ts|*.tsx`, build caller-file set excluding the definition file, cross-check `### Affected Files` paths, WARN per missing caller file. Stop-list common trait/method names (`new`, `next`, `default`, `clone`, `len`, `is_empty`, `fmt`, `drop`, `hash`, `eq`, `partial_cmp`, `cmp`); skip lines starting with `assert!`/`debug_assert!`/`dbg!`; 8-char minimum function name (env `QOR_PLAN_LINT_MIN_FN_LEN`). Escape hatch `<!-- signature-widening-exempt: <fn> -->`. CLI `--plan <path> --repo-root <dir>`; WARN-only, exit 0.

### Unit Tests

- `tests/test_plan_signature_widening_caller_lint.py::test_widening_with_complete_caller_enumeration_passes` - all caller files enumerated -> no warnings (invokes lint, asserts empty findings).
- `::test_widening_with_missing_caller_file_warns` - one caller file omitted -> warning naming that file.
- `::test_escape_hatch_comment_suppresses_warning` - exempt comment present -> no warning.
- `::test_stop_listed_name_skipped` - `new(` cascade -> skipped.
- `::test_short_function_name_skipped` - sub-threshold name -> skipped.
- `::test_no_widening_prose_passes` - no signature-change grammar -> no warnings.
- `::test_macro_caller_skipped` - macro-invocation line -> not counted as caller.

## Phase 3: plan_data_round_trip_lint (#134)

### Affected Files

- `tests/test_plan_data_round_trip_lint.py` - NEW. Behavioral tests for struct-field persistence-cascade completeness.
- `qor/scripts/plan_data_round_trip_lint.py` - NEW. Parses struct-field-addition grammar; greps `CREATE TABLE`, `FromRow` derives, `INSERT`/`SELECT`; WARNs when a FromRow field lacks a schema column or the Affected Files omit the persistence update.
- `qor/skills/governance/qor-audit/SKILL.md` - AMENDED. Wire into Step 0.6 ladder.

### Changes

Per #134: struct-field-addition regex (`widen \`Struct\` to add field \`f\``, `add ... field \`f\` to \`Struct\``); for each `(struct, field)`, parse literal `CREATE TABLE` column lists, match `FromRow`-derived struct fields against schema columns, check `INSERT`/`SELECT` projections; WARN on cascade gap. Escape hatch `<!-- transient-field: Struct.field reason: <prose> -->`. Unparseable SQL emits a `skipping` stderr note (no false WARN). CLI `--plan <path> --repo-root <dir>`; WARN-only, exit 0.

### Unit Tests

- `tests/test_plan_data_round_trip_lint.py::test_field_added_with_schema_update_in_affected_files_passes`
- `::test_field_added_without_schema_update_warns`
- `::test_transient_field_escape_hatch_suppresses`
- `::test_field_added_with_explicit_transient_prose`
- `::test_no_field_addition_passes`
- `::test_unparseable_sql_emits_skip_note` - asserts a skip note is emitted (captured), not a false warning.

## Phase 4: audit_risk_score cascade signals (#135)

### Affected Files

- `tests/test_audit_risk_score.py` - AMENDED. Add the seven signal tests (three new signals + regression + API-compat).
- `qor/scripts/audit_risk_score.py` - AMENDED. Add `signature-widening-cascade`, `struct-field-cross-persistence-boundary`, `scope-narrowing-prose-in-multi-entrypoint-file` detectors; extend `score_plan(plan_path, repo_root=None)`; add `--repo-root` CLI arg; reuse `_lint_utils.find_callers`.

### Changes

Per #135: three `_detect_<signal>(text, repo_root) -> bool` functions appended to the open `flags` tuple. Signal 1 fires when signature-change grammar present AND function appears in >=3 caller files. Signal 2 fires when struct-field-addition grammar present AND struct appears in a `FromRow` derive or `CREATE TABLE`. Signal 3 fires when a MODIFY scope narrows to named functions in a file that has additional unenumerated public functions. `option_b_required` stays True iff any flag fires. `score_plan` gains `repo_root: Path | None = None` (defaults cwd) - backward compatible.

### Unit Tests

- `tests/test_audit_risk_score.py::test_signature_widening_3plus_callers_flags_option_b`
- `::test_signature_widening_2_callers_does_not_flag`
- `::test_struct_field_addition_with_persistence_flags`
- `::test_struct_field_addition_no_persistence_does_not_flag`
- `::test_scope_narrowing_in_multi_entrypoint_file_flags`
- `::test_no_new_signals_preserves_existing_behavior` - regression: existing two-signal behavior unchanged.
- `::test_repo_root_default_to_cwd` - API-compat: `score_plan(plan)` still callable without repo_root.

## Phase 5: qor-plan Step 5 cascade-discipline bullet (#137)

### Affected Files

- `tests/test_qor_plan_cascade_checklist.py` - NEW. Asserts the Step 5 checklist contains the cascade-discipline bullet citing SG-AffectedFilesContract-A.
- `qor/skills/sdlc/qor-plan/SKILL.md` - AMENDED. Insert the 9th Step 5 checklist bullet (text from #137).
- `qor/dist/variants/{claude,codex,kilo-code}/skills/**` - REGENERATED. Variants reflect the source skill edit.

### Changes

Insert the cascade-discipline checklist bullet after the SG-PlanTextDrift-A bullet, citing `SG-AffectedFilesContract-A`. Regenerate variants.

### Unit Tests

- `tests/test_qor_plan_cascade_checklist.py::test_step5_has_cascade_discipline_bullet` - invokes a parser over the qor-plan SKILL.md; asserts a Step 5 checklist item references both caller (cross-file) enumeration and persistence touchpoints and cites `SG-AffectedFilesContract-A`. Fails if the bullet is absent.

## Definition of Done

### Deliverable D-110.1: Affected-Files-Contract doctrine
- **D1**: The shadow-genome countermeasure catalog names the `SG-AffectedFilesContract-A` family with call-graph and persistence sub-leaves.
- **D2**: Entry added to `doctrine-shadow-genome-countermeasures.md`; the two in-repo sibling entries (`SG-CitationDrift-A`, `SG-AuthorAuditMomentum-A`) back-reference it.
- **D3**: Doctrine is the structured countermeasure layer; entry follows the established shape.
- **D4**: `tests/test_affected_files_contract_doctrine.py` passes (entry + bidirectional cross-refs).

### Deliverable D-110.2: signature-widening caller lint
- **D1**: A pre-audit lint surfaces caller files not enumerated in Affected Files on a declared signature widening.
- **D2**: `qor/scripts/plan_signature_widening_caller_lint.py` with CLI `--plan --repo-root`; shared `_lint_utils.find_callers`.
- **D3**: Wired into `/qor-audit` Step 0.6 (`|| true`).
- **D4**: `tests/test_plan_signature_widening_caller_lint.py` passes all seven cases.

### Deliverable D-110.3: data round-trip lint
- **D1**: A pre-audit lint surfaces struct-field persistence-cascade gaps.
- **D2**: `qor/scripts/plan_data_round_trip_lint.py` with CLI `--plan --repo-root`.
- **D3**: Wired into `/qor-audit` Step 0.6 (`|| true`).
- **D4**: `tests/test_plan_data_round_trip_lint.py` passes all six cases.

### Deliverable D-110.4: audit_risk_score cascade signals
- **D1**: Option B auto-mandates an independent reviewer on signature-widening / persistence-cascade / scope-narrowing signals.
- **D2**: Three detectors added; `score_plan(plan, repo_root=None)` backward compatible; `--repo-root` CLI arg.
- **D3**: Reuses `_lint_utils.find_callers`; flags appended to the open tuple.
- **D4**: `tests/test_audit_risk_score.py` passes the seven new/regression cases.

### Deliverable D-110.5: qor-plan cascade checklist bullet
- **D1**: Plan authors are reminded at Step 5 to enumerate caller + persistence cascade or declare exempt.
- **D2**: 9th Step 5 checklist bullet added; variants regenerated.
- **D3**: Bullet cites `SG-AffectedFilesContract-A`.
- **D4**: `tests/test_qor_plan_cascade_checklist.py` passes.

## CI Commands

- `python -m pytest tests/test_affected_files_contract_doctrine.py -q` - doctrine entry + cross-refs.
- `python -m pytest tests/test_plan_signature_widening_caller_lint.py -q` - caller-enumeration lint.
- `python -m pytest tests/test_plan_data_round_trip_lint.py -q` - persistence-cascade lint.
- `python -m pytest tests/test_audit_risk_score.py -q` - cascade signals + regression.
- `python -m pytest tests/test_qor_plan_cascade_checklist.py -q` - Step 5 bullet.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.check_variant_drift` - generated variant drift.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase110-affected-files-contract.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase110-affected-files-contract.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

Pre-existing repo-wide CI jobs not relevant to this audit-tooling phase:

- `test_packaging_install` - packaging integration smoke; orthogonal.
- `gate_chain_completeness` - sealed-phase chain audit; runs every PR.
- `dependency_admission_lint` - dependency cooling-period check; no dependency changes here.
