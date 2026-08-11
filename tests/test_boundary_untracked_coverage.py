"""Phase 219 (GH #309): the boundary lint must see untracked files.

The filed issue says the lint misses files *staged* but not committed. It does
not: `git ls-files` reads the index, so a `git add`ed file is scanned.
**Untracked** files are invisible -- and the seal ceremony runs no boundary lint
at all, while `/qor-audit` Step 0.6 runs it WARN-only over a tree that predates
implementation.

So no fail-closed, identity-aware run ever sees implementation's new files
before they are committed. That is why four leaks passed four green runs, the
most recent being this session's own `research-iter1.json`, which carried an
operator path, reported clean while untracked, and surfaced only after
`git add -A`.

Ignored files stay out. They are not published, and the operator's private terms
overlay lives among them.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qor.scripts import publication_boundary_lint as lint

VIOLATION = "See https://github.com/SomeOtherOrg/some-other-repo for details.\n"  # boundary-lint: ok=detector-fixture


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
    return root


def _findings(root: Path, name: str) -> list[str]:
    return [f for f in lint.collect_findings(root, no_git=False).findings if name in f]


def test_untracked_violation_is_found(repo: Path):
    """THE COUNTERFACTUAL. Fails at HEAD, which lists only the index."""
    (repo / "docs" / "new.md").write_text(VIOLATION, encoding="utf-8")

    assert _findings(repo, "new.md"), (
        "an untracked file is the state every new artifact is in when the "
        "ceremony runs; it must be scanned"
    )


def test_staged_violation_still_found(repo: Path):
    """REGRESSION. The index surface is not lost by adding untracked coverage."""
    p = repo / "docs" / "staged.md"
    p.write_text(VIOLATION, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", str(p)], check=True)

    assert _findings(repo, "staged.md")


def test_committed_violation_still_found(repo: Path):
    """REGRESSION. The original tracked surface is intact."""
    p = repo / "docs" / "committed.md"
    p.write_text(VIOLATION, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", str(p)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "add"], check=True)

    assert _findings(repo, "committed.md")


def test_gitignored_file_is_not_scanned(repo: Path):
    """Ignored files are not published, and the private overlay lives among them.

    Scanning them would report findings the operator cannot act on and would
    read the very denylist the boundary exists to keep out of the repository.
    """
    (repo / ".gitignore").write_text("secrets/\n", encoding="utf-8")
    (repo / "secrets").mkdir()
    (repo / "secrets" / "notes.md").write_text(VIOLATION, encoding="utf-8")

    assert _findings(repo, "notes.md") == []
