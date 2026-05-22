"""Phase 85: behavior tests for the hoisted doc-integrity corpus scan (GH #96 FIX B/C).

The hoist moves the directory walk + file read out of the per-term loop in
check_term_drift / check_cross_doc_conflicts. These tests prove the hoisted
functions still produce the correct findings, and that _scan_corpus
materializes one correct entry per in-scope file.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from qor.scripts.doc_integrity_strict import (
    _scan_corpus,
    check_cross_doc_conflicts,
    check_term_drift,
)

_GLOSSARY = textwrap.dedent("""\
    # Glossary

    ```yaml
    term: Widgetron
    definition: A canonical example concept used only in tests.
    home: qor/references/doctrine-example.md
    referenced_by:
    {referenced_by}
    introduced_in_plan: phase85-ci-health-fixes
    ```
    """)


def _build_repo(tmp_path: Path, referenced_by: list[str], files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    rb = "\n".join(f"  - {r}" for r in referenced_by) if referenced_by else "  []"
    written = {
        "qor/references/glossary.md": _GLOSSARY.format(referenced_by=rb),
        "qor/references/doctrine-example.md": "# Example doctrine\n",
        **files,
    }
    for rel, content in written.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return repo


def test_check_term_drift_flags_out_of_scope_term_use(tmp_path):
    repo = _build_repo(
        tmp_path,
        referenced_by=["qor/references/doctrine-example.md"],
        files={"docs/architecture.md": "The Widgetron appears here out of scope.\n"},
    )
    findings = check_term_drift(
        str(repo / "qor/references/glossary.md"), str(repo))
    assert findings == [
        "Term 'Widgetron' used in docs/architecture.md not declared as referenced_by"
    ]


def test_check_term_drift_clean_when_term_in_scope(tmp_path):
    repo = _build_repo(
        tmp_path,
        referenced_by=["qor/references/doctrine-example.md", "docs/architecture.md"],
        files={"docs/architecture.md": "The Widgetron appears here, now in scope.\n"},
    )
    findings = check_term_drift(
        str(repo / "qor/references/glossary.md"), str(repo))
    assert findings == []


def test_check_cross_doc_conflicts_flags_divergent_definition(tmp_path):
    repo = _build_repo(
        tmp_path,
        referenced_by=["qor/references/doctrine-example.md"],
        files={"docs/lifecycle.md": "Widgetron is a totally different made-up gadget thing\n"},
    )
    findings = check_cross_doc_conflicts(
        str(repo / "qor/references/glossary.md"), str(repo))
    assert len(findings) == 1
    assert "Widgetron" in findings[0] and "docs/lifecycle.md" in findings[0]


def test_check_term_drift_strict_raises_on_finding(tmp_path):
    repo = _build_repo(
        tmp_path,
        referenced_by=["qor/references/doctrine-example.md"],
        files={"docs/architecture.md": "The Widgetron appears here out of scope.\n"},
    )
    with pytest.raises(ValueError):
        check_term_drift(
            str(repo / "qor/references/glossary.md"), str(repo), strict=True)


def test_scan_corpus_returns_one_correct_entry_per_file(tmp_path):
    repo = tmp_path / "repo"
    contents = {
        "qor/references/a.md": "alpha content\n",
        "qor/skills/b.md": "beta content\n",
        "docs/c.md": "gamma content\n",
    }
    for rel, content in contents.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    scanned = _scan_corpus(str(repo))
    assert len(scanned) == len(contents)
    by_rel = dict(scanned)
    assert set(by_rel) == set(contents)
    for rel, content in contents.items():
        assert by_rel[rel] == content
