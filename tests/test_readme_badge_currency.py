"""Phase 49: README badge currency enforcement (G-4).

Each test invokes the unit (the counting helper or pytest collect),
parses the README badge declared value, asserts on the (declared, actual)
tuple. Functionality tests, not presence checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_badge_currency_module_importable():
    """Helper module exists with the canonical surface."""
    from qor.scripts import badge_currency
    assert callable(badge_currency.count_tests)
    assert callable(badge_currency.count_ledger_entries)
    assert callable(badge_currency.count_skills)
    assert callable(badge_currency.count_agents)
    assert callable(badge_currency.count_doctrines)
    assert callable(badge_currency.parse_readme_badges)
    assert callable(badge_currency.check_currency)


def test_parse_readme_badges_returns_all_keys():
    """parse_readme_badges() finds Tests, Ledger, Skills, Agents, Doctrines."""
    from qor.scripts.badge_currency import parse_readme_badges
    declared = parse_readme_badges(REPO_ROOT / "README.md")
    expected_keys = {"tests", "ledger", "skills", "agents", "doctrines"}
    assert expected_keys.issubset(declared.keys()), (
        f"README must declare badges for {expected_keys}; got {declared.keys()}"
    )
    for key, val in declared.items():
        assert isinstance(val, int), f"{key} declared value must parse to int; got {val!r}"
        assert val > 0, f"{key} declared value must be positive; got {val}"


def test_readme_ledger_badge_matches_entry_count():
    """README Ledger badge declares the actual entry count (strict equality)."""
    from qor.scripts.badge_currency import count_ledger_entries, parse_readme_badges
    actual = count_ledger_entries(REPO_ROOT / "docs" / "META_LEDGER.md")
    declared = parse_readme_badges(REPO_ROOT / "README.md")["ledger"]
    assert declared == actual, (
        f"README Ledger badge declares {declared} but actual entry count is {actual}. "
        f"Update README.md or run /qor-substantiate."
    )


def test_readme_skills_badge_matches_skill_count():
    from qor.scripts.badge_currency import count_skills, parse_readme_badges
    actual = count_skills(REPO_ROOT)
    declared = parse_readme_badges(REPO_ROOT / "README.md")["skills"]
    assert declared == actual, (
        f"README Skills badge declares {declared} but actual SKILL.md count is {actual}."
    )


def test_readme_agents_badge_matches_agent_count():
    from qor.scripts.badge_currency import count_agents, parse_readme_badges
    actual = count_agents(REPO_ROOT)
    declared = parse_readme_badges(REPO_ROOT / "README.md")["agents"]
    assert declared == actual, (
        f"README Agents badge declares {declared} but actual agent count is {actual}."
    )


def test_readme_tests_badge_matches_test_count():
    """README Tests badge declares the actual test count (strict equality).

    Closes the F7 prompt-surface-review finding: prior to this test, the
    currency suite covered ledger/skills/agents/doctrines but not the
    Tests badge, which had silently drifted by 91 tests (declared 1740;
    actual 1831 at the time of the gap-detection).
    """
    from qor.scripts.badge_currency import count_tests, parse_readme_badges
    actual = count_tests(REPO_ROOT)
    declared = parse_readme_badges(REPO_ROOT / "README.md")["tests"]
    assert declared == actual, (
        f"README Tests badge declares {declared} but actual test count is {actual}. "
        f"Update README.md."
    )


def test_readme_doctrines_badge_matches_doctrine_count():
    from qor.scripts.badge_currency import count_doctrines, parse_readme_badges
    actual = count_doctrines(REPO_ROOT)
    declared = parse_readme_badges(REPO_ROOT / "README.md")["doctrines"]
    assert declared == actual, (
        f"README Doctrines badge declares {declared} but actual doctrine count is {actual}."
    )


def test_check_currency_returns_clean_for_synthetic_match(tmp_path):
    """Functional test of check_currency() with synthetic README + ledger.

    Invokes the function with controlled inputs; asserts the returned mismatch
    list is empty when declared == actual.
    """
    from qor.scripts.badge_currency import check_currency

    # Build a tiny synthetic repo layout with matching declared/actual values.
    (tmp_path / "qor" / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "qor" / "skills" / "demo" / "SKILL.md").write_text("test")
    (tmp_path / "qor" / "agents").mkdir(parents=True)
    (tmp_path / "qor" / "agents" / "demo.md").write_text("test")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "doctrine-demo.md").write_text("test")
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("### Entry #1\n### Entry #2\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(
        # Use real shields.io badge URL format that parse_readme_badges() matches.
        "img.shields.io/badge/Tests-100%20passing-x "
        "img.shields.io/badge/Ledger-2%20entries-x "
        "img.shields.io/badge/Skills-1-x "
        "img.shields.io/badge/Agents-1-x "
        "img.shields.io/badge/Doctrines-1-x ",
        encoding="utf-8",
    )
    mismatches = check_currency(
        tmp_path, ledger, tests_tolerance=10000, skip_tests=True,
    )
    assert mismatches == [], f"clean state should produce empty list; got {mismatches}"


def test_check_currency_reports_mismatch_for_synthetic_drift(tmp_path):
    """Functional test: returned list names which badges drift."""
    from qor.scripts.badge_currency import check_currency

    (tmp_path / "qor" / "skills" / "a").mkdir(parents=True)
    (tmp_path / "qor" / "skills" / "a" / "SKILL.md").write_text("test")
    (tmp_path / "qor" / "skills" / "b").mkdir(parents=True)
    (tmp_path / "qor" / "skills" / "b" / "SKILL.md").write_text("test")
    (tmp_path / "qor" / "agents").mkdir(parents=True)
    (tmp_path / "qor" / "references").mkdir(parents=True)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("", encoding="utf-8")
    readme = tmp_path / "README.md"
    # Declared 5 skills, actual 2 → mismatch
    readme.write_text(
        "img.shields.io/badge/Tests-100-x "
        "img.shields.io/badge/Ledger-0-x "
        "img.shields.io/badge/Skills-5-x "
        "img.shields.io/badge/Agents-0-x "
        "img.shields.io/badge/Doctrines-0-x ",
        encoding="utf-8",
    )
    mismatches = check_currency(
        tmp_path, ledger, tests_tolerance=10000, skip_tests=True,
    )
    assert any("skills" in m.lower() for m in mismatches), (
        f"mismatch list should name 'skills'; got {mismatches}"
    )
