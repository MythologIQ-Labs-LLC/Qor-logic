# Plan: Phase 189 - /qor-onboard tutorial bundle (GH #241)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-onboard-tutorial-2026-07-13.md (ledger entry #474, session `2026-07-13T1255-08b7e7`); GH #241. Adoption-cost counterweight: first-session operators walk the full gate chain on a 30-minute trivial change instead of learning it mid-flight on load-bearing work.

## Locked Decisions

- **LD-1: new meta workflow bundle; the near-name skill stays untouched.**
  `grep -nE 'type: workflow-bundle' qor/skills/meta/qor-onboard-codebase/SKILL.md -> 3` (external-intake job; phases [research, organize, audit, plan]) -- extending it would complect intake with pedagogy. New `qor/skills/meta/qor-onboard/SKILL.md`, frontmatter mirroring the sibling bundle shape (type workflow-bundle, phases [ideate, research, plan, audit, implement, substantiate], checkpoints [after-ideate, after-audit], budget block), body under 8 KB with ALL narration prose in references/ (progressive disclosure; the corpus size lint WARNs at 25 KB).
- **LD-2: term-at-first-use is a linking discipline.**
  The tutorial narration links each doctrine term to its glossary home at first use and NEVER restates a definition -- prose of the definitional form registers as divergent-glossary term drift and ABORTs the seal (the recorded Phase 135/178 class). The rule is stated once in references/tutorial-narration.md and enforced by a test-level guard over the three new markdown files.
- **LD-3: registration surfaces are exactly three, plus automatic discovery.**
  `grep -nE 'Skills-29' README.md -> 14`; docs/SKILL_REGISTRY.md meta section (29 total today); qor/gates/delegation-table.md workflow-bundle section. skill_admission, gate_skill_matrix, and dist_compile discover the new skill from the corpus walk with no manual matrix edits; the cline command-count test computes from source lists.
- **LD-4: the bundle orchestrates, never analyzes.**
  Per the delegation-table bundle anti-pattern rule, every phase delegates to its single-purpose skill; the bundle adds only (a) the improvement scan menu (references/improvement-scan.md candidate classes; operator confirms the change), (b) per-phase narration, (c) the Review Boundary hold at substantiate.

## Phase 1: Skill + references (structure-first)

### Affected Files

- qor/skills/meta/qor-onboard/SKILL.md - NEW workflow bundle
- qor/skills/meta/qor-onboard/references/tutorial-narration.md - NEW per-phase narration script + the glossary-linking rule
- qor/skills/meta/qor-onboard/references/improvement-scan.md - NEW candidate classes + risk criteria + operator confirmation step
- docs/SKILL_REGISTRY.md - meta row + count updates (29 -> 30)
- README.md - Skills badge 29 -> 30
- qor/gates/delegation-table.md - bundle row
- qor/dist/ - recompiled (new skill propagates to all six variants)

### Changes

SKILL.md: purpose, when-to-use (first governed session; post-seed empty chain), execution protocol delegating ideate -> research -> plan -> audit -> implement -> substantiate with narration pointers, two operator checkpoints, Review Boundary hold at the substantiate publish menu, Next Step section. references/ carry the tutorial prose.

### Unit Tests

- tests/test_qor_onboard_skill.py - test_skill_admission_admits_onboard: `skill_admission` main over qor-onboard exits 0 (red until the skill exists)
- tests/test_qor_onboard_skill.py - test_gate_skill_matrix_resolves_with_onboard: matrix run reports zero broken handoffs with the new skill present (red until handoffs are real)
- tests/test_qor_onboard_skill.py - test_bundle_structural_contract: frontmatter declares type workflow-bundle and the six phases in chain order; both references files exist and are cited by name from SKILL.md (red today)
- tests/test_qor_onboard_skill.py - test_registry_and_badge_updated: SKILL_REGISTRY carries the qor-onboard row and the README badge count equals the registry row count (red today)
- tests/test_qor_onboard_skill.py - test_no_definitional_prose_for_glossary_terms: none of the three new markdown files contains a definitional-form line ("<Term> is/means/refers to") for any glossary term (guards the LD-2 discipline; green by construction, locks the class)

## Feature Inventory Touches

(empty -- skill corpus; no src/ features)

## Definition of Done

### Deliverable: guided first governed cycle

- **D1**: A first-session operator runs `/qor-onboard` after `qor-logic seed` and walks the full chain on one operator-confirmed trivial change, every gate artifact produced for real, every doctrine term linked to its glossary home at first use (GH #241).
- **D2**: qor/skills/meta/qor-onboard/SKILL.md + two references files; bundle frontmatter per LD-1; propagated to all six dist variants; check_variant_drift green.
- **D3**: SKILL_REGISTRY row + counts, README badge 30, delegation-table row; ledger entries for plan/audit/implement/seal; CHANGELOG feature entry.
- **D4**: The five tests in tests/test_qor_onboard_skill.py observe admission, matrix resolution, the structural contract, registration consistency, and the no-definitional-prose guard; red-then-green twice. The full operator flow (issue acceptance) is an LLM-executed session recorded as a documented follow-up validation, not a pytest subject.

## CI Commands

- `python -m pytest tests/test_qor_onboard_skill.py tests/test_dist_compile_injection.py tests/test_install_sync_with_source.py -q` - focused suites (run twice for determinism)
- `python -m qor.scripts.check_variant_drift` - dist matches regeneration after recompile
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
