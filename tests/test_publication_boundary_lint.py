"""Phase 172: structural publication-boundary lint tests.

The lint enforces qor/references/doctrine-publication-boundary.md without
itself carrying any outside identity: structural patterns (absolute local
path shapes; foreign GitHub URLs; cross-repo issue shapes) plus an OPTIONAL
operator-local, gitignored terms file for identity terms.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import publication_boundary_lint as pbl


def _run(tmp_path: Path, files: dict[str, str], terms: str | None = None) -> tuple[int, str]:
    import io
    from contextlib import redirect_stdout

    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    argv = ["--repo-root", str(tmp_path), "--no-git"]
    if terms is not None:
        tf = tmp_path / "terms.txt"
        tf.write_text(terms, encoding="utf-8")
        argv += ["--terms-file", str(tf)]
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = pbl.main(argv)
    return rc, buf.getvalue()


def test_flags_absolute_local_paths(tmp_path):
    rc, out = _run(tmp_path, {"docs/a.md": "see F:/SomeWorkspace/tool.py and /Users/dev/repo/x.py\n"})
    assert rc == 1
    assert "docs/a.md" in out.replace("\\", "/")
    assert out.count("[boundary]") == 2


def test_flags_foreign_github_urls_not_self(tmp_path):
    own = "https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/1"
    foreign = "https://github.com/other-org/other-repo/pull/2"
    rc, out = _run(tmp_path, {"docs/b.md": f"{own}\n{foreign}\n"})
    assert rc == 1
    assert "other-org/other-repo" in out
    assert "Qor-logic/issues/1" not in out


def test_flags_cross_repo_issue_shape(tmp_path):
    rc, out = _run(tmp_path, {"docs/c.md": "fixed in OtherRepo#123 but relates to #45 here\n"})
    assert rc == 1
    assert "OtherRepo#123" in out
    assert out.count("[boundary]") == 1  # bare #45 self-reference passes


def test_local_terms_file_overlay(tmp_path):
    files = {"docs/d.md": "the SecretSibling repo pattern\n"}
    rc, _ = _run(tmp_path, dict(files))
    assert rc == 0  # structural patterns alone do not know identity terms
    rc, out = _run(tmp_path, dict(files), terms="SecretSibling\n# comment line\n")
    assert rc == 1
    assert "SecretSibling" in out


def test_exit_codes(tmp_path):
    rc, out = _run(tmp_path, {"docs/clean.md": "a neutral sentence citing qor/scripts/x.py\n"})
    assert rc == 0
    assert "0 finding(s)" in out
