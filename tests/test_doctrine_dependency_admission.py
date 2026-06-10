"""Phase 103 (GH #118 P2): doctrine-dependency-admission.md content tests."""
from __future__ import annotations

import pathlib

# Resolve from __file__ so the test runs from any cwd (GAP-TEST-10), not only repo-root.
_REPO = pathlib.Path(__file__).resolve().parent.parent
_DOCTRINE = _REPO / "qor" / "references" / "doctrine-dependency-admission.md"


def _read() -> str:
    return _DOCTRINE.read_text(encoding="utf-8")


def test_doctrine_file_exists():
    assert _DOCTRINE.is_file(), (
        "qor/references/doctrine-dependency-admission.md must be committed"
    )


def test_doctrine_declares_minimum_age_threshold():
    text = _read().lower()
    # Doctrine must explicitly name the 14-day window
    assert "14 days" in text or "14-day" in text, (
        "doctrine must name the 14-day minimum-age threshold explicitly"
    )
    # And explain the cooling-period concept
    assert "cooling-period" in text or "cooling period" in text, (
        "doctrine must describe the cooling-period concept"
    )


def test_doctrine_declares_override_procedure():
    text = _read().lower()
    # Three components of the override procedure must each be present
    assert "meta_ledger" in text or "ledger entry" in text, (
        "override procedure must name the META_LEDGER entry requirement"
    )
    assert "dep-admit-override" in text, (
        "override procedure must name the dep-admit-override PR label"
    )
    assert "30 days" in text or "30-day" in text, (
        "override procedure must name the 30-day follow-up re-evaluation window"
    )


def test_doctrine_references_dependency_review_workflow():
    """Coordination with the Phase 102 dependency-review workflow must be explicit."""
    text = _read()
    assert "pr-dependency-review.yml" in text or "dependency-review-action" in text, (
        "doctrine must reference the Phase 102 dep-review workflow as coordinated control"
    )


def test_doctrine_carries_ssdf_mapping():
    text = _read()
    # NIST SSDF practice tags should be referenced for compliance traceability
    assert "PS.2.1" in text, "doctrine must cite SSDF PS.2.1"
    assert "RV.1.1" in text, "doctrine must cite SSDF RV.1.1"
