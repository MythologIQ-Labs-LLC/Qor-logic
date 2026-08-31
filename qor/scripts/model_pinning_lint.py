"""Retired model-admission metadata lint and fabrication-risk guard.

Phase 240 makes execution-context capability evidence authoritative and removes
named-model admission from live Qor skills. This module name remains temporarily
for command compatibility, but it no longer contains a model-family allowlist or
vendor-specific capability ladder.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import execution_context


RETIRED_MODEL_FIELDS: tuple[str, ...] = (
    "model_compatibility",
    "min_model_capability",
)

_FABRICATION_RISK_SKILLS = {"qor-audit", "qor-plan", "qor-substantiate"}
_GUARD_POINTER = "doctrine-negative-constraints"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


@dataclass(frozen=True)
class ModelPinningWarning:
    skill: str
    reason: str


def _frontmatter(text: str) -> str:
    match = _FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def _retired_fields(frontmatter: str) -> tuple[str, ...]:
    found: list[str] = []
    for field in RETIRED_MODEL_FIELDS:
        if re.search(rf"^{re.escape(field)}\s*:", frontmatter, re.MULTILINE):
            found.append(field)
    return tuple(found)


def _check_retired_model_fields(skill_path: Path) -> ModelPinningWarning | None:
    text = skill_path.read_text(encoding="utf-8", errors="replace")
    fields = _retired_fields(_frontmatter(text))
    if not fields:
        return None
    return ModelPinningWarning(
        skill=skill_path.parent.name,
        reason=(
            "live skill carries retired named-model admission metadata: "
            + ", ".join(fields)
        ),
    )


def _check_fabrication_guard(skill_path: Path) -> ModelPinningWarning | None:
    skill_name = skill_path.parent.name
    if skill_name not in _FABRICATION_RISK_SKILLS:
        return None
    text = skill_path.read_text(encoding="utf-8", errors="replace")
    if _GUARD_POINTER in text:
        return None
    return ModelPinningWarning(
        skill=skill_name,
        reason=(
            "fabrication-risk skill lacks the negative-constraints pointer; "
            "add the doctrine-negative-constraints reference line"
        ),
    )


def check(
    repo_root: Path,
    *,
    current_model: str | None = None,
) -> list[ModelPinningWarning]:
    """Return live-corpus migration and fabrication-risk warnings.

    ``current_model`` is accepted only for CLI/caller compatibility. Model
    identity does not affect the result and cannot grant or deny authority.
    """
    del current_model
    warnings: list[ModelPinningWarning] = []
    for skill in (repo_root / "qor" / "skills").rglob("SKILL.md"):
        retired = _check_retired_model_fields(skill)
        if retired:
            warnings.append(retired)
        guard = _check_fabrication_guard(skill)
        if guard:
            warnings.append(guard)
    return warnings


def scan_with_errors(repo_root: Path) -> tuple[list[dict], list[str]]:
    """Scan every execution contract, accumulating per-skill errors instead of
    raising: ``load_contract`` raises ``ValueError`` on the first malformed
    contract, and the prior path caught it and returned -- one bad
    ``rendering_recipes`` value silently suppressed inspection of every
    remaining skill while still exiting 0 (Phase 240 iteration-2 audit)."""
    active = execution_context.detect_context()
    results: list[dict] = []
    errors: list[str] = []
    for path in sorted((repo_root / "qor" / "skills").rglob("SKILL.md")):
        try:
            contract = execution_context.load_contract(path)
        except ValueError as exc:
            errors.append(f"{path.parent.name}: {exc}")
            continue
        if contract is not None:
            results.append(execution_context.inspect_contract(contract, active))
    return results, errors


def _print_execution_context(repo_root: Path) -> None:
    try:
        results, errors = scan_with_errors(repo_root)
    except ImportError as exc:
        print(f"WARN [execution-context]: inspection unavailable: {exc}", file=sys.stderr)
        return
    for error in errors:
        # Phase 240 iteration-2 audit: a malformed contract is reported per
        # skill; it no longer aborts inspection of the remaining corpus.
        print(f"WARN [execution-context]: malformed contract: {error}", file=sys.stderr)
    unverified = sum(len(row["unverified_hard_requirements"]) for row in results)
    missing = sum(len(row["missing_hard_requirements"]) for row in results)
    print(
        f"INFO [execution-context]: {len(results)} contracts; "
        f"{missing} missing, {unverified} unverified hard requirements"
        + (f"; {len(errors)} malformed contract(s)" if errors else ""),
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.model_pinning_lint")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--current-model", type=str, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root or Path.cwd()

    _print_execution_context(repo_root)
    warnings = check(repo_root, current_model=args.current_model)
    for warning in warnings:
        print(
            f"WARN [model-admission-retired] {warning.skill}: {warning.reason}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
