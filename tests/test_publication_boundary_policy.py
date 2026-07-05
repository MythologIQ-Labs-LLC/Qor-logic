"""The public-repository boundary must remain visible to every agent."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTRINE = ROOT / "qor" / "references" / "doctrine-publication-boundary.md"


def test_repository_agent_rules_make_boundary_mandatory() -> None:
    body = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "every human or automated agent" in body
    assert "applies retroactively" in body
    assert "MUST be deleted or anonymized" in body
    assert "docs/Lessons-Learned/" in body


def test_host_and_contributor_instructions_link_canonical_doctrine() -> None:
    paths = (
        ROOT / "CLAUDE.md",
        ROOT / "GEMINI.md",
        ROOT / ".github" / "copilot-instructions.md",
        ROOT / ".kilocode" / "rules" / "publication-boundary.md",
        ROOT / "CONTRIBUTING.md",
    )
    for path in paths:
        body = path.read_text(encoding="utf-8")
        assert "doctrine-publication-boundary.md" in body, path


def test_doctrine_covers_persisted_surfaces_and_only_exception() -> None:
    body = DOCTRINE.read_text(encoding="utf-8")
    assert "MUST NOT directly identify" in body
    assert "This doctrine applies retroactively" in body
    assert "The only exception" in body
    assert "`docs/Lessons-Learned/`" in body
    assert "persistable output" in body
