# Roadmap: target-aware prompt compiler

Maps GH issue #39 (Architecture Proposal: Target-Aware Governed Prompt Compilation) to a 5-sub-phase implementation. Phase 50 delivers sub-phase 1.

Doctrine: `qor/references/doctrine-prompt-compilation.md`.

## Phase table

| Phase | Sub-phase | Deliverables | Status |
|---|---|---|---|
| 50 | IR + single-target | `qor/compiler/{__init__,types,intent_parser,protocol,compile}.py` + `qor/compiler/providers/anthropic.py` + tests | DONE v0.50.0 (META_LEDGER #153) |
| 51 | Governance gate | `qor/compiler/governance/{gate,policies,decisions}.py`; `GovernanceDecision`; raises `GovernanceViolation` on policy violation; runs before provider compile | DONE v0.51.0 (META_LEDGER #154) |
| 52 | Rulepack registry | `qor/compiler/rulepacks/{__init__,registry}.py` + `qor/compiler/rulepacks/anthropic/v1.py`; `ProviderRulepack` frozen dataclass; `RulepackRegistry`; auto-bootstrap anthropic v1 | DONE v0.52.0 (META_LEDGER #155) |
| 53 | Execution modes | `compile_plan` (execution-plan mode) + `compile_compare` (benchmarking mode); both explicit-opt-in. `single_target` (Phase 50) remains default. | DONE v0.53.0 (META_LEDGER #156) |
| 54 | Evaluation loop | `validate_output` (format check; json round-trip), `compare_against_intent` (word-overlap drift score; threshold flag), `record_feedback` (JSONL under `.qor/evaluation/<sid>.jsonl`) | DONE v0.54.0 (META_LEDGER #157) |

**Roadmap COMPLETE**: all 5 sub-phases of GH #39 delivered across Phases 50-54. The prompt compiler subsystem is V1-complete. Subsequent enhancements (jsonschema validation, LLM-as-judge evaluation, YAML rulepacks, OpenAI/Google compilers) are out of scope of GH #39 and would file as separate issues.

## Phase 50 acceptance (closed by this seal)

- [x] `PromptIR`, `ParsedIntent`, `TargetProfile`, `CompiledPrompt` frozen dataclasses with tuple collections.
- [x] `parse_intent(raw_prompt) -> ParsedIntent` stdlib regex heuristic.
- [x] `ProviderCompiler` typing.Protocol.
- [x] `AnthropicCompiler` (one provider, pure, no API I/O).
- [x] `compile_prompt(raw_prompt, target) -> CompiledPrompt`; `ValueError` on unsupported provider; other compilers NOT invoked when not targeted.
- [x] Stdlib-only; no Pydantic; no new `pyproject.toml` deps.

## Phase 51+ entry criteria

A subsequent plan touching `qor/compiler/` must:

1. Name the sub-phase it delivers (51 / 52 / 53 / 54).
2. Update this roadmap row's Status column with the sealing version + META_LEDGER entry id.
3. Not regress Phase 50's `compile_prompt(target).provider` invariant: other provider compilers MUST NOT execute when not targeted under single-target mode. Compare and execution-plan modes (Phase 53) are explicit opt-ins.

## Non-goals across all 5 phases

- Bridging to a runtime execution layer (Anthropic/OpenAI/Google SDK client instantiation). The compiler emits prompts; execution is the caller's concern.
- Cost estimation as part of single-target mode. Compare mode (Phase 53) adds cost annotations explicitly.
- Streaming response handling.
