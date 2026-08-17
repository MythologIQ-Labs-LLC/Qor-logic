"""Phase 225 (GH #336): one grammar parses every markdown styling of a statement.

The corpus writes the mandated evidence statement three ways: bare inside a code
fence, in one backticked span, and in two backticked spans with the observation
in its own span. The shipped regex parsed only the bare form cleanly: the
two-span form did not match at all, and the one-span form captured its closing
backtick into ``observed``, so a true statement failed ``reproduces``. These
tests bind the normalization contract: backticks are markdown formatting, not
statement content.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import plan_evidence as pe


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "sample.py").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, check=True)
    return tmp_path


def test_two_span_statement_parses_to_one_statement():
    """The styling every recent real plan uses; the shipped regex matched none of it."""
    block = ("## Locked Decisions\n\n"
             "> `git show v1.0.0:sample.py | grep -nE 'beta'` -> `2:beta`\n")
    stmts = pe.parse_evidence_statements(block)
    assert len(stmts) == 1
    assert (stmts[0].ref, stmts[0].path, stmts[0].line) == ("v1.0.0", "sample.py", 2)
    assert stmts[0].observed.strip() == "beta"


def test_one_span_true_statement_reproduces(tmp_path):
    """The closing span delimiter must not corrupt the observed text."""
    repo = _repo(tmp_path)
    block = ("## Locked Decisions\n\n"
             "- `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta`\n")
    stmts = pe.parse_evidence_statements(block)
    assert len(stmts) == 1
    assert stmts[0].observed.strip() == "beta"
    assert pe.reproduces(stmts[0], repo) is True


def test_bare_fenced_statement_still_parses():
    """The Phase 223 fixture styling is unchanged by normalization."""
    block = ("## Locked Decisions\n\n"
             "git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta\n")
    stmts = pe.parse_evidence_statements(block)
    assert len(stmts) == 1
    assert stmts[0].observed.strip() == "beta"


def test_statement_without_line_prefix_is_not_parsed():
    """The pre-amendment doctrine form carries nothing a truth check can resolve."""
    block = ("## Locked Decisions\n\n"
             "`git show v1.0.0:sample.py | grep -nE 'beta' -> beta`\n")
    assert pe.parse_evidence_statements(block) == []


def test_every_admitted_extension_resolves_through_both_paths():
    """F5 remedy, behavioral: for each admitted extension, a citation is
    demanded and a working-tree statement path is captured -- through the
    compiled regexes' actual behavior, not a parse of their source."""
    for ext in pe._PATH_EXT.split("|"):
        block = f"## Locked Decisions\n- see `dir/f.{ext}:7` with no statement\n"
        assert pe._demand_set(block) == [f"dir/f.{ext}:7"], ext
        stmt_block = f"## Locked Decisions\ngrep -nE 'x' dir/f.{ext} -> 7:x\n"
        stmts = pe.parse_evidence_statements(stmt_block)
        assert [s.path for s in stmts] == [f"dir/f.{ext}"], ext


def test_unresolvable_ref_is_distinct_from_wrong_text(tmp_path):
    """An environment that cannot answer is not an answer that is wrong."""
    repo = _repo(tmp_path)
    missing_ref = pe.EvidenceStatement(ref="no-such-ref", path="sample.py", line=2, observed="beta")
    wrong_text = pe.EvidenceStatement(ref="v1.0.0", path="sample.py", line=3, observed="beta")

    assert pe.resolve_line(missing_ref, repo) is None
    assert pe.resolve_line(wrong_text, repo) == "gamma"
    assert pe.reproduces(wrong_text, repo) is False
