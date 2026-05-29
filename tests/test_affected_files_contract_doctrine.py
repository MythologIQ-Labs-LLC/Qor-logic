"""Phase 110 (#136): SG-AffectedFilesContract-A doctrine anchor.

Invokes a parser over the countermeasure catalog and asserts on its structured
output (entry presence + sub-leaves + bidirectional sibling cross-refs), so a
silently-dropped entry or a missing back-reference fails the suite.
"""
from __future__ import annotations

import re
from pathlib import Path

_DOCTRINE = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-shadow-genome-countermeasures.md"


def _section(text: str, sg_id: str) -> str:
    """Body of the `## <sg_id> ...` section up to the next `## ` heading."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("## ") and sg_id in ln), None)
    if start is None:
        return ""
    body = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        body.append(ln)
    return "\n".join(body)


def test_entry_defined_with_required_sections():
    text = _DOCTRINE.read_text(encoding="utf-8")
    body = _section(text, "SG-AffectedFilesContract-A")
    assert body, "SG-AffectedFilesContract-A entry must exist"
    low = body.lower()
    # both named sub-leaves present
    assert "signature-widening cascade" in low or "call-graph" in low
    assert "persistence cascade" in low or "persistence-layer cascade" in low or "persistence-cascade" in low
    # names its countermeasure issues
    for issue in ("#133", "#134", "#135", "#137"):
        assert issue in body, f"entry must name countermeasure {issue}"


def test_sibling_cross_references_are_bidirectional():
    text = _DOCTRINE.read_text(encoding="utf-8")
    for sibling in ("SG-CitationDrift-A", "SG-AuthorAuditMomentum-A"):
        body = _section(text, sibling)
        assert body, f"{sibling} section must exist"
        assert "SG-AffectedFilesContract-A" in body, (
            f"{sibling} must back-reference SG-AffectedFilesContract-A"
        )
