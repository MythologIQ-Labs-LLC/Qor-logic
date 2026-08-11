"""Digest the installed skill corpus (Phase 217; GH #314).

A seal establishes what the plan promised, what the tests proved, and what the
ledger chains -- but not which ceremony executed. Two seals with identical
entries could come from materially different skill corpora and the ledger
cannot tell them apart.

One digest over the installed ``SKILL.md`` set closes that. It identifies
content, not location, so a seal produced on one machine is comparable to a
seal produced on another.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def _skill_files(skills_dir: Path) -> list[Path]:
    return sorted(skills_dir.glob("*/SKILL.md"))


def digest(host: str = "claude", scope: str = "repo") -> str | None:
    """SHA256 over the sorted ``(skill name, file sha256)`` pairs.

    Returns ``None`` when no install exists at the scope. That case is
    deliberately not a hash: a digest over an empty set is a real digest and
    would read as evidence of a ceremony that never ran, so callers must
    handle absence explicitly rather than receive a plausible-looking value.

    Sorting the input makes the result order-independent by construction
    rather than by accident of directory iteration, which is not guaranteed
    to be stable across platforms.
    """
    from qor import hosts

    try:
        skills_dir = hosts.resolve(host, scope=scope).skills_dir
    except (KeyError, ValueError):
        return None

    files = _skill_files(skills_dir)
    if not files:
        return None

    accumulator = hashlib.sha256()
    for path in files:
        body = path.read_bytes().replace(b"\r\n", b"\n")
        accumulator.update(path.parent.name.encode("utf-8"))
        accumulator.update(b"\0")
        accumulator.update(hashlib.sha256(body).hexdigest().encode("ascii"))
        accumulator.update(b"\n")
    return accumulator.hexdigest()
