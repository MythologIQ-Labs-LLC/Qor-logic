"""Phase 148 (GAP-CLI-01): the typed SDK surface ships a PEP 561 marker.

Without `qor/py.typed`, downstream consumers' type checkers (mypy/pyright) treat
the typed `qor.sdk` / `qor.compliance.enforce` API as untyped. The marker makes
the package's inline types consumable.
"""
from __future__ import annotations

from pathlib import Path

_QOR = Path(__file__).resolve().parents[1] / "qor"


def test_py_typed_ships():
    marker = _QOR / "py.typed"
    assert marker.is_file(), "qor/py.typed PEP 561 marker must exist"
    # PEP 561 marker is empty (or a partial-stub directive); ours is the empty form.
    assert marker.read_text(encoding="utf-8").strip() == ""
