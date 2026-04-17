"""Phase 26 Phase 2: audit template slot presence lint."""
from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "qor" / "skills" / "governance" / "qor-audit" / "references" / "qor-audit-templates.md"
FIXTURES = Path(__file__).parent / "fixtures"

GROUND_CLASS_HEADERS = (
    "Section 4 Razor",
    "Orphan file / Macro-arch breach",
    "Plan-text",
    "Process-level",
    "Code-logic defect",
)
ADVISORY_MARKER = "<!-- qor:veto-pattern-advisory -->"
DIRECTIVE_RE = re.compile(r"\*\*Required next action:\*\*")


def _slot_errors(text: str) -> list[str]:
    errors: list[str] = []
    for header in GROUND_CLASS_HEADERS:
        if header not in text:
            errors.append(f"missing ground-class header: {header!r}")
            continue
        # Each ground-class header must be followed (within 20 lines) by a
        # "**Required next action:**" directive.
        idx = text.find(header)
        window = text[idx:idx + 2000]
        if not DIRECTIVE_RE.search(window):
            errors.append(f"missing directive after header: {header!r}")
    if ADVISORY_MARKER not in text:
        errors.append(f"missing marker: {ADVISORY_MARKER}")
    if "## Process Pattern Advisory" not in text:
        errors.append("missing section: '## Process Pattern Advisory'")
    return errors


def test_canonical_template_has_all_slots():
    assert TEMPLATE.exists(), f"missing template: {TEMPLATE}"
    errors = _slot_errors(TEMPLATE.read_text(encoding="utf-8"))
    assert not errors, "Template lint failed:\n  " + "\n  ".join(errors)


def test_fixture_good_passes_lint():
    text = (FIXTURES / "audit_template_good.md").read_text(encoding="utf-8")
    assert _slot_errors(text) == []


def test_fixture_missing_slot_fails_lint():
    text = (FIXTURES / "audit_template_missing_slot.md").read_text(encoding="utf-8")
    errors = _slot_errors(text)
    assert errors, "bad fixture must fail lint"
    assert any("directive" in e for e in errors)
    assert any("Process Pattern Advisory" in e for e in errors)
