"""Phase 61 path_match tests."""
from __future__ import annotations

from qor.scripts.path_match import find_matching_prefix, matches, matches_any


def test_matches_exact_equality():
    assert matches("qor/scripts/ledger_hash.py", "qor/scripts/ledger_hash.py") is True


def test_matches_directory_boundary():
    assert matches("qor/skills/governance/qor-audit/SKILL.md", "qor/skills/governance") is True


def test_matches_extension_boundary():
    assert matches("qor/scripts/ledger_hash.py", "qor/scripts/ledger_hash") is True


def test_matches_rejects_sibling_lookalike():
    """The M1 regression case: bare prefix must not match a longer module."""
    assert matches("qor/scripts/ledger_hash_validation.py", "qor/scripts/ledger_hash") is False
    assert matches("qor/scripts/ledger_hash_v2.py", "qor/scripts/ledger_hash") is False


def test_matches_rejects_partial_segment_match():
    assert matches("qor/scripts/foo_bar.py", "qor/scripts/foo") is False


def test_matches_returns_false_when_not_a_prefix():
    assert matches("qor/scripts/ledger_hash.py", "qor/scripts/hash_guard") is False


def test_matches_empty_prefix_matches_only_empty_path():
    assert matches("", "") is True
    # Empty prefix would otherwise match anything by startswith; boundary rule
    # rejects when path[0] is not a boundary char.
    assert matches("anything", "") is False


def test_matches_any_returns_true_on_first_hit():
    assert matches_any("qor/scripts/ledger_hash.py", ("docs/", "qor/scripts/ledger_hash")) is True


def test_matches_any_returns_false_when_no_hit():
    assert matches_any("qor/scripts/x.py", ("docs/", "tests/")) is False


def test_matches_any_short_circuits_on_empty_prefixes():
    assert matches_any("anything", ()) is False


def test_find_matching_prefix_returns_first_match():
    out = find_matching_prefix(
        "qor/skills/governance/qor-substantiate/SKILL.md",
        ("docs/", "qor/skills/", "qor/skills/governance/"),
    )
    assert out == "qor/skills/"


def test_find_matching_prefix_returns_none_when_no_match():
    assert find_matching_prefix("qor/x.py", ("docs/", "tests/")) is None
