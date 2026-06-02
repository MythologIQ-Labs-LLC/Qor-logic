# Plan: Restructure qor-substantiate Step 4.5 / Step Z (fix misplaced embedded gate-write block)

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: Fix the pre-existing structural defect in `qor/skills/governance/qor-substantiate/SKILL.md` where the entire `### Step Z: Write Gate Artifact` body (the `gate_chain.write_gate_artifact` + `ai_provenance.build_manifest` code AND the `session.rotate()` code) is pasted INSIDE the Step 4.5 "Skill File Integrity Check" required-sections checklist item, splitting that list across the embedded block. The fix: (1) restore Step 4.5 to a clean required-sections list naming `<skill>` block / `## Execution Protocol` / `### Step Z: Write Gate Artifact` / `## Constraints` / `## Next Step` with no embedded code; (2) extract the gate-artifact WRITE into a standalone `### Step Z: Write Gate Artifact (Phase 11D wiring)` section placed BEFORE Step 7.8 (gate-chain completeness verifies this phase's `substantiate.json`, so the write must precede it); (3) move `session.rotate()` into a final `### Step 9.8: Session Rotation (Phase 30 wiring)` section after Step 9.7 (rotating at Step 4.5 would corrupt `.qor/session/current` mid-seal, breaking SESSION_ID resolution for Steps 7.x-9.x). Recompile dist variants.
- non_goals: Changing any gate command, threshold, or the Critical-Invariant gate ladder ordering (Step 7.8 stays a named invariant); editing qor-audit or any other skill; changing `session.rotate()` or `write_gate_artifact` behavior (code is untouched -- only the skill prose that instructs the operator moves). No semantic change to what the seal does.
- exclusions: No change to `gate_chain_completeness`, `session`, `ai_provenance`, or schema modules.

## Open Questions

None. The write-before-7.8 ordering is mandated by `gate_chain_completeness.check` walking the current phase's SESSION SEAL entry (written at Step 7); the rotate-last ordering is mandated by every post-4.5 step resolving `SESSION_ID` from `.qor/session/current`. Both are deterministic from the code.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/skills/governance/qor-substantiate/SKILL.md` + recompiled `qor/dist/variants/**` + tests.)

- entry_id: `n/a` · operation: `MODIFIED` · test_path: `tests/test_substantiate_stepz_structure.py` · test_descriptor: `the test parses qor-substantiate/SKILL.md and compares character offsets: it asserts offset('### Step Z') < offset('### Step 7.8') (gate-write ordered before the completeness check) and offset('session.rotate()') > offset('### Step 7.8') (rotation runs as the final action, not mid-seal); it also slices the Step 4.5 region and asserts the slice has no python code fence and no write_gate_artifact token. A regression that re-tangles the block into Step 4.5 or moves rotate early flips these offset comparisons and fails the assertion.`

## Phase 1: Restructure the skill + regression test

### Affected Files

- `tests/test_substantiate_stepz_structure.py` - NEW. Written first; red against the current malformed SKILL.md (rotate offset currently < Step 7.8 offset; Step 4.5 currently contains a python fence).
- `qor/skills/governance/qor-substantiate/SKILL.md` - clean Step 4.5; add standalone `### Step Z` (write) before Step 7.8; add `### Step 9.8: Session Rotation` after Step 9.7.
- `qor/dist/variants/**/skills/qor-substantiate/SKILL.md` (+ gemini `qor-substantiate.toml`) - regenerated via `dist_compile`.

### Changes

Move-not-delete of the operative content: the `write_gate_artifact` + `build_manifest` code and the `session.rotate()` code are preserved verbatim, only relocated into well-formed sections in the correct order. Step 4.5's checklist becomes a plain comma-separated section-name list. No code module changes.

### Unit Tests

- `tests/test_substantiate_stepz_structure.py::test_step_4_5_has_no_embedded_codefence` - extract the text between `### Step 4.5` and `### Step 4.6`; assert it contains no ```` ```python ```` fence and no `write_gate_artifact(` (the gate-write code is gone from 4.5).
- `::test_single_step_z_heading_with_provenance` - assert exactly one `### Step Z: Write Gate Artifact` heading; the Step Z section body contains both `gate_chain.write_gate_artifact(` and `ai_provenance.build_manifest(`.
- `::test_step_z_write_precedes_completeness_check` - assert `text.index("### Step Z")` < `text.index("### Step 7.8")` (artifact written before gate-chain completeness verifies it).
- `::test_session_rotate_is_final_action` - assert `text.index("session.rotate()")` > `text.index("### Step 7.8")` AND a `### Step 9.8` (Session Rotation) heading exists after `### Step 9.7` (rotation no longer at Step 4.5).
- `::test_required_sections_list_intact` - the Step 4.5 region names all five required sections (`<skill>`, `## Execution Protocol`, `### Step Z`, `## Constraints`, `## Next Step`) in an unbroken list.

## Definition of Done

### Deliverable: well-formed substantiate skill

- **D1**: the qor-substantiate skill no longer embeds the Step Z gate-write/rotate block inside the Step 4.5 checklist; the gate-artifact write is a standalone step ordered before the completeness check, and session rotation is the final step.
- **D2**: cleaned Step 4.5 + new `### Step Z: Write Gate Artifact` (pre-7.8) + new `### Step 9.8: Session Rotation` (post-9.7) in `qor-substantiate/SKILL.md`; regenerated dist variants.
- **D3**: META_LEDGER SESSION SEAL entry; patch version bump (0.102.0 -> 0.102.1).
- **D4**: `tests/test_substantiate_stepz_structure.py::test_step_z_write_precedes_completeness_check` + `::test_session_rotate_is_final_action` + `::test_step_4_5_has_no_embedded_codefence` green; full `python -m pytest -q` green (no regression in `test_skill_corpus_consolidation`, `test_skill_prose_cites_ai_provenance`, `test_session_marker_path_unified`).

## CI Commands

- `python -m pytest tests/test_substantiate_stepz_structure.py -q` — the restructure regression suite.
- `python -m qor.reliability.skill_admission qor-substantiate` — skill still well-formed.
- `python -m pytest tests/test_skill_corpus_consolidation.py tests/test_skill_prose_cites_ai_provenance.py tests/test_session_marker_path_unified.py -q` — no regression in the structure/wiring guardrails.
- `python -m pytest -q` — full suite green before substantiate.

## CI Coverage Exemptions

- `dependency_admission_lint` — pre-existing dependency-admission job; this phase touches no dependencies.
- `check_variant_drift` — satisfied by the seal-time `dist_compile` recompile.
- `ledger_hash.py verify` — pre-existing ledger chain-integrity check.
- `test_packaging_install` — pre-existing install-smoke job.
- `gate_chain_completeness` — pre-existing gate-chain check, satisfied by the seal process.
