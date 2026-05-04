"""Phase 59: doctrine round-trip integrity for ideation readiness."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-ideation-readiness.md"
SCHEMA = REPO_ROOT / "qor" / "gates" / "schema" / "ideation.schema.json"


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
                         re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else ""


def test_doctrine_declares_all_10_section_subsections():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## The 10 ideation artifact sections")
    sections = re.findall(r"^### \d+\.\s+", body, re.MULTILINE)
    assert len(sections) == 10, f"expected 10 ### subsections; got {len(sections)}"


def test_doctrine_routing_decision_matrix_lists_all_readiness_status_values():
    text = DOCTRINE.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    enum = schema["properties"]["readiness"]["properties"]["status"]["enum"]
    matrix = _section_body(text, "## Routing decision matrix")
    for value in enum:
        assert value in matrix, f"routing matrix missing readiness.status enum {value!r}"


def test_doctrine_failure_mode_catalog_lists_8_canonical_unraveling_points():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Failure-mode catalog (8 unraveling points)")
    expected = [
        "Premature Solutioning", "Language Drift", "Assumption Laundering",
        "Scope Seepage", "Research Asymmetry", "Failure Blindness",
        "Premature Decomposition", "Validation Collapse",
    ]
    for pattern in expected:
        assert pattern in body, f"failure-mode catalog missing {pattern!r}"
