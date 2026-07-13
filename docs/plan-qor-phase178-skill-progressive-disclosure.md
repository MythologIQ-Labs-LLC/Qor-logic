# Plan: Phase 178 - Progressive-disclosure pass on qor-audit + qor-substantiate (GH #266)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-skill-progressive-disclosure-2026-07-13.md (ledger entry #430, session `2026-07-13T0640-f49940`); GH #266. Prose relocation only -- zero behavioral change; the binding spine (step headers, commands, ABORT/VETO invariants, prerequisite table) stays inline byte-exact.

## Locked Decisions

- **LD-1: the guardrail set is the specification.**
  `tests/test_skill_corpus_consolidation.py` spine locks (AUDIT_INVARIANTS/STEPS/COMMANDS at lines 65-85; SUBST_* at 93-109; relocated-rationale assertions at 163-177), `tests/test_seal_flow_ordering.py`, `tests/test_substantiate_tag_timing_wired.py`, `tests/test_qor_substantiate_capability_declarations.py` (table header + 12 step IDs + per-step Phase 75 cross-refs), `tests/test_substantiate_staging_gates.py` (Step 9.5 block + <40,960 budget + variant equality), `tests/test_skill_doctrine.py` (every references/X.md citation resolves). Any relocation that reddens one of these is wrong BY DEFINITION and reverts.
- **LD-2: reduction target is recovered headroom, not the 30 KB aspiration.**
  Sizes verified live: audit 40,890 / substantiate 40,935 vs EXCEEDED 40,960 (`grep -nE 'EXCEEDED_BYTES' qor/scripts/skill_size_budget_lint.py -> 24`). Target: BOTH files < 39,936 bytes (>= 1 KB recovered headroom), locked by extending the Phase 176 budget test to cover both skills at the tighter bound. The 30 KB aspiration is deferred (research F4 rationale recorded on GH #266 at disposition).
- **LD-3: destinations are already-cited references only.**
  qor-audit rationale -> `references/adversarial-mode.md` + `references/phase37-subpasses.md` (both cited in the skill today; `tests/test_skill_doctrine.py:142-147` requires resolution, which holds). qor-substantiate rationale -> `references/seal-gate-ladder.md` + `references/release-and-tag-timing.md` (both cited today). No NEW reference files (no glossary referenced_by churn; no doc-integrity term surface).
- **LD-4: relocation form.**
  Each moved block is replaced inline by at most one pointer sentence naming the reference; the moved prose lands under a clearly titled subsection in the destination (appended; existing content untouched so the Phase 135/162 relocated-rationale assertions keep matching). Code blocks, tables, and any sentence in the LD-1 lock set never move.

## Phase 1: Budget guardrail (TDD first -- red against current sizes)

### Affected Files

- tests/test_substantiate_staging_gates.py - the budget test generalizes: parametrized over BOTH governance skills at a 39,936-byte bound (naturally red today: 40,890 and 40,935 both exceed it)

### Changes

`test_skill_stays_under_exceeded_budget` becomes `test_governance_skills_keep_headroom`, parametrized over (qor-audit, qor-substantiate) with `HEADROOM_BYTES = 39 * 1024` and an assertion message naming GH #266. The old <40,960 property is implied by the tighter bound.

### Unit Tests

- tests/test_substantiate_staging_gates.py::test_governance_skills_keep_headroom[qor-audit] - byte size < 39,936 (red today at 40,890)
- tests/test_substantiate_staging_gates.py::test_governance_skills_keep_headroom[qor-substantiate] - byte size < 39,936 (red today at 40,935)

## Phase 2: qor-audit disclosure pass

### Affected Files

- qor/skills/governance/qor-audit/SKILL.md - four rationale blocks -> pointer sentences
- qor/skills/governance/qor-audit/references/adversarial-mode.md - gains the Step 1 dispatch rationale + Self-Application origin narrative (appended subsections)
- qor/skills/governance/qor-audit/references/phase37-subpasses.md - gains the Phase 99 V2 ramp narrative (appended subsection)

### Changes

Move (per LD-4): Step 1 adversarial-mode dispatch protocol prose (Option A/B narrative, external-reviewer bridge rationale -- code blocks stay), the Critical Invariants "V2 ramp note" paragraph body (the numbered invariant list stays byte-exact), the Self-Application pattern-origin sentences, and the Environment section's Phase 75 SKIP-cascade narrative (the preflight code block and one contract sentence stay). Every AUDIT_INVARIANTS/STEPS/COMMANDS token verified present after the edit.

### Unit Tests

- (behavioral net) tests/test_skill_corpus_consolidation.py + tests/test_skill_doctrine.py green after the pass -- the spine and reference resolution are the assertions
- tests/test_substantiate_staging_gates.py::test_governance_skills_keep_headroom[qor-audit] flips green

## Phase 3: qor-substantiate disclosure pass

### Affected Files

- qor/skills/governance/qor-substantiate/SKILL.md - four rationale blocks -> pointer sentences
- qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md - gains Step 6.5 phase-class rationale, Step 6.8 no-override philosophy, Step 4.7.5 self-policing narrative (appended subsections)
- qor/skills/governance/qor-substantiate/references/release-and-tag-timing.md - gains any Step 9.x timing narrative trimmed (only if needed for the bound)
- qor/dist/variants/*/skills/... - regenerated via dist_compile

### Changes

Move (per LD-4): Step 6.5's Phase 31/33/49 conditional-rule narrative (the Phase 49 ABORT code block + its one binding sentence stay -- SUBST_INVARIANTS locks the `|| ABORT` sentence), Step 6.8's rationale paragraphs (validation code blocks stay), Step 4.7.5's operator-flow narrative (command block stays), and Step Prerequisites table ANNOTATION prose (table structure + all 12 step IDs + "Phase 75"/"Prerequisite" cross-refs stay byte-exact). Step 9.5 block untouched (Phase 176 lock).

### Unit Tests

- tests/test_qor_substantiate_capability_declarations.py green (table contract intact)
- tests/test_seal_flow_ordering.py + tests/test_substantiate_tag_timing_wired.py green (ordering/token contracts intact)
- tests/test_substantiate_staging_gates.py all green incl. both headroom parameters and variant equality (after dist_compile)

## Feature Inventory Touches

(empty -- skill prose relocation only)

## Definition of Done

### Deliverable: recovered skill-size headroom

- **D1**: Neither governance skill can block a seal by a single wiring-paragraph addition: both files sit under 39 KB with the bound test-locked (GH #266; the 30 KB aspiration deferred with recorded rationale).
- **D2**: Rationale relocated to already-cited references per LD-4; every LD-1 locked token inline byte-exact; zero behavioral change.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #266 disposition records the deferral rationale; no glossary/doctrine changes.
- **D4**: `test_governance_skills_keep_headroom` (both parameters) red-then-green; the full guardrail set stays green (the relocation's correctness proof).

## CI Commands

- `python -m pytest tests/test_substantiate_staging_gates.py tests/test_skill_corpus_consolidation.py tests/test_skill_doctrine.py tests/test_qor_substantiate_capability_declarations.py tests/test_seal_flow_ordering.py tests/test_substantiate_tag_timing_wired.py -q` - focused guardrail suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
