# Plan: Phase 78 - qor-audit Filter-Stage Ordering Coherence sub-pass (GH #47)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #47 -- Wave 2 multi-agent review (qa-expert + qor-judge) consistently catches stage-by-stage correctness defects but misses composition-by-composition defects: when stage N depends on an invariant established by stage M (M < N conceptually) but the code runs N before M, candidates violating I survive into N. Concrete reproduction: the sibling consumer workspace's Skill-Forge V1 dispatcher (META_LEDGER #209) ran tier -> classification -> vendor -> cost filters without invoking validator() first; invalid manifests with low cost dominated selection until operator-caught at PR merge (commit 0999e47).

**terms_introduced**:
- term: pipeline stage dependency graph
  home: qor/skills/governance/qor-audit/SKILL.md
- term: filter-stage ordering coherence
  home: qor/skills/governance/qor-audit/SKILL.md
- term: SG-FilterOrderInversion-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - V1 prose-only audit-pass extension under `/qor-audit` Step 3. No mechanical lint helper this phase (would require AST parsing across Rust + Python + TypeScript pipeline shapes; deferred to V2 if operator demand surfaces).
  - V1 heuristic is operator-judgment-based: the audit names the dependency-graph + topological-sort check; the audit operator (Judge persona) constructs the graph for the plan-cited pipeline and verifies the implementation matches.
- non_goals:
  - No new `qor/scripts/plan_filter_stage_lint.py`.
  - No `findings_categories` enum change (the existing `composition` or `infrastructure-mismatch` categories absorb the new sub-rule via prose sub-tagging).
  - No changes to `/qor-plan`, `/qor-implement`, `/qor-substantiate`.
- exclusions:
  - No CI workflow changes.
  - No retroactive review of prior phase audits.

## Open Questions

None. GH #47 specifies the rule shape (4 steps: identify preconditions; identify invariants; construct dependency graph; verify code order is a topological sort). V1 codifies the prose; mechanical helper deferred.

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| qor-audit Step 3 Filter-Stage Ordering Coherence sub-pass | NEW | tests/test_qor_audit_filter_stage_ordering.py reads qor-audit SKILL.md and asserts Step 3 contains "Filter-Stage Ordering Coherence" heading + 4-step procedure + sub-tag name |
| SG-FilterOrderInversion-A doctrine entry | NEW | tests/test_doctrine_sg_filter_order_inversion_a.py reads doctrine file, asserts SG entry exists with pattern description + countermeasure cross-reference |

## Phase 1: Filter-Stage Ordering Coherence sub-pass (qor-audit Step 3)

### Affected Files

- `qor/skills/governance/qor-audit/SKILL.md` -- append a Filter-Stage Ordering Coherence sub-pass under Step 3, after the existing Infrastructure Alignment and Ghost UI Pass extensions.
- `tests/test_qor_audit_filter_stage_ordering.py` -- NEW. 3 tests asserting the SKILL.md region names the sub-pass + heuristic + sub-tag.

### Changes

Append a Filter-Stage Ordering Coherence sub-pass to Step 3 with this 4-step procedure:

1. Identify each filter stage's preconditions (what invariants must hold on inputs).
2. Identify each filter stage's invariants (what it enforces on outputs).
3. Construct the dependency graph: stage N depends on stage M iff M enforces an invariant that N's correctness assumes.
4. Verify the actual code order is a topological sort of the dependency graph.

Detection heuristic (V1 operator-judgment): for any function/method with the shape "candidate set -> multiple filter stages -> selection" (heuristically detected via `.filter().filter().filter().map()` functional style, or sequential `let after_X = filter_X(...)` blocks, or chained Python `dict.values()` / `filter(predicate, ...)` blocks), the audit raises the question: "did the validation referenced here run before the filter that depends on it?"

VETO category remains `composition` (or `infrastructure-mismatch` when the missing precondition is an external-state assumption); sub-tag `filter-order-inversion` (prose sub-tag; no schema enum change).

### Unit Tests

- `tests/test_qor_audit_filter_stage_ordering.py::test_step3_names_filter_stage_ordering_coherence` -- reads audit SKILL.md, asserts Step 3 region names the Filter-Stage Ordering Coherence sub-pass.
- `tests/test_qor_audit_filter_stage_ordering.py::test_step3_lists_four_step_procedure` -- asserts the region names the 4-step procedure (preconditions / invariants / dependency graph / topological sort).
- `tests/test_qor_audit_filter_stage_ordering.py::test_step3_names_filter_order_inversion_subtag` -- asserts the region names the `filter-order-inversion` sub-tag and cross-references SG-FilterOrderInversion-A.

## Phase 2: SG-FilterOrderInversion-A doctrine entry

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` -- new SG-FilterOrderInversion-A entry catalogueing the pattern, originating recurrence (the sibling consumer workspace's Skill-Forge V1 dispatcher: tier -> classification -> vendor -> cost without validator-first; META_LEDGER #209; operator-caught at PR merge commit 0999e47), and countermeasure (qor-audit Step 3 Filter-Stage Ordering Coherence sub-pass).
- `tests/test_doctrine_sg_filter_order_inversion_a.py` -- NEW. 2 tests asserting the doctrine carries the SG entry.

### Changes

SG entry follows the standard format (Pattern / Originating recurrence / Countermeasure / Cross-reference). Pattern description: stage-by-stage correctness review (Wave 2 multi-agent or single-reviewer audit) passes each stage individually but fails to verify that filter-stage composition respects an invariant-dependency graph; invariant-violating candidates survive into downstream stages. Originating recurrence: a sibling consumer workspace 2026-05-08 session, validator-not-first in skill_forge dispatcher; operator caught at merge review, regression test `test_dispatch_skips_invalid_skill_and_selects_valid_candidate` locked the invariant.

### Unit Tests

- `tests/test_doctrine_sg_filter_order_inversion_a.py::test_doctrine_carries_sg_filter_order_inversion_a` -- reads doctrine file, asserts the SG entry exists with the canonical pattern description.
- `tests/test_doctrine_sg_filter_order_inversion_a.py::test_doctrine_cites_countermeasure` -- asserts the SG entry body cross-references the Step 3 Filter-Stage Ordering Coherence sub-pass.

## Phase 3: Glossary terms

### Affected Files

- `qor/references/glossary.md` -- add 3 new terms: `pipeline stage dependency graph`, `filter-stage ordering coherence`, `SG-FilterOrderInversion-A`.
- `tests/test_glossary_filter_stage_terms.py` -- NEW. 1 test asserting the 3 terms are defined.

### Changes

Add the 3 glossary entries pointing at their homes per the `terms_introduced` block above. Each gets a 1-2 sentence definition matching the SKILL.md / doctrine prose.

### Unit Tests

- `tests/test_glossary_filter_stage_terms.py::test_glossary_defines_filter_stage_terms` -- asserts the 3 terms are present in `qor/references/glossary.md`.

## CI Commands

- `python -m pytest tests/test_qor_audit_filter_stage_ordering.py tests/test_doctrine_sg_filter_order_inversion_a.py tests/test_glossary_filter_stage_terms.py -v` -- validates Phase 78 tests.
- `python -m qor.scripts.dist_compile` -- regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase78-filter-stage-ordering.md` -- self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` -- full suite.
