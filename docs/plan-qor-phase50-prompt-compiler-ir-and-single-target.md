# Plan: Phase 50 — Prompt compiler V1 (canonical IR + single-target compile)

**change_class**: feature

**doc_tier**: system

**originating_remediation**: closes GH #39 sub-phase 1 (Architecture Proposal: Target-Aware Governed Prompt Compilation)

**terms_introduced**:
- term: PromptIR
  home: qor/compiler/types.py
- term: ParsedIntent
  home: qor/compiler/types.py
- term: TargetProfile
  home: qor/compiler/types.py
- term: CompiledPrompt
  home: qor/compiler/types.py
- term: ProviderCompiler
  home: qor/compiler/protocol.py
- term: parse_intent
  home: qor/compiler/intent_parser.py
- term: compile_prompt
  home: qor/compiler/compile.py
- term: AnthropicCompiler
  home: qor/compiler/providers/anthropic.py
- term: single-target compile mode
  home: qor/references/doctrine-prompt-compilation.md

**boundaries**:
- limitations:
  - V1 ships single-target compile mode only. Execution-plan mode (multi-provider per execution plan) and compare mode (explicit benchmarking) deferred to Phase 53.
  - V1 governance is OUT OF SCOPE; `compile_prompt` does NOT invoke a governance gate. Phase 51 adds the gate before provider compilation.
  - V1 rulepacks are inline-constant in `AnthropicCompiler` source. Versioned rulepack registry deferred to Phase 52.
  - V1 evaluation loop is OUT OF SCOPE. Compiled prompts are returned to the caller; no output validation. Phase 54 adds `OutputContract` validation.
  - V1 intent parser is a stdlib regex heuristic: task_type from a 6-keyword whitelist; explicit_constraints from lines starting with "must"/"do not"/"avoid"/"no"; user_goal is the remainder. Implicit constraints, required_outputs, context_dependencies, ambiguity_flags, risk_hints are populated as empty tuples in V1.
  - V1 ships ONE provider compiler (`AnthropicCompiler`). OpenAI / Google compilers deferred to Phase 51+.
  - V1 `AnthropicCompiler` does NOT call the Anthropic API. It returns a CompiledPrompt object with system_prompt + user_prompt strings; the caller invokes the API. The compiler is pure (no I/O) for testability.
- non_goals:
  - Bridging to a runtime execution layer (`anthropic.Anthropic()` client). The compiler emits prompts; execution is the caller's concern.
  - Cost estimation or latency budgeting. Deferred to Phase 53 execution-plan mode.
  - Streaming or tool-use orchestration. Phase 50 emits a single static CompiledPrompt.
- exclusions:
  - No new runtime dependencies. Stdlib dataclasses + typing.Protocol only.
  - No changes to existing skill bodies (`qor-plan`, `qor-audit`, `qor-implement`, `qor-substantiate`). Phase 50 is a greenfield package; lifecycle wiring (if any) lands in Phase 51+.
  - No CLI for `compile_prompt`. Library API only; CLI deferred until evaluation loop (Phase 54) makes end-to-end useful.

## Open Questions

None at submission. The 5 open questions in the issue body (first-provider choice, governance hooks, JSON serialization, content hash, cost estimation) are deferred to subsequent phases per the boundaries above.

---

## Phase 1: Compiler types + intent parser + provider protocol

### Affected Files

- `qor/compiler/__init__.py` — NEW. Package marker; re-exports `compile_prompt`, public types.
- `qor/compiler/types.py` — NEW. Frozen dataclasses: `OutputContract`, `ContextContract`, `ToolContract`, `EvaluationContract`, `GovernanceContract`, `ParsedIntent`, `PromptIR`, `TargetProfile`, `CompiledPrompt`. Stdlib-only. All collections are tuples (immutable).
- `qor/compiler/intent_parser.py` — NEW. `parse_intent(raw_prompt: str) -> ParsedIntent`. Stdlib regex heuristic; populates task_type from a closed 6-keyword vocabulary + user_goal + explicit_constraints; leaves implicit fields as empty tuples in V1.
- `qor/compiler/protocol.py` — NEW. `ProviderCompiler` typing.Protocol with one method `compile(prompt_ir: PromptIR, target: TargetProfile) -> CompiledPrompt`. No rulepack argument in V1 (registry is Phase 52).
- `tests/test_compiler_types.py` — NEW.
- `tests/test_intent_parser.py` — NEW.
- `tests/test_compiler_protocol.py` — NEW.

### Changes

**`qor/compiler/types.py`** — V1 surface (all frozen dataclasses):

```python
@dataclass(frozen=True)
class OutputContract:
    format: str = "markdown"        # "markdown" | "json" | "text"
    schema: str | None = None        # JSON schema as string when format == "json"

@dataclass(frozen=True)
class ContextContract:
    must_include: tuple[str, ...] = ()
    must_exclude: tuple[str, ...] = ()

@dataclass(frozen=True)
class ToolContract:
    allowed: tuple[str, ...] = ()
    denied: tuple[str, ...] = ()

@dataclass(frozen=True)
class EvaluationContract:
    success_criteria: tuple[str, ...] = ()

@dataclass(frozen=True)
class GovernanceContract:
    # V1 placeholder; populated by Phase 51's governance gate.
    risk_level: str = "unknown"     # "low" | "medium" | "high" | "blocked" | "unknown"
    required_controls: tuple[str, ...] = ()

@dataclass(frozen=True)
class ParsedIntent:
    task_type: str                  # closed vocabulary; see TASK_TYPES
    user_goal: str
    explicit_constraints: tuple[str, ...] = ()
    implicit_constraints: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()
    context_dependencies: tuple[str, ...] = ()
    ambiguity_flags: tuple[str, ...] = ()
    risk_hints: tuple[str, ...] = ()

@dataclass(frozen=True)
class PromptIR:
    intent: ParsedIntent
    output_contract: OutputContract = OutputContract()
    context_contract: ContextContract = ContextContract()
    tool_contract: ToolContract = ToolContract()
    governance_contract: GovernanceContract = GovernanceContract()
    evaluation_contract: EvaluationContract = EvaluationContract()

@dataclass(frozen=True)
class TargetProfile:
    provider: str                    # "anthropic" (V1); "openai" | "google" in V2+
    model: str | None = None
    role: str | None = None

@dataclass(frozen=True)
class CompiledPrompt:
    provider: str
    model: str | None
    system_prompt: str
    user_prompt: str
    output_format: str               # mirrors OutputContract.format
    tool_instructions: tuple[str, ...] = ()
    governance_annotations: tuple[str, ...] = ()

TASK_TYPES: tuple[str, ...] = (
    "draft", "implement", "review", "analyze", "explain", "summarize",
)
```

**`qor/compiler/intent_parser.py`** — V1 heuristic:

- Lowercase the prompt; scan for any leading TASK_TYPES verb (first word match); fall back to `"draft"` when none match.
- Split prompt on sentence boundaries (`. ` or newlines); collect lines whose lowercase starts with `must`, `do not`, `no `, `avoid `, `cannot ` as `explicit_constraints`.
- `user_goal` = the original prompt with the first task-type verb stripped (if present), trimmed.
- All other ParsedIntent fields populated as empty tuples in V1.

```python
def parse_intent(raw_prompt: str) -> ParsedIntent: ...
```

**`qor/compiler/protocol.py`** — V1 Protocol:

```python
from typing import Protocol

class ProviderCompiler(Protocol):
    provider_name: str
    def compile(self, prompt_ir: PromptIR, target: TargetProfile) -> CompiledPrompt: ...
```

### Unit Tests

- `tests/test_compiler_types.py`:
  - `test_prompt_ir_is_frozen_dataclass` — assigning to a field raises `dataclasses.FrozenInstanceError`.
  - `test_parsed_intent_defaults_implicit_fields_to_empty_tuples`.
  - `test_target_profile_requires_provider_field`.
  - `test_compiled_prompt_exposes_provider_and_prompts`.
  - `test_governance_contract_default_is_unknown_risk` — asserts default `risk_level == "unknown"` (Phase 51 will replace).
  - `test_task_types_is_closed_6_value_tuple`.

- `tests/test_intent_parser.py`:
  - `test_parse_intent_detects_draft_verb` — "Draft a migration plan" → `task_type == "draft"`.
  - `test_parse_intent_detects_implement_verb`.
  - `test_parse_intent_detects_review_verb`.
  - `test_parse_intent_falls_back_to_draft_when_no_keyword_matches` — "Hello there" → `task_type == "draft"` (default).
  - `test_parse_intent_extracts_explicit_must_constraints` — "Do this. Must not use eval()." → constraint captured.
  - `test_parse_intent_extracts_do_not_constraints`.
  - `test_parse_intent_extracts_avoid_constraints`.
  - `test_parse_intent_user_goal_strips_leading_verb` — "Draft a plan" → `user_goal == "a plan"`.
  - `test_parse_intent_leaves_v1_deferred_fields_empty` — required_outputs / context_dependencies / ambiguity_flags / risk_hints all `()`.

- `tests/test_compiler_protocol.py`:
  - `test_protocol_satisfied_by_class_with_provider_name_and_compile_method` — declares a fake class that implements the protocol; asserts `isinstance` works under `runtime_checkable` OR (V1) just that calling `.compile()` returns a CompiledPrompt.

---

## Phase 2: Anthropic provider compiler + single-target compile API

### Affected Files

- `qor/compiler/providers/__init__.py` — NEW. Package marker.
- `qor/compiler/providers/anthropic.py` — NEW. `AnthropicCompiler` class implementing `ProviderCompiler`. Pure function (no I/O).
- `qor/compiler/compile.py` — NEW. `compile_prompt(raw_prompt, target, *, output_format="markdown", explicit_tools=(), denied_tools=())` end-to-end API: parses intent → builds PromptIR → resolves target → dispatches to provider compiler → returns CompiledPrompt.
- `qor/compiler/__init__.py` — re-exports `compile_prompt` + types.
- `tests/test_anthropic_compiler.py` — NEW.
- `tests/test_compile_prompt_single_target.py` — NEW.

### Changes

**`qor/compiler/providers/anthropic.py`**:

- `AnthropicCompiler` class; `provider_name = "anthropic"`.
- `compile(prompt_ir, target)`: builds system_prompt + user_prompt strings from PromptIR fields. V1 template:
  - `system_prompt`: brief preamble naming the task_type + a "Constraints" section enumerating `explicit_constraints` when non-empty + an "Output format" line keyed to `output_contract.format`.
  - `user_prompt`: the `intent.user_goal` verbatim. No prompt rewriting.
- `model` from `target.model` (no default; caller responsible).
- `tool_instructions`: empty tuple in V1 (tool-use orchestration is V2+).
- `governance_annotations`: one annotation line citing `governance_contract.risk_level` for traceability even when V1 default is `"unknown"`.

**`qor/compiler/compile.py`** — V1 single-target API:

```python
def compile_prompt(
    raw_prompt: str,
    target: TargetProfile,
    *,
    output_format: str = "markdown",
    explicit_tools: tuple[str, ...] = (),
    denied_tools: tuple[str, ...] = (),
) -> CompiledPrompt:
    """Parse intent, build IR, dispatch to provider compiler, return CompiledPrompt.
    V1 single-target mode only; ValueError on unsupported provider."""
    ...

_PROVIDERS: dict[str, type[ProviderCompiler]] = {
    "anthropic": AnthropicCompiler,
}
```

`ValueError` raised when `target.provider` not in `_PROVIDERS`. Operator-facing message names the unsupported provider and lists supported ones.

### Unit Tests

- `tests/test_anthropic_compiler.py`:
  - `test_anthropic_provider_name_is_anthropic_literal`.
  - `test_anthropic_compile_returns_compiled_prompt_with_provider_set`.
  - `test_anthropic_compile_model_propagates_from_target`.
  - `test_anthropic_system_prompt_includes_task_type` — "implement" task → system_prompt contains "implement" in some form.
  - `test_anthropic_system_prompt_lists_explicit_constraints` — PromptIR with two constraints → both appear in system_prompt.
  - `test_anthropic_system_prompt_includes_output_format_line` — `output_contract.format == "json"` → system_prompt mentions JSON.
  - `test_anthropic_user_prompt_equals_intent_user_goal_verbatim`.
  - `test_anthropic_governance_annotation_cites_risk_level` — `risk_level == "unknown"` (V1 default) appears in governance_annotations.
  - `test_anthropic_compile_is_pure_no_api_call` — patch `anthropic` module not imported by the compiler module (assert `sys.modules` does not contain `anthropic` after import).

- `tests/test_compile_prompt_single_target.py`:
  - `test_compile_prompt_with_anthropic_target_returns_compiled_prompt`.
  - `test_compile_prompt_propagates_raw_prompt_into_user_prompt` — round-trip the user_goal field.
  - `test_compile_prompt_attaches_explicit_tools_to_tool_contract` — V1 stores them on IR but emits empty tool_instructions (deferred).
  - `test_compile_prompt_raises_value_error_on_unknown_provider` — `TargetProfile(provider="openai", ...)` → `ValueError`.
  - `test_compile_prompt_does_not_invoke_other_provider_compilers` — registers a fake OpenAICompiler in `_PROVIDERS`; asserts its `compile()` is NOT called when target is anthropic (closes the issue body's central concern about wasteful multi-provider work).
  - `test_compile_prompt_default_output_format_is_markdown`.

---

## Phase 3: Doctrine + roadmap + audit-skill cross-reference

### Affected Files

- `qor/references/doctrine-prompt-compilation.md` — NEW. Defines the compiler architecture, V1 scope, V2+ deferrals.
- `docs/roadmap-prompt-compiler.md` — NEW. Maps issue #39 to Phase 50 (V1 done) → Phase 51 (governance gate) → Phase 52 (rulepack registry) → Phase 53 (execution modes) → Phase 54 (evaluation loop).
- `qor/skills/governance/qor-audit/SKILL.md` — single-line cross-reference under the existing Macro-Level Architecture pass noting that prompt-compiler subsystem is governed by `doctrine-prompt-compilation.md` and its V1 scope is intentionally narrow.
- `tests/test_doctrine_prompt_compilation_present.py` — NEW.
- `tests/test_roadmap_prompt_compiler_present.py` — NEW.

### Changes

**`qor/references/doctrine-prompt-compilation.md`** — top-level sections:

- §"Architecture": parse intent → canonical PromptIR → (governance gate, Phase 51) → resolve target → provider-specific compile → return CompiledPrompt → (evaluation, Phase 54).
- §"V1 scope (Phase 50)": IR + ParsedIntent + TargetProfile + ProviderCompiler protocol + AnthropicCompiler + single-target compile API. No governance gate. No registry. No execution modes. No evaluation loop. One provider.
- §"V2+ deferrals": maps each deferred concern to a phase placeholder (51-54).
- §"Anti-pattern: parallel provider compile by default": cites the issue body's central concern. Single-target mode is the default; compare mode is an opt-in for benchmarking only.
- §"Stdlib-only discipline": no Pydantic; frozen dataclasses + manual validation per existing framework convention.

**`docs/roadmap-prompt-compiler.md`** — table format:

| Phase | Sub-phase | Deliverables | Status |
|---|---|---|---|
| 50 | IR + single-target | types, parser, protocol, AnthropicCompiler, compile_prompt | THIS PHASE |
| 51 | Governance gate | GovernanceGate, GovernanceDecision, policies | queued |
| 52 | Rulepack registry | versioned per-provider rulepacks, registry loader | queued |
| 53 | Execution modes | single_target (Phase 50) / execution_plan / compare | queued |
| 54 | Evaluation loop | OutputContract validation, drift comparison, feedback records | queued |

**`qor-audit` SKILL.md** — append to Macro-Level Architecture pass:

```
- [ ] If the plan touches `qor/compiler/`, verify it advances the roadmap in `docs/roadmap-prompt-compiler.md` (does not regress earlier sub-phases). Per `qor/references/doctrine-prompt-compilation.md`.
```

### Unit Tests

- `tests/test_doctrine_prompt_compilation_present.py`:
  - `test_doctrine_file_exists`.
  - `test_doctrine_declares_v1_scope_section`.
  - `test_doctrine_declares_v2_plus_deferrals_section`.
  - `test_doctrine_states_stdlib_only_discipline`.
  - `test_doctrine_cites_anti_pattern_parallel_provider_compile_by_default`.

- `tests/test_roadmap_prompt_compiler_present.py`:
  - `test_roadmap_file_exists`.
  - `test_roadmap_lists_phases_50_to_54`.
  - `test_roadmap_marks_phase_50_as_current`.
  - `test_roadmap_cites_governance_rulepack_modes_evaluation_per_phase`.

---

## CI Commands

- `python -m pytest tests/test_compiler_types.py tests/test_intent_parser.py tests/test_compiler_protocol.py -v`
- `python -m pytest tests/test_anthropic_compiler.py tests/test_compile_prompt_single_target.py -v`
- `python -m pytest tests/test_doctrine_prompt_compilation_present.py tests/test_roadmap_prompt_compiler_present.py -v`
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py`
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase50-prompt-compiler-ir-and-single-target.md`
- `python -m qor.scripts.pipeline_inversion_lint --repo-root qor/compiler/`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md`
