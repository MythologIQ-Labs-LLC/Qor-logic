"""Phase 59 (GH #48): seal-critical hash validation + fail-closed toolkit guard.

Public surface:
- ``HashEvidence`` frozen dataclass: digest + path + byte count.
- ``HEX_SHA256_RE``: anchored regex for lowercase 64-hex SHA-256 digests.
- ``hash_file(path)``: compute digest of a file, returning ``HashEvidence``.
- ``validate_sha256(value, *, label)``: raise ``ValueError`` on placeholder /
  empty / wrong-length / uppercase / non-hex strings; return the value when
  it's a legitimate digest.
- ``require_toolkit_modules(modules)``: raise ``RuntimeError`` listing every
  module that fails ``importlib.util.find_spec``.

Stdlib only. Fail-closed semantics: nothing in this module silently passes.
Used by ``/qor-substantiate`` Step 6.8 and ``qor.scripts.ledger_hash.verify``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PLACEHOLDER_DIGESTS = {"0" * 64}


@dataclass(frozen=True)
class HashEvidence:
    path: str
    sha256: str
    byte_count: int


def hash_file(path: Path) -> HashEvidence:
    raw = Path(path).read_bytes()
    return HashEvidence(
        path=str(path),
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
    )


def validate_sha256(value: str, *, label: str) -> str:
    """Validate a SHA-256 hex digest. Raises ``ValueError`` with ``label`` in the
    message on any failure. Returns ``value`` unchanged on success."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: empty or non-string value")
    if len(value) != 64:
        raise ValueError(
            f"{label}: expected 64 hex chars, got {len(value)} ({value!r})"
        )
    if not HEX_SHA256_RE.match(value):
        raise ValueError(
            f"{label}: value is not lowercase 64-hex (placeholder, uppercase, "
            f"or non-hex character detected): {value!r}"
        )
    if value in _PLACEHOLDER_DIGESTS:
        raise ValueError(f"{label}: placeholder digest is not valid evidence: {value!r}")
    return value


def validate_sha256_optional(value: str | None, *, label: str) -> str | None:
    """Variant of `validate_sha256` that accepts None. Use this for schema
    fields typed `["string", "null"]` (e.g., `audit.target_content_hash` from
    Phase 45). Returns the value unchanged on None or success; raises only
    when a non-None value fails format validation."""
    if value is None:
        return None
    return validate_sha256(value, label=label)


def require_toolkit_modules(modules: tuple[str, ...]) -> None:
    """Import-check each module; raise ``RuntimeError`` listing every absent one."""
    missing: list[str] = []
    for name in modules:
        try:
            spec = importlib.util.find_spec(name)
        except (ValueError, ModuleNotFoundError, ImportError):
            spec = None
        if spec is None:
            missing.append(name)
    if missing:
        raise RuntimeError(
            "seal-critical toolkit modules missing: " + ", ".join(missing)
        )
