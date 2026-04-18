"""Phase 30 Phase 4 (Ground 1 remediation): doc_integrity modules stay under 250 lines.

SG-Phase30-A countermeasure: additive edits to doc_integrity.py already
tripped the Razor cap once (Phase 28: 258 -> 244 trim). This test guards
both the core and the sibling strict module going forward.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE = REPO_ROOT / "qor" / "scripts" / "doc_integrity.py"
STRICT = REPO_ROOT / "qor" / "scripts" / "doc_integrity_strict.py"


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_doc_integrity_core_under_250():
    lines = _count_lines(CORE)
    assert lines <= 250, f"doc_integrity.py is {lines} lines (cap 250)"


def test_doc_integrity_strict_under_250():
    lines = _count_lines(STRICT)
    assert lines <= 250, f"doc_integrity_strict.py is {lines} lines (cap 250)"


def test_strict_module_import_surface():
    import sys
    sys.path.insert(0, str(REPO_ROOT / "qor" / "scripts"))
    import doc_integrity_strict as dis
    assert callable(getattr(dis, "check_term_drift", None))
    assert callable(getattr(dis, "check_cross_doc_conflicts", None))
