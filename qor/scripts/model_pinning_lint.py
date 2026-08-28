"""Legacy model-pinning compatibility shim.

Phase 240 replaces named-model execution authority with execution-context
inspection. Legacy pinning metadata is retained as provenance/deprecation
input only. The independent fabrication-risk doctrine guard remains active.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# Backwards-compatible exports for historical callers. These values no longer
# grant or deny authority to execute a Qor skill.
_CAPABILITY_ORDER: tuple[str, ...] = ("haiku", "sonnet", "opus")
_TIER_RE = re.compile(r"claude-(haiku|sonnet|opus)-")
_FABRICATION_RISK_SKILLS = {"qor-audit", "qor-plan", "qor-substantiate"}
_GUARD_POINTER = "doctrine-negative-constraints"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_LIST_KEY_RE = re.compile(r"^model_compatibility\s*:\s*\[([^\]]*)\]", re.MULTILINE)
_MIN_KEY_RE = re.compile(r"^min_model_capability\s*:\s*(\S+)", re.MULTILINE)


@dataclass(frozen=True)
class ModelPinningWarning:
    skill: str
    declared_min: str | None
    declared_compatibility: tuple[str, ...]
    current_model: str | None
    reason: str


def extract_capability_tier(model_family: str | None) -> str | None:
    """Deprecated helper retained for historical imports and sealed evidence."""
    if not model_family:
        return None
    match = _TIER_RE.search(model_family)
    return match.group(1) if match else None


def _parse_pinning_keys(frontmatter: str) -> tuple[tuple[str, ...], str | None]:
    list_match = _LIST_KEY_RE.search(frontmatter)
    compatibility: tuple[str, ...] = ()
    if list_match:
        compatibility = tuple(
            value.strip() for value in list_match.group(1).split(",") if value.strip()
        )
    min_match = _MIN_KEY_RE.search(frontmatter)
    minimum = min_match.group(1).strip() if min_match else None
    return compatibility, minimum


def _legacy_pin_count(repo_root: Path) -> int:
    count = 0
    for skill in (repo_root / "qor" / "skills").rglob("SKILL.md"):
        text = skill.read_text(encoding="utf-8", errors="replace")
        match = _FRONTMATTER_RE.match(text)
        if not match:
            continue
        compatibility, minimum = _parse_pinning_keys(match.group(1))
        if compatibility or minimum:
            count += 1
    return count


def _check_fabrication_guard(skill_path: Path) -> ModelPinningWarning | None:
    skill_name = skill_path.parent.name
    if skill_name not in _FABRICATION_RISK_SKILLS:
        return None
    text = skill_path.read_text(encoding="utf-8", errors="replace")
    if _GUARD_POINTER in text:
        return None
    return ModelPinningWarning(
        skill=skill_name,
        declared_min=None,
        declared_compatibility=(),
        current_model=None,
        reason=(
            "fabrication-risk skill lacks the negative-constraints pointer; "
            "add the doctrine-negative-constraints reference line"
        ),
    )


def check(
    repo_root: Path, *, current_model: str | None = None,
) -> list[ModelPinningWarning]:
    """Return safety warnings only; model-family mismatches are non-authoritative."""
    del current_model
    warnings: list[ModelPinningWarning] = []
    for skill in (repo_root / "qor" / "skills").rglob("SKILL.md"):
        guard = _check_fabrication_guard(skill)
        if guard:
            warnings.append(guard)
    return warnings


def _print_execution_context(repo_root: Path) -> None:
    try:
        from qor.scripts.execution_context import scan
        results = scan(repo_root)
    except (ImportError, ValueError) as exc:
        print(f"WARN [execution-context]: inspection unavailable: {exc}", file=sys.stderr)
        return
    unverified = sum(len(row["unverified_hard_requirements"]) for row in results)
    missing = sum(len(row["missing_hard_requirements"]) for row in results)
    print(
        f"INFO [execution-context]: {len(results)} contracts; "
        f"{missing} missing, {unverified} unverified hard requirements",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.model_pinning_lint")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--current-model", type=str, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root or Path.cwd()
    legacy_count = _legacy_pin_count(repo_root)
    if legacy_count:
        print(
            f"WARN [model-pinning]: {legacy_count} skill(s) still carry legacy model "
            "metadata; it is advisory provenance only, not execution authority",
            file=sys.stderr,
        )
    _print_execution_context(repo_root)
    warnings = check(repo_root, current_model=args.current_model or os.getenv("QOR_MODEL_FAMILY"))
    for warning in warnings:
        print(f"WARN [model-pinning]: {warning.skill}: {warning.reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
