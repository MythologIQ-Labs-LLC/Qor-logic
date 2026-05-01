"""Model-pinning frontmatter lint (Phase 55).

Walks ``qor/skills/**/SKILL.md``; reads each frontmatter for
``model_compatibility`` and ``min_model_capability``; compares declared
minimum-capability tier against the harness-supplied current model
(``QOR_MODEL_FAMILY`` env or ``--current-model`` argv).

Maps to OWASP LLM05 (Supply Chain — model-pinning) and NIST AI RMF GV-6.1
(third-party AI risk).

WARN-only (Phase 54-style declarative-only rollout); Phase 56+ may promote
to ABORT.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# Canonical capability tier ordering. Lower index = lower capability.
_CAPABILITY_ORDER: tuple[str, ...] = ("haiku", "sonnet", "opus")

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_LIST_KEY_RE = re.compile(
    r"^model_compatibility\s*:\s*\[([^\]]*)\]",
    re.MULTILINE,
)
_MIN_KEY_RE = re.compile(
    r"^min_model_capability\s*:\s*(\S+)",
    re.MULTILINE,
)
_TIER_RE = re.compile(r"claude-(haiku|sonnet|opus)-")


@dataclass(frozen=True)
class ModelPinningWarning:
    skill: str
    declared_min: str | None
    declared_compatibility: tuple[str, ...]
    current_model: str | None
    reason: str


def extract_capability_tier(model_family: str | None) -> str | None:
    """Extract capability tier from a model family string."""
    if not model_family:
        return None
    match = _TIER_RE.search(model_family)
    return match.group(1) if match else None


def _parse_pinning_keys(frontmatter: str) -> tuple[tuple[str, ...], str | None]:
    list_match = _LIST_KEY_RE.search(frontmatter)
    compatibility: tuple[str, ...] = tuple()
    if list_match:
        compatibility = tuple(
            s.strip() for s in list_match.group(1).split(",") if s.strip()
        )
    min_match = _MIN_KEY_RE.search(frontmatter)
    min_capability = min_match.group(1).strip() if min_match else None
    return compatibility, min_capability


def _check_one_skill(
    skill_path: Path, current_model: str | None,
) -> ModelPinningWarning | None:
    text = skill_path.read_text(encoding="utf-8", errors="replace")
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return None
    compatibility, min_capability = _parse_pinning_keys(fm_match.group(1))
    if min_capability is None and not compatibility:
        return None  # skill not in scoped pinning set
    if not current_model:
        return None  # cannot warn without known model

    current_tier = extract_capability_tier(current_model)
    if current_tier is None:
        return None  # unknown model family; skip lint

    skill_name = skill_path.parent.name
    if min_capability and min_capability in _CAPABILITY_ORDER:
        if _CAPABILITY_ORDER.index(current_tier) < _CAPABILITY_ORDER.index(min_capability):
            return ModelPinningWarning(
                skill=skill_name, declared_min=min_capability,
                declared_compatibility=compatibility, current_model=current_model,
                reason=f"current model tier {current_tier!r} < declared min {min_capability!r}",
            )
    if compatibility and current_model not in compatibility:
        return ModelPinningWarning(
            skill=skill_name, declared_min=min_capability,
            declared_compatibility=compatibility, current_model=current_model,
            reason=f"current model {current_model!r} not in compatibility list {list(compatibility)}",
        )
    return None


def check(
    repo_root: Path, *, current_model: str | None = None,
) -> list[ModelPinningWarning]:
    """Walk skills; emit warnings for pinning mismatches."""
    if current_model is None:
        current_model = os.environ.get("QOR_MODEL_FAMILY")
    skills_dir = repo_root / "qor" / "skills"
    warnings: list[ModelPinningWarning] = []
    for skill in skills_dir.rglob("SKILL.md"):
        warning = _check_one_skill(skill, current_model)
        if warning:
            warnings.append(warning)
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.model_pinning_lint")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--current-model", type=str, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path.cwd()
    warnings = check(repo_root, current_model=args.current_model)
    if not warnings:
        return 0
    for w in warnings:
        print(
            f"WARN [model-pinning] {w.skill}: {w.reason}",
            file=sys.stderr,
        )
    return 0  # WARN-only per Open Question 3 default


if __name__ == "__main__":
    raise SystemExit(main())
