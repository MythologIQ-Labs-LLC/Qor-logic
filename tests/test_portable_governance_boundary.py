"""Regression contract for the Phase 241 portable/enterprise boundary."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs" / "ADR_PORTABLE_GOVERNANCE_ENGINE_BOUNDARY.md"
REFERENCE = ROOT / "qor" / "references" / "downstream-enforcement-boundary.md"


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


def test_procedure_execution_evidence_semantics_stay_in_base() -> None:
    text = (_text(ADR) + _text(REFERENCE)).lower()
    assert "governed-procedure execution evidence" in text
    assert "canonical qor owns the portable evidence satisfaction semantics" in text
    assert "downstream signer" in text or "downstream wrapper" in text


def test_platform_cannot_promote_agent_self_report_to_independent_evidence() -> None:
    text = _text(REFERENCE).lower()
    assert "platform success state cannot promote agent self-report" in text
    assert "cannot decide by itself that procedure-execution evidence is valid" in text


def test_procedure_evidence_is_distinct_from_projection_receipt_and_authority() -> None:
    text = (_text(ADR) + _text(REFERENCE)).lower()
    assert "not the same thing as evidence that a governed skill/procedure executed" in text
    assert "does not substitute for human approval" in text


def test_base_boundary_forbids_platform_administration() -> None:
    text = _text(ADR).lower()
    assert "does **not** own enterprise platform administration" in text
    assert "no github api client" in text
    # Iteration-5 hardening (independent-audit F5): assert the reference's
    # actual binding guard sentence, not the absence of a phrase nobody
    # would write there.
    assert (
        "Canonical Qor does not define a GitHub/GitLab/Azure DevOps/Bitbucket "
        "mutation API for these concepts." in _text(REFERENCE)
    )


def test_authority_direction_block_survives_as_a_block() -> None:
    """Iteration-5 hardening (independent-audit F5): the ADR's authority-flow
    diagram must survive as an ordered block -- a document gutted to a bullet
    list of scattered phrases must fail here."""
    text = _text(ADR)
    block = text[text.index("```text"):]
    for upstream, downstream in (
        ("Qor invariant contract + portable evidence semantics",
         "portable repository facts + evidence verdicts"),
        ("portable repository facts + evidence verdicts",
         "enterprise desired state (downstream)"),
        ("enterprise desired state (downstream)",
         "platform-specific projection (downstream)"),
        ("platform-specific projection (downstream)",
         "GitHub / GitLab / other enforcement"),
    ):
        assert block.index(upstream) < block.index(downstream), (
            f"authority direction inverted or broken: {upstream!r} must "
            f"precede {downstream!r}"
        )


def test_no_qor_module_imports_a_forge_sdk() -> None:
    """Iteration-5 hardening (independent-audit F5): the non-goal 'no forge
    mutation surface' is enforced against executable code, not prose."""
    import re

    forge = re.compile(
        r"^\s*(?:import|from)\s+(?:github|gitlab|azure\.devops|atlassian|pygithub)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    offenders = [
        str(p) for p in (ROOT / "qor").rglob("*.py")
        if forge.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    assert offenders == []


def test_first_enterprise_consumer_stays_publication_safe() -> None:
    text = _text(ADR) + _text(REFERENCE)
    assert "paired private enterprise tracer bullet" in text.lower()
    assert "Qor-logic-plus#" not in text
    assert "MythologIQ-Labs-LLC/Qor-logic-plus" not in text
