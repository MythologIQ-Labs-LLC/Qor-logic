"""Phase 244: qor-harden implementation-quality contract tests."""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-harden" / "SKILL.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-implementation-quality.md"
SWEEP = REPO_ROOT / "qor" / "references" / "implementation-quality-sweep.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_harden_skill_and_shared_quality_contract_exist():
    assert SKILL.is_file()
    assert DOCTRINE.is_file()
    assert SWEEP.is_file()


def test_harden_is_explicitly_environment_agnostic():
    text = _read(SKILL).lower()
    for term in (
        "agent",
        "host",
        "repository",
        "language",
        "framework",
        "provider",
        "forge",
        "runtime",
    ):
        assert term in text
    assert "never" in text and "infer ai authorship" in text


def test_harden_supports_all_scope_modes_and_dispositions():
    text = _read(SKILL)
    for mode in ("focused", "changeset", "component", "comprehensive"):
        assert f"`{mode}`" in text
    assert "`review`" in text
    assert "`repair`" in text


def test_harden_uses_canonical_taxonomy_without_language_specific_rules():
    skill = _read(SKILL)
    sweep = _read(SWEEP)
    dimensions = (
        "IQ-COMPLETE",
        "IQ-CORRECT",
        "IQ-TRUST",
        "IQ-CONTEXT",
        "IQ-COMPLEX",
        "IQ-RESOURCE",
        "IQ-CONTRACT",
        "IQ-MAINTAIN",
        "IQ-OBSERVE",
    )
    for dimension in dimensions:
        assert dimension in sweep
        assert dimension in skill

    # The canonical contract must not hard-code one ecosystem's package or
    # language-specific anti-pattern vocabulary as a universal requirement.
    lower = (skill + sweep + _read(DOCTRINE)).lower()
    for forbidden in ("npm install", "pip install", "cargo add", "as any is a bug"):
        assert forbidden not in lower


def test_review_disposition_is_non_mutating_and_repair_is_scope_bound():
    text = _read(SKILL).lower()
    assert "never** mutate implementation in `review` disposition" in text
    assert "repair mode changes only confirmed in-scope defects" in text
    assert "never** widen mutation scope" in text


def test_abstention_is_a_required_successful_outcome():
    doctrine = _read(DOCTRINE)
    skill = _read(SKILL)
    sweep = _read(SWEEP)
    assert "Abstention is a successful outcome" in doctrine
    assert "A `YES` with zero code changes is a successful result." in skill
    assert "`YES` with no code changes is a valid" in sweep


def test_existing_lifecycle_profile_boundaries_are_defined():
    sweep = _read(SWEEP)
    for skill in (
        "/qor-plan",
        "/qor-audit",
        "/qor-implement",
        "/qor-debug",
        "/qor-refactor",
        "/qor-substantiate",
        "/qor-deep-audit",
    ):
        assert skill in sweep


def test_harden_preserves_debug_refactor_substantiate_authority_boundaries():
    text = _read(SKILL)
    assert "cause is uncertain for an observed failure -> `/qor-debug`" in text
    assert "known structural simplification -> `/qor-refactor`" in text
    assert "independent proof is required after implementation -> `/qor-substantiate`" in text


def test_ship_verdict_is_truthful_and_three_state():
    text = _read(SKILL)
    assert "`YES`" in text
    assert "`NO`" in text
    assert "`INCONCLUSIVE`" in text
    assert "NEVER** claim verification that was not executed" in text
