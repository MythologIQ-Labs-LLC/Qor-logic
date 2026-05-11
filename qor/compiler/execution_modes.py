"""Phase 53: prompt compiler execution modes.

Three modes total. `compile_prompt` (Phase 50) is `single_target`. This module
adds:
- `compile_plan(raw_prompt, plan)` — execution-plan mode: caller provides an
  ordered tuple of TargetProfile; each target compiles once.
- `compile_compare(raw_prompt, providers)` — explicit benchmarking mode:
  caller provides a tuple of provider names; each gets a default target
  profile. Labelled `mode="compare"` for cost-awareness traceability.

Both modes are explicit-opt-in. Single-target remains the default for
`compile_prompt`. No mode is invoked implicitly.
"""
from __future__ import annotations

from dataclasses import dataclass

from qor.compiler.compile import compile_prompt
from qor.compiler.types import CompiledPrompt, TargetProfile


@dataclass(frozen=True)
class PlanResult:
    mode: str
    compiled: tuple[CompiledPrompt, ...]
    targets: tuple[TargetProfile, ...]


def compile_plan(
    raw_prompt: str,
    plan: tuple[TargetProfile, ...],
) -> PlanResult:
    if not plan:
        raise ValueError("compile_plan requires at least one TargetProfile")
    compiled = tuple(compile_prompt(raw_prompt, target) for target in plan)
    return PlanResult(mode="execution_plan", compiled=compiled, targets=tuple(plan))


def compile_compare(
    raw_prompt: str,
    providers: tuple[str, ...],
) -> PlanResult:
    if not providers:
        raise ValueError("compile_compare requires at least one provider")
    targets = tuple(TargetProfile(provider=p) for p in providers)
    compiled = tuple(compile_prompt(raw_prompt, target) for target in targets)
    return PlanResult(mode="compare", compiled=compiled, targets=targets)
