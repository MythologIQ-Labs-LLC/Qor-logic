# Doctrine: Prompt Compilation (target-aware)

`qor/compiler/` is the prompt-compilation subsystem. It treats prompt generation as a deterministic compilation pipeline: parse intent → canonical `PromptIR` → (Phase 51 governance gate) → resolve target → provider-specific compile → return `CompiledPrompt` → (Phase 54 evaluation loop).

Source proposal: GH #39 (Architecture Proposal: Target-Aware Governed Prompt Compilation). Phase 50 implements sub-phase 1.

## Architecture

```
raw prompt
   │
   ▼
parse_intent  ─►  ParsedIntent
                       │
                       ▼
                  build PromptIR  ─►  (Phase 51 governance gate)
                                          │
                                          ▼
                                     resolve target  ─►  TargetProfile
                                                              │
                                                              ▼
                                                       provider compiler  ─►  CompiledPrompt
                                                                                    │
                                                                                    ▼
                                                                            (Phase 54 evaluation)
```

## V1 scope (Phase 50)

Delivered in this phase:

- **Canonical IR types** (`qor/compiler/types.py`): frozen dataclasses for `PromptIR`, `ParsedIntent`, `OutputContract`, `ContextContract`, `ToolContract`, `EvaluationContract`, `GovernanceContract`, `TargetProfile`, `CompiledPrompt`. All collections are tuples (immutable).
- **Intent parser** (`qor/compiler/intent_parser.py`): stdlib regex heuristic. `task_type` from closed 6-keyword vocabulary (`draft`, `implement`, `review`, `analyze`, `explain`, `summarize`); `explicit_constraints` from sentences starting with must / do not / no / avoid / cannot.
- **`ProviderCompiler` protocol** (`qor/compiler/protocol.py`): `typing.Protocol` with `provider_name: str` + `compile(prompt_ir, target) -> CompiledPrompt`.
- **`AnthropicCompiler`** (`qor/compiler/providers/anthropic.py`): pure function (no API I/O). V1 ships ONE provider compiler.
- **`compile_prompt(raw_prompt, target)`** (`qor/compiler/compile.py`): end-to-end single-target API. Raises `ValueError` on unsupported provider. **Never invokes provider compilers other than the targeted one** — this is the structural answer to the anti-pattern named below.

## V2+ deferrals

Each deferred concern maps to a numbered phase:

| Phase | Concern | Status |
|---|---|---|
| 51 | Governance gate: `GovernanceGate.evaluate(ir) -> GovernanceDecision`; raises `GovernanceViolation` when blocked; 4 V1 policies (denied-tool, output-format whitelist, sensitive-data hint, prompt-injection hint); risk levels `low/medium/high/blocked` | DONE v0.51.0 |
| 52 | Rulepack registry: `ProviderRulepack` frozen dataclass + `RulepackRegistry`; Python module format (no YAML in V1) with `instruction_hierarchy`, `formatting_rules`, `anti_patterns`, `examples`; auto-bootstrap anthropic v1 | DONE v0.52.0 |
| 53 | Execution modes: `single_target` (Phase 50 default) + `compile_plan` (execution-plan) + `compile_compare` (explicit benchmarking, mode-labelled `compare`); both new modes are explicit-opt-in | DONE v0.53.0 |
| 54 | Evaluation loop: `validate_output` (json round-trip; markdown/text always accept), `compare_against_intent` (word-overlap drift; configurable threshold), `record_feedback` (JSONL under `.qor/evaluation/<sid>.jsonl`); deterministic, no LLM-as-judge in V1 | DONE v0.54.0 |

`docs/roadmap-prompt-compiler.md` carries the live status.

## Anti-pattern: parallel provider compile by default

GH #39 names a specific anti-pattern: systems that optimize the SAME prompt in parallel for OpenAI / Anthropic / Google and then execute against only one of them waste both compute and design coherence. Phase 50's structural answer:

- `compile_prompt` runs ONE compile path, the one matching `target.provider`.
- Tests cover the negative case: when target is `anthropic`, registering a fake `openai` compiler in `_PROVIDERS` MUST NOT cause that compiler's `compile()` to be called.
- Multi-provider compile becomes an explicit `execution_plan` (Phase 53) or `compare` (Phase 53) mode — never the default.

## Stdlib-only discipline

The framework's other helpers (`host_capability`, `feature_index_verify`, `pipeline_inversion_lint`, `plan_text_consistency_lint`) are stdlib-only. The compiler subsystem follows that discipline:

- `dataclasses` for IR types (frozen, tuples not lists, no Pydantic).
- `typing.Protocol` for `ProviderCompiler`.
- `re` for the intent parser's regex heuristic.
- No new runtime dependency added to `pyproject.toml`.

This keeps the subsystem auditable under existing lint rules and avoids dependency-shape regressions per `SG-Phase24-C` ("reflexive dependency introduction for trivial work").

## Subsystem governance

When a future plan touches `qor/compiler/`, `/qor-audit` Step 3 Macro-Level Architecture pass verifies the plan advances the roadmap: it cannot regress a sealed sub-phase, and it must name the next sub-phase it delivers. See `docs/roadmap-prompt-compiler.md` for the queued sub-phase list.
