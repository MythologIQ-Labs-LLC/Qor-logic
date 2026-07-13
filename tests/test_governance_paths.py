"""Behavioral tests for the shared canonical governance-path resolver (GH #282).

Every test invokes the resolver and asserts on its return value or the raised
GovernancePathError -- no presence-only checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import governance_paths as gp


def _index(root: Path, registered: list[str]) -> None:
    (root / "docs").mkdir(exist_ok=True)
    rows = "\n".join(f"| Doc | `{p}` | stable |" for p in registered)
    (root / "docs" / "GOVERNANCE_INDEX.md").write_text(
        "# Governance Index\n\n**Last Reviewed**: 2026-07-13\n\n" + rows + "\n",
        encoding="utf-8",
    )


# ---------- resolve_architecture_authority ----------

def test_system_tier_resolves_registered_architecture_plan(tmp_path):
    """Sole registered authority docs/ARCHITECTURE_PLAN.md (no architecture.md)."""
    _index(tmp_path, ["docs/ARCHITECTURE_PLAN.md"])
    (tmp_path / "docs" / "ARCHITECTURE_PLAN.md").write_text("# arch plan\n", encoding="utf-8")
    got = gp.resolve_architecture_authority(tmp_path)
    assert got == (tmp_path / "docs" / "ARCHITECTURE_PLAN.md")


def test_legacy_literal_takes_precedence_when_registered_and_present(tmp_path):
    """architecture.md present + registered wins even when ARCHITECTURE_PLAN.md also is."""
    _index(tmp_path, ["docs/architecture.md", "docs/ARCHITECTURE_PLAN.md"])
    (tmp_path / "docs" / "architecture.md").write_text("# arch\n", encoding="utf-8")
    (tmp_path / "docs" / "ARCHITECTURE_PLAN.md").write_text("# arch plan\n", encoding="utf-8")
    got = gp.resolve_architecture_authority(tmp_path)
    assert got == (tmp_path / "docs" / "architecture.md")


def test_no_index_legacy_fallback(tmp_path):
    """No governance index: the legacy literal is the fallback when present."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture.md").write_text("# arch\n", encoding="utf-8")
    got = gp.resolve_architecture_authority(tmp_path)
    assert got == (tmp_path / "docs" / "architecture.md")


def test_missing_architecture_authority_raises(tmp_path):
    _index(tmp_path, ["docs/README.md"])
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_architecture_authority(tmp_path)


def test_multiple_registered_architecture_docs_raises(tmp_path):
    """Two registered architecture-stemmed docs, no legacy literal -> ambiguous."""
    _index(tmp_path, ["docs/ARCHITECTURE_PLAN.md", "docs/architecture-system.md"])
    (tmp_path / "docs" / "ARCHITECTURE_PLAN.md").write_text("# a\n", encoding="utf-8")
    (tmp_path / "docs" / "architecture-system.md").write_text("# b\n", encoding="utf-8")
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_architecture_authority(tmp_path)


def test_unregistered_architecture_doc_present_but_not_in_index_raises(tmp_path):
    """architecture.md on disk but not registered (index present) -> fail closed."""
    _index(tmp_path, ["docs/README.md"])
    (tmp_path / "docs" / "architecture.md").write_text("# arch\n", encoding="utf-8")
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_architecture_authority(tmp_path)


# ---------- resolve_governance_plan_path ----------

def test_registered_non_phase_plan_resolves(tmp_path):
    _index(tmp_path, ["docs/plan-governance-hardening.md"])
    p = tmp_path / "docs" / "plan-governance-hardening.md"
    p.write_text("# plan\n", encoding="utf-8")
    got = gp.resolve_governance_plan_path("docs/plan-governance-hardening.md", tmp_path)
    assert got == p.resolve()


def test_always_allowed_phase_plan_resolves_without_index(tmp_path):
    (tmp_path / "docs").mkdir()
    p = tmp_path / "docs" / "plan-qor-phase99-foo.md"
    p.write_text("# plan\n", encoding="utf-8")
    got = gp.resolve_governance_plan_path("docs/plan-qor-phase99-foo.md", tmp_path)
    assert got == p.resolve()


def test_traversal_rejected_before_read(tmp_path):
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_governance_plan_path("docs/../../etc/passwd", tmp_path)


def test_outside_root_absolute_rejected(tmp_path):
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_governance_plan_path("/etc/passwd", tmp_path)


def test_unsupported_extension_rejected(tmp_path):
    _index(tmp_path, ["docs/plan-governance-hardening.txt"])
    (tmp_path / "docs" / "plan-governance-hardening.txt").write_text("x\n", encoding="utf-8")
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_governance_plan_path("docs/plan-governance-hardening.txt", tmp_path)


def test_unregistered_plan_rejected(tmp_path):
    _index(tmp_path, ["docs/plan-listed.md"])
    (tmp_path / "docs" / "plan-unlisted.md").write_text("x\n", encoding="utf-8")
    with pytest.raises(gp.GovernancePathError):
        gp.resolve_governance_plan_path("docs/plan-unlisted.md", tmp_path)
