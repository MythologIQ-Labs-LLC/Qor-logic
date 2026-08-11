"""Phase 219 (GH #309 gap 2): a green boundary result must carry its own scope.

The terms overlay is gitignored on purpose -- a tracked denylist of private
identifiers in a public repository publishes the strings it exists to suppress.
So CI runs the four structural detectors only, and both identity-term leaks the
issue cites were invisible to it, correctly.

That cannot be fixed by scanning more. What can be fixed is that an unqualified
"0 findings" from CI and from a local run mean different things and currently
look identical. The scope travels with the result.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import publication_boundary_lint as lint


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("# Clean\n", encoding="utf-8")
    return root


def test_scope_reports_structural_only_without_overlay(tmp_path: Path):
    """No overlay present -- identity terms were not examined, and it says so."""
    result = lint.collect_findings(_repo(tmp_path), no_git=True, terms_file=None)

    assert result.scope == "structural", result.scope


def test_scope_reports_identity_when_overlay_present(tmp_path: Path):
    """Overlay present -- identity coverage is claimed only when it is real."""
    root = _repo(tmp_path)
    overlay = root / "terms.txt"
    overlay.write_text("AcmeInternal\n", encoding="utf-8")

    result = lint.collect_findings(root, no_git=True, terms_file=overlay)

    assert result.scope == "structural+identity", result.scope


def test_empty_overlay_is_structural_only(tmp_path: Path):
    """A present-but-empty overlay contributes no identity coverage.

    Claiming identity scope from an empty file would be the same false assurance
    the disclosure exists to prevent.
    """
    root = _repo(tmp_path)
    overlay = root / "terms.txt"
    overlay.write_text("# only comments\n\n", encoding="utf-8")

    assert lint.collect_findings(root, no_git=True, terms_file=overlay).scope == "structural"


def test_scope_is_machine_readable(tmp_path: Path):
    """The seal records the scope; it must not have to parse prose to do it."""
    result = lint.collect_findings(_repo(tmp_path), no_git=True, terms_file=None)

    assert isinstance(result.scope, str)
    assert isinstance(result.findings, list)
    assert result.scope in ("structural", "structural+identity")
