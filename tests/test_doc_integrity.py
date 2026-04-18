"""Phase 28 Phase 1: doc_integrity topology / glossary / orphan checks.

Tests run against tmp_path-based synthetic repos (deterministic, no live-state
coupling per doctrine-test-discipline Rule 3).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


def _write_glossary(path: Path, entries: list[str]) -> None:
    body = "# Glossary\n\n" + "\n\n".join(entries) + "\n"
    path.write_text(body, encoding="utf-8")


def _entry(
    term: str,
    definition: str = "A thing.",
    home: str = "README.md",
    referenced_by: list[str] | None = None,
    introduced_in_plan: str | None = None,
) -> str:
    lines = [
        "```yaml",
        f"term: {term}",
        f"definition: {definition}",
        f"home: {home}",
    ]
    if referenced_by is not None:
        lines.append(f"referenced_by: {referenced_by}")
    if introduced_in_plan is not None:
        lines.append(f"introduced_in_plan: {introduced_in_plan}")
    lines.append("```")
    return "\n".join(lines)


# ---------- check_topology ----------

def test_check_topology_minimal_raises_without_readme(tmp_path):
    with pytest.raises(ValueError, match="README"):
        doc_integrity.check_topology("minimal", str(tmp_path))


def test_check_topology_minimal_passes_with_readme(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    doc_integrity.check_topology("minimal", str(tmp_path))


def test_check_topology_standard_raises_without_glossary(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    with pytest.raises(ValueError, match="glossary"):
        doc_integrity.check_topology("standard", str(tmp_path))


@pytest.mark.parametrize(
    "missing",
    ["architecture.md", "lifecycle.md", "operations.md", "policies.md"],
)
def test_check_topology_system_raises_per_artifact(tmp_path, missing):
    (tmp_path / "README.md").write_text("# x\n")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text("# g\n")
    (tmp_path / "docs").mkdir(exist_ok=True)
    for name in ("architecture.md", "lifecycle.md", "operations.md", "policies.md"):
        if name != missing:
            (tmp_path / "docs" / name).write_text("# x\n")
    with pytest.raises(ValueError, match=missing):
        doc_integrity.check_topology("system", str(tmp_path))


def test_check_topology_legacy_no_op(tmp_path):
    doc_integrity.check_topology("legacy", str(tmp_path))


def test_check_topology_rejects_unknown_tier(tmp_path):
    with pytest.raises(ValueError, match="tier"):
        doc_integrity.check_topology("bogus", str(tmp_path))


# ---------- check_glossary ----------

def test_check_glossary_raises_on_missing_term(tmp_path):
    g = tmp_path / "g.md"
    _write_glossary(g, [_entry("Known")])
    with pytest.raises(ValueError, match="Foo"):
        doc_integrity.check_glossary(str(g), declared_terms=["Foo"])


def test_check_glossary_raises_on_empty_definition(tmp_path):
    g = tmp_path / "g.md"
    _write_glossary(g, [_entry("Foo", definition="")])
    with pytest.raises(ValueError, match="definition"):
        doc_integrity.check_glossary(str(g), declared_terms=["Foo"])


def test_check_glossary_raises_on_bad_home_path(tmp_path):
    g = tmp_path / "g.md"
    _write_glossary(g, [_entry("Foo", home="does-not-exist.md")])
    with pytest.raises(ValueError, match="home"):
        doc_integrity.check_glossary(str(g), declared_terms=["Foo"], repo_root=str(tmp_path))


def test_check_glossary_passes_with_valid_entry(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    g = tmp_path / "g.md"
    _write_glossary(g, [_entry("Foo", home="README.md")])
    doc_integrity.check_glossary(str(g), declared_terms=["Foo"], repo_root=str(tmp_path))


# ---------- check_orphans ----------

def test_check_orphans_raises_on_no_consumers(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    g = tmp_path / "g.md"
    _write_glossary(g, [_entry("Dead", home="README.md")])
    with pytest.raises(ValueError, match="Dead"):
        doc_integrity.check_orphans(
            str(g), current_session_plan_tag="phase99-other", repo_root=str(tmp_path)
        )


def test_check_orphans_allows_new_term_with_plan_marker(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    g = tmp_path / "g.md"
    _write_glossary(
        g,
        [_entry("New", home="README.md", introduced_in_plan="phase28-doc-integrity")],
    )
    doc_integrity.check_orphans(
        str(g), current_session_plan_tag="phase28-doc-integrity", repo_root=str(tmp_path)
    )


def test_check_orphans_allows_term_with_referenced_by(tmp_path):
    (tmp_path / "README.md").write_text("# x\n")
    g = tmp_path / "g.md"
    _write_glossary(
        g, [_entry("Used", home="README.md", referenced_by=["CLAUDE.md"])]
    )
    doc_integrity.check_orphans(
        str(g), current_session_plan_tag="phase99-other", repo_root=str(tmp_path)
    )
