# Plan: Phase 75 - Skill capability declaration for /qor-substantiate (GH #38 V1)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #38 -- /qor-substantiate hard-couples to Python toolkit and release shape; fails on non-Python repos. Phase 76 ideation (session `2026-05-14T2216-a5f692`) selected Option 1 (skill capability declaration).

**terms_introduced**:
- term: substantiate step prerequisite
  home: qor/scripts/substantiate_capability.py
- term: gate_skipped_prerequisite_absent
  home: qor/gates/schema/shadow_event.schema.json
- term: SG-HalfSealedClaim-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 ships capability declarations as a structured table in qor-substantiate SKILL.md + a pure-function parser/checker + CLI. Operators run the CLI before substantiate to see which steps will run vs skip; the seal entry references the capability report.
  - V1 does NOT auto-skip steps mechanically -- operator-driven: skill prose explicitly references each step's prerequisite, and operators on non-Python hosts manually skip steps when prereq is absent. The capability report gives them a structured basis for the decision.
  - V1 covers Step 4.6 (intent_lock + skill_admission + gate_skill_matrix), Step 4.6.5 (secret_scanner), Step 4.6.6 (procedural_fidelity), Step 4.7 (doc_integrity), Step 6.5 (doc currency), Step 6.8 (seal hash gate), Step 7.4 (SSDF tagger), Step 7.5 (pyproject bump), Step 7.6 (CHANGELOG stamp), Step 7.7 (seal_entry_check), Step 7.8 (gate_chain_completeness), Step 8.5 (dist_compile). 12 capability declarations.
- non_goals:
  - NOT writing pluggable backends for version_bump / changelog_stamp / release_artifact_compile (Option 2; deferred to V2).
  - NOT splitting qor-substantiate into core + release tracks (Option 3; deferred to V3).
  - NOT changing chain_hash / content_hash / Merkle-seal algorithms.
- exclusions:
  - No changes to /qor-plan, /qor-audit, /qor-implement, /qor-research, /qor-organize.
  - No new gate steps; only capability declarations on existing steps.
- forbidden_interpretations:
  - This is NOT permission to silently skip security gates without surfacing the gap in the seal entry. The seal entry MUST cite the capability report.

## Open Questions

None. Ideation packet (2026-05-14T2216-a5f692) decided Option 1 explicitly.

## Phase 1: Capability helper + CLI

### Affected Files

- `qor/scripts/substantiate_capability.py` - NEW (~120 LOC). Pure-function module: parses `## Step Prerequisites` table in qor-substantiate SKILL.md; runs per-step predicate (file-exists, module-importable, command-on-path); returns `CapabilityReport` namedtuple with `step_id`, `requires`, `present` (bool), `evidence` (path or import-check result).
- `qor/cli_handlers/substantiate.py` - NEW (~40 LOC). `do_substantiate_capability(args)` handler that prints a per-step capability table (markdown table form, paste-able into seal entry).
- `qor/cli.py` - extend `argparse` subparser tree with `substantiate-capability` subcommand routing to the new handler.
- `tests/test_substantiate_capability_helper.py` - NEW. 4 tests asserting parser correctness on a real SKILL.md fixture, present/absent predicate behavior, namedtuple shape, error handling for malformed prereq declarations.
- `tests/test_substantiate_capability_cli.py` - NEW. 2 tests asserting CLI invocation produces a markdown table with expected columns + subprocess exit semantics.

### Changes

`substantiate_capability.check_step(step_id, repo_root)` returns `CapabilityReport(step_id, requires, present, evidence)`. Predicate kinds the V1 parser recognizes (per SKILL.md table):

- `file:<path>` (e.g., `file:pyproject.toml`) -- predicate `(repo_root / path).is_file()`.
- `module:<dotted>` (e.g., `module:qor.scripts.secret_scanner`) -- predicate `importlib.util.find_spec(dotted) is not None`.
- `command:<bin>` (e.g., `command:git`) -- predicate `shutil.which(bin) is not None`.

Capability report rendering (CLI output, markdown table):

```markdown
| Step | Requires | Present | Evidence |
|---|---|---|---|
| 4.6 intent_lock verify | module:qor.reliability.intent_lock | ✅ | qor/reliability/intent_lock.py |
| 4.6.5 secret_scanner | module:qor.scripts.secret_scanner | ✅ | qor/scripts/secret_scanner.py |
| 7.5 version bump | file:pyproject.toml | ❌ | (not found) |
| 7.6 changelog stamp | file:CHANGELOG.md | ❌ | (not found) |
```

### Unit Tests

- `tests/test_substantiate_capability_helper.py::test_parser_extracts_step_prerequisites_table_from_skill_md` - reads qor-substantiate SKILL.md, asserts the parser returns a non-empty list of (step_id, requires) pairs with the expected 12 V1 declarations.
- `tests/test_substantiate_capability_helper.py::test_check_step_file_predicate_returns_present_when_path_exists` - calls `check_step` with synthetic SKILL.md fixture declaring `requires: file:CHANGELOG.md`, asserts `report.present is True` and `report.evidence` is the resolved path.
- `tests/test_substantiate_capability_helper.py::test_check_step_module_predicate_returns_absent_when_module_missing` - calls `check_step` with `requires: module:nonexistent.module.X`, asserts `report.present is False` and `report.evidence` describes the spec-not-found state.
- `tests/test_substantiate_capability_helper.py::test_check_step_command_predicate_returns_absent_when_binary_not_on_path` - calls `check_step` with `requires: command:definitely-not-a-real-cli-12345`, asserts `report.present is False`.
- `tests/test_substantiate_capability_cli.py::test_cli_prints_markdown_table_with_expected_columns` - subprocess invokes `python -m qor.cli substantiate-capability`, asserts stdout contains `| Step | Requires | Present | Evidence |` header AND at least 12 rows.
- `tests/test_substantiate_capability_cli.py::test_cli_exit_code_zero_when_all_prereqs_present_on_python_host` - subprocess invocation on the canonical Python host returns exit 0 (V1: report is informational; exit always 0).

## Phase 2: SKILL.md prose declarations

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - add a new `## Step Prerequisites` section (after `## Purpose`, before `## Execution Protocol`) declaring the 12 V1 entries in a markdown table. Each existing step (4.6, 4.6.5, 4.6.6, 4.7, 6.5, 6.8, 7.4, 7.5, 7.6, 7.7, 7.8, 8.5) gains a Phase 75 wiring sentence pointing at its row.
- `tests/test_qor_substantiate_capability_declarations.py` - NEW. 2 tests asserting SKILL.md contains the `## Step Prerequisites` section with the 12 expected rows AND each affected step body cross-references the capability table.

### Changes

Add a single declarative table immediately after `## Purpose`:

```markdown
## Step Prerequisites (Phase 75 wiring; GH #38)

This skill is multi-step; each step declares its prerequisite so non-Python hosts can use `qor-logic substantiate-capability` to identify which steps will run vs skip on their archetype.

| Step | Requires | Notes |
|---|---|---|
| 4.6 intent_lock verify | module:qor.reliability.intent_lock | Python toolkit reliability gate |
| ... (12 rows total) | ... | ... |
```

Each step body (4.6, 4.6.5, etc.) gains: `**Prerequisite (Phase 75)**: see Step Prerequisites table; this step requires <X>. Operators on hosts where the prerequisite is absent should record SKIP in the seal entry and emit a `gate_skipped_prerequisite_absent` shadow event.`

### Unit Tests

- `tests/test_qor_substantiate_capability_declarations.py::test_skill_md_contains_step_prerequisites_table` - reads qor-substantiate SKILL.md, asserts the `## Step Prerequisites` heading exists AND the table body contains all 12 V1 step rows (4.6, 4.6.5, 4.6.6, 4.7, 6.5, 6.8, 7.4, 7.5, 7.6, 7.7, 7.8, 8.5).
- `tests/test_qor_substantiate_capability_declarations.py::test_each_step_body_cross_references_capability_table` - parses each Step heading region, asserts the body contains the `Prerequisite (Phase 75)` cross-reference phrase.

## Phase 3: Shadow-event schema extension + SG doctrine entry

### Affected Files

- `qor/gates/schema/shadow_event.schema.json` - extend `event_type` enum with `gate_skipped_prerequisite_absent`.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG-HalfSealedClaim-A entry.
- `tests/test_shadow_event_gate_skipped_prerequisite_absent.py` - NEW. 2 tests: synthetic shadow event with the new event_type validates against the schema; event without the new type still validates (no enum-rename breakage).
- `tests/test_doctrine_sg_half_sealed_claim_a.py` - NEW. 2 tests: doctrine carries the SG entry with the canonical pattern description; SG entry cross-references the substantiate-capability CLI as the countermeasure surface.

### Changes

Schema enum gains `gate_skipped_prerequisite_absent` (severity-1 default per ideation governance profile). SG entry catalogues the pattern: "operator runs /qor-substantiate against a non-Python host; gates whose prerequisites are absent silently fail or no-op; seal entry claims completeness it doesn't have." Originating recurrence: 2026-05-06 incident (Customer-App-3.0 React+bun+Supabase, 8 of 15 gates failed/skipped, session ended SUBSTANTIATE DEFERRED rather than seal). Countermeasure: `qor-logic substantiate-capability` CLI surfaces per-step prereq status; operators paste the capability report into the seal entry; missing prereqs emit `gate_skipped_prerequisite_absent` shadow events.

### Unit Tests

- `tests/test_shadow_event_gate_skipped_prerequisite_absent.py::test_schema_accepts_new_event_type` - jsonschema Draft 2020-12 validator: a synthetic event with `event_type: "gate_skipped_prerequisite_absent"` validates against the updated schema.
- `tests/test_shadow_event_gate_skipped_prerequisite_absent.py::test_schema_still_rejects_unknown_event_type` - asserts an event with `event_type: "fabricated_event"` still raises ValidationError.
- `tests/test_doctrine_sg_half_sealed_claim_a.py::test_doctrine_carries_sg_half_sealed_claim_a` - reads doctrine file, asserts `## SG-HalfSealedClaim-A` heading exists with pattern description naming "half-checked seal" or "claims coverage" or equivalent canonical phrase + 2026-05-06 originating-recurrence reference.
- `tests/test_doctrine_sg_half_sealed_claim_a.py::test_doctrine_cites_substantiate_capability_cli` - asserts SG entry body references `qor-logic substantiate-capability` (the V1 countermeasure surface).

## CI Commands

- `python -m pytest tests/test_substantiate_capability_helper.py tests/test_substantiate_capability_cli.py tests/test_qor_substantiate_capability_declarations.py tests/test_shadow_event_gate_skipped_prerequisite_absent.py tests/test_doctrine_sg_half_sealed_claim_a.py -v` - validates Phase 75 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase75-skill-capability-declaration.md` - self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
