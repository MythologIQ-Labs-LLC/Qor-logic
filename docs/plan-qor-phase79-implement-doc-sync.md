# Plan: Phase 79 - /qor-implement Step 8.5 Documentation Sync (GH #52)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #52 -- documentation lifecycle was structurally backloaded to substantiation (Steps 4.7 / 6 / 6.5), where the agent has lost the implementation-time context needed to write accurate docs. Across the originating-incident's 18+ ledger entries, ARCHITECTURE_PLAN.md file tree went stale; new tables / functions / migrations were not reflected in any architecture or operations docs; substantiate's Documentation Currency check fired post-hoc as WARN-only severity-2 shadow events but did not prevent the drift from happening. The substantiation phase is a verification gate, not an authoring phase; the missing protocol step is a doc-authoring sub-step inside /qor-implement.

**terms_introduced**:
- term: implement documentation sync
  home: qor/skills/sdlc/qor-implement/SKILL.md
- term: SG-DocsBackloadedToSubstantiate-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 prose-only addition to `/qor-implement` SKILL.md. No mechanical lint helper this phase. The Step 8.5 checklist is operator-judgment-based; mechanical verification of "ARCHITECTURE_PLAN.md file tree reflects new files" is deferred to a follow-on phase.
  - doc_tier-aware behavior: `minimal` -> WARN-skip; `standard` -> require ARCHITECTURE_PLAN.md file tree + relevant architecture-doc section update; `system` -> additionally require operations.md + schema docs when applicable.
- non_goals:
  - No new `qor/scripts/plan_doc_sync_lint.py`.
  - No changes to `/qor-substantiate` Steps 4.7 / 6 / 6.5 (they remain verification gates; this phase adds the upstream authoring step that those gates verify).
  - No schema change to `qor/gates/schema/implement.schema.json` (Step 8.5 is procedural, not artifact-shaped).
- exclusions:
  - No CI workflow changes.
  - No retroactive amendment of past implement gate artifacts.

## Open Questions

None. GH #52 specifies the exact insertion point (between Step 8 and Step 9), the checklist contents (4 bullets covering ARCHITECTURE_PLAN.md file tree / architecture docs / operations docs / schema docs), and the doc_tier-aware skip semantics. V1 codifies the prose; mechanical helper deferred.

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| /qor-implement Step 8.5 Documentation Sync | NEW | tests/test_qor_implement_doc_sync.py reads qor-implement SKILL.md and asserts Step 8.5 exists between Step 8 and Step 9 with the 4-item checklist + doc_tier-aware skip |
| SG-DocsBackloadedToSubstantiate-A doctrine entry | NEW | tests/test_doctrine_sg_docs_backloaded_to_substantiate_a.py reads doctrine file, asserts SG entry exists with pattern description + countermeasure cross-reference |

## Phase 1: Step 8.5 Documentation Sync (qor-implement)

### Affected Files

- `qor/skills/sdlc/qor-implement/SKILL.md` -- insert new Step 8.5 between existing Step 8 (Post-Build Cleanup) and Step 9 (Complexity Self-Check).
- `tests/test_qor_implement_doc_sync.py` -- NEW. 3 tests asserting Step 8.5 prose contents + insertion-point ordering + doc_tier-aware skip semantics.

### Changes

Insert a new `### Step 8.5: Documentation Sync (Phase 79 wiring; GH #52)` between Step 8 and Step 9. Step body declares a 4-item operator checklist scoped to files created or modified in this implementation pass:

1. ARCHITECTURE_PLAN.md file tree: add new files, remove deleted files. (Required when `doc_tier in {standard, system}` and `src/` files were touched.)
2. Architecture docs: update interface contracts, data flows, dependency tables for new tables, functions, env vars, or cron jobs introduced. (Required at `system`; encouraged at `standard`.)
3. Operations docs: document new scripts, env vars, deployment steps. (Required at `system` when operational surfaces were touched.)
4. Schema docs: document new migrations, RLS policies, function signatures. (Required at `system` when schema-affecting files were touched.)

doc_tier behavior:
- `minimal`: skip Step 8.5 with WARN ("doc_tier=minimal; doc sync skipped; substantiate Step 6.5 will WARN if it detects drift").
- `standard`: require items 1 + at least the relevant architecture-doc section from item 2.
- `system`: require items 1-4 as applicable to touched files.
- `legacy`: skip (matches doctrine-documentation-integrity legacy-tier bypass).

Step body cross-references `/qor-substantiate` Steps 4.7 / 6 / 6.5 / 4.6.6 as the downstream verification gates that confirm Step 8.5 ran; the substantiation gates remain WARN-or-ABORT depending on tier, unchanged by this phase.

### Unit Tests

- `tests/test_qor_implement_doc_sync.py::test_step_8_5_exists_between_step_8_and_step_9` -- reads qor-implement SKILL.md, asserts `### Step 8.5: Documentation Sync` heading appears AFTER `### Step 8: Post-Build Cleanup` and BEFORE `### Step 9: Complexity Self-Check`.
- `tests/test_qor_implement_doc_sync.py::test_step_8_5_lists_four_item_checklist` -- asserts Step 8.5 body names ARCHITECTURE_PLAN.md file tree + architecture docs + operations docs + schema docs.
- `tests/test_qor_implement_doc_sync.py::test_step_8_5_names_doc_tier_aware_skip` -- asserts Step 8.5 body names `doc_tier` semantics (minimal/standard/system) and cross-references substantiate verification gates.

## Phase 2: SG-DocsBackloadedToSubstantiate-A doctrine entry

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` -- new SG-DocsBackloadedToSubstantiate-A entry catalogueing the pattern (doc lifecycle backloaded to substantiation when implementing agent has lost authoring context), originating recurrence (18+ ledger entries in a multi-session analytics program where ARCHITECTURE_PLAN.md file tree went stale and new tables/functions/migrations had no architecture-doc updates; substantiate Step 6.5 fired WARN-only), and countermeasure (/qor-implement Step 8.5 Documentation Sync).
- `tests/test_doctrine_sg_docs_backloaded_to_substantiate_a.py` -- NEW. 2 tests asserting doctrine carries the SG entry.

### Changes

SG entry follows the standard format (Pattern / Originating recurrence / Countermeasure / Cross-reference). Pattern description: documentation authoring deferred to `/qor-substantiate` (Steps 4.7 / 6 / 6.5) when the implementing agent has discarded the context needed for accurate docs; substantiation's WARN-only currency check catches drift post-hoc but does not prevent it.

### Unit Tests

- `tests/test_doctrine_sg_docs_backloaded_to_substantiate_a.py::test_doctrine_carries_sg_docs_backloaded_to_substantiate_a` -- reads doctrine file, asserts SG entry with pattern description (backloaded + lost context + WARN-only).
- `tests/test_doctrine_sg_docs_backloaded_to_substantiate_a.py::test_doctrine_cites_countermeasure` -- asserts SG entry body cross-references qor-implement Step 8.5.

## Phase 3: Glossary terms

### Affected Files

- `qor/references/glossary.md` -- add 2 new terms: `implement documentation sync`, `SG-DocsBackloadedToSubstantiate-A`.
- `tests/test_glossary_implement_doc_sync_terms.py` -- NEW. 1 test asserting the 2 terms are defined.

### Changes

Add glossary entries pointing at their homes per `terms_introduced` above.

### Unit Tests

- `tests/test_glossary_implement_doc_sync_terms.py::test_glossary_defines_implement_doc_sync_terms` -- asserts the 2 terms are present with the Phase 79 plan slug.

## CI Commands

- `python -m pytest tests/test_qor_implement_doc_sync.py tests/test_doctrine_sg_docs_backloaded_to_substantiate_a.py tests/test_glossary_implement_doc_sync_terms.py -v` -- validates Phase 79 tests.
- `python -m qor.scripts.dist_compile` -- regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase79-implement-doc-sync.md` -- self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` -- full suite.
