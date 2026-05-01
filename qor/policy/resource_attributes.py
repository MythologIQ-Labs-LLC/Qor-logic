"""Per-resource-kind attribute computation for the cedar evaluator.

`qor.policy.evaluator` reads attributes from a caller-supplied ``entities``
dict via ``_resolve_attr``. This module is the canonical caller-side helper
that classifies a path as a ``Code::"governance"`` resource (markdown under
``docs/`` or ``qor/references/``) and computes its attributes.

Single source of truth for governance-resource classification. Path filter
is a literal allowlist; no operator-controlled paths reach the scanner
without normalization through ``compute_governance_attributes``.

Phase 53: governance markdown canary attributes.
Phase 55: skill admission tool/subagent scope attributes.
Phase 56: production code secret-scan attribute (drives `has_hardcoded_secrets`).

Per Phase 53 plan and SG-PromptInjection-A; Phase 55 plan and Cedar admission;
Phase 56 plan and SG-SecretLeakAtSeal-A.
"""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from qor.scripts.prompt_injection_canaries import scan
from qor.scripts.secret_scanner import scan_text as _scan_secrets


_GOVERNANCE_PATH_PREFIXES: tuple[str, ...] = (
    "docs/",
    "qor/references/",
)


# Phase 55: canonical Tool name set. Single source of truth; doctrine
# round-trips against this tuple via test_canonical_tools_set_matches_documented_tool_names.
_CANONICAL_TOOLS: frozenset[str] = frozenset({
    "Read", "Write", "Edit", "Glob", "Grep", "Bash",
    "Agent", "WebFetch", "WebSearch", "TodoWrite",
})


def is_governance_path(path: str | Path) -> bool:
    """True when `path` is a `.md` file under a governance-allowlisted prefix."""
    posix = PurePosixPath(str(path).replace("\\", "/"))
    if posix.suffix != ".md":
        return False
    if ".." in posix.parts:
        return False
    s = posix.as_posix()
    return any(s.startswith(prefix) for prefix in _GOVERNANCE_PATH_PREFIXES)


def compute_governance_attributes(
    path: str | Path, content: str
) -> dict[str, bool]:
    """Compute cedar evaluator attributes for a `Code::"governance"` resource.

    Raises ``ValueError`` when `path` is not a governance-classified path.
    """
    if not is_governance_path(path):
        raise ValueError(f"not a governance resource path: {path!r}")
    has_canary = bool(scan(content))
    return {"has_prompt_injection_canary": has_canary}


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_LIST_KEY_RE = re.compile(
    r"^(?P<key>permitted_tools|permitted_subagents)\s*:\s*"
    r"(?:\[(?P<inline>[^\]]*)\]"
    r"|\n(?P<block>(?:\s+-\s+\S+\n?)+))",
    re.MULTILINE,
)
_BASH_FENCE_RE = re.compile(r"```(?:bash|shell|sh)\b", re.IGNORECASE)
_AGENT_INVOCATION_RE = re.compile(
    r"Agent\s*\(\s*(?:[^)]*?,\s*)?subagent_type\s*=\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)


def _parse_list_keys(frontmatter: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for match in _LIST_KEY_RE.finditer(frontmatter):
        key = match.group("key")
        inline = match.group("inline")
        block = match.group("block")
        if inline is not None:
            items = [s.strip() for s in inline.split(",") if s.strip()]
        else:
            items = [
                line.strip().lstrip("- ").strip()
                for line in (block or "").splitlines() if line.strip()
            ]
        out[key] = items
    return out


def _detect_tool_invocations(body: str) -> set[str]:
    """Detect canonical Tool invocations in skill prose."""
    found: set[str] = set()
    if _BASH_FENCE_RE.search(body):
        found.add("Bash")
    for tool in _CANONICAL_TOOLS:
        if tool == "Bash":
            continue
        if re.search(rf"\bTool:\s*{tool}\b", body):
            found.add(tool)
    return found


def _detect_subagent_invocations(body: str) -> set[str]:
    return {m.group(1) for m in _AGENT_INVOCATION_RE.finditer(body)}


def compute_skill_admission_attributes(
    skill_md_path: str | Path,
) -> dict[str, bool]:
    """Phase 55: compute admission attributes for a Skill resource.

    Returns ``{registered, has_frontmatter, actual_tool_invocations_exceed_scope,
    actual_subagent_invocations_exceed_scope}``.
    Skills missing the permitted_tools / permitted_subagents declarations are
    treated as the empty allowlist (default-deny posture per AI RMF GV-6.1).
    """
    path = Path(skill_md_path)
    if not path.exists():
        return {
            "registered": False, "has_frontmatter": False,
            "actual_tool_invocations_exceed_scope": True,
            "actual_subagent_invocations_exceed_scope": True,
        }
    text = path.read_text(encoding="utf-8")
    fm_match = _FRONTMATTER_RE.match(text)
    has_frontmatter = fm_match is not None
    frontmatter = fm_match.group(1) if has_frontmatter else ""
    body = text[fm_match.end():] if fm_match else text

    keys = _parse_list_keys(frontmatter)
    declared_tools = set(keys.get("permitted_tools", []))
    declared_subagents = set(keys.get("permitted_subagents", []))

    actual_tools = _detect_tool_invocations(body)
    actual_subagents = _detect_subagent_invocations(body)

    return {
        "registered": True,
        "has_frontmatter": has_frontmatter,
        "actual_tool_invocations_exceed_scope": bool(actual_tools - declared_tools),
        "actual_subagent_invocations_exceed_scope": bool(actual_subagents - declared_subagents),
    }


def compute_production_attributes(
    path: str | Path, content: str
) -> dict[str, bool]:
    """Phase 56: compute Cedar attributes for a `Code::"production"` resource.

    Drives the long-standing `has_hardcoded_secrets` boolean (Phase 23 rule).
    Path is metadata only — detection is purely from `content` per Phase 56
    plan Open Question 1 / Phase 2 wiring. Allowlist semantics are inherited
    from `qor.scripts.secret_scanner._ALLOWLIST`.
    """
    findings = _scan_secrets(content, file=str(path))
    return {"has_hardcoded_secrets": bool(findings)}
