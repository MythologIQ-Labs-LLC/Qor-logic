# Plan: Phase 187 - Negative-constraints doctrine + weak-tier variant injection (GH #243)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: Negative constraint
  home: qor/references/doctrine-negative-constraints.md

**boundaries**:
- limitations: [rules are prompt-level guidance for weak-tier execution; they are not a runtime enforcement gate]
- non_goals: [model-tier detection at compile time (host model is unknowable when compiling), rewriting the claude variant (install_drift_check mirrors source), inline rule bodies in the two big governance skills (headroom lock)]
- exclusions: [secret_scanner changes (NR-001 is instruction-level; the scanner already covers artifacts), gemini TOML format changes beyond body content]

## Open Questions

(none)

## Origin

Research brief docs/research-brief-negative-constraints-2026-07-13.md (ledger entry #466, session `2026-07-13T1025-96f825`); GH #243. Empirical basis recorded in the issue: weak-tier A/B evals showed mandatory definition/rationale slots induce secret reproduction and rationale fabrication.

## Locked Decisions

- **LD-1: rules live in a doctrine file; source skills carry a one-line pointer.**
  Headroom lock at tests/test_substantiate_staging_gates.py:48-62 (`HEADROOM_BYTES = 39 * 1024`) with qor-audit at 39,355 B / qor-substantiate at 39,321 B -> inline rule bodies do not fit; a ~180-byte pointer line does. New `qor/references/doctrine-negative-constraints.md` defines NR-001 (secret shapes: never reproduce secret-shaped strings; refer by prefix or descriptor) and NR-002 (no-fabrication: a mandatory rationale/definition/justification slot with no source fact takes the literal text "not established" -- never an invented fact). Registered in docs/GOVERNANCE_INDEX.md; glossary entry added.
- **LD-2: injection happens inside dist_compile for kilo-code/codex/gemini only.**
  `grep -nE 'def emit_(claude|kilocode|codex)' qor/scripts/dist_compile.py -> 47,64,69` (identity emitters); `grep -nE 'compile_mod.compile_all' qor/scripts/check_variant_drift.py -> 60` (drift check regenerates THROUGH compile_all, so deterministic in-compile transforms stay green); `grep -nE 'source and the installed counterpart' qor/scripts/install_drift_check.py -> 8` (installs mirror qor/skills source -> claude variant stays untransformed). `_FABRICATION_RISK_SKILLS = {"qor-audit", "qor-plan", "qor-substantiate"}`; `inject_negative_constraints(text, skill_name)` inserts a deterministic preamble block after YAML frontmatter. emit_kilocode/emit_codex become real implementations (copy then rewrite risk-skill SKILL.md); `emit_gemini` gains an optional `transform` callable applied to skill text before TOML rendering (`grep -nE 'def _emit_one|def emit_gemini' qor/scripts/gemini_variant.py -> 101,112`), passed by compile_all. The stale module docstring ("codex writes only a .gitkeep stub") is corrected.
- **LD-3: model_pinning_lint gains a WARN-only fabrication-guard scan.**
  `grep -nE 'def check' qor/scripts/model_pinning_lint.py -> 102` -- additive scan in the same walk: a skill in the fabrication-risk set whose SOURCE text lacks a `doctrine-negative-constraints` pointer emits a ModelPinningWarning. Exit stays 0 (Phase 55 contract).
- **LD-4: gemini description derivation is unaffected.**
  `grep -nE 'meta.get."description"' qor/scripts/gemini_variant.py -> 38` -- frontmatter description wins; the injected preamble cannot become the command description for the three risk skills (all declare frontmatter descriptions).

## Phase 1: Doctrine + pointer lines

### Affected Files

- qor/references/doctrine-negative-constraints.md - NEW: NR-001/NR-002, applicability, wiring
- docs/GOVERNANCE_INDEX.md - register the doctrine
- qor/references/glossary.md - add "Negative constraint" entry (home: the doctrine)
- qor/skills/governance/qor-audit/SKILL.md - one pointer line
- qor/skills/governance/qor-substantiate/SKILL.md - one pointer line
- qor/skills/sdlc/qor-plan/SKILL.md - one pointer line

### Changes

Doctrine file (~2.5 KB): problem statement (generalized eval finding from GH #243), the two rules verbatim-quotable, applicability (skills declaring `min_model_capability` above the executing model's tier), wiring map (dist_compile injection + lint scan). Pointer line in each risk skill directly after the `<skill>` block.

### Unit Tests

- tests/test_model_pinning_frontmatter.py - test_fabrication_guard_scan_clean_on_live_corpus: the lint over the real repo emits zero fabrication-guard warnings (pointer lines present and recognized by the scan)

## Phase 2: dist_compile injection (TDD first)

### Affected Files

- tests/test_dist_compile_injection.py - NEW test file (written red first)
- qor/scripts/dist_compile.py - `_FABRICATION_RISK_SKILLS`, `NEGATIVE_CONSTRAINTS_BLOCK`, `inject_negative_constraints`, real emit_kilocode/emit_codex, transform pass-through to gemini, docstring fix
- qor/scripts/gemini_variant.py - `transform` keyword on emit_gemini/_emit_one
- qor/dist/ - recompiled variants (kilo-code/codex/gemini risk skills carry the preamble)

### Changes

`inject_negative_constraints(text, skill_name)`: returns text unchanged unless skill_name is in the risk set AND text starts with well-formed `---` frontmatter; otherwise inserts the block between frontmatter close and the first body line. Block content cites both rules and the doctrine path. emit_kilocode/emit_codex: `emit_claude(...)` then rewrite each risk skill's SKILL.md through the injector. compile_all passes `transform=inject_negative_constraints` to emit_gemini; `_emit_one` applies it (with the skill name) before frontmatter parsing.

### Unit Tests

- tests/test_dist_compile_injection.py - test_inject_adds_block_after_frontmatter: synthetic risk-skill text -> block present, frontmatter intact, title heading after block (red today)
- tests/test_dist_compile_injection.py - test_inject_noop_for_non_risk_skill: unchanged bytes (red today)
- tests/test_dist_compile_injection.py - test_inject_noop_without_frontmatter: unchanged bytes
- tests/test_dist_compile_injection.py - test_compile_all_injects_weak_tier_variants_only: compile_all into tmp out_root -> kilo-code + codex SKILL.md and gemini qor-audit.toml carry NR-001/NR-002; claude variant byte-equals source (red today)

## Phase 3: model_pinning_lint scan (TDD first)

### Affected Files

- tests/test_model_pinning_frontmatter.py - fabrication-guard tests appended
- qor/scripts/model_pinning_lint.py - fabrication-risk set + guard scan in check()

### Changes

Guard scan: for each walked skill whose directory name is in the risk set, WARN when the source text lacks the `doctrine-negative-constraints` pointer. The lint keeps its own copy of the risk set (no runtime coupling to dist_compile); a test asserts the two constants stay equal.

### Unit Tests

- tests/test_model_pinning_frontmatter.py - test_fabrication_guard_warns_when_pointer_missing: synthetic risk skill without pointer -> warning naming the skill (red today)
- tests/test_model_pinning_frontmatter.py - test_fabrication_guard_silent_when_pointer_present: with pointer -> no warning
- tests/test_model_pinning_frontmatter.py - test_risk_set_matches_dist_compile: the lint's risk set equals dist_compile's (drift lock)

## Feature Inventory Touches

(empty -- governance/distribution tooling; no src/ features)

## Definition of Done

### Deliverable: weak-tier negative-rules channel

- **D1**: Skills that may execute below design tier carry explicit negative rules (GH #243): secret-shape reproduction and mandatory-slot fabrication are named, prohibited behaviors with prescribed alternatives.
- **D2**: `inject_negative_constraints` in qor/scripts/dist_compile.py; kilo-code/codex/gemini variants of qor-audit/qor-plan/qor-substantiate carry the NR-001/NR-002 preamble; claude variant remains byte-identical to source; check_variant_drift green after recompile.
- **D3**: Doctrine registered in GOVERNANCE_INDEX; glossary entry; ledger entries for plan/audit/implement/seal; CHANGELOG feature entry.
- **D4**: test_compile_all_injects_weak_tier_variants_only observes the compiled artifacts; test_fabrication_guard_warns_when_pointer_missing observes the lint behavior; both red-then-green.

## CI Commands

- `python -m pytest tests/test_dist_compile_injection.py tests/test_model_pinning_frontmatter.py tests/test_compile.py tests/test_dist_compile_gemini.py -q` - focused suites (run twice for determinism)
- `python -m qor.scripts.check_variant_drift` - dist matches regeneration after recompile
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
