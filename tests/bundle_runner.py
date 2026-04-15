"""Bundle execution test helper (Phase 12).

Parses bundle SKILL.md frontmatter, walks declared phases, mocks subskill
invocations. Used by tests/test_bundles.py to exercise bundle behavior
without actually invoking /qor-* skills.

Bundles are markdown-only; their behavior is doctrine + frontmatter +
documented protocol. This runner verifies the mechanical contract:
- Bundle declares phases/checkpoints/budget per workflow-bundles.md
- Phase order matches documentation
- Decomposition pointers are valid (target bundles exist)
- Constituent skills referenced by `/qor-*` triggers actually exist
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class BundleSpec:
    name: str
    type: str
    phases: list[str]
    checkpoints: list[str]
    budget: dict
    decomposes_into: list[str] = field(default_factory=list)
    skill_path: Path | None = None
    body: str = ""


def parse_bundle(skill_md: Path) -> BundleSpec:
    text = skill_md.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise ValueError(f"No frontmatter: {skill_md}")
    fm_body = m.group(1)
    body = text[m.end():]

    spec = {"name": "", "type": "", "phases": [], "checkpoints": [],
            "budget": {}, "decomposes_into": []}
    current_block: str | None = None
    indent_stack: list[tuple[int, dict]] = [(0, spec)]

    for raw in fm_body.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        # Pop nested context if dedented
        while indent_stack and indent < indent_stack[-1][0]:
            indent_stack.pop()
        target = indent_stack[-1][1] if indent_stack else spec

        if line.startswith("- "):
            val = line[2:].strip().strip('"').strip("'")
            # We're in a list under the most recent key context
            if current_block and current_block in target:
                if isinstance(target[current_block], list):
                    target[current_block].append(val)
            continue

        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        current_block = key

        if not val:
            # Could be a nested dict (budget) or a list (phases on next lines)
            # Heuristic: if next-keys are scalars, it's dict; if lines start with `- `, list
            # Initialize as list; if scalar children appear, switch
            target[key] = []
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            target[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        elif val in ("true", "True"):
            target[key] = True
        elif val in ("false", "False"):
            target[key] = False
        elif _is_number(val):
            target[key] = float(val) if "." in val else int(val)
        else:
            target[key] = val.strip('"').strip("'")

    # Promote scalar children of "budget" if they were misparsed
    # Re-parse budget block specifically
    budget = {}
    in_budget = False
    for raw in fm_body.splitlines():
        if raw.strip().startswith("budget:"):
            in_budget = True
            continue
        if in_budget:
            if raw and not raw.startswith(" "):
                in_budget = False
                continue
            line = raw.strip()
            if ":" in line and not line.startswith("- "):
                k, _, v = line.partition(":")
                v = v.strip()
                if _is_number(v):
                    budget[k.strip()] = float(v) if "." in v else int(v)
                elif v:
                    budget[k.strip()] = v.strip('"')
    if budget:
        spec["budget"] = budget

    return BundleSpec(
        name=spec.get("name", ""),
        type=spec.get("type", ""),
        phases=spec.get("phases", []) if isinstance(spec.get("phases"), list) else [],
        checkpoints=spec.get("checkpoints", []) if isinstance(spec.get("checkpoints"), list) else [],
        budget=spec.get("budget", {}),
        decomposes_into=spec.get("decomposes_into", []) if isinstance(spec.get("decomposes_into"), list) else [],
        skill_path=skill_md,
        body=body,
    )


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def find_skill_dirs(name: str) -> list[Path]:
    return list(SKILLS_ROOT.rglob(f"{name}/SKILL.md"))


def extract_skill_refs(body: str) -> set[str]:
    """All /qor-* references in the body."""
    return set(re.findall(r"/qor-[a-z-]+", body))


def list_all_bundles() -> list[BundleSpec]:
    """Parse every SKILL.md whose frontmatter declares type: workflow-bundle."""
    bundles = []
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        try:
            spec = parse_bundle(skill_md)
        except (ValueError, KeyError):
            continue
        if spec.type == "workflow-bundle":
            bundles.append(spec)
    return bundles
