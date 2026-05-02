"""Phase 58: doctrine round-trip integrity for procedural-fidelity."""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts.procedural_fidelity import DEVIATION_CLASSES

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-procedural-fidelity.md"


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
                         re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else ""


def test_doctrine_declares_all_4_v1_deviation_classes():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## The four v1 deviation classes")
    for cls in DEVIATION_CLASSES:
        assert f"### `{cls}`" in body, f"doctrine missing subsection for `{cls}`"


def test_doctrine_doc_surface_coverage_rule_lists_all_4_system_docs():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Doc-surface coverage rule")
    for doc in (
        "docs/SYSTEM_STATE.md", "docs/operations.md",
        "docs/architecture.md", "docs/lifecycle.md",
    ):
        assert doc in body, f"doc-surface coverage rule missing literal {doc!r}"


def test_doctrine_references_section_cites_implementation_module():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## References")
    assert "qor/scripts/procedural_fidelity.py" in body
    assert "SG-DocSurfaceUncovered-A" in body
