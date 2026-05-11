# Plan: Phase 46 — Feature-level TDD + Inventory Discipline

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: docs/research-brief-open-issues-grouping-2026-05-09.md (γ-bundle: GH issues #40, #41)

**terms_introduced**:
- term: FEATURE_INDEX
  home: qor/references/doctrine-feature-inventory.md
- term: feature_inventory_touches
  home: qor/gates/schema/plan.schema.json
- term: Feature Test Coverage Pass
  home: qor/skills/governance/qor-audit/SKILL.md
- term: per-feature TDD-Light
  home: qor/references/doctrine-feature-tdd.md
- term: feature-test-undeclared
  home: qor/gates/schema/audit.schema.json
- term: outside-scope regression
  home: qor/skills/governance/qor-substantiate/SKILL.md

**boundaries**:
- limitations:
  - V1 substantiate verification helper parses FEATURE_INDEX.md row counts and surfaces totals in seal entry; deep cross-check (does this test actually exercise this feature?) remains operator-eyes judgment per the SG-035 acceptance question.
  - FEATURE_INDEX.md location is operator choice (path declared at bootstrap or per project); doctrine specifies format + verification protocol, not the path.
  - V1 covers `feature_inventory_touches.operation` enum: `NEW | MODIFIED | n/a-justified`; richer state (e.g., DEPRECATED, MOVED) deferred.
  - V1 introduces the `feature-test-undeclared` finding category as a VETO ground when audit's Feature Test Coverage Pass identifies a `feature_inventory_touches` entry without a passing test descriptor.
- non_goals:
  - Auto-populating FEATURE_INDEX.md from source — repo populates manually as features land.
  - Cross-project FEATURE_INDEX comparison or shared index registry.
- exclusions:
  - No new GitHub Actions workflow; coverage gate fires at substantiate seal-time.
  - Append-only Merkle-friendly FEATURE_INDEX format is OUT OF SCOPE this phase; deferred to a future phase that resolves SG-039 / SG-038 patterns against the feature-index document itself.

## Open Questions

None at submission.

---

## Phase 1: Doctrine + schemas + worked example

### Affected Files

- `qor/references/doctrine-feature-inventory.md` — NEW. Defines FEATURE_INDEX format, status enum, lifecycle hooks, regression protocol.
- `qor/references/doctrine-feature-tdd.md` — NEW. Defines per-unit vs per-feature TDD layering, acceptance question, red-then-green cycle.
- `qor/gates/schema/plan.schema.json` — add `feature_inventory_touches` array field (optional; required-shaped per `if-then` when plan touches `src/`-equivalent — V1 keeps optional with operator discipline).
- `qor/gates/schema/audit.schema.json` — extend `findings_categories` enum with `feature-test-undeclared`.
- `qor/gates/schema/feature_index.schema.json` — NEW. JSON-schema mirror of the FEATURE_INDEX markdown table format.
- `qor/templates/FEATURE_INDEX.example.md` — NEW. Worked-example with 5 representative entries showing verified / unverified / n/a status values.

### Changes

**`qor/references/doctrine-feature-inventory.md`**:

- Standing artifact (`FEATURE_INDEX.md` or equivalent) tracking every user-touchable feature in the product, one row per feature.
- Row format: `| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |`
- Status enum: `verified` / `unverified` / `n/a` (with justification when n/a).
- Lifecycle hooks summary:
  - `/qor-plan` Step 7 — declare every feature touched in `feature_inventory_touches`.
  - `/qor-audit` Step 3 — Feature Test Coverage Pass verifies each declared touch has a test descriptor; VETO category `feature-test-undeclared`.
  - `/qor-implement` Step 5 — per-feature TDD-Light: failing-test-before-code at the path declared in plan.
  - `/qor-implement` Step 12.5 — append FEATURE_INDEX rows for new features; update existing rows for modified features.
  - `/qor-substantiate` Step 6 — re-tally totals; surface counts in seal entry; fail seal on outside-scope regression (any feature outside this plan's `feature_inventory_touches` that regressed from `verified` to `unverified` since last seal).

**`qor/references/doctrine-feature-tdd.md`**:

- Per-unit TDD (existing): one minimal failing test before implementing a helper, function, or unit. Governed by `qor/references/doctrine-test-discipline.md`.
- Per-feature TDD (this doctrine): for every entry in plan's `feature_inventory_touches`, author the failing feature-level test FIRST at the path declared in the plan, with the assertion declared in the plan; run it red; implement; run it green. The two layers coexist — per-unit tests cover helpers; per-feature tests cover user-touchable surface (routes, commands, UI events, services).
- Acceptance question (per SG-035 extension): "If the feature were silently broken but the test artifact still existed, would this assertion fail?" Test descriptors that cannot answer "yes" are presence-only and route to VETO category `feature-test-undeclared`.

**`qor/gates/schema/plan.schema.json`** — add property:

```json
"feature_inventory_touches": {
  "description": "Phase 46 (#41): every user-touchable feature this plan touches. Each entry names the FEATURE_INDEX row affected, the operation (NEW/MODIFIED/n/a-justified), the test file path, and the test descriptor naming the assertion that proves the feature works.",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["entry_id", "operation", "test_path", "test_descriptor"],
    "properties": {
      "entry_id": { "type": "string", "minLength": 1 },
      "operation": { "type": "string", "enum": ["NEW", "MODIFIED", "n/a-justified"] },
      "test_path": { "type": "string", "minLength": 1 },
      "test_descriptor": { "type": "string", "minLength": 1 }
    }
  }
}
```

**`qor/gates/schema/audit.schema.json`** — extend `findings_categories.items.enum`:

```diff
       "specification-drift",
       "test-failure",
       "coverage-gap",
-      "infrastructure-mismatch"
+      "infrastructure-mismatch",
+      "feature-test-undeclared"
```

**`qor/gates/schema/feature_index.schema.json`** — NEW (JSON-schema mirror):

Defines the row shape (`id`, `name`, `source_of_truth`, `doc_citation`, `test_path`, `status`) and the status enum (`verified` / `unverified` / `n/a` + `n/a_rationale` when n/a). Useful for tooling that parses the markdown into structured form.

**`qor/templates/FEATURE_INDEX.example.md`** — worked example with 5 entries:
- FX001 verified (test exists, exercises feature, passes)
- FX002 unverified (no test)
- FX003 unverified (presence-only test that fails SG-035 acceptance question)
- FX004 n/a (human-judgment surface — explicit rationale)
- FX005 modified (test updated in lockstep with feature change)

### Unit Tests

- `tests/test_doctrine_feature_inventory_present.py`:
  - `test_doctrine_feature_inventory_md_exists`
  - `test_doctrine_states_status_enum_with_three_values` — `verified / unverified / n/a` present.
  - `test_doctrine_states_lifecycle_hooks_in_order` — plan → audit → implement → substantiate.

- `tests/test_doctrine_feature_tdd_present.py`:
  - `test_doctrine_feature_tdd_md_exists`
  - `test_doctrine_distinguishes_per_unit_from_per_feature`
  - `test_doctrine_states_acceptance_question_with_sg_035_anchor`

- `tests/test_plan_schema_feature_inventory_touches.py`:
  - `test_schema_accepts_omitted_field` (backward compat).
  - `test_schema_accepts_well_formed_array` (NEW / MODIFIED / n/a-justified each).
  - `test_schema_rejects_bad_operation_enum_value`.
  - `test_schema_rejects_missing_required_subfields` (entry_id, operation, test_path, test_descriptor each).

- `tests/test_audit_schema_feature_test_undeclared_enum.py`:
  - `test_audit_schema_accepts_feature_test_undeclared_category_on_veto`.
  - `test_audit_schema_existing_categories_still_valid`.

- `tests/test_feature_index_schema.py`:
  - `test_feature_index_schema_file_exists`
  - `test_schema_accepts_minimal_row` (verified + populated test_path).
  - `test_schema_accepts_n_a_row_with_rationale`.
  - `test_schema_rejects_unknown_status_value`.
  - `test_schema_rejects_n_a_row_without_rationale`.

- `tests/test_feature_index_example_template.py`:
  - `test_example_file_present_at_template_path`
  - `test_example_contains_at_least_one_verified_entry`
  - `test_example_contains_at_least_one_n_a_entry_with_rationale`

---

## Phase 2: SKILL amendments (plan, audit, implement, substantiate)

### Affected Files

- `qor/skills/sdlc/qor-plan/SKILL.md` — add Step 7 sub-bullet requiring `feature_inventory_touches` declaration when plan touches `src/`-equivalent code; reference doctrine.
- `qor/skills/governance/qor-audit/SKILL.md` — add Feature Test Coverage Pass under Step 3 (between Self-Targeting Remediation Pass and Section 4 Razor); references new finding category.
- `qor/skills/sdlc/qor-implement/SKILL.md` — Step 5 amendment: per-feature TDD-Light alongside per-unit TDD-Light; Step 12.5 amendment: append/update FEATURE_INDEX rows for declared touches before staging.
- `qor/skills/governance/qor-substantiate/SKILL.md` — Step 6 amendment: invoke FEATURE_INDEX verification helper; surface counts; fail seal on outside-scope regression.
- `qor/scripts/feature_index_verify.py` — NEW. Parses FEATURE_INDEX.md (markdown table or whatever path the host repo declares), tallies counts by status, returns regression list (vs prior seal's count snapshot).
- `tests/test_plan_skill_step_7_feature_touches.py` — wiring test.
- `tests/test_audit_skill_feature_test_coverage_pass.py` — wiring test.
- `tests/test_implement_skill_per_feature_tdd.py` — wiring test.
- `tests/test_substantiate_skill_feature_verification.py` — wiring test.
- `tests/test_feature_index_verify_helper.py` — helper behavior tests.

### Changes

**`qor-plan` Step 7** insertion (after current Step 5 review checklist, before "Step Z Write Gate Artifact"):

```markdown
### Step 7: Feature Inventory Touches (Phase 46 wiring — #40 / #41)

When the plan touches user-facing code (routes, commands, UI events, services), declare every affected feature in the plan top-matter as:

\`\`\`yaml
feature_inventory_touches:
  - entry_id: FX091
    operation: NEW
    test_path: tests/test_marketplace_install.py
    test_descriptor: POST /api/marketplace/install/<id> returns 200 with nonce structure
\`\`\`

Operations: `NEW` (entry not yet in FEATURE_INDEX), `MODIFIED` (entry exists, plan changes surface), `n/a-justified` (entry exists, plan affects neighborhood, declared for traceability).

Plans that only change docs / governance may declare empty.

Per `qor/references/doctrine-feature-inventory.md` and `qor/references/doctrine-feature-tdd.md`. Step Z carries the array to `plan.json` per the new `feature_inventory_touches` schema field.
```

**`qor-audit` Feature Test Coverage Pass** (under Step 3, between Self-Targeting Remediation Pass and Section 4 Razor Pass):

```markdown
#### Feature Test Coverage Pass (Phase 46 wiring — #41)

For every entry in the plan's `feature_inventory_touches`, verify:

1. Test path cites a specific file (existing or NEW in Affected Files).
2. Test descriptor names the assertion that proves the feature works (e.g., "POST returns 200 + nonce structure", not "route exists").
3. Descriptor survives the SG-035 acceptance question: "If the feature were silently broken but the test artifact still existed, would this assertion fail?"

Any entry without a passing descriptor → VETO with category `feature-test-undeclared`.

Empty `feature_inventory_touches` is acceptable for plans that only change docs / governance; the Judge confirms the plan is not touching `src/`-equivalent code before clearing.
```

**`qor-implement` Step 5 amendment** (extend the existing TDD-Light text):

```markdown
**Per-feature layer** (Phase 46 wiring — #41): for each entry in the plan's `feature_inventory_touches`:

1. Author the failing feature-level test FIRST at the path declared in the plan, with the assertion declared in the plan.
2. Run it. It MUST fail. (Anti-vacuous-green guard.)
3. Implement the feature.
4. Run it again. It MUST pass before the feature is considered shipped.

The existing per-unit TDD-Light continues to apply for helpers introduced inside the feature implementation. This adds a per-feature TDD layer on top, per `qor/references/doctrine-feature-tdd.md`.
```

**`qor-implement` Step 12.5 amendment** (append FEATURE_INDEX update as hard step):

```markdown
**FEATURE_INDEX update** (Phase 46 wiring — #40): for each entry in the plan's `feature_inventory_touches`:

- `NEW` operation: append a row to FEATURE_INDEX with status `verified` (feature shipped with green test in same commit).
- `MODIFIED` operation: update existing row's `Source-of-truth file:line` and/or `Test path` to reflect the change.
- `n/a-justified`: no row change; the declaration in plan.json is the only artifact.

Block staging on any `feature_inventory_touches` entry that does not resolve to a green test in this commit. Per `qor/references/doctrine-feature-inventory.md`.
```

**`qor-substantiate` Step 6 amendment** (insert verification pass before existing Step 6 sync state):

```markdown
**FEATURE_INDEX verification** (Phase 46 wiring — #40):

\`\`\`python
from qor.scripts import feature_index_verify as fiv

summary = fiv.tally(repo_root=".", index_path="docs/FEATURE_INDEX.md")
# summary = {"total": N, "verified": V, "unverified": U, "n_a": A, "newly_unverified": [...]}
\`\`\`

Surface counts in the SESSION SEAL ledger body: `Total: N / verified: V / unverified: U / n/a: A`.

Outside-scope regression rule: if any feature outside the current plan's `feature_inventory_touches` regressed from `verified` to `unverified` since the last seal, **fail the seal** (per `qor/references/doctrine-feature-inventory.md`). Plans must explicitly own regression in their own scope or escalate to a hotfix cycle.

Repos without a FEATURE_INDEX.md: the helper returns `summary = {"total": 0, "missing_index": True}`; the seal proceeds with a single-line note "FEATURE_INDEX not configured for this host repo (per doctrine, optional artifact)."
```

**`qor/scripts/feature_index_verify.py`** — V1 helper, stdlib-only:

Public surface:

```python
@dataclass(frozen=True)
class IndexSummary:
    total: int
    verified: int
    unverified: int
    n_a: int
    newly_unverified: tuple[str, ...]      # entry_ids that regressed since prior_snapshot
    missing_index: bool = False

def tally(repo_root: str, index_path: str, prior_snapshot: dict[str, str] | None = None) -> IndexSummary: ...

def parse_index_rows(text: str) -> list[dict[str, str]]: ...   # markdown table -> row dicts

def write_seal_snapshot(repo_root: str, sid: str, rows: list[dict[str, str]]) -> Path: ...
```

The verifier reads the markdown table, tallies statuses, and (when prior snapshot is provided) returns the list of entry IDs that moved from `verified` to `unverified`. It does NOT verify that test files actually exist or that tests pass — those are upstream concerns of `/qor-implement` Step 12.5 + `/qor-substantiate`'s existing test-green precondition.

### Unit Tests

- `tests/test_plan_skill_step_7_feature_touches.py`:
  - `test_plan_skill_has_step_7_anchor`
  - `test_step_7_cites_feature_inventory_touches_field`
  - `test_step_7_enumerates_three_operation_values` — NEW / MODIFIED / n/a-justified.
  - `test_step_7_cites_both_doctrines`

- `tests/test_audit_skill_feature_test_coverage_pass.py`:
  - `test_audit_skill_has_feature_test_coverage_pass_anchor`
  - `test_pass_appears_between_self_targeting_and_razor`
  - `test_pass_cites_sg_035_acceptance_question`
  - `test_pass_routes_to_feature_test_undeclared_category`

- `tests/test_implement_skill_per_feature_tdd.py`:
  - `test_step_5_carries_per_feature_layer_section`
  - `test_step_5_demands_red_before_green_cycle`
  - `test_step_12_5_appends_feature_index_rows`
  - `test_step_12_5_blocks_staging_on_unresolved_touch`

- `tests/test_substantiate_skill_feature_verification.py`:
  - `test_step_6_invokes_feature_index_verify`
  - `test_step_6_surfaces_counts_in_seal_entry`
  - `test_step_6_declares_outside_scope_regression_rule`
  - `test_step_6_handles_missing_index_gracefully`

- `tests/test_feature_index_verify_helper.py`:
  - `test_parse_index_rows_extracts_columns_from_markdown_table`
  - `test_parse_index_rows_skips_separator_row`
  - `test_tally_counts_each_status`
  - `test_tally_missing_index_returns_missing_flag`
  - `test_tally_detects_newly_unverified_against_prior_snapshot`
  - `test_tally_ignores_n_a_in_newly_unverified_set` — `n/a` is not a regression target.

---

## Phase 3: Doctrine tests + integration

### Affected Files

- `tests/test_feature_inventory_integration.py` — NEW. End-to-end: write a fake plan declaring `feature_inventory_touches`, fake FEATURE_INDEX.md with prior snapshot, invoke `feature_index_verify.tally`, assert behavior across the regression scenarios.

### Changes

Integration scenarios (parameterized):

1. Fresh repo, no FEATURE_INDEX → `missing_index=True`, seal proceeds.
2. FEATURE_INDEX with 3 verified entries, no prior snapshot → all counts 3/0/0, `newly_unverified=[]`.
3. Same FEATURE_INDEX, prior snapshot = same → `newly_unverified=[]`.
4. FEATURE_INDEX with FX001 flipped verified → unverified, prior snapshot shows FX001 verified → `newly_unverified=["FX001"]`.
5. FEATURE_INDEX with FX002 n/a (was verified), prior snapshot shows FX002 verified → `newly_unverified=[]` (n/a is intentional removal, not regression).

### Unit Tests

Already enumerated under each phase's test list. No additional standalone tests in Phase 3 beyond the integration suite above.

---

## CI Commands

- `python -m pytest tests/test_doctrine_feature_inventory_present.py tests/test_doctrine_feature_tdd_present.py -v`
- `python -m pytest tests/test_plan_schema_feature_inventory_touches.py tests/test_audit_schema_feature_test_undeclared_enum.py tests/test_feature_index_schema.py tests/test_feature_index_example_template.py -v`
- `python -m pytest tests/test_plan_skill_step_7_feature_touches.py tests/test_audit_skill_feature_test_coverage_pass.py tests/test_implement_skill_per_feature_tdd.py tests/test_substantiate_skill_feature_verification.py -v`
- `python -m pytest tests/test_feature_index_verify_helper.py tests/test_feature_inventory_integration.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase46-feature-tdd-and-inventory.md`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
