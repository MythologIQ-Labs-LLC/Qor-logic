"""Phase 30 Phase 4: Check Surface D (term-drift grep).

Lenient-by-default. Returns drift findings for terms used outside their
declared referenced_by list. Scope-fenced to markdown files.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity_strict as dis  # noqa: E402


def _mk_repo(tmp_path: Path, glossary_body: str, extra_files: dict) -> tuple[str, str]:
    (tmp_path / "qor" / "references").mkdir(parents=True, exist_ok=True)
    glossary = tmp_path / "qor" / "references" / "glossary.md"
    glossary.write_text(glossary_body, encoding="utf-8")
    for rel, body in extra_files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return str(glossary), str(tmp_path)


_FOO_ENTRY = (
    "# Glossary\n\n"
    "```yaml\n"
    "term: Foo\n"
    "definition: A thing.\n"
    "home: docs/architecture.md\n"
    "referenced_by:\n"
    "  - docs/architecture.md\n"
    "```\n"
)


def test_term_drift_flags_undeclared_usage(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _FOO_ENTRY,
        {"docs/architecture.md": "# arch\nFoo lives here.\n",
         "docs/other.md": "# other\nFoo is used here too.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert any("docs/other.md" in f for f in findings), f"Expected drift, got {findings}"


def test_term_drift_respects_scope_fence(tmp_path):
    """Code files (.py) are out of scope for term-drift grep."""
    glossary, root = _mk_repo(
        tmp_path,
        _FOO_ENTRY,
        {"docs/architecture.md": "# arch\nFoo lives here.\n",
         "qor/scripts/example.py": "# module\n# Foo is mentioned but this is code not docs\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not any("qor/scripts/example.py" in f for f in findings), (
        f"Code file should be excluded from scan: {findings}"
    )


def test_term_drift_lenient_mode_does_not_raise(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _FOO_ENTRY,
        {"docs/architecture.md": "# arch\nFoo lives here.\n",
         "docs/drift.md": "# drift\nFoo is used here.\n"},
    )
    # No exception raised even though drift is found
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert isinstance(findings, list)


def test_term_drift_strict_mode_raises(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _FOO_ENTRY,
        {"docs/architecture.md": "# arch\nFoo lives here.\n",
         "docs/drift.md": "# drift\nFoo is used here.\n"},
    )
    with pytest.raises(ValueError, match="Foo"):
        dis.check_term_drift(glossary, root, strict=True)


def test_term_drift_declared_consumer_passes(tmp_path):
    """Term used in its referenced_by file -- no drift."""
    glossary, root = _mk_repo(
        tmp_path,
        _FOO_ENTRY,
        {"docs/architecture.md": "# arch\nFoo lives here.\n"},
    )
    findings = dis.check_term_drift(glossary, root, strict=False)
    assert not findings, f"Declared consumer should not trigger drift: {findings}"
