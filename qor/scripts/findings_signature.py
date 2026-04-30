#!/usr/bin/env python3
"""Findings signature (Phase 37 B20b).

Computes a stable 16-character SHA256 prefix over the unique sorted set of
``findings_categories`` on an audit gate record. Used by ``stall_walk`` and
``remediate_pattern_match`` to detect repeated audit VETOs against a stable
finding profile.

Absent-field sentinel: pre-Phase-37 audit records did not carry
``findings_categories``. For those, ``compute_record`` returns the literal
string ``"LEGACY"``. The sentinel contains ``L``, ``G``, ``Y`` (non-hex
characters) and therefore cannot collide with a real 16-hex-char signature.

``UnmappedCategoryError`` is raised when any category outside the closed
schema enum is encountered. No ``other`` category exists -- drift must force
a deliberate schema amendment rather than passing silently.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qor.scripts import validate_gate_artifact as _vga


LEGACY_SENTINEL = "LEGACY"

_VALID_CATEGORIES = frozenset({
    "razor-overage",
    "ghost-ui",
    "security-l3",
    "owasp-violation",
    "orphan-file",
    "macro-architecture",
    "dependency-unjustified",
    "schema-migration-missing",
    "specification-drift",
    "test-failure",
    "coverage-gap",
    "infrastructure-mismatch",
    "prompt-injection",
})


class UnmappedCategoryError(ValueError):
    """Raised when a findings category is not in the closed schema enum."""


def compute_record(record: dict) -> str:
    """Compute signature from one audit gate record.

    Returns ``"LEGACY"`` when ``findings_categories`` is absent (pre-Phase-37
    records). Raises ``UnmappedCategoryError`` on any non-enum category.
    """
    if "findings_categories" not in record:
        return LEGACY_SENTINEL
    categories = record["findings_categories"]
    unknown = [c for c in categories if c not in _VALID_CATEGORIES]
    if unknown:
        raise UnmappedCategoryError(
            f"categories not in closed enum: {unknown}. Amend audit.schema.json "
            f"findings_categories.items.enum if a new category is needed."
        )
    normalized = sorted(set(categories))
    joined = "|".join(normalized)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return digest[:16]


def compute_path(path: str | Path) -> str:
    """Load a single audit gate JSON file and compute its signature."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    return compute_record(record)
