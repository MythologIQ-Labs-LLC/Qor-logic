"""Phase 181 (GH #238 residual): seed emits a .gitattributes pinning
governance artifacts to LF, so canonical bytes never drift with host
autocrlf settings (the verify-layer half shipped in Phases 156-158)."""
from __future__ import annotations

from pathlib import Path

from qor import seed as seed_mod

REPO = Path(__file__).resolve().parent.parent


def test_seed_creates_gitattributes_with_lf_stanza(tmp_path):
    seed_mod.seed(tmp_path, quiet=True)
    target = tmp_path / ".gitattributes"
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "docs/*.md text eol=lf" in text
    assert "docs/**/*.md text eol=lf" in text
    assert ".qor/** text eol=lf" in text


def test_reseed_never_overwrites_operator_customization(tmp_path):
    custom = "# operator-tuned\n*.md text eol=crlf\n"
    (tmp_path / ".gitattributes").write_text(custom, encoding="utf-8")
    seed_mod.seed(tmp_path, quiet=True)
    assert (tmp_path / ".gitattributes").read_text(encoding="utf-8") == custom


def test_repo_root_carries_the_stanza():
    # Phase 181 self-application lock: this repository pins the same rules.
    text = (REPO / ".gitattributes").read_text(encoding="utf-8")
    for rule in ("docs/*.md text eol=lf", "docs/**/*.md text eol=lf",
                 ".qor/** text eol=lf"):
        assert rule in text
