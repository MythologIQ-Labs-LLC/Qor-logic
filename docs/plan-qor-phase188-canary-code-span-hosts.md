# Plan: Phase 188 - Canary code-span nuance + adapter-matrix host expansion (GH #244)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-canary-inline-code-2026-07-13.md (ledger entry #470, session `2026-07-13T1145-3ee3e2`); GH #244 (both items in one issue = one scope boundary). Naming discipline: this plan and all phase artifacts never spell the hidden-html canary's markup literal; it is "the tag alternation" (NR-001-style descriptor reference -- the audit-site canary scan is strict and would hit its own plan).

## Locked Decisions

- **LD-1: per-class CLI downgrade; scan() stays pure and strict.**
  `grep -nE 'class_name="hidden-html"' qor/scripts/prompt_injection_canaries.py -> 99`; `grep -nE 'def mask_code_blocks' -> 137` with the strict-at-audit rationale at lines 143-144. In `main()` only: compute the masked text once; a hidden-html hit whose full span lies inside a masked (code) region prints `CANARY WARN [hidden-html/code-span]` and does not count toward exit 1. New `--strict` flag restores current behavior byte-for-byte. The four instruction classes and unicode-directionality stay binding inside code spans (imperative text is an instruction wherever it sits). `scan()` signature and behavior unchanged.
- **LD-2: two new hosts mirror the published adapter matrix, anonymously.**
  `grep -nE '_HOSTS: dict' qor/hosts.py -> 84`; `grep -nE 'TARGETS = ' qor/scripts/dist_compile.py -> 22`. `cursor`: base `.cursor`, claude-shaped skills/agents map. `cline`: base `.clinerules`, install_map `{"workflows/": base / "workflows"}` (the layout is shared by three assistants; one variant serves all). Publication boundary: the source framework is referred to generically everywhere.
- **LD-3: both new variants are weak-tier channels and receive the Phase 187 injection.**
  `grep -nE 'def _rewrite_risk_skills' qor/scripts/dist_compile.py -> 74`. emit_cursor = emit_claude + `_rewrite_risk_skills`. emit_cline flattens: for every skill dir and loose skill, write `workflows/command-<name>.md` whose content is `inject_negative_constraints(source_text, name)` (byte-preserving IO as in Phase 187). Agents flatten to `workflows/agent-<name>.md` (mirrors the gemini naming precedent, `grep -nE 'agent-' qor/scripts/gemini_variant.py -> 127`).
- **LD-4: sync contracts extend explicitly.**
  tests/test_install_sync_with_source.py: `cursor` joins the injected-sync loop (claude-shaped layout); `cline` gets a documented exclusion plus its own content tests (flattened layout, like the gemini exclusion at the file foot).

## Phase 1: Canary code-span nuance (TDD first)

### Affected Files

- tests/test_prompt_injection_canary.py - Phase 188 tests appended (red first)
- qor/scripts/prompt_injection_canaries.py - `--strict` flag + code-span downgrade for hidden-html in main()

### Changes

`main()` gains `--strict`; after reading content it computes `mask_code_blocks(content)` once and partitions hits: hidden-html hits whose span text in the masked copy is all whitespace are code-span hits -> WARN line, excluded from the exit-1 count unless `--strict`. All other hits unchanged.

### Unit Tests

- tests/test_prompt_injection_canary.py - test_code_span_hidden_html_downgrades_to_warn: a plan file whose only hit is the tag alternation inside an inline code span -> exit 0, stderr carries "CANARY WARN [hidden-html/code-span]" (red today)
- tests/test_prompt_injection_canary.py - test_code_span_hidden_html_strict_restores_abort: same file with --strict -> exit 1 (red today)
- tests/test_prompt_injection_canary.py - test_prose_hidden_html_still_aborts: the tag alternation in prose -> exit 1
- tests/test_prompt_injection_canary.py - test_instruction_class_in_code_span_still_aborts: an instruction-redirect sentence inside backticks -> exit 1 (the deliberate asymmetry)

## Phase 2: Host expansion (TDD first)

### Affected Files

- tests/test_hosts_cursor_cline.py - NEW test file (red first)
- tests/test_dist_compile_injection.py - cursor/cline variant assertions appended
- tests/test_install_sync_with_source.py - cursor joins injected-sync; cline documented exclusion
- qor/hosts.py - `_cursor_target`, `_cline_target`, registry entries
- qor/scripts/dist_compile.py - TARGETS + emit_cursor + emit_cline dispatch
- qor/dist/ - recompiled (two new variant trees)

### Changes

hosts.py: two factories following the existing `_scoped_base` pattern; cline's install_map uses the `workflows/` prefix (gemini's `commands/` precedent). dist_compile: TARGETS becomes six; emit_cursor delegates to emit_claude then `_rewrite_risk_skills`; emit_cline writes flattened `command-<name>.md` / `agent-<name>.md` files with byte-preserving injection for risk skills.

### Unit Tests

- tests/test_hosts_cursor_cline.py - test_cursor_repo_scope / test_cline_repo_scope: resolve() returns the `.cursor` / `.clinerules` bases with the right install maps (red today)
- tests/test_hosts_cursor_cline.py - test_cline_no_skills_prefix: cline's map has only `workflows/` (mirrors gemini's shape test)
- tests/test_dist_compile_injection.py - test_compile_all_cursor_and_cline_variants: compile_all over the real corpus -> cursor risk skill carries NR-001/NR-002 and non-risk skill byte-equals source; cline `workflows/command-qor-audit.md` exists and carries the rules; cline command count covers every skill dir + loose skill (red today)

## Feature Inventory Touches

(empty -- security lint + distribution tooling; no src/ features)

## Definition of Done

### Deliverable 1: code-span-aware canary gate

- **D1**: Technical plans can legitimately discuss CLI placeholders and countermeasure examples inside code spans without a false ABORT, while every imperative-instruction canary stays binding everywhere (GH #244 item 1).
- **D2**: `--strict` flag + hidden-html code-span downgrade in qor/scripts/prompt_injection_canaries.py `main()`; `scan()` unchanged.
- **D3**: Ledger entries for plan/audit/implement/seal; CHANGELOG feature entry.
- **D4**: The four Phase 1 tests observe exit codes and stderr, red-then-green twice.

### Deliverable 2: cursor + cline adapter targets

- **D1**: Qor-logic installs into the two highest-adjacency assistant layouts from the published adapter matrix (GH #244 item 2), widening reach at low design cost.
- **D2**: `_cursor_target`/`_cline_target` in qor/hosts.py; TARGETS six-wide; both variants carry the Phase 187 risk-skill injection; check_variant_drift green after recompile.
- **D3**: Sync contracts extended (cursor in the injected-sync loop; cline documented exclusion + content tests).
- **D4**: test_compile_all_cursor_and_cline_variants observes compiled artifacts, red-then-green twice.

## CI Commands

- `python -m pytest tests/test_prompt_injection_canary.py tests/test_hosts_cursor_cline.py tests/test_dist_compile_injection.py tests/test_install_sync_with_source.py tests/test_compile.py -q` - focused suites (run twice for determinism)
- `python -m qor.scripts.check_variant_drift` - dist matches regeneration after recompile
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity
