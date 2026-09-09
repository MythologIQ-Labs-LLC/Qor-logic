"""Shared versioned ledger-dialect parser (GH #282).

Single source of truth for the accepted ledger hash-markup dialect and the one
historical compatibility boundary, consumed by ``ledger_hash``,
``seal_entry_check``, and (transitively, via ``ledger_hash.verify``)
``governance_health``.

Recognizes three hash-value forms -- inline-backtick, ``SHA256(...) = <hex>``,
and a fenced block whose content is a bare 64-hex line -- plus a separate
``**Phase**:`` line as a phase source when the entry header lacks ``Phase <N>``.

The value forms are additive: no accepted value form is removed. What is
narrowed is where a field is recognized. A label must begin its line, must be
followed by a colon, and must reach its value through connective tissue only --
whitespace, backticks and fences, a ``SHA256(...)`` formula, ``=``. A value must
still be a 64-char lowercase hex, and the consumers still fail on content/chain
mismatch, malformed hashes, post-boundary duplicate previous hashes, and
tampering.

A hash label written in prose is no longer read as a field when it appears
mid-line, when no colon follows it, or when narrative text separates it from its
value. Two cases remain captured and are not addressed here: a hash label inside
a fenced or indented code block, and a field-shaped line whose value is a prose
digest followed by trailing prose. See GH #428.
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


# A field label begins its line. A label quoted inside a sentence does not, and
# before GH #428 such a label was read as a field (docs/META_LEDGER.md entry
# #741). Deliberately whitespace-only: list and blockquote markers are excluded
# because `> **Content Hash**: ...` is a defect when it quotes another entry's
# field inside this one and legitimate when a whole entry is quoted, and nothing
# available here can tell those apart.
_FIELD_PREFIX = r"^[ \t]*"
# Connective tissue between a label and its value: a colon, then only
# whitespace, backticks and fences, a SHA256(...) formula, and ``=``. Narrative
# text between the two no longer reaches a value, so prose cannot displace the
# field's own digest.
_HASH_CONNECTIVE = r":(?:[^\S\n]|\r?\n|`|=|SHA256\([^)\n]*\))*"


def _field_re(name: str) -> re.Pattern:
    return re.compile(
        rf"{_FIELD_PREFIX}\*\*{name}{_FIELD_SUFFIX}\*\*{_FIELD_SUFFIX}"
        rf"{_HASH_CONNECTIVE}{_HASH_VALUE}",
        re.MULTILINE,
    )


CONTENT_HASH_RE = _field_re("Content Hash")
PREV_HASH_RE = _field_re("Previous Hash")
CHAIN_HASH_RE = _field_re("Chain Hash")


#: The label FORMS this module owns, per document (GH #469). Structure cannot
#: decide aliasing: `**Previous Chain Hash**` is a Previous Hash form while
#: `**Superseded Content Hash**` is a distinct field, and the two are
#: structurally identical. So the owner declares, rather than a rule inferring.
OWNS = {
    ("docs/META_LEDGER.md", "Content Hash"): ("Content Hash", "META_LEDGER Content Hash"),
    ("docs/META_LEDGER.md", "Previous Hash"): ("Previous Hash", "Previous Chain Hash"),
    ("docs/META_LEDGER.md", "Chain Hash"): ("Chain Hash", "Session Seal"),
}


def _label_re(name: str) -> re.Pattern:
    return re.compile(rf"\*\*{name}{_FIELD_SUFFIX}\*\*")


CONTENT_HASH_LABEL_RE = _label_re("Content Hash")
PREV_HASH_LABEL_RE = _label_re("Previous Hash")
CHAIN_HASH_LABEL_RE = _label_re("Chain Hash")


def any_hash_label_present(body: str) -> bool:
    """True if the entry names at least one hash field, independent of whether
    its value parses as a recognized hash form (GH #363).

    ``CONTENT_HASH_RE`` et al. match label *and* a validly-shaped value
    together, so a labeled field whose value is fabricated garbage of the
    right length but the wrong alphabet (e.g. 64 non-hex characters) fails
    the combined match and is indistinguishable, by that regex alone, from an
    entry that never named the field at all. This label-only check lets a
    caller tell "unmarked historical entry" apart from "marked but
    unparseable" so the latter can be reported rather than silently dropped.
    """
    return bool(
        CONTENT_HASH_LABEL_RE.search(body)
        or PREV_HASH_LABEL_RE.search(body)
        or CHAIN_HASH_LABEL_RE.search(body)
    )

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
