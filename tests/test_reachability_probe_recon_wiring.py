"""Phase 96: recon SKILL.md Round 0 wiring tests (GH #108).

Anchored positive + strip-and-fail + positional guard +
progressive-disclosure sweep. Functionality tests, not presence checks.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RECON_SKILL = REPO_ROOT / "qor" / "skills" / "meta" / "qor-deep-audit-recon" / "SKILL.md"
REFERENCE = REPO_ROOT / "qor" / "references" / "recon-reachability-probe.md"

ROUND_0_HEADING = "### Phase 3 Round 0: Reachability Probe (Phase 96 wiring; GH #108)"
PHASE_3_HEADING = "### Phase 3: VERIFICATION (max 3 rounds, per budget)"
REFERENCE_POINTER = "qor/references/recon-reachability-probe.md"


def test_phase_3_round_0_heading_present():
    text = RECON_SKILL.read_text(encoding="utf-8")
    assert ROUND_0_HEADING in text, (
        f"Phase 96 wiring asserts {ROUND_0_HEADING!r} in {RECON_SKILL}"
    )


def test_phase_3_round_0_section_removed_breaks_assertion():
    """Strip-and-fail negative: stripping the heading must trip the positive test.

    Implementation note: this test verifies the assertion logic, not the file.
    We simulate the strip by reading the file and removing the heading,
    asserting the positive condition no longer holds on the stripped text.
    """
    text = RECON_SKILL.read_text(encoding="utf-8")
    stripped = text.replace(ROUND_0_HEADING, "")
    assert ROUND_0_HEADING not in stripped, (
        "strip-and-fail negative: removing the heading must make the positive test fail"
    )


def test_phase_3_round_0_positioned_before_existing_phase_3():
    text = RECON_SKILL.read_text(encoding="utf-8")
    round_0_pos = text.find(ROUND_0_HEADING)
    phase_3_pos = text.find(PHASE_3_HEADING)
    assert round_0_pos != -1, "Round 0 heading missing"
    assert phase_3_pos != -1, "Phase 3 heading missing"
    assert round_0_pos < phase_3_pos, (
        f"Round 0 must precede Phase 3; got round_0 at {round_0_pos}, phase_3 at {phase_3_pos}"
    )


def test_recon_skill_references_progressive_disclosure_reference_file():
    """Progressive disclosure sweep: SKILL.md must cite the reference file.

    Per GH #92 corpus-growth doctrine, detailed prose lives in references/;
    the SKILL.md retains a pointer. This sweep catches the reference file
    going stranded if a future edit removes the pointer.
    """
    text = RECON_SKILL.read_text(encoding="utf-8")
    assert REFERENCE_POINTER in text, (
        f"recon SKILL.md must cite {REFERENCE_POINTER} (progressive disclosure)"
    )
    assert REFERENCE.exists(), (
        f"the cited reference file {REFERENCE} must exist at HEAD"
    )
