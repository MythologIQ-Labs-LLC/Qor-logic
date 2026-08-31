"""Execution-context inspection and bounded rendering for Qor skills.

Model identity is provenance, not authority. This module combines observable
host/runtime facts with skill execution requirements and selects one bounded
presentation recipe without changing governance semantics.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import yaml


RENDER_RECIPES = ("conservative", "outcome-first", "explicit-checklist")
_RECIPE_DIRECTIVES = {
    "conservative": (
        "Preserve source order and every mandatory check.",
        "Keep explicit constraints visible; do not compress required steps.",
    ),
    "outcome-first": (
        "Foreground the objective and success condition before procedure.",
        "Then execute every mandatory check without deletion or weakening.",
    ),
    "explicit-checklist": (
        "Present mandatory checks as an explicit checklist.",
        "Preserve every authority, evidence, gate, and stop condition.",
    ),
}

_ENV_CAPABILITIES = "QOR_EXECUTION_CAPABILITIES"
_ENV_CAPABILITIES_COMPLETE = "QOR_EXECUTION_CAPABILITIES_COMPLETE"
_ENV_MODEL = "QOR_MODEL_FAMILY"
_ENV_RESPONDER = "QOR_RESPONDER_MODEL_FAMILY"
_ENV_REASONING = "QOR_REASONING_MODE"
_ENV_RENDER_HINT = "QOR_RENDERING_HINT"


@dataclass(frozen=True)
class ExecutionContext:
    host: str
    declared_model_family: str
    responder_model_family: str
    reasoning_mode: str
    capabilities: tuple[str, ...]
    capabilities_complete: bool
    rendering_hint: str | None


@dataclass(frozen=True)
class SkillExecutionContract:
    skill: str
    hard_requirements: tuple[str, ...]
    quality_requirements: tuple[str, ...]
    rendering_recipes: tuple[str, ...]
    default_recipe: str


def _csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(sorted({item.strip() for item in value.split(",") if item.strip()}))


def _truthy(value: object) -> bool:
    if isinstance(value, list):
        return bool(value)
    return bool(value)


def _platform_context() -> tuple[str, set[str]]:
    try:
        from qor.scripts import qor_platform
    except ImportError:
        return "unknown", set()
    state = qor_platform.current() or {}
    detected = state.get("detected", {}) if isinstance(state, dict) else {}
    declared = state.get("declared", {}) if isinstance(state, dict) else {}
    host = detected.get("host") if isinstance(detected, dict) else None
    if not host or host == "unknown":
        host = declared.get("host_declared") if isinstance(declared, dict) else None
    if not host:
        host = qor_platform.detect_host()
    capabilities: set[str] = set()
    for mapping in (detected, declared):
        if not isinstance(mapping, dict):
            continue
        for key, value in mapping.items():
            if key in {"host", "host_declared"} or not _truthy(value):
                continue
            capabilities.add(key.replace("_", "-"))
    return str(host or "unknown"), capabilities


def detect_context(env: Mapping[str, str] | None = None) -> ExecutionContext:
    env = os.environ if env is None else env
    host, platform_capabilities = _platform_context()
    explicit_capabilities = set(_csv(env.get(_ENV_CAPABILITIES)))
    complete = env.get(_ENV_CAPABILITIES_COMPLETE, "").lower()
    return ExecutionContext(
        host=host,
        declared_model_family=env.get(_ENV_MODEL, "unknown") or "unknown",
        responder_model_family=env.get(_ENV_RESPONDER, "unknown") or "unknown",
        reasoning_mode=env.get(_ENV_REASONING, "unknown") or "unknown",
        capabilities=tuple(sorted(platform_capabilities | explicit_capabilities)),
        capabilities_complete=complete in {"1", "true", "yes", "on"},
        rendering_hint=env.get(_ENV_RENDER_HINT) or None,
    )


def _frontmatter(text: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    loaded = yaml.safe_load(match.group(1)) or {}
    return loaded if isinstance(loaded, dict) else {}


def _as_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    raise ValueError(f"expected string/list, got {type(value).__name__}")


def _legacy_contract(fm: dict, path: Path) -> SkillExecutionContract | None:
    if "model_compatibility" not in fm and "min_model_capability" not in fm:
        return None
    return SkillExecutionContract(
        skill=str(fm.get("name") or path.parent.name),
        hard_requirements=(),
        quality_requirements=("legacy-model-metadata-advisory",),
        rendering_recipes=("conservative",),
        default_recipe="conservative",
    )


def load_contract(path: Path) -> SkillExecutionContract | None:
    fm = _frontmatter(path.read_text(encoding="utf-8"))
    hard = _as_tuple(fm.get("hard_execution_requirements"))
    quality = _as_tuple(fm.get("advisory_quality_requirements"))
    recipes = _as_tuple(fm.get("rendering_recipes"))
    default = str(fm.get("default_rendering_recipe", "conservative"))
    if not (hard or quality or recipes or "default_rendering_recipe" in fm):
        return _legacy_contract(fm, path)
    recipes = recipes or ("conservative",)
    unknown = set(recipes) - set(RENDER_RECIPES)
    if unknown:
        raise ValueError(f"unsupported rendering recipe(s): {sorted(unknown)}")
    if default not in recipes:
        raise ValueError(f"default recipe {default!r} is not admitted by {path}")
    return SkillExecutionContract(
        skill=str(fm.get("name") or path.parent.name),
        hard_requirements=hard,
        quality_requirements=quality,
        rendering_recipes=recipes,
        default_recipe=default,
    )


def select_recipe(contract: SkillExecutionContract, context: ExecutionContext) -> str:
    if context.reasoning_mode.lower() in {"high", "extended", "deep"}:
        if "outcome-first" in contract.rendering_recipes:
            return "outcome-first"
    if context.rendering_hint in contract.rendering_recipes:
        return str(context.rendering_hint)
    return contract.default_recipe


def inspect_contract(contract: SkillExecutionContract, context: ExecutionContext) -> dict:
    available = set(context.capabilities)
    unsatisfied = tuple(req for req in contract.hard_requirements if req not in available)
    missing = unsatisfied if context.capabilities_complete else ()
    unverified = () if context.capabilities_complete else unsatisfied
    recipe = select_recipe(contract, context)
    return {
        "skill": contract.skill,
        "context": asdict(context),
        "hard_execution_requirements": list(contract.hard_requirements),
        "advisory_quality_requirements": list(contract.quality_requirements),
        "rendering_recipe": recipe,
        "rendering_directives": list(_RECIPE_DIRECTIVES[recipe]),
        "missing_hard_requirements": list(missing),
        "unverified_hard_requirements": list(unverified),
        "authority_note": (
            "model identity and rendering hints are advisory; they do not alter "
            "gates, authority, evidence, or semantic obligations"
        ),
    }


def _skill_paths(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "qor" / "skills").rglob("SKILL.md"))


def _find_skill(repo_root: Path, name: str) -> Path:
    matches = [path for path in _skill_paths(repo_root) if path.parent.name == name]
    if len(matches) != 1:
        raise ValueError(f"expected one skill named {name!r}, found {len(matches)}")
    return matches[0]


def inspect_skill(
    repo_root: Path, name: str, context: ExecutionContext | None = None,
) -> dict:
    contract = load_contract(_find_skill(repo_root, name))
    if contract is None:
        raise ValueError(f"skill {name!r} has no execution-context contract")
    return inspect_contract(contract, context or detect_context())


def scan(repo_root: Path, context: ExecutionContext | None = None) -> list[dict]:
    active = context or detect_context()
    results: list[dict] = []
    for path in _skill_paths(repo_root):
        contract = load_contract(path)
        if contract is not None:
            results.append(inspect_contract(contract, active))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.execution_context")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--skill", required=True)
    inspect_parser.add_argument("--enforce-hard", action="store_true")
    sub.add_parser("scan")
    args = parser.parse_args(argv)
    if args.cmd == "scan":
        result: object = scan(args.repo_root)
        exit_code = 0
    else:
        result = inspect_skill(args.repo_root, args.skill)
        exit_code = 2 if args.enforce_hard and result["missing_hard_requirements"] else 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
