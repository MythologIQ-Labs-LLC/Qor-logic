"""Shared versioned ledger-dialect parser (GH #282).

Single source of truth for the accepted ledger hash-markup dialect and the one
historical compatibility boundary, consumed by ``ledger_hash``,
``seal_entry_check``, and (transitively, via ``ledger_hash.verify``)
``governance_health``.

Recognizes three hash-value forms -- inline-backtick, ``SHA256(...) = <hex>``,
and a fenced block whose content is a bare 64-hex line -- plus a separate
``**Phase**:`` line as a phase source when the entry header lacks ``Phase <N>``.

The forms are additive: no rejection is relaxed. A value must still be a 64-char
lowercase hex, still bounded to its own field span (the span stops at the next
``**Field**`` marker, so prose hex and a later field's value are never
captured), and the consumers still fail on content/chain mismatch, malformed
hashes, post-boundary duplicate previous hashes, and tampering.
"""
from __future__ import annotations

import re

# The single historical compatibility boundary. Entries at/after this number
# MUST carry verifiable hash markup (one of the three recognized forms); an
# unmarked one is a FAIL, not a silent skip. Entries below are pre-convention
# historical residuals recorded only in the skip summary.
MARKUP_COMPAT_BOUNDARY = 123

_HEX = r"[0-9a-f]{64}"
_FIELD_SUFFIX = r"(?:\s*\([^)]+\))?"
# Bounded span: any characters up to (but not into) the next bold field marker.
_HASH_SPAN = r"(?:(?!\n\s*\*\*[A-Z])[\s\S])*?"
# Three value forms. Capture-group order: inline-backtick, ``= <hex>``, and a
# bare hex alone on its line (the fenced-block form). The lone-line anchoring of
# the third form keeps it from capturing inline prose hex.
_HASH_VALUE = (
    rf"(?:`({_HEX})`"
    rf"|=\s*({_HEX})\b"
    rf"|(?:^|\n)[ \t]*({_HEX})[ \t]*(?:\r?\n|$))"
)


def _field_re(name: str) -> re.Pattern:
    return re.compile(rf"\*\*{name}{_FIELD_SUFFIX}\*\*{_HASH_SPAN}{_HASH_VALUE}")


CONTENT_HASH_RE = _field_re("Content Hash")
PREV_HASH_RE = _field_re("Previous Hash")
CHAIN_HASH_RE = _field_re("Chain Hash")

# Historical Session-Seal markup: ``**Session Seal**: ... = `<hex>```.
SESSION_SEAL_RE = re.compile(rf"\*\*Session Seal\*\*{_HASH_SPAN}=\s*`({_HEX})`")

_PHASE_HEADER_RE = re.compile(r"Phase\s*(\d+)")
_PHASE_LINE_RE = re.compile(r"^\*\*Phase\*\*:.*?(\d+)", re.MULTILINE)


def hash_value(match: re.Match | None) -> str | None:
    """First populated capture group of a hash-field match (any of the three
    recognized forms), or ``None`` when there is no match."""
    if match is None:
        return None
    return match.group(1) or match.group(2) or match.group(3)


def entry_phase(header: str, body: str) -> int | None:
    """Phase number from the header ``Phase <N>`` form, else from a separate
    ``**Phase**: ... <N>`` line in the body, else ``None``."""
    m = _PHASE_HEADER_RE.search(header)
    if m:
        return int(m.group(1))
    m = _PHASE_LINE_RE.search(body)
    return int(m.group(1)) if m else None
