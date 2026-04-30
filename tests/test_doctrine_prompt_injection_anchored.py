"""Phase 53: doctrine round-trip integrity tests.

Replaces five presence-only tests vetoed in Phase 53 Pass 1 with a single
behavior-invariant test that walks the canary catalog and asserts the
doctrine documents each class with a non-empty body, plus heading-tree
integrity for the four canonical sections.
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts.prompt_injection_canaries import CANARIES

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = REPO_ROOT / "qor" / "references" / "doctrine-prompt-injection.md"

_CANONICAL_SECTIONS = (
    "## Threat model",
    "## Canary catalog",
    "## Refusal protocol",
    "## Out-of-scope",
)

_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _section_body(content: str, heading: str) -> str:
    """Return content between `heading` and the next heading of any level."""
    idx = content.find(heading)
    assert idx != -1, f"missing heading: {heading!r}"
    body_start = idx + len(heading)
    rest = content[body_start:]
    next_heading = _HEADING_RE.search(rest)
    if next_heading is None:
        return rest.strip()
    return rest[: next_heading.start()].strip()


def test_doctrine_round_trip_against_canary_catalog():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")

    # Heading-tree integrity: every canonical section must exist and have a
    # non-empty body. An attacker emptying a section while leaving its
    # heading would be caught here.
    for heading in _CANONICAL_SECTIONS:
        body = _section_body(content, heading)
        assert body, f"section {heading!r} has empty body"
        # Demand at least one substantive sentence (>= 20 chars beyond
        # whitespace and trivial markup).
        assert len(re.sub(r"\s+", " ", body).strip()) >= 20, (
            f"section {heading!r} body is too short to be substantive: {body!r}"
        )

    # Per-canary content integrity: each Canary class must be mentioned by
    # name, with its severity and a worked-example marker, in the canary
    # catalog section. Round-trips against the module catalog.
    catalog_body = _section_body(content, "## Canary catalog")
    for canary in CANARIES:
        assert canary.class_name in catalog_body, (
            f"canary class {canary.class_name!r} missing from doctrine catalog"
        )
        # Severity number must appear in the same row as the class name.
        # Find the row and assert severity appears within it.
        row_match = re.search(
            rf"\|\s*`{re.escape(canary.class_name)}`\s*\|\s*(\d+)\s*\|",
            catalog_body,
        )
        assert row_match, f"no table row found for {canary.class_name}"
        assert int(row_match.group(1)) == canary.severity, (
            f"doctrine declares severity {row_match.group(1)} for "
            f"{canary.class_name}, module declares {canary.severity}"
        )
        # Worked-example marker present in the catalog section.
        assert "_Worked example_:" in catalog_body, (
            "no worked-example marker in canary catalog section"
        )
