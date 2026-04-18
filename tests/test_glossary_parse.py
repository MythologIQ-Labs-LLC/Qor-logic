"""Phase 28 Phase 1: glossary frontmatter parser.

Confirms the parser uses yaml.safe_load (SG-Phase24-B) and produces structured
Entry records with actionable error messages.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


def _glossary(body: str) -> str:
    return "# Glossary\n\n" + body + "\n"


def test_parse_empty_glossary_ok(tmp_path):
    p = tmp_path / "g.md"
    p.write_text("# Glossary\n\nNo entries yet.\n", encoding="utf-8")
    assert doc_integrity.parse_glossary(str(p)) == []


def test_parse_single_entry_round_trip(tmp_path):
    p = tmp_path / "g.md"
    p.write_text(
        _glossary(
            "```yaml\n"
            "term: Phase\n"
            "definition: A stage in the governance lifecycle.\n"
            "home: qor/gates/chain.md\n"
            "referenced_by:\n"
            "  - CLAUDE.md\n"
            "  - qor/gates/delegation-table.md\n"
            "```"
        ),
        encoding="utf-8",
    )
    entries = doc_integrity.parse_glossary(str(p))
    assert len(entries) == 1
    e = entries[0]
    assert e.term == "Phase"
    assert e.definition.startswith("A stage")
    assert e.home == "qor/gates/chain.md"
    assert e.referenced_by == ["CLAUDE.md", "qor/gates/delegation-table.md"]


def test_parse_malformed_yaml_raises(tmp_path):
    p = tmp_path / "g.md"
    p.write_text(
        _glossary("```yaml\nterm: Foo\n  bad: : indent\n```"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="YAML"):
        doc_integrity.parse_glossary(str(p))


def test_parse_duplicate_term_raises(tmp_path):
    p = tmp_path / "g.md"
    p.write_text(
        _glossary(
            "```yaml\nterm: Foo\ndefinition: a\nhome: README.md\n```\n\n"
            "```yaml\nterm: Foo\ndefinition: b\nhome: README.md\n```"
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        doc_integrity.parse_glossary(str(p))


def test_parse_glossary_rejects_unsafe_tags(tmp_path):
    """Proves yaml.safe_load is in use: unsafe tags raise rather than instantiate.
    Addresses SG-Phase24-B (unsafe deserializer defaults).
    """
    p = tmp_path / "g.md"
    p.write_text(
        _glossary(
            "```yaml\n"
            "term: Evil\n"
            "definition: !!python/object/apply:os.system ['echo pwn']\n"
            "home: README.md\n"
            "```"
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        doc_integrity.parse_glossary(str(p))


def test_yaml_safe_load_discipline_covers_doc_integrity():
    """Confirms doc_integrity.py is within tests/test_yaml_safe_load_discipline.py
    scan scope. Addresses SG-Phase25-A (discipline scope gap).
    """
    import test_yaml_safe_load_discipline as disc
    repo = Path(__file__).resolve().parent.parent
    # Scanner roots include 'qor'; doc_integrity.py lives at qor/scripts/doc_integrity.py
    assert "qor" in disc._ROOTS
    target = repo / "qor" / "scripts" / "doc_integrity.py"
    assert target.exists(), f"doc_integrity.py missing at {target}"
    # The scanner's _scan would include it by virtue of rglob('*.py') under 'qor'.
    # No widening required; this test fails only if the scanner's roots change.
