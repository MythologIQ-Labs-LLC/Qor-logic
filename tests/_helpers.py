"""Shared test helpers (Phase 52, Section 4 Razor compliance).

Extracted from tests/test_doctrine_test_functionality.py to bring that file
under the 250-line razor cap. Reusable across other proximity-anchor lint
tests.
"""
from __future__ import annotations

import re


def proximity(body: str, header_pattern: str, phrase_pattern: str, span: int = 1500) -> bool:
    """Search for `phrase_pattern` within `span` chars after the named header."""
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_pattern, window, re.IGNORECASE | re.DOTALL) is not None


def strip_section(body: str, header_pattern: str, span: int = 4000) -> str:
    """Replace `span` chars after the named header with neutral filler.

    Used by negative-path tests to prove proximity-anchor assertions are
    section-anchored rather than blind substring checks. Filler is the same
    length as the stripped span so content past the strip does not slide
    into the proximity window.
    """
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return body
    start = m.end()
    end = min(len(body), start + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    return body[:start] + filler[: end - start] + body[end:]


def fenced_block_after(body: str, header_pattern: str) -> str | None:
    """Extract the first ``` fenced code block following the named header."""
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return None
    rest = body[m.end():]
    fence = re.search(r"```[a-z]*\n(.*?)\n```", rest, re.DOTALL)
    return fence.group(1) if fence else None
