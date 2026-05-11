# Plan: Phase 53 — Prompt compiler execution modes

**change_class**: feature

**doc_tier**: system

**originating_remediation**: GH #39 sub-phase 4 (per docs/roadmap-prompt-compiler.md)

**terms_introduced**:
- term: compile_plan
  home: qor/compiler/execution_modes.py
- term: compile_compare
  home: qor/compiler/execution_modes.py
- term: ExecutionMode
  home: qor/compiler/execution_modes.py
- term: PlanResult
  home: qor/compiler/execution_modes.py

**boundaries**:
- limitations:
  - V1 ships ONE provider compiler upstream (AnthropicCompiler from Phase 50). `compile_compare` and `compile_plan` work mechanically with multiple providers, but the registry must be extended before they produce meaningful multi-provider output. Tests use ad-hoc fake compilers via monkeypatch.
  - `compile_plan` accepts a tuple of `TargetProfile`s; each target compiles once. No deduplication; caller controls.
  - `compile_compare` is explicit-opt-in and labels output as `mode="compare"` for cost-awareness traceability.
- non_goals:
  - Cost estimation. Phase 54 evaluation loop is its own concern.
  - Latency budgeting.

## Open Questions
None.

## Phase 1: execution_modes module

### Affected Files
- `qor/compiler/execution_modes.py` — NEW.
- `qor/compiler/__init__.py` — re-export `compile_plan`, `compile_compare`, `PlanResult`.
- `tests/test_compiler_execution_modes.py` — NEW.

### Changes
Public surface:

```python
@dataclass(frozen=True)
class PlanResult:
    mode: str                              # "single_target" | "execution_plan" | "compare"
    compiled: tuple[CompiledPrompt, ...]
    targets: tuple[TargetProfile, ...]

def compile_plan(raw_prompt: str, plan: tuple[TargetProfile, ...]) -> PlanResult: ...
def compile_compare(raw_prompt: str, providers: tuple[str, ...]) -> PlanResult: ...
```

`compile_plan` runs `compile_prompt` once per target in order; preserves target order. `compile_compare` constructs `TargetProfile(provider=p)` for each provider and runs through. Both raise `ValueError` when targets/providers list is empty or contains an unsupported provider.

### Unit Tests
- `test_plan_result_is_frozen`
- `test_compile_plan_empty_targets_raises`
- `test_compile_plan_single_target_returns_one_compiled`
- `test_compile_plan_two_targets_with_fake_provider_runs_both` (monkeypatch a fake openai compiler)
- `test_compile_plan_preserves_target_order`
- `test_compile_plan_unsupported_provider_raises`
- `test_compile_compare_empty_providers_raises`
- `test_compile_compare_runs_each_provider_once` (monkeypatch openai compiler)
- `test_compile_compare_labels_mode_as_compare`
- `test_single_target_compile_prompt_unaffected_by_execution_modes_module`

## Phase 2: doctrine + roadmap

### Affected Files
- `docs/roadmap-prompt-compiler.md` — mark Phase 53 done.
- `qor/references/doctrine-prompt-compilation.md` — V1 scope: enumerate three modes.
- `tests/test_roadmap_phase_53_marked_done.py` — NEW.

## CI Commands
- `python -m pytest tests/test_compiler_execution_modes.py tests/test_roadmap_phase_53_marked_done.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
