"""Regression contract for the Phase 241 portable/enterprise boundary."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs" / "ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md"
REFERENCE = ROOT / "qor" / "platform" / "enforcement.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_base_names_portable_governance_engine() -> None:
    assert "portable governance engine" in _text(ADR).lower()
    assert "portable governance engine" in _text(REFERENCE).lower()


def test_three_surfaces_have_separate_owners() -> None:
    text = _text(REFERENCE).lower()
    for phrase in (
        "execution adaptation",
        "portable governance evaluation",
        "enterprise enforcement projection",
    ):
        assert phrase in text


def test_platform_state_is_not_semantic_authority() -> None:
    text = _text(ADR).lower() + _text(REFERENCE).lower()
    assert "platform state is evidence" in text
    assert "reverse direction is prohibited" in text


def test_uncertainty_and_coverage_are_not_silently_promoted() -> None:
    text = _text(REFERENCE)
    assert "`indeterminate`" in text
    assert "`not_projectable`" in text
    assert "never treat this as satisfied" in text
    assert "never silently drop it" in text


def test_base_boundary_forbids_platform_administration() -> None:
    text = _text(ADR).lower()
    assert "does **not** own enterprise platform administration" in text
    assert "no github api client" in text
    assert "no github api client" not in _text(REFERENCE).lower()


def test_first_enterprise_consumer_stays_publication_safe() -> None:
    text = _text(ADR) + _text(REFERENCE)
    assert "paired private enterprise tracer bullet" in text.lower()
    assert "Qor-logic-plus#" not in text
    assert "MythologIQ-Labs-LLC/Qor-logic-plus" not in text
