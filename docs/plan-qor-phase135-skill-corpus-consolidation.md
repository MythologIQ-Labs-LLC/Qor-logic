# Plan: Pre-1.0 skill-corpus consolidation — qor-audit + qor-substantiate progressive disclosure

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Pure progressive-disclosure consolidation of the two EXCEEDED skills (`qor-audit` 52.7 KB, `qor-substantiate` 47.9 KB) under the 40 KB hard budget the Phase 95 `skill_size_budget_lint` enforces. Multi-paragraph "Phase NN wiring / Per SG-X / originating-recurrence" RATIONALE moves to `references/` files (precedent: `qor-audit/references/phase37-subpasses.md`, GH #92); each inline pass keeps its operative spine and gains a one-line pointer. The operative spine that MUST stay inline verbatim: frontmatter, the `<skill>` block, `## Critical Invariants` (all numbered contracts + line pointers), every `### Step` header, every gate command/code block, every VETO/ABORT checklist, the `findings_categories` mapping table, the Step Z gate-artifact code, and `## Constraints`. Net result: behavior of the skills is unchanged; only the location of explanatory prose moves.
- non_goals: Restructuring operative steps (e.g. the pre-existing misplaced embedded Step Z inside `qor-substantiate` Step 4.5 is OUT of scope — a size phase must not change step structure); editing any gate logic, command, or threshold; touching any other skill; cutting operative content to hit the 25 KB WARN line (the binding budget is the 40 KB EXCEEDED line; WARN is advisory).
- exclusions: No change to `skill_size_budget_lint` thresholds; no change to `dist_compile` (it already `copytree`s `references/`, so new reference files propagate to variants on the Step 8.5 recompile).

## Open Questions

None. The target (under the 40 KB EXCEEDED budget), the safe-extraction class (rationale prose, not operative spine), and the reference-file precedent are all established. The behavioral test asserts both the size reduction AND that no operative spine element was dropped (moved-not-deleted), so a consolidation that silently cut a Critical Invariant or gate command fails red.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/skills/governance/**` + new `references/*.md` + tests + recompiled `qor/dist/variants/**`.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_skill_corpus_consolidation.py` · test_descriptor: `invoking skill_size_budget_lint over qor/skills returns a findings list whose EXCEEDED set excludes both qor-audit/SKILL.md and qor-substantiate/SKILL.md (the transformation's size output); the consolidated SKILL.md text retains every Critical-Invariant contract, Step header, and gate-command token (so a silently dropped invariant fails the assertion); each extracted reference file's text carries a verbatim sentence the SKILL.md no longer inlines (proving relocation, not deletion); and running skill_admission on each skill returns exit 0`

## Phase 1: Extract qor-audit rationale to references — `qor/skills/governance/qor-audit/`

### Affected Files

- `tests/test_skill_corpus_consolidation.py` - NEW. Written first; red before any extraction (sizes still EXCEEDED, new reference files absent). Behavioral assertions per the Feature Inventory `test_descriptor`.
- `qor/skills/governance/qor-audit/references/pre-audit-lints.md` - NEW. Holds the Step 0.6 per-lint wiring rationale (Phase 110/67/89/130/127/94 paragraphs explaining each lint's originating recurrence + SG mapping).
- `qor/skills/governance/qor-audit/references/adversarial-mode.md` - EXISTING; append the Step 1 mode-selection rationale moved out of SKILL.md (external-reviewer bridge prose, Option B dispatch protocol, Phase 87 author-momentum rationale). The operative code blocks stay inline.
- `qor/skills/governance/qor-audit/references/phase37-subpasses.md` - EXISTING; append the Step 3 Filter-Stage Ordering 4-step procedure + heuristic, the Live-Progress Invariant sub-checklist rationale, and the Infrastructure-Alignment Phase 99/72/83 rationale. The Step 3 VETO categories + the runnable commands stay inline.
- `qor/skills/governance/qor-audit/SKILL.md` - replace each moved rationale block with a one-line pointer (`Rationale + SG mapping: see references/<file>.md`). Keep all operative spine.

### Changes

Move-not-delete. For each extraction site the SKILL.md keeps: the section/step header, the operative checklist or command/code block, the binding VETO/ABORT category line, and the `Per qor/references/doctrine-*.md` routing line. It loses only the multi-paragraph explanatory rationale, replaced by a single pointer line into the reference file. The reference file gains a section (with a heading naming the pass/step) carrying the verbatim moved prose.

### Unit Tests

(Single shared test module; assertions for both skills — see Phase 3.)

- `tests/test_skill_corpus_consolidation.py::test_audit_under_budget` - call `skill_size_budget_lint`'s find-findings API over `qor/skills`; assert no `EXCEEDED` finding names the qor-audit SKILL.md.
- `::test_audit_spine_preserved` - assert every one of the 9 Critical-Invariant binding contracts, every `### Step` header (0, 0.3, 0.4, 0.5, 0.6, 1, 2, 3, 4, 4.1, 4.2, 5, 6, 7, Z), and every gate command substring (`plan_iteration_status_lint`, `prompt_injection_canaries`, `runtime_contract_walk`, `audit_risk_score`, the Step 0.6 lint list) is present in the consolidated SKILL.md.
- `::test_audit_references_resolve` - every `references/<x>.md` cited in qor-audit/SKILL.md resolves to an existing file under the skill dir.
- `::test_audit_rationale_moved` - each extracted reference file contains a distinctive sentence verbatim moved from the SKILL.md (proves moved, not deleted).

## Phase 2: Extract qor-substantiate rationale to references — `qor/skills/governance/qor-substantiate/`

### Affected Files

- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` - NEW. Holds the Step 4.6.x / 4.7.x gate rationale (the per-gate "Per SG-X / originating recurrence / V1 WARN V2 reserved / fail-closed since Phase NN" paragraphs). Commands + ABORT semantics stay inline.
- `qor/skills/governance/qor-substantiate/references/release-and-tag-timing.md` - NEW. Holds the Step 7.5/7.6 pluggable-backend rationale and the Step 9.5.4/9.5.5/9.6/9.7 seal-tag-timing rationale (the off-by-one history + release.yml reachability explanation). The commands/code + the Constraints lines stay inline.
- `qor/skills/governance/qor-substantiate/SKILL.md` - replace each moved rationale block with a one-line pointer. Keep all operative spine (Critical Invariants, Step Prerequisites table, every Step header, every gate command, Step Z code, Constraints). Do NOT touch the misplaced Step 4.5 embedded block (out of scope; flag at handoff).

### Changes

Same move-not-delete discipline as Phase 1. The Step Prerequisites table (lines ~64-79) is operative (consumed by `substantiate-capability`) and stays inline verbatim.

### Unit Tests

- `::test_substantiate_under_budget` - assert no `EXCEEDED` finding names the qor-substantiate SKILL.md.
- `::test_substantiate_spine_preserved` - assert the 4 Critical Invariants, every `### Step` header (0, 1, 2, 2.5, 3, 3.5, 4, 4.5, 4.6, 4.6.5, 4.6.6, 4.6.7, 4.6.8, 4.6.9, 4.6.10, 4.7, 4.7.5, 5, 6, 6.5, 6.8, 7, 7.4, 7.5, 7.6, 7.7, 7.8, 8, 8.5, 9, 9.5, 9.5.4, 9.5.5, 9.6, 9.7), and every gate command substring (`intent_lock verify`, `skill_admission`, `gate_skill_matrix`, `secret_scanner --staged`, `merge_velocity_check`, `data_api_acl_lint`, `governance-index`, `--enforce`, `gate_chain_completeness`, `dist_compile`, `seal_trailer_check`) are present.
- `::test_substantiate_references_resolve` - every cited reference file resolves.
- `::test_substantiate_rationale_moved` - each new reference file carries a distinctive moved sentence.

## Phase 3: Cross-skill integrity — both skills

### Affected Files

- `tests/test_skill_corpus_consolidation.py` - add the cross-skill admission assertions.

### Unit Tests

- `::test_both_skills_admission_passes` - run `qor.reliability.skill_admission` over both skills; assert exit 0 (frontmatter + required sections intact after edit).
- `::test_corpus_no_exceeded` - call the corpus report; assert `oversized skills == 0` after consolidation.

## Definition of Done

### Deliverable: consolidated governance skills under budget

- **D1**: the two largest governance skills are brought under the 40 KB EXCEEDED budget by progressive disclosure, with zero change to their operative behavior (every Critical Invariant, Step, gate command, and VETO/ABORT contract preserved inline; only explanatory rationale relocates to `references/`).
- **D2**: `qor-audit/SKILL.md` < 40960 bytes and `qor-substantiate/SKILL.md` < 40960 bytes; new reference files `pre-audit-lints.md`, `seal-gate-ladder.md`, `release-and-tag-timing.md` plus appended sections in `adversarial-mode.md` / `phase37-subpasses.md`; recompiled variants under `qor/dist/variants/**`.
- **D3**: META_LEDGER SESSION SEAL entry recording the consolidation + version bump; `docs/GOVERNANCE_INDEX.md` Last-Reviewed advanced (the new reference files match the existing Tier-5 `qor/references/*.md` / skill-local references pattern; no new tier row needed).
- **D4**: `tests/test_skill_corpus_consolidation.py::test_audit_spine_preserved` + `::test_substantiate_spine_preserved` + `::test_audit_under_budget` + `::test_substantiate_under_budget` + `::test_both_skills_admission_passes` all green; full `python -m pytest -q` green.

## CI Commands

- `python -m pytest tests/test_skill_corpus_consolidation.py -q` — the consolidation behavioral suite (spine-preserved + under-budget + admission).
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — confirms zero EXCEEDED findings post-consolidation (advisory).
- `python -m qor.reliability.skill_admission qor-audit && python -m qor.reliability.skill_admission qor-substantiate` — both skills well-formed.
- `python -m qor.reliability.gate_skill_matrix` — all cross-skill handoff references still resolve.
- `python -m pytest -q` — full suite green before substantiate.

## CI Coverage Exemptions

- `dependency_admission_lint` — pre-existing dependency-admission cooling-period job in `pr-dependency-review.yml`; this phase touches no dependencies (skill markdown + tests only), so the job is not phase-relevant infrastructure.
- `check_variant_drift` — pre-existing `ci.yml` variant-drift guard; satisfied by the seal-time `dist_compile` recompile (Step 8.5), not a phase-specific local command.
- `ledger_hash.py verify` — pre-existing `ci.yml` ledger chain-integrity check; standing infrastructure run on every PR.
- `test_packaging_install` — pre-existing `ci.yml` install-smoke integration job; standing packaging infrastructure, unaffected by markdown consolidation.
- `gate_chain_completeness` — pre-existing `ci.yml` gate-chain completeness check; satisfied by the seal process, not a phase-specific local command.
