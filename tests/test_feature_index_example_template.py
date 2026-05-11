"""Phase 46 worked-example presence + structure tests."""
from __future__ import annotations

from pathlib import Path

PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "templates" / "FEATURE_INDEX.example.md"
)


def _body():
    return PATH.read_text(encoding="utf-8")


def test_example_file_present_at_template_path():
    assert PATH.exists()


def test_example_contains_at_least_one_verified_entry():
    body = _body()
    assert "| verified |" in body or "verified |" in body


def test_example_contains_at_least_one_n_a_entry_with_rationale():
    body = _body()
    assert "n/a" in body
    assert "rationale" in body.lower() or "qa-checklist" in body.lower() or "manual qa" in body.lower()
