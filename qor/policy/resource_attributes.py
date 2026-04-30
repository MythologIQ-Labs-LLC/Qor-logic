"""Per-resource-kind attribute computation for the cedar evaluator (Phase 53).

`qor.policy.evaluator` reads attributes from a caller-supplied ``entities``
dict via ``_resolve_attr``. This module is the canonical caller-side helper
that classifies a path as a ``Code::"governance"`` resource (markdown under
``docs/`` or ``qor/references/``) and computes its attributes.

Single source of truth for governance-resource classification. Path filter
is a literal allowlist; no operator-controlled paths reach the scanner
without normalization through ``compute_governance_attributes``.

Per Phase 53 plan §Phase 2 and SG-PromptInjection-A.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

from qor.scripts.prompt_injection_canaries import scan


_GOVERNANCE_PATH_PREFIXES: tuple[str, ...] = (
    "docs/",
    "qor/references/",
)


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
