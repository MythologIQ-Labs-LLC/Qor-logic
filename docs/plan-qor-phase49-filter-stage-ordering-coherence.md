# Plan: Phase 49 — Filter-stage ordering coherence (Wave 2 blind spot)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: closes GH #47 (operator-filed 2026-05-10 from COREFORGE session)

**terms_introduced**:
- term: Filter-Stage Ordering Coherence Pass
  home: qor/skills/governance/qor-audit/SKILL.md
- term: composition-defect
  home: qor/gates/schema/audit.schema.json
- term: pipeline_inversion_lint
  home: qor/scripts/pipeline_inversion_lint.py
- term: SG-040
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: filter dependency graph
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 runnable helper (`pipeline_inversion_lint`) covers Python source only via stdlib `ast`. Rust / TypeScript / Go static analysis is OUT OF SCOPE; for those languages the audit pass is operator-instructional (the Judge applies the checklist manually).
  - V1 detection is heuristic: flags any `.filter()` chain or sequential `if/continue` block whose predicate references a struct/dict field that ALSO appears in a function whose name matches `validate_*`, `check_*`, `verify_*`, or `is_valid*`. False positives expected; the Judge dispositions them.
  - V1 emits findings for the Judge to weigh; it does NOT produce ordering proofs. Operator (or Judge) confirms the dependency graph manually.
  - The `composition-defect` finding category is added to the audit-schema enum but applies broadly to any audit-pass that detects an ordering / composition-level defect, not solely this pass.
- non_goals:
  - Automatic dependency-graph construction from invariant inference. V2+ territory.
  - Topological sort verification of arbitrary filter pipelines. Operator/Judge judgment in V1.
  - Cross-function call-graph analysis. V1 walks one function at a time.
- exclusions:
  - No changes to `qor-plan`, `qor-implement`, `qor-substantiate` skills — Phase 49 is a `qor-audit` Step 3 extension only.
  - No new shadow event types; findings surface through existing `composition-defect` finding category (additions to `findings_categories` enum).

## Open Questions

None at submission.

---

## Phase 1: Doctrine + audit schema enum extension

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` — append SG-040 entry between SG-039 and SG-InfrastructureMismatch.
- `qor/gates/schema/audit.schema.json` — add `composition-defect` to `findings_categories` enum.
- `tests/test_doctrine_sg_040_present.py` — NEW.
- `tests/test_audit_schema_composition_defect_enum.py` — NEW.

### Changes

**`doctrine-shadow-genome-countermeasures.md`** — append after SG-039:

```markdown
## SG-040: filter-stage ordering invariant violation

A multi-stage filter / decision pipeline where each stage assumes a prior stage enforced its invariant. When the implementation runs stage N before stage M (where N depends on an invariant enforced by M), candidates that violate that invariant survive into stage N and may win the pipeline.

Distinct from SG-038 (numeric drift) and SG-039 (same-operation prose drift): SG-040 targets COMPOSITION defects — each stage is individually correct, but the order of stages violates invariant dependencies. Wave 2 stage-by-stage review consistently misses this because review questions ask "is each filter correct?" not "if filter A's invariant is checked elsewhere, do filters B-Z assume A ran first?"

**Countermeasure** (Phase 49): runnable lint at `qor/scripts/pipeline_inversion_lint.py` (Python AST scan) invoked at `/qor-audit` Step 3 Filter-Stage Ordering Coherence Pass. Detects filter chains and sequential filter blocks whose predicates reference fields that also appear in `validate_*` / `check_*` / `verify_*` / `is_valid*` functions; raises a Judge question about ordering. Findings route to `composition-defect` finding category.

For Rust / TypeScript / Go code, the discipline is operator-instructional in V1: the Judge enumerates filter stages, identifies preconditions and invariants, constructs the dependency graph, and verifies the code order is a topological sort.

**Verification hint**: for any function shaped `candidates → filter → filter → … → select`, ask:
1. What invariant does each stage enforce on outputs?
2. What invariant does each stage assume on inputs?
3. Are the assumed-input invariants enforced by an earlier stage in this function (not by an external `validate()` that may or may not have run)?

**Source incident**: COREFORGE session 2026-05-08T1610-21dfe5; `dispatcher::decide()` filter pipeline accepted invalid manifests because validator ran outside `decide()` (caller responsibility). Operator caught at merge review; fix at commit `0999e47` makes validator the first filter stage. Wave 2 reviewers (qa-expert + qor-judge) flagged the missing test for `DispatchError::ValidatorFailure` but did not probe the structural condition that would make the branch fire. Filed upstream as GH #47.
```

**`audit.schema.json`** — extend `findings_categories.items.enum`:

```diff
       "infrastructure-mismatch",
-      "feature-test-undeclared"
+      "feature-test-undeclared",
+      "composition-defect"
```

### Unit Tests

- `tests/test_doctrine_sg_040_present.py`:
  - `test_sg_040_anchor_exists`
  - `test_sg_040_block_has_countermeasure_and_verification_hint`
  - `test_sg_040_distinguishes_from_sg_038_and_sg_039`
  - `test_sg_040_cites_pipeline_inversion_lint_module`
  - `test_sg_040_cites_composition_defect_finding_category`

- `tests/test_audit_schema_composition_defect_enum.py`:
  - `test_audit_schema_accepts_composition_defect_on_veto`
  - `test_audit_schema_existing_categories_still_valid` (regression guard for the 13 existing values + Phase 46 `feature-test-undeclared`).

---

## Phase 2: `pipeline_inversion_lint` helper + qor-audit Step 3 sub-pass

### Affected Files

- `qor/scripts/pipeline_inversion_lint.py` — NEW. Stdlib-only Python AST scan. Public surface:
  ```python
  @dataclass(frozen=True)
  class PipelineFinding:
      file: str
      function: str
      line: int
      stage_descriptors: tuple[str, ...]
      validator_function: str | None       # name of the *_validate / is_valid function whose fields are referenced
      shared_fields: tuple[str, ...]       # field names appearing in both the filter predicates and the validator
      message: str
  def scan(path: Path) -> list[PipelineFinding]: ...
  def main(argv: list[str] | None = None) -> int: ...  # CLI --check <file> | --repo-root <dir>
  ```
- `qor/skills/governance/qor-audit/SKILL.md` — add Filter-Stage Ordering Coherence Pass under Step 3 between Feature Test Coverage Pass and Section 4 Razor Pass.
- `tests/test_pipeline_inversion_lint.py` — NEW.
- `tests/test_audit_skill_filter_stage_pass.py` — NEW.

### Changes

**`pipeline_inversion_lint.py`** behavior:

1. Walk Python files in `--repo-root` (or single `--check` file).
2. For each function, collect:
   - **Validator functions**: names matching `validate*`, `check*`, `verify*`, `is_valid*` (case-insensitive) whose bodies reference at least one attribute access (`x.field`) or subscript (`x["field"]`).
   - **Pipeline functions**: any function containing two or more sequential `.filter(...)` method calls OR two or more `if <expr>: continue` blocks within a single `for` loop OR two or more `if <expr>: return ...` early-exit guards.
3. For each pipeline function, extract the field names referenced in filter predicates.
4. Cross-reference: if a field appears in pipeline predicates AND in a validator function's body in the same module, emit a `PipelineFinding`.
5. Findings are advisory; operator (or the Judge at audit time) confirms whether the ordering is correct.

CLI:
- `--check <file>`: scan one file; exit 0 on no findings, 1 on findings.
- `--repo-root <dir>`: scan directory recursively for `.py` files (skip `tests/` by default; `--include-tests` opts in).

**`qor-audit` SKILL.md** — new sub-pass under Step 3 (after Feature Test Coverage Pass):

```markdown
#### Filter-Stage Ordering Coherence Pass (Phase 49 wiring — #47)

For any function shaped `candidates → filter → filter → … → select`, the Judge confirms that the order of filter stages enforces invariant dependencies. Stage N must not run before stage M when N's correctness assumes the invariant M enforces.

Python source receives an automated heuristic via `qor.scripts.pipeline_inversion_lint`:

\`\`\`bash
python -m qor.scripts.pipeline_inversion_lint --repo-root . || true
\`\`\`

Findings are advisory: the Judge dispositions each by enumerating the function's filter stages, identifying preconditions and invariants, and confirming the code order is a topological sort of the dependency graph. Confirmed inversions VETO with finding category `composition-defect`.

For Rust / TypeScript / Go source, the discipline is operator-instructional in V1. The Judge walks the function manually using the SG-040 verification hint.

See `qor/references/doctrine-shadow-genome-countermeasures.md` SG-040.
```

### Unit Tests

- `tests/test_pipeline_inversion_lint.py`:
  - `test_scan_returns_empty_for_simple_file_with_no_pipelines`
  - `test_scan_detects_filter_chain_referencing_validator_field`
  - `test_scan_detects_sequential_if_continue_pipeline`
  - `test_scan_detects_early_return_guard_pipeline`
  - `test_scan_returns_no_findings_when_no_validator_function_in_module`
  - `test_scan_returns_no_findings_when_no_shared_fields`
  - `test_scan_reports_function_name_and_line`
  - `test_cli_check_exit_code_zero_on_clean_file`
  - `test_cli_check_exit_code_one_on_finding`
  - `test_cli_repo_root_walks_directory_skips_tests_by_default`
  - `test_cli_include_tests_flag_walks_tests_directory`

- `tests/test_audit_skill_filter_stage_pass.py`:
  - `test_audit_skill_has_filter_stage_pass_anchor`
  - `test_pass_appears_between_feature_test_coverage_and_razor`
  - `test_pass_cites_pipeline_inversion_lint_module`
  - `test_pass_cites_sg_040`
  - `test_pass_routes_to_composition_defect_category`
  - `test_pass_includes_rust_typescript_go_operator_instruction`

---

## Phase 3: Self-application + integration check

### Affected Files

- `tests/test_phase49_self_application.py` — NEW. Runs the lint against `qor/scripts/` and asserts the framework's own code does not contain unflagged composition defects. Documents any expected findings as benign (with rationale).

### Changes

Run `pipeline_inversion_lint.scan(repo_root="qor/scripts/")` and capture the result. Two outcomes acceptable for the framework's own seal:

1. Empty findings — framework is clean.
2. Non-empty findings with operator review: each finding has an accompanying rationale recorded in the seal entry under "SG-040 self-application disposition".

The test asserts that EITHER (1) findings are empty OR (2) every finding's `function` name is on an allowlist constant `_KNOWN_BENIGN_FUNCTIONS` declared in this test module. The allowlist is empty in V1; framework regressions surface as new findings until added with rationale.

### Unit Tests

- `tests/test_phase49_self_application.py`:
  - `test_framework_python_scripts_have_no_unallowlisted_composition_findings`

---

## CI Commands

- `python -m pytest tests/test_doctrine_sg_040_present.py tests/test_audit_schema_composition_defect_enum.py -v`
- `python -m pytest tests/test_pipeline_inversion_lint.py tests/test_audit_skill_filter_stage_pass.py -v`
- `python -m pytest tests/test_phase49_self_application.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase49-filter-stage-ordering-coherence.md`
- `python -m qor.scripts.pipeline_inversion_lint --repo-root qor/scripts/`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
