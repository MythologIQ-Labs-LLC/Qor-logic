# Plan: Phase 112 - Hierarchical Governance Index (#140)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Governance Index
  home: qor/references/doctrine-governance-index.md
- term: Governance Freshness Tier
  home: qor/references/doctrine-governance-index.md
- term: Governance Index Drift
  home: qor/references/doctrine-governance-index.md

**boundaries**:
- limitations: V1 ships the scaffold, the 6-tier doctrine, and a WARN-only drift checker (Tier-1 freshness + unregistered-governance-file detection). It does NOT implement automated Tier 3->6 / Tier 4->6 archival, the `/qor-validate` ledger-cross-check, or a hard `/qor-implement` block on stale Tier 1 — those are deferred V2 enforcement.
- non_goals: Not a replacement for META_LEDGER (decision history) or FEATURE_INDEX (code feature -> test). Not a CMS; Markdown tables, hand-edited, audited by the checker. No JSON-backed manifest in V1.
- exclusions: No FailSafe-specific paths (`.failsafe/`); qor-logic's governance set is the default. No `paths.governance` config knob in V1 (V2).

## Open Questions

None. The proposal's four open questions are resolved by evidence/convention (recorded in Locked Decisions): docs/ placement, hand-edited Markdown, the 6-tier numbered+named model verbatim, and the default-governance-set (no config knob in V1).

## Locked Decisions

- **LD1 (placement)**: `docs/GOVERNANCE_INDEX.md` — co-locates with META_LEDGER / SYSTEM_STATE / BACKLOG, matches Phase 109's framing of GOVERNANCE_INDEX as the future freshness surface.
- **LD2 (format)**: hand-edited Markdown tables + a Markdown-parsing checker. JSON-backed manifest deferred to V2 (proposal: "for now").
- **LD3 (tiers)**: the 6 tiers (1 Canonical Source, 2 Doctrine & Policy, 3 Active Initiative, 4 Per-Plan Artifact, 5 Reference Material, 6 Archived) named verbatim.
- **LD4 (scope set)**: governance set defaults to qor-logic's standard artifacts (reuse `governance_health` required-artifact registry); the `paths.governance` config knob is V2.
- **LD5 (registry coupling)**: `GOVERNANCE_INDEX.md` becomes a seed scaffold target and joins `governance_health.REQUIRED_ARTIFACTS`, realizing Phase 109's "future freshness surface" (LD1 of Phase 109). The Phase 109 anti-drift test (`SCAFFOLD_OWNED == seed file targets`) continues to hold because `SCAFFOLD_OWNED` derives from `seed.scaffold_file_targets()`.

## Context

Long-running Qor projects accumulate governance docs across many dirs; without a single freshness-tiered index, drift is invisible and "one incorrect governance value cascades into failures." This phase introduces `docs/GOVERNANCE_INDEX.md` (6-tier map) + a WARN-only drift checker, building on Phase 109's governance-health registry.

## Feature Inventory Touches

Empty. Governance scaffold + tooling + doctrine; no `src/` user-touchable product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: GOVERNANCE_INDEX scaffold + registry coupling

### Affected Files

- `tests/test_governance_index_seed.py` - NEW. Behavioral: seed creates `docs/GOVERNANCE_INDEX.md`; the template carries all six tier headings; `governance_health.REQUIRED_ARTIFACTS` and `SCAFFOLD_OWNED` include it; Phase 109 anti-drift invariant still holds.
- `qor/templates/GOVERNANCE_INDEX.md` - NEW. 6-tier template; Tier 1 pre-populated with qor-logic canonical docs; Tiers 2-5 empty tables with one worked example each; "Last Reviewed" header; add/retire recipe at the foot.
- `qor/seed.py` - AMENDED. Add `SeedTarget("docs/GOVERNANCE_INDEX.md", "GOVERNANCE_INDEX.md", "file")` to `SEED_TARGETS`.
- `qor/scripts/governance_health.py` - AMENDED. Add `docs/GOVERNANCE_INDEX.md` to `REQUIRED_ARTIFACTS` (it is now scaffold-owned via the seed coupling).
- `docs/GOVERNANCE_INDEX.md` - NEW. The qor-logic repo's own governance index (dogfooding), so `governance_health` does not report it MISSING for this repo. Populated from the template with qor-logic's actual Tier-1/2 artifacts and a current "Last Reviewed" date.

### Unit Tests

- `tests/test_governance_index_seed.py::test_seed_creates_governance_index` - invokes `seed(tmp)`; asserts `docs/GOVERNANCE_INDEX.md` exists and the template body contains all six tier headings.
- `tests/test_governance_index_seed.py::test_required_and_scaffold_sets_include_index` - asserts `"docs/GOVERNANCE_INDEX.md"` in `governance_health.REQUIRED_ARTIFACTS` and in `governance_health.SCAFFOLD_OWNED`.
- `tests/test_governance_index_seed.py::test_phase109_scaffold_owned_invariant_holds` - re-asserts `SCAFFOLD_OWNED == seed.scaffold_file_targets()` after the addition (no drift).

## Phase 2: governance_index drift checker

### Affected Files

- `tests/test_governance_index.py` - NEW. Behavioral tests for Tier-1 freshness + unregistered-file detection + parse.
- `qor/scripts/governance_index.py` - NEW. Parse the index (tier tables + "Last Reviewed" date); `check_index_drift(base) -> list[IndexFinding]` returns Tier-1 staleness (Last Reviewed older than the latest sealed META_LEDGER entry date) and governance files present on disk but absent from any tier table. CLI `python -m qor.scripts.governance_index --repo-root .` exits 0 (clean) / 1 (drift). WARN-only contract documented.

### Changes

`IndexFinding(kind, path, reason)` with kinds `stale-tier1`, `unregistered`. Parse "Last Reviewed: YYYY-MM-DD"; compare against the newest `### Entry #N: SESSION SEAL` timestamp date in META_LEDGER. Enumerate `docs/*.md` + root `*.md` governance files; flag any not named in a tier table (excludes the index itself + an exempt list). Missing index -> single `missing-index` finding (legal next: `qor-logic seed`).

### Unit Tests

- `tests/test_governance_index.py::test_stale_last_reviewed_flags_tier1_drift` - index "Last Reviewed" predates the latest seal entry -> `stale-tier1` finding.
- `tests/test_governance_index.py::test_current_last_reviewed_passes` - "Last Reviewed" >= latest seal date -> no stale-tier1 finding.
- `tests/test_governance_index.py::test_unregistered_governance_doc_flags` - a `docs/NEWDOC.md` not in any tier table -> `unregistered` finding naming it.
- `tests/test_governance_index.py::test_registered_doc_does_not_flag` - the same doc added to a tier table -> no finding.
- `tests/test_governance_index.py::test_missing_index_returns_missing_finding` - no index file -> single `missing-index` finding.

## Phase 3: doctrine + glossary + status surface

### Affected Files

- `tests/test_governance_index_doctrine.py` - NEW. Asserts the doctrine defines the six tiers and the drift contract, and the glossary carries the three terms with homes.
- `qor/references/doctrine-governance-index.md` - NEW. The 6-tier model, freshness contracts, drift-detection contract, and the V2 deferral note (archival + validate-cross-check + hard-block).
- `qor/references/glossary.md` - AMENDED. Add `Governance Index`, `Governance Freshness Tier`, `Governance Index Drift`.
- `qor/skills/memory/qor-status/SKILL.md` - AMENDED. Add a one-line governance-index drift indicator to the Step 4 output (entries count, Last Reviewed, stale Tier-1 count); WARN-only surface in V1.
- `qor/dist/variants/{claude,codex,kilo-code}/skills/**` - REGENERATED.

### Unit Tests

- `tests/test_governance_index_doctrine.py::test_doctrine_defines_six_tiers` - invokes a parser; asserts all six tier names present and the drift contract is stated.
- `tests/test_governance_index_doctrine.py::test_glossary_has_governance_index_terms` - parses glossary YAML entries; asserts the three terms exist with `home` set to the doctrine.

## Definition of Done

### Deliverable D-112.1: scaffold + registry coupling
- **D1**: `docs/GOVERNANCE_INDEX.md` is a seeded canonical artifact in the qor governance set.
- **D2**: `SeedTarget` added; `governance_health.REQUIRED_ARTIFACTS` includes it; `SCAFFOLD_OWNED` derives it.
- **D3**: Phase 109 anti-drift invariant preserved.
- **D4**: `tests/test_governance_index_seed.py` passes.

### Deliverable D-112.2: drift checker
- **D1**: A WARN-only checker surfaces Tier-1 staleness and unregistered governance docs.
- **D2**: `qor/scripts/governance_index.py` with `check_index_drift` + CLI (exit 0/1).
- **D3**: Parses hand-edited Markdown (LD2); no JSON dependency.
- **D4**: `tests/test_governance_index.py` passes all five cases.

### Deliverable D-112.3: doctrine + glossary + status surface
- **D1**: The 6-tier model + drift contract are doctrine; `/qor-status` surfaces a one-line drift indicator.
- **D2**: `doctrine-governance-index.md` NEW; glossary terms added; qor-status SKILL amended; variants regenerated.
- **D3**: V2 deferrals (archival, validate cross-check, hard block) explicitly documented.
- **D4**: `tests/test_governance_index_doctrine.py` passes.

## CI Commands

- `python -m pytest tests/test_governance_index_seed.py -q` - scaffold + registry coupling.
- `python -m pytest tests/test_governance_index.py -q` - drift checker.
- `python -m pytest tests/test_governance_index_doctrine.py -q` - doctrine + glossary.
- `python -m pytest tests/test_governance_health.py tests/test_seed_scaffold.py tests/test_cli_seed.py -q` - Phase 109 + seed regression (registry/seed coupling).
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.check_variant_drift` - generated variant drift.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase112-governance-index.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase112-governance-index.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging integration smoke; orthogonal.
- `gate_chain_completeness` - sealed-phase chain audit; runs every PR.
- `dependency_admission_lint` - dependency cooling-period check; no dependency changes here.
