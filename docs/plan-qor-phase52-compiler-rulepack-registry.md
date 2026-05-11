# Plan: Phase 52 — Prompt compiler rulepack registry

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #39 sub-phase 3 (per docs/roadmap-prompt-compiler.md)

**terms_introduced**:
- term: ProviderRulepack
  home: qor/compiler/rulepacks/__init__.py
- term: RulepackRegistry
  home: qor/compiler/rulepacks/registry.py
- term: anthropic rulepack v1
  home: qor/compiler/rulepacks/anthropic/v1.py

**boundaries**:
- limitations:
  - V1 rulepacks are Python modules (frozen dataclass instances) rather than YAML/JSON files. Stdlib-only discipline; no YAML parser dependency. V2 can add a YAML loader if operators need editable rulepacks without code changes.
  - One rulepack per provider in V1. Multi-version coexistence (v1, v2 side-by-side) deferred to a later phase.
  - Registry is process-local. Hot-reload deferred.
- non_goals:
  - Network fetch of provider documentation. Rulepacks are local and versioned.
  - Per-tenant rulepacks. Single global rulepack per provider in V1.

## Open Questions
None.

## Phase 1: rulepack types + registry

### Affected Files
- `qor/compiler/rulepacks/__init__.py` — NEW. `ProviderRulepack` frozen dataclass + re-exports.
- `qor/compiler/rulepacks/registry.py` — NEW. `RulepackRegistry` with `register`, `get`, `list_providers`.
- `qor/compiler/rulepacks/anthropic/__init__.py` — NEW.
- `qor/compiler/rulepacks/anthropic/v1.py` — NEW. Concrete `ANTHROPIC_V1` rulepack instance.
- `tests/test_compiler_rulepacks.py` — NEW.

### Changes
`ProviderRulepack` fields: `provider: str`, `version: str`, `instruction_hierarchy: tuple[str,...]`, `formatting_rules: tuple[str,...]`, `anti_patterns: tuple[str,...]`, `examples: tuple[str,...]`.

`RulepackRegistry` is a small registry singleton instance auto-populated with `ANTHROPIC_V1` at import.

### Unit Tests
- `test_provider_rulepack_is_frozen`
- `test_anthropic_v1_rulepack_loads_with_expected_provider_and_version`
- `test_anthropic_v1_rulepack_has_at_least_one_formatting_rule`
- `test_registry_get_returns_registered_rulepack`
- `test_registry_get_raises_on_unknown_provider`
- `test_registry_list_providers_includes_anthropic`

## Phase 2: AnthropicCompiler consumes rulepack

### Affected Files
- `qor/compiler/providers/anthropic.py` — accept optional `rulepack: ProviderRulepack`; default loaded from registry. Inject instruction_hierarchy lines into system_prompt after the task preamble.
- `qor/compiler/compile.py` — pass rulepack from registry into provider compiler.
- `tests/test_anthropic_compiler_with_rulepack.py` — NEW.

### Changes
`AnthropicCompiler.compile(prompt_ir, target, rulepack=None)`. When rulepack is None, fetches `ANTHROPIC_V1` from the registry. System prompt now includes an "Instruction hierarchy:" section after the preamble when the rulepack supplies one.

### Unit Tests
- `test_anthropic_default_rulepack_is_v1`
- `test_system_prompt_includes_instruction_hierarchy_lines_from_rulepack`
- `test_system_prompt_includes_formatting_rules_from_rulepack`
- `test_explicit_rulepack_override_is_respected`
- `test_compile_prompt_uses_registry_lookup_when_rulepack_unspecified`

## Phase 3: doctrine + roadmap update

### Affected Files
- `docs/roadmap-prompt-compiler.md` — mark Phase 52 done.
- `qor/references/doctrine-prompt-compilation.md` — update §V2+ deferrals row.
- `tests/test_roadmap_phase_52_marked_done.py` — NEW.

## CI Commands
- `python -m pytest tests/test_compiler_rulepacks.py tests/test_anthropic_compiler_with_rulepack.py tests/test_roadmap_phase_52_marked_done.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
