"""Phase 56 (GH #51): stable UID for ledger entries.

Workers in a federated session author entries as fragments without
guessing the next sequential `Entry #N`. Each fragment carries a stable
UID derived from (ts, session_id, target, content_hash). Canonicalization
later assigns display numbers; the UID is the cross-worker identity.

Stdlib only. Format: ``le_<16 hex>`` where the hex is the first 16 chars
of SHA-256 over the canonical tuple string.
"""
from __future__ import annotations

import hashlib
import re

_UID_RE = re.compile(r"^le_[0-9a-f]{16}$")


def make_entry_uid(*, ts: str, session_id: str, target: str, content_hash: str) -> str:
    """Derive a stable 16-hex UID from the entry's identifying tuple."""
    payload = "|".join(("ts=" + ts, "sid=" + session_id, "tgt=" + target, "ch=" + content_hash))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return "le_" + digest[:16]


def validate_entry_uid(value: str) -> str:
    """Raise ``ValueError`` if ``value`` is not a well-formed UID."""
    if not isinstance(value, str):
        raise ValueError(f"entry uid must be a string, got {type(value).__name__}")
    if not _UID_RE.match(value):
        raise ValueError(
            f"entry uid must match 'le_<16 hex>': {value!r}"
        )
    return value
