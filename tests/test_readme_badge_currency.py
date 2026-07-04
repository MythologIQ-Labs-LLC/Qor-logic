"""Phase 49: README badge currency helpers (G-4); Phase 164 retirement.

The five live-equality tests (declared badge == current repo truth) were
retired in Phase 164 (generate-not-assert, research entry #378 rec 2): that
class broke on every seal. Currency is now enforced where repo state is
stable -- substantiate Step 6.5 `seal_artifacts --check` (ABORT) and the CI
`seal-artifacts currency` step. The remaining tests here exercise the helper
functions against synthetic fixtures.
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
