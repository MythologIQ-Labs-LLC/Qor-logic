"""Phase 64 (#48 follow-up): regression test for doc_integrity strict-mode import.

Locks the contract that `qor.scripts.doc_integrity.run_all_checks_from_plan`
with `strict=True` reaches Check Surface D + E without raising
`ModuleNotFoundError` on the package import path.

Pre-Phase-64, line 218 used a bare `import doc_integrity_strict` which only
resolved when `sys.path` happened to include `qor/scripts/`. From any other
working directory the strict path crashed before doing useful work, causing
`/qor-substantiate` Step 4.7 to ABORT with a misleading ModuleNotFoundError
rather than a real doc-integrity finding.

Acceptance question: "If the unit's behavior were silently broken but the
artifact still existed, would this test fail?" - yes. Reverting the import
to the bare form makes this test fail with ModuleNotFoundError.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import doc_integrity


def _minimal_standard_plan() -> dict:
    return {
        "doc_tier": "standard",
        "terms": [],
        "plan_slug": "plan-qor-phase64-seal-hash-substantiate-wiring",
    }


def test_strict_mode_does_not_raise_module_not_found(tmp_path):
    """Reaching Check Surface D + E must not crash on a bare import path."""
    plan = _minimal_standard_plan()
    # Use repo_root='.' so the call exercises the production path used by
    # /qor-substantiate Step 4.7. The strict-mode branch must import
    # doc_integrity_strict via the package path; a bare `import
    # doc_integrity_strict` raises ModuleNotFoundError here.
    try:
        doc_integrity.run_all_checks_from_plan(plan, repo_root=".", strict=True)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"strict=True path raised ModuleNotFoundError: {exc}. "
            f"doc_integrity must import doc_integrity_strict via "
            f"the qor.scripts package path."
        )
    except ValueError:
        # ValueError is the expected raise-class for real doc-integrity
        # violations; that's a real check firing, not the import bug.
        pass


def test_lenient_mode_still_skips_strict_checks(tmp_path):
    """Lenient mode (strict=False) must not import doc_integrity_strict at all.

    This guards against a future refactor that hoists the import to module
    scope, breaking the lazy-import contract that lets lenient callers run
    without pulling in the heavier strict-check dependencies.
    """
    plan = _minimal_standard_plan()
    try:
        doc_integrity.run_all_checks_from_plan(plan, repo_root=".", strict=False)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"strict=False path should not import doc_integrity_strict; "
            f"got: {exc}"
        )
    except ValueError:
        pass


def test_strict_import_uses_package_path():
    """Inspect the source to confirm the import is the package form, not bare.

    Behavioral test (above) catches the runtime crash; this test catches
    a regression where someone reverts to the bare form but happens to
    have sys.path populated during their local test run.
    """
    source = Path("qor/scripts/doc_integrity.py").read_text(encoding="utf-8")
    assert "from qor.scripts import doc_integrity_strict" in source, (
        "qor/scripts/doc_integrity.py must import doc_integrity_strict "
        "via the qor.scripts package path; a bare `import "
        "doc_integrity_strict` is the GH #48 follow-up bug"
    )
    # And confirm the bare form is not present (anchor against future drift).
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import doc_integrity_strict"):
            pytest.fail(
                f"bare import found: {line!r}; use the qor.scripts package path"
            )
