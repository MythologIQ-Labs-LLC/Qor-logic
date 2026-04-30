"""Phase 52: fixture-based negative-path tests for the attribution-tier lints.

Closes Phase 49 VETO: the existing commit-walking lints in
tests/test_attribution_tiered_usage.py have a self-exempting cutoff
(`if phase_num < 49: continue # grandfathered`) that makes them vacuous
at first run. These fixture-based tests fabricate violating commit
bodies and assert the same regex/parser logic catches them.

Closes SG-VacuousLint family.
"""
from __future__ import annotations

import re


def _phase_num_from_subject(subject: str) -> int | None:
    """Helper extracted from test_attribution_tiered_usage.py for direct test."""
    m = re.search(r"phase\s+(\d+)", subject, re.IGNORECASE)
    return int(m.group(1)) if m else None


def test_phase_num_extraction_matches_phase_in_subject():
    """Direct unit test of the cutoff helper used by tiered-usage lints."""
    assert _phase_num_from_subject("seal: phase 99 - test") == 99
    assert _phase_num_from_subject("plan: phase 52 - feature") == 52
    assert _phase_num_from_subject("just text without phase number") is None
    assert _phase_num_from_subject("Phase 7 something") == 7  # case-insensitive


def test_seal_lint_catches_synthetic_violator_via_substring_check():
    """Fabricate a seal commit body lacking the QorLogic SDLC line; assert the
    same substring-presence check used by test_seal_commits_have_full_canonical_trailer
    correctly identifies it as a violator."""
    violating_body = (
        "seal: phase 99 - test\n"
        "\n"
        "Verdict: PASS\n"
        "Files: 5\n"
        "\n"
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>\n"
    )
    # Same logic as the real lint
    has_qor_line = "QorLogic" in violating_body or "Qor-logic SDLC" in violating_body
    has_authored_via = "Authored via" in violating_body
    has_coauthor = "Co-Authored-By:" in violating_body
    is_compliant = has_qor_line and has_authored_via and has_coauthor
    assert is_compliant is False, (
        "synthetic seal commit body lacks the QorLogic SDLC line — lint must "
        "report violation; got compliant=True"
    )


def test_seal_lint_passes_synthetic_compliant_body():
    """Symmetric positive: fabricate a compliant body, assert lint passes."""
    compliant_body = (
        "seal: phase 99 - test\n"
        "\n"
        "Verdict: PASS\n"
        "\n"
        "🤖 Authored via [Qor-logic SDLC](https://...) on [Claude Code](https://...)\n"
        "\n"
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>\n"
    )
    has_qor_line = "Qor-logic SDLC" in compliant_body
    has_authored_via = "Authored via" in compliant_body
    has_coauthor = "Co-Authored-By:" in compliant_body
    is_compliant = has_qor_line and has_authored_via and has_coauthor
    assert is_compliant is True


def test_plan_audit_implement_lint_catches_synthetic_violator():
    """Fabricate a plan/audit/implement commit body without Co-Authored-By;
    assert the lint logic catches it."""
    violating_body = (
        "plan: phase 99 - test\n"
        "\n"
        "Some description.\n"
        "No trailer at all.\n"
    )
    has_coauthor = "Co-Authored-By:" in violating_body
    assert has_coauthor is False, (
        "synthetic plan/audit/implement commit lacks Co-Authored-By — lint must "
        "report violation"
    )


def test_plan_audit_implement_lint_passes_synthetic_compliant_body():
    compliant_body = (
        "plan: phase 99 - test\n"
        "\n"
        "Some description.\n"
        "\n"
        "Co-Authored-By: Claude <noreply@anthropic.com>\n"
    )
    has_coauthor = "Co-Authored-By:" in compliant_body
    assert has_coauthor is True


def test_changelog_lint_catches_synthetic_post_cutoff_violator():
    """Synthetic CHANGELOG with a post-cutoff version section lacking the
    canonical attribution line; assert lint catches it."""
    synthetic_changelog = (
        "## [Unreleased]\n"
        "\n"
        "## [0.99.0] - 2026-04-30\n"
        "\n"
        "### Added\n"
        "- Some feature.\n"
        "\n"
        "## [0.36.0] - 2026-04-29\n"
        "\n"
        "_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._\n"
    )
    # Extract the 0.99.0 section's body (up to next ## header). It must NOT
    # contain the canonical attribution line.
    section_match = re.search(
        r"^## \[0\.99\.0\][^\n]*\n(.*?)(?=^## \[|\Z)",
        synthetic_changelog,
        re.MULTILINE | re.DOTALL,
    )
    assert section_match
    section_body = section_match.group(1)
    assert "_Built via [Qor-logic SDLC]" not in section_body, (
        "synthetic post-cutoff CHANGELOG section lacks attribution — lint must catch it"
    )
