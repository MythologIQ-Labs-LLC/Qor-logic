"""Phase 76: content-addressable entry ID for META_LEDGER entries.

Returns a deterministic ID derived from (timestamp, phase, content_hash) so
concurrent federation workers cannot produce colliding entry identifiers.
The 12-char default truncation provides ~48 bits of collision space.

Per Phase 76 wiring (GH #51) -- forward-only V1: new entries from Phase 76
onward carry an Entry ID field; past Entries #1-#207 are not modified.
"""
from __future__ import annotations

import hashlib
import os


def derive_entry_id(ts: str, phase: str, content_hash: str, length: int = 12) -> str:
    """Return a content-addressable ID for a META_LEDGER entry.

    Default returns 12-char hex (48 bits). Setting environment variable
    ``QOR_ENTRY_ID_FULL_HASH=1`` overrides to a 64-char full SHA256 digest
    for federation deployments scaling past ~10^7 entries.
    """
    if os.environ.get("QOR_ENTRY_ID_FULL_HASH") == "1":
        length = 64
    digest = hashlib.sha256(f"{ts}|{phase}|{content_hash}".encode("utf-8")).hexdigest()
    return digest[:length]
