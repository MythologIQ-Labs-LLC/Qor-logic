# Plan: Phase 98 — Meta-skill example blocks → references/ (F5+F6)

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: F5+F6 (internal prompt-surface review)

**boundaries**:
- limitations: V1 moves the `## Examples` section from two meta-skill
  SKILL.md files (`qor-meta-log-decision` and `qor-meta-track-shadow`)
  into per-skill `references/` files, leaves a pointer in SKILL.md per
  the progressive-disclosure doctrine, and adds structural tests
  preventing regression. V1 does NOT move the `## Meta-Ledger File
  Structure` / `## Shadow Genome File Structure` blocks (these are
  artifact-format reference, not invocation examples; they remain
  inline as integral skill contract documentation).
- non_goals: rewriting the example content; auto-generating examples
  from real ledger entries; extending the same treatment to other
  meta skills (governance/qor-audit, etc. — out of scope per the
  cluster sequencing memo's F5+F6 surface specifically targeting the
  two qor-meta-* skills); merging the references files into a shared
  examples doc.
- exclusions: no changes to skill behavior; no changes to any other
  SKILL.md content beyond the section move; no changes to existing
  Step 0.6 audit lints or Step 4.6.* substantiate gates; no changes
  to the Meta-Ledger File Structure sections (which contain the
  example META_LEDGER text incorrectly flagged as a stranded "Entry
  #6 fragment" by the research brief — see Design notes).

## Open Questions

None. The Decision Point for the "stranded Entry #6 fragment" closed
during plan authoring: re-reading the file at HEAD confirms the
fragment is inside the `## Meta-Ledger File Structure` fenced code
block (a deliberate artifact-format example), not stranded. The
research brief misread the structure. No move/delete needed; the
File Structure section remains intact.

## Feature Inventory Touches

Empty. Skill-prose move + new references files + structural tests.
`feature_inventory_touches`: `[]`.

## Design notes

F5+F6 of the internal prompt-surface review documented that two meta
skills carry sizable `## Examples` sections (three numbered concrete
invocation examples each, in fenced code blocks) that load into every
skill invocation. Per the GH #92 progressive-disclosure doctrine, this
example prose should live in `references/` and be pointed at from
SKILL.md, not loaded inline on every invocation.

**At HEAD**:
- `qor/skills/meta/qor-meta-log-decision/SKILL.md` (545 lines, ~16.4 KB):
  - `## Examples` lines 292-382 (~90 lines): three examples
    (Architecture L2, Security L3, Scope Change L2) in fenced
    markdown code blocks.
  - `## Meta-Ledger File Structure` lines 386-451 (~65 lines): example
    META_LEDGER artifact format with sub-headings including the
    line-437 `### Entry #6: Keystore Migration (L3)` block (this is
    intentional artifact-format example content, NOT stranded).
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md` (357 lines, ~12.3 KB):
  - `## Examples` lines 156-219 (~65 lines): three examples
    (Dependency Bloat SG-001, Premature Optimization SG-002,
    Hallucination SG-003) in fenced markdown code blocks.
  - `## Shadow Genome File Structure` lines 221+ : artifact format
    example.

**Move targets**:

- `qor/skills/meta/qor-meta-log-decision/SKILL.md` lines 292-382 →
  `qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`
  (NEW). The SKILL.md `## Examples` section is replaced with a short
  pointer paragraph + reference link.
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md` lines 156-219 →
  `qor/skills/meta/qor-meta-track-shadow/references/example-shadow-genome-events.md`
  (NEW). Same treatment.

**Estimated skill-size reductions** (per Phase 95 skill_size_budget_lint):
- qor-meta-log-decision: ~16.4 KB → ~13.7 KB (savings ~90 lines of
  example prose offloaded; still well under the 25 KB WARN threshold).
- qor-meta-track-shadow: ~12.3 KB → ~10.4 KB (savings ~65 lines).

Neither skill was at risk of WARN/EXCEEDED before; this phase is
hygiene, not size-budget repair. The Phase 95 lint will continue to
report the two standing qor-audit + qor-substantiate EXCEEDED findings
unchanged.

**Decision Point CLOSED at plan-authoring time**: the operator-deferred
question about the "stranded Entry #6 fragment" at
`qor-meta-log-decision/SKILL.md:437` resolved during file inspection.
The fragment is part of the `## Meta-Ledger File Structure` example
META_LEDGER text inside a fenced code block (lines 386-451); the
brief's "stranded" framing was a misread. No edit needed; the File
Structure section remains intact in SKILL.md as integral artifact-
format documentation.

**Structural countermeasure**: per the cluster pattern, each phase
adds a structural test catching regression of the discipline it
introduces. Phase 98 adds two tests asserting:
1. Each migrated SKILL.md cites the references file by path (progressive-
   disclosure pointer is the structural guard against the references
   file going stranded).
2. The references file exists at HEAD with the expected content
   headings.

## Phase 1: example moves + reference creation + structural tests

### Affected Files

- `qor/skills/meta/qor-meta-log-decision/SKILL.md` — replace
  `## Examples` (lines 292-382) with short pointer paragraph + link
  to references file. ~90 lines removed; ~5 lines added.
- `qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`
  — NEW. Contains the three examples (Architecture / Security / Scope
  Change) verbatim from the SKILL.md, plus a brief framing paragraph.
- `qor/skills/meta/qor-meta-track-shadow/SKILL.md` — replace
  `## Examples` (lines 156-219) with short pointer paragraph + link.
  ~65 lines removed; ~5 lines added.
- `qor/skills/meta/qor-meta-track-shadow/references/example-shadow-genome-events.md`
  — NEW. Contains the three examples (Dependency Bloat / Premature
  Optimization / Hallucination) verbatim, plus framing.
- `tests/test_meta_skill_examples_progressive_disclosure.py` — NEW.
  Six assertions (three per migrated skill: pointer present in
  SKILL.md, references file exists, references file contains the
  expected example IDs).
- `docs/plan-qor-phase98-meta-skill-examples-to-references.md` — NEW.
  This plan.

### Unit Tests

- `tests/test_meta_skill_examples_progressive_disclosure.py`
  - `test_qor_meta_log_decision_skill_cites_examples_reference` —
    anchored positive: SKILL.md text contains the path
    `references/example-decision-entries.md`.
  - `test_qor_meta_log_decision_examples_reference_file_exists` —
    the references file is reachable at HEAD.
  - `test_qor_meta_log_decision_examples_reference_carries_all_three_examples`
    — the references file contains all three example headings
    (Architecture / Security / Scope Change) preserved from SKILL.md.
  - `test_qor_meta_track_shadow_skill_cites_examples_reference` —
    anchored positive: SKILL.md text contains the path
    `references/example-shadow-genome-events.md`.
  - `test_qor_meta_track_shadow_examples_reference_file_exists` —
    the references file is reachable at HEAD.
  - `test_qor_meta_track_shadow_examples_reference_carries_all_three_examples`
    — the references file contains all three example IDs
    (SG-001 / SG-002 / SG-003).

### Changes

`qor/skills/meta/qor-meta-log-decision/SKILL.md` `## Examples` section
replaced with:

```markdown
## Examples

Concrete invocation examples (Architecture L2, Security L3, Scope
Change L2) are documented in
`qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`
per the progressive-disclosure doctrine (`SG-SkillCorpusGrowth-A`).
The reference file shows command, output, and contextual narration
for each tier.
```

`qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`
contains the three examples verbatim under a brief framing paragraph.

Same pattern for `qor-meta-track-shadow` with
`references/example-shadow-genome-events.md`.

## Definition of Done

### Deliverable: qor-meta-log-decision examples moved

- **D1**: The Examples section moves from inline SKILL.md prose into
  `references/example-decision-entries.md`; SKILL.md retains a short
  pointer.
- **D2**: `qor/skills/meta/qor-meta-log-decision/SKILL.md` shows the
  `## Examples` section replaced with the pointer paragraph;
  `qor/skills/meta/qor-meta-log-decision/references/example-decision-entries.md`
  exists with all three example bodies verbatim.
- **D3**: Plan + ledger + SYSTEM_STATE Phase 98 entry seal the move.
- **D4**: `tests/test_meta_skill_examples_progressive_disclosure.py`
  carries three assertions for this skill (pointer present, file
  exists, all three example IDs preserved); all pass.

### Deliverable: qor-meta-track-shadow examples moved

- **D1**: Same as above for the shadow-genome skill.
- **D2**: `qor/skills/meta/qor-meta-track-shadow/SKILL.md` shows the
  pointer paragraph;
  `qor/skills/meta/qor-meta-track-shadow/references/example-shadow-genome-events.md`
  exists with all three example bodies verbatim.
- **D3**: Plan + ledger entry cover the move.
- **D4**: Three assertions for this skill; all pass.

### Deliverable: structural countermeasure test

- **D1**: A test exists asserting the progressive-disclosure
  invariant for both migrated skills, preventing regression where a
  future edit removes the pointer.
- **D2**: `tests/test_meta_skill_examples_progressive_disclosure.py`
  exists with six assertions (three per skill).
- **D3**: Plan + ledger seal.
- **D4**: All six pass twice deterministically. The test is the
  dogfooding shipping-correctness anchor (it would have caught the
  inline-examples loading-cost pattern if it had existed earlier).

## CI Coverage Exemptions

None.

## CI Commands

- `python -m pytest tests/test_meta_skill_examples_progressive_disclosure.py -q` — Phase 98 structural tests.
- `python -m pytest tests/ -v` — full regression.
- `python qor/scripts/check_variant_drift.py` — ci.yml.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — install-smoke.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — gate-chain.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase98-meta-skill-examples-to-references.md` — plan-internal.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase98-meta-skill-examples-to-references.md --workflows-dir .github/workflows` — Phase 89 ci-coverage.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase98-meta-skill-examples-to-references.md` — Phase 92 DoD check.
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — Phase 95 skill-corpus-budget lint (WARN-only; both qor-meta-* skills are well under WARN threshold pre and post-move).
