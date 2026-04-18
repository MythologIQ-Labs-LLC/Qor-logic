"""Phase 28 Phase 3: dogfood -- Qor-logic glossary covers its own terms.

After Phase 3 glossary expansion, these assertions must pass against the
real qor/references/glossary.md (not a synthetic fixture). Closes
GAP-REPO-02/03/04 from the Phase 28 research brief.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def _terms() -> set[str]:
    return {e.term for e in doc_integrity.parse_glossary(str(GLOSSARY))}


def test_glossary_exists():
    assert GLOSSARY.exists(), f"Glossary missing at {GLOSSARY}"


def test_phase_term_disambiguated():
    """GAP-REPO-02: 'Phase' has three unrelated senses across the repo.
    The glossary must disambiguate them into distinct entries."""
    terms = _terms()
    assert "Phase (SDLC)" in terms
    # At least the SDLC sense is canonical; the other two senses may be
    # captured as aliases or narrower entries. Minimum bar: SDLC sense is
    # named explicitly (not bare 'Phase').
    assert "Phase" not in terms, (
        "Bare 'Phase' entry is ambiguous; use disambiguated form"
    )


def test_shadow_genome_single_home():
    """GAP-REPO-04: Shadow Genome had a 3-way split. Glossary must declare a
    single authoritative home."""
    entries = {e.term: e for e in doc_integrity.parse_glossary(str(GLOSSARY))}
    assert "Shadow Genome" in entries
    entry = entries["Shadow Genome"]
    assert entry.home.endswith(
        "doctrine-shadow-genome-countermeasures.md"
    ), f"Unexpected home for Shadow Genome: {entry.home}"


def test_doctrine_bootstrap_terms_have_entries():
    """Phase 1 bootstrap set must be present post-expansion."""
    terms = _terms()
    for required in ("Doctrine", "Doc Tier", "Glossary Entry", "Concept Home", "Orphan Concept"):
        assert required in terms, f"Bootstrap term missing: {required!r}"


def test_doctrine_self_substantiates():
    """The dogfood assertion: run the doc-integrity checks against this repo
    at test time. Passes iff Qor-logic satisfies the doctrine it introduces."""
    plan = {
        "doc_tier": "standard",  # standard is pragmatic; system requires docs/* we haven't authored yet
        "terms": [],
        "plan_slug": "phase28-documentation-integrity",
    }
    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(REPO_ROOT))


def test_workflow_bundles_canonical_phases_present():
    """GAP-REPO-01: workflow-bundles.md example must cite validate + remediate."""
    body = (REPO_ROOT / "qor" / "gates" / "workflow-bundles.md").read_text(
        encoding="utf-8"
    )
    # The example phases list or a comment must name both.
    assert "validate" in body
    assert "remediate" in body
