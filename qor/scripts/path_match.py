"""Phase 61 (qor-debug M6): unified path-boundary matcher.

Closes the M1-class defect at its root: three independent prefix-match call
sites (`qor/capabilities/risk.py::_matches_any`, `qor/capabilities/context.py
::_prefix_match`, and audit-side trigger detection) all need the same
discipline — match boundary must be `/`, `.`, or exact equality so that a
prefix like `qor/scripts/ledger_hash` does not match `ledger_hash_v2.py`.

Stdlib only. Boundary characters are restricted to filesystem-natural
separators (`/`) and file-extension dots (`.`).
"""
from __future__ import annotations

_BOUNDARY_CHARS: frozenset[str] = frozenset({"/", "."})


def matches(path: str, prefix: str) -> bool:
    """Path-boundary-aware prefix match.

    Two cases keep the discipline ergonomic:

    1. Prefix ends with a boundary char (`/` or `.`) — the prefix itself
       establishes the boundary; `path.startswith(prefix)` is sufficient.
       Example: prefix ``qor/skills/`` matches ``qor/skills/governance/...``.

    2. Prefix does NOT end with a boundary char — the next char in `path`
       after the prefix must BE a boundary char, or the path must equal the
       prefix exactly. Example: prefix ``qor/scripts/ledger_hash`` matches
       ``qor/scripts/ledger_hash.py`` and ``qor/scripts/ledger_hash/foo``
       but NOT ``qor/scripts/ledger_hash_v2.py``.
    """
    if not path.startswith(prefix):
        return False
    if path == prefix:
        return True
    if prefix and prefix[-1] in _BOUNDARY_CHARS:
        return True
    boundary = path[len(prefix):len(prefix) + 1]
    return boundary in _BOUNDARY_CHARS


def matches_any(path: str, prefixes: tuple[str, ...]) -> bool:
    """True iff `path` matches any of `prefixes` under the boundary rule."""
    return any(matches(path, p) for p in prefixes)


def find_matching_prefix(path: str, prefixes: tuple[str, ...]) -> str | None:
    """Return the first matching prefix, or None when nothing matches."""
    for p in prefixes:
        if matches(path, p):
            return p
    return None
