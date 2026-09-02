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


# ---------- GH #282: system-tier topology via registered architecture authority ----------

def _system_repo(tmp_path: Path, registered: list[str], make_arch_plan: bool = True) -> None:
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text("# g\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("lifecycle.md", "operations.md", "policies.md"):
        (docs / name).write_text("# x\n", encoding="utf-8")
    if make_arch_plan:
        (docs / "ARCHITECTURE_PLAN.md").write_text("# arch plan\n", encoding="utf-8")
    rows = "\n".join(f"| Doc | `{p}` | stable |" for p in registered)
    (docs / "GOVERNANCE_INDEX.md").write_text(
        "# Index\n\n**Last Reviewed**: 2026-07-13\n\n" + rows + "\n", encoding="utf-8"
    )


# ---------- GH #394: run_all_checks_from_plan must not vacuously pass ----------

def test_run_all_checks_from_plan_raises_on_unregistered_term(tmp_path):
    """The full plan-dict entry point (not just check_glossary's explicit
    declared_terms list) must fail closed when a plan declares a term under
    the canonical `terms` key that has no glossary entry."""
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    _write_glossary(tmp_path / "qor" / "references" / "glossary.md", [])
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Unregistered", "home": "README.md"}],
    }
    with pytest.raises(ValueError, match="Unregistered"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))


def test_run_all_checks_from_plan_rejects_a_terms_introduced_only_plan(tmp_path):
    """Phase 251 (GH #414) supersedes this test's original premise.

    Phase 248 (GH #394) wrote it to document that a plan carrying only the
    retired `terms_introduced` alias evaluates to zero declared terms at this
    layer, with the real protection living at the schema boundary. GH #414
    closed the remaining route: a standard-tier plan that declares no canonical
    `terms` key now fails here regardless of what else it carries.

    The alias case turns out to be a subset of the omission case, so this now
    asserts the stronger outcome rather than the documented gap.
    """
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    _write_glossary(tmp_path / "qor" / "references" / "glossary.md", [])
    plan = {
        "doc_tier": "standard",
        "terms_introduced": [{"term": "Unregistered", "home": "README.md"}],
    }
    with pytest.raises(ValueError, match="terms"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))

def test_check_topology_system_passes_with_registered_architecture_plan(tmp_path):
    """No docs/architecture.md; docs/ARCHITECTURE_PLAN.md is the registered authority."""
    _system_repo(tmp_path, ["docs/ARCHITECTURE_PLAN.md"])
    doc_integrity.check_topology("system", str(tmp_path))  # must not raise


def test_check_topology_system_fails_when_architecture_authority_unregistered(tmp_path):
    _system_repo(tmp_path, ["docs/README.md"])  # ARCHITECTURE_PLAN.md present but not registered
    with pytest.raises(ValueError, match="architecture"):
        doc_integrity.check_topology("system", str(tmp_path))


# --- Phase 251 (GH #414): the omission route into a vacuous glossary check ---
#
# GH #394 closed the alias route (the schema rejects `terms_introduced`). The
# omission route stayed open: a plan declaring NEITHER key evaluated to zero
# declared terms, so the gate inspected nothing and reported success. Enforced
# here rather than in plan.schema.json -- an `if/then` on doc_tier would
# retroactively invalidate 109 already-sealed plan artifacts, since Phase 248's
# sealed_history exemption strips only the top-level `not` clause.


def _consumer(tmp_path):
    (tmp_path / "README.md").write_text("# r\n", encoding="utf-8")
    g = tmp_path / "qor" / "references"
    g.mkdir(parents=True, exist_ok=True)
    (g / "glossary.md").write_text("# Glossary\n", encoding="utf-8")
    return tmp_path


def test_standard_tier_requires_a_terms_declaration(tmp_path):
    """`declared empty` and `never declared` must stop being the same thing."""
    root = _consumer(tmp_path)
    plan = {"doc_tier": "standard"}  # no `terms` key at all

    with pytest.raises(ValueError, match="terms"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(root))


def test_standard_tier_accepts_an_explicit_empty_terms(tmp_path):
    """Declaring no vocabulary stays possible, and stays a claim the author made."""
    root = _consumer(tmp_path)

    doc_integrity.run_all_checks_from_plan(
        {"doc_tier": "standard", "terms": []}, repo_root=str(root)
    )


def test_minimal_tier_does_not_require_terms(tmp_path):
    """The exemption holds, so this does not become the unconditional
    requirement GH #414 explicitly rejects."""
    root = _consumer(tmp_path)

    doc_integrity.run_all_checks_from_plan({"doc_tier": "minimal"}, repo_root=str(root))


def test_sealed_plan_artifacts_still_validate_against_the_schema():
    """Permanent guard against this rule migrating into plan.schema.json.

    109 sealed plan artifacts carry doc_tier standard|system with no `terms`
    key. A schema `if/then` would abort every future seal via
    gate_chain_completeness. Passes today; it exists to fail loudly if anyone
    moves the rule.
    """
    from qor.reliability import gate_chain_completeness as gcc
    from qor.scripts import validate_gate_artifact as vga

    # Scoped to the sessions gate_chain_completeness actually inspects -- the
    # ones a SESSION SEAL entry names -- rather than every file under .qor/gates,
    # which also holds test fixtures that were never sealed.
    repo = Path(__file__).resolve().parents[1]
    ledger = (repo / "docs" / "META_LEDGER.md").read_text(encoding="utf-8")
    sessions = set(gcc._extract_seal_sessions(ledger, 52).values())

    checked = 0
    for sid in sorted(sessions):
        artifact = repo / ".qor" / "gates" / sid / "plan.json"
        if not artifact.is_file():
            continue
        errs = vga.validate_one("plan", artifact, sealed_history=True)
        assert errs == [], f"sealed plan artifact no longer validates: {sid}: {errs[:1]}"
        checked += 1
    assert checked > 50, f"expected the sealed corpus, inspected only {checked}"
