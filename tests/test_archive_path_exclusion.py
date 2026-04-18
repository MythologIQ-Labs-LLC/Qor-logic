"""Phase 32 Phase 2: archive-path exclusion in Check Surface D/E scope fence.

Historical/immutable docs (plan files, META_LEDGER, SHADOW_GENOME, phase-
era snapshots) legitimately reference core concepts without being adopt-
able consumers. Exclude them from drift scan to enable strict-mode wiring
in Phase 3.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity_strict as dis  # noqa: E402


_FOO_ENTRY = (
    "# Glossary\n\n"
    "```yaml\n"
    "term: Foo\n"
    "definition: A thing.\n"
    "home: qor/references/doctrine-a.md\n"
    "referenced_by:\n"
    "  - qor/references/doctrine-a.md\n"
    "```\n"
)


def _mk_repo(tmp_path: Path, extra_files: dict) -> tuple[str, str]:
    (tmp_path / "qor" / "references").mkdir(parents=True, exist_ok=True)
    glossary = tmp_path / "qor" / "references" / "glossary.md"
    glossary.write_text(_FOO_ENTRY, encoding="utf-8")
    (tmp_path / "qor" / "references" / "doctrine-a.md").write_text(
        "# doctrine-a\nFoo is defined here.\n", encoding="utf-8"
    )
    for rel, body in extra_files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return str(glossary), str(tmp_path)


def test_plan_file_excluded(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        {"docs/plan-qor-phase28-documentation-integrity.md": "Foo used in old plan.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("plan-qor-phase28" in f for f in findings), (
        f"Plan archive file should be excluded: {findings}"
    )


def test_meta_ledger_excluded(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        {"docs/META_LEDGER.md": "# Ledger\nFoo mentioned here.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("META_LEDGER" in f for f in findings), (
        f"META_LEDGER must be excluded: {findings}"
    )


def test_shadow_genome_excluded(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        {"docs/SHADOW_GENOME.md": "# Shadow\nFoo referenced here.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("SHADOW_GENOME" in f for f in findings), (
        f"SHADOW_GENOME must be excluded: {findings}"
    )


def test_phase_snapshot_excluded(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        {"docs/phase10-findings.md": "# Phase 10\nFoo mentioned here.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("phase10-findings" in f for f in findings), (
        f"Phase snapshot docs must be excluded: {findings}"
    )


def test_non_archive_doc_still_flagged(tmp_path):
    """Regression guard: exclusion must not over-reach."""
    glossary, root = _mk_repo(
        tmp_path,
        {"qor/gates/other.md": "# gate doc\nFoo used here.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert any("qor/gates/other.md" in f for f in findings), (
        f"Non-archive doc must still flag: {findings}"
    )


def test_system_tier_docs_still_flagged(tmp_path):
    """Regression guard: the 4 system-tier docs (architecture/lifecycle/
    operations/policies) are LIVING and NOT excluded. Terms used there
    must be in referenced_by."""
    glossary, root = _mk_repo(
        tmp_path,
        {"docs/architecture.md": "Foo used in architecture.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert any("docs/architecture.md" in f for f in findings), (
        f"System-tier docs must NOT be excluded: {findings}"
    )
