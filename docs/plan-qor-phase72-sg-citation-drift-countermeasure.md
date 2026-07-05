# Plan: Phase 72 - SG-CitationDrift-A countermeasure (Infrastructure Citation Inventory + full re-walk)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #56 (SG-CitationDrift-A -- strengthen /qor-plan + /qor-audit to prevent cross-iteration unverified-citation drift).

**terms_introduced**:
- term: Infrastructure Citation Inventory
  home: qor/skills/sdlc/qor-plan/SKILL.md
- term: grep-evidence statement
  home: qor/skills/sdlc/qor-plan/SKILL.md

**boundaries**:
- limitations:
  - V1 enforces operator discipline via skill prose (P1 + P2) + doctrine documentation (P3); the heuristic lint extension (P4) is advisory-only.
  - The lint detects sealed-infrastructure citation patterns heuristically (file paths matching `qor/`, `docs/`, `tests/`, `.qor/` plus line-number suffixes); cannot semantically verify every citation.
- non_goals:
  - Replacing operator review with the lint heuristic.
  - Auto-fetching grep evidence on the operator's behalf.
- exclusions:
  - No changes to `/qor-implement` or `/qor-substantiate`.
  - No new CLI commands beyond the existing `plan_grep_lint` invocation.

## Open Questions

None. Issue #56 specifies P1-P3 prose contents in full; the lint extension scope (P4) is bounded to heuristic detection per the issue acceptance criteria.

## Phase 1: /qor-plan Step 2 Infrastructure Citation Inventory (P1)

### Affected Files

- `tests/test_qor_plan_infrastructure_citation_inventory.py` - NEW. 3 tests asserting Step 2 prose names the Infrastructure Citation Inventory section, requires grep-evidence statements, and treats unverified citations as Open Questions.
- `qor/skills/sdlc/qor-plan/SKILL.md` - extend Step 2 (Research Existing Code) with an "Infrastructure Citation Inventory" sub-section that requires every LD citing sealed infrastructure to carry a paired grep-evidence statement.

### Changes

Add prose under Step 2 stating that every LD citing sealed infrastructure (sealed migration name, function signature, file:line, table schema, enum value, index/constraint name, env-var name, edge-function path) MUST be paired with a grep-evidence statement of the form:

> `git show <sealed-ref>:<path> | grep -nE '<pattern>' → <exact observed text>`

Citations without paired grep-evidence are Open Questions to be resolved before `/qor-audit`. Plans with unverified citations in load-bearing LDs return to `/qor-plan` without consuming an audit cycle.

### Unit Tests

- `tests/test_qor_plan_infrastructure_citation_inventory.py::test_step_2_names_citation_inventory` - asserts `qor/skills/sdlc/qor-plan/SKILL.md` Step 2 region contains the literal phrase `Infrastructure Citation Inventory`.
- `tests/test_qor_plan_infrastructure_citation_inventory.py::test_step_2_requires_grep_evidence` - asserts the section body references `grep-evidence` and shows the canonical form (`git show ... grep ...`).
- `tests/test_qor_plan_infrastructure_citation_inventory.py::test_step_2_routes_unverified_to_open_questions` - asserts the section body names the Open Questions routing for unverified citations.

## Phase 2: /qor-audit Infrastructure Alignment Pass full re-walk on iter-N>1 (P2)

### Affected Files

- `tests/test_qor_audit_full_citation_rewalk.py` - NEW. 3 tests asserting the audit Step 3 Infrastructure Alignment Pass prose names the iter-N>1 full-plan re-walk requirement, references SG-CitationDrift-A as origin, and ties VETO to `infrastructure-mismatch` category.
- `qor/skills/governance/qor-audit/SKILL.md` - extend the Infrastructure Alignment Pass with an iter-N>1 sub-section: on iterations after the first, the Judge re-walks the FULL Locked Decision set (not just diff-from-iter-N-1) and grep-verifies every sealed-infrastructure citation.

### Changes

Add prose under the existing Infrastructure Alignment Pass stating: iter-N>1 audit behavior is full Locked Decision re-walk, not diff-from-iter-N-1. Citations without inline grep-evidence (per Phase 1's P1 contract) trigger immediate Infrastructure Alignment Pass VETO with `infrastructure-mismatch` category, regardless of whether the LD was amended in the current iteration.

### Unit Tests

- `tests/test_qor_audit_full_citation_rewalk.py::test_infrastructure_alignment_documents_full_rewalk` - asserts the audit SKILL.md Infrastructure Alignment Pass region names the iter-N>1 full-plan re-walk semantics.
- `tests/test_qor_audit_full_citation_rewalk.py::test_full_rewalk_cites_sg_citation_drift_a` - asserts the prose references `SG-CitationDrift-A` as the originating pattern.
- `tests/test_qor_audit_full_citation_rewalk.py::test_full_rewalk_ties_veto_to_infrastructure_mismatch` - asserts the prose names `infrastructure-mismatch` as the findings category.

## Phase 3: Doctrine SG-CitationDrift-A entry (P3)

### Affected Files

- `tests/test_doctrine_sg_citation_drift_a.py` - NEW. 2 tests asserting the doctrine carries the SG entry with the canonical pattern description and cross-references the P1+P2 countermeasures.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG entry `SG-CitationDrift-A`.

### Changes

Doctrine entry catalogs the pattern (cross-iteration unverified citation), originating recurrence (an external QA exemplar's attribution-12g iter-1 → iter-3 cycle 2026-05-13), and the P1+P2 countermeasures.

### Unit Tests

- `tests/test_doctrine_sg_citation_drift_a.py::test_doctrine_carries_sg_citation_drift_a` - reads the doctrine file, asserts `SG-CitationDrift-A` entry exists with the canonical pattern description.
- `tests/test_doctrine_sg_citation_drift_a.py::test_doctrine_cites_countermeasures` - asserts the SG entry body names both P1 (Infrastructure Citation Inventory) and P2 (full-plan re-walk).

## CI Commands

- `python -m pytest tests/test_qor_plan_infrastructure_citation_inventory.py tests/test_qor_audit_full_citation_rewalk.py tests/test_doctrine_sg_citation_drift_a.py -v` - validates Phase 72 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase72-sg-citation-drift-countermeasure.md` - self-application with Phase 67's discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
