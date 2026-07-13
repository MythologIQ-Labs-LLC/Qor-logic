# Plan: Phase 190 - Spec corpus Phase A: grammar lint + deterministic merge (GH #239)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-spec-corpus-2026-07-13.md (ledger entry #478, session `2026-07-13T1405-331255`); GH #239 Phase A per the issue's own sequencing ("small, shippable first"). Phases B (gate-chain wiring) and C (requirement-level verify) defer with recorded grounds; the corpus rides UNDER the gate chain and Phase A tools carry no chain authority.

## Locked Decisions

- **LD-1: grammar contract lives in a non-doctrine reference.**
  `qor/references/spec-grammar.md` (NEW) defines the spec file shape (`### Requirement: <name>` headings; exactly one RFC-2119 SHALL/MUST statement per requirement body; >= 1 nested `#### Scenario: <name>` in GIVEN/WHEN/THEN bullets; observable behavior only) and the delta shape (`## ADDED Requirements` / `## MODIFIED Requirements` / `## REMOVED Requirements`; ADDED and MODIFIED carry complete requirement blocks; REMOVED lists headings). Non-doctrine naming keeps the README doctrine-inventory lock untouched; the fail-closed unregistered scan covers root+docs only (`grep -nE 'for rel_dir in' qor/scripts/governance_index.py -> 57`). Registered as a curated GOVERNANCE_INDEX Tier 2 row for discoverability.
- **LD-2: spec_lint is pure and CLI-fronted, house style.**
  `grep -nE 'def main' qor/scripts/check_variant_drift.py -> 53` (style precedent). `qor/scripts/spec_lint.py`: `check(text, strict=True) -> list[Finding]` (Finding: line, code, message); codes: missing-rfc2119 (zero or multiple SHALL/MUST in a requirement body), missing-scenario, malformed-scenario (a Scenario without GIVEN/WHEN/THEN bullets), orphan-scenario (Scenario outside any Requirement). CLI `--files PATH [PATH ...]` exits 0 clean / 1 findings.
- **LD-3: spec_merge is heading-keyed, loud, and deterministic.**
  `qor/scripts/spec_merge.py`: `apply(spec_text, delta_text) -> str`. ADDED appends complete blocks (duplicate heading -> `SpecMergeError`); MODIFIED replaces the whole block in place, preserving document order; REMOVED deletes the block; MODIFIED/REMOVED naming an absent heading -> `SpecMergeError` (never a silent skip -- the concurrency-conflict surface fails loudly). Same inputs always produce byte-identical output. CLI `--spec PATH --delta PATH [--write]` prints or writes the merged text; exit 0 ok / 1 merge error.
- **LD-4: the scaffold signposts, nothing more.**
  `qor/specs/README.md` (NEW): where capability specs live, the brownfield accretion rule (spec only what a plan touches), and a pointer to the grammar reference. No seed integration in Phase A (seeding a specs tree is Phase B's call when the fold gains chain authority).

## Phase 1: Grammar lint (TDD first)

### Affected Files

- tests/test_spec_lint.py - NEW (red first)
- qor/scripts/spec_lint.py - NEW per LD-2
- qor/references/spec-grammar.md - NEW per LD-1
- docs/GOVERNANCE_INDEX.md - Tier 2 row

### Changes

Line-oriented parser: split on `### Requirement:` headings; per body, count RFC-2119 keywords and collect `#### Scenario:` children; per scenario, require at least one bullet each starting GIVEN/WHEN/THEN (case-insensitive, list-marker tolerant).

### Unit Tests

- tests/test_spec_lint.py - test_valid_spec_passes: a two-requirement spec with scenarios -> no findings (red today)
- tests/test_spec_lint.py - test_missing_rfc2119_flagged / test_double_rfc2119_flagged: zero and two SHALL statements -> one finding each naming the requirement (red today)
- tests/test_spec_lint.py - test_missing_scenario_flagged: requirement without scenarios -> finding
- tests/test_spec_lint.py - test_malformed_scenario_flagged: scenario lacking a WHEN bullet -> finding
- tests/test_spec_lint.py - test_cli_exit_codes: clean file exit 0; findings exit 1 with the finding code on stderr

## Phase 2: Deterministic merge (TDD first)

### Affected Files

- tests/test_spec_merge.py - NEW (red first)
- qor/scripts/spec_merge.py - NEW per LD-3
- qor/specs/README.md - NEW per LD-4

### Changes

Block model: parse both documents into (heading -> complete block, ordered list). ADDED extends; MODIFIED replaces in place; REMOVED deletes; errors per LD-3. Rendering joins blocks with a single blank line; a trailing newline is guaranteed.

### Unit Tests

- tests/test_spec_merge.py - test_added_appends_block (red today)
- tests/test_spec_merge.py - test_modified_replaces_whole_block_in_place: unmodified neighbors keep exact order and bytes (red today)
- tests/test_spec_merge.py - test_removed_deletes_block
- tests/test_spec_merge.py - test_modified_absent_target_raises / test_removed_absent_target_raises / test_added_duplicate_raises: SpecMergeError with the heading named
- tests/test_spec_merge.py - test_merge_is_deterministic: applying the same delta to the same spec twice (fresh calls) yields byte-identical outputs
- tests/test_spec_merge.py - test_merged_output_passes_lint: apply a valid delta to a valid spec; spec_lint.check over the result -> no findings (the two modules compose)

## Feature Inventory Touches

(empty -- governance tooling; no src/ features)

## Definition of Done

### Deliverable: Phase A spec toolchain

- **D1**: Operators can author per-capability behavioral specs in a deterministic grammar and fold change deltas into them mechanically (GH #239 Phase A); the corpus rides under the gate chain with no chain authority until Phase B.
- **D2**: `spec_lint.check` + CLI and `spec_merge.apply` + CLI in qor/scripts/, stdlib-only, house CLI style; `qor/specs/README.md` scaffold; `qor/references/spec-grammar.md` contract.
- **D3**: GOVERNANCE_INDEX Tier 2 row; ledger entries for plan/audit/implement/seal; CHANGELOG feature entry recording the B/C deferral roadmap.
- **D4**: The twelve tests observe lint findings, merge semantics (including the three loud-error paths), determinism, and cross-module composition; red-then-green twice.

## CI Commands

- `python -m pytest tests/test_spec_lint.py tests/test_spec_merge.py -q` - focused suites (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
