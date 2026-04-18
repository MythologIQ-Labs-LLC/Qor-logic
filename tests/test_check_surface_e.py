"""Phase 30 Phase 4: Check Surface E (cross-doc conflict detection).

Lenient-by-default. Returns findings where a glossary term is defined in
a non-home file with text diverging from the canonical glossary definition.
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


_WIDGET_ENTRY = (
    "# Glossary\n\n"
    "```yaml\n"
    "term: Widget\n"
    "definition: A canonical synchronization primitive used across layers.\n"
    "home: docs/architecture.md\n"
    "referenced_by:\n"
    "  - docs/architecture.md\n"
    "```\n"
)


def test_conflict_detects_divergent_definition(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _WIDGET_ENTRY,
        {
            "docs/architecture.md": "# arch\nWidget is the canonical primitive.\n",
            "docs/bad.md": "# bad\nWidget refers to an entirely unrelated user-interface element.\n",
        },
    )
    findings = dis.check_cross_doc_conflicts(glossary, root, strict=False)
    assert any("docs/bad.md" in f for f in findings), (
        f"Expected divergent-definition drift, got {findings}"
    )


def test_conflict_scope_fence(tmp_path):
    """Code files (.py) are out of scope."""
    glossary, root = _mk_repo(
        tmp_path,
        _WIDGET_ENTRY,
        {
            "docs/architecture.md": "# arch\nWidget is the canonical primitive.\n",
            "qor/scripts/mod.py": "# Widget is a completely different thing in this file\n",
        },
    )
    findings = dis.check_cross_doc_conflicts(glossary, root, strict=False)
    assert not any("qor/scripts/mod.py" in f for f in findings), (
        f"Code files should be scope-fenced out: {findings}"
    )


def test_conflict_lenient_mode_does_not_raise(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _WIDGET_ENTRY,
        {
            "docs/architecture.md": "# arch\nWidget is the canonical primitive.\n",
            "docs/bad.md": "# bad\nWidget refers to an entirely unrelated UI element.\n",
        },
    )
    findings = dis.check_cross_doc_conflicts(glossary, root, strict=False)
    assert isinstance(findings, list)  # no raise


def test_conflict_strict_mode_raises(tmp_path):
    glossary, root = _mk_repo(
        tmp_path,
        _WIDGET_ENTRY,
        {
            "docs/architecture.md": "# arch\nWidget is the canonical primitive.\n",
            "docs/bad.md": "# bad\nWidget refers to an entirely unrelated UI element.\n",
        },
    )
    with pytest.raises(ValueError, match="Widget"):
        dis.check_cross_doc_conflicts(glossary, root, strict=True)
