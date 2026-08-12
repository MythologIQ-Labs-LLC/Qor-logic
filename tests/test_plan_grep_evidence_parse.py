"""Phase 223 (GH #330): an evidence statement becomes a resolvable value.

`plan_grep_lint` has checked since Phase 125 that a Locked Decision citing sealed
infrastructure *carries* a grep-evidence statement. It has never checked that the
statement is true. A plan shipped to audit with `-> 39:` against an actual line 42
and passed that lint (ledger #565).

These tests define the parsing and resolution contract before it exists. The
negative cases are load-bearing: without them a parser returning `[]` forever
satisfies every positive assertion.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qor.scripts import plan_grep_lint as pgl

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"

#: Revision the fixtures pin. Chosen because `qor-substantiate/SKILL.md` line 250
#: differs materially between it and `2d356ec`, which is what makes
#: `test_resolve_line_reads_the_named_revision_not_head` able to fail.
ANCESTOR_REV = "6424413"
PINNED_REV = "2d356ec"
SEAL_SKILL_REL = "qor/skills/governance/qor-substantiate/SKILL.md"


def _fixture(name: str) -> str:
    return (FIXTURES / f"evidence_{name}.md").read_text(encoding="utf-8")


def _git_available() -> bool:
    out = subprocess.run(["git", "rev-parse", "--verify", ANCESTOR_REV],
                         cwd=REPO_ROOT, capture_output=True)
    return out.returncode == 0


# --------------------------------------------------------------------------
# parse_evidence_statements
# --------------------------------------------------------------------------

def test_parses_a_git_show_evidence_statement():
    stmts = pgl.parse_evidence_statements(_fixture("true"))
    assert len(stmts) == 1
    s = stmts[0]
    assert s.ref == PINNED_REV
    assert s.path == "qor/scripts/plan_grep_lint.py"
    assert s.line == 97
    assert s.observed.strip() == '_EVIDENCE_RE = re.compile(r"grep\\b.*->")'


def test_parses_a_working_tree_evidence_statement():
    """No `git show` prefix means the working tree, not a pinned revision."""
    text = "## Locked Decisions\n\ngrep -nE 'POLICY' qor/scripts/plan_grep_lint.py -> 12:POLICY = 1\n"
    stmts = pgl.parse_evidence_statements(text)
    assert len(stmts) == 1
    assert stmts[0].ref is None
    assert stmts[0].line == 12


def test_a_statement_without_an_observation_is_not_parsed():
    """THE COUNTERFACTUAL for the legacy shape.

    `grep foo -> bar` satisfies the Phase 125 predicate and carries nothing a
    truth check can resolve. It must not be mistaken for a verifiable statement.
    """
    text = "## Locked Decisions\n\ngrep -nE 'foo' some/path.py -> bar\n"
    assert pgl.parse_evidence_statements(text) == []


def test_a_grep_o_statement_is_not_parsed_as_file_line():
    """`grep -oE` emits the matched span with no line number."""
    text = ("## Locked Decisions\n\n"
            "git show 2d356ec:qor/references/x.md | grep -oE 'some literal' -> some literal\n")
    assert pgl.parse_evidence_statements(text) == []


def test_multiple_statements_in_one_block_all_parse():
    stmts = pgl.parse_evidence_statements(_fixture("distinct_lines_same_file"))
    assert {s.line for s in stmts} == {97, 101}


# --------------------------------------------------------------------------
# resolve_line / reproduces
# --------------------------------------------------------------------------

@pytest.mark.skipif(not _git_available(), reason=f"{ANCESTOR_REV} unreachable (shallow clone?)")
def test_resolve_line_reads_the_named_revision_not_head():
    """One path, one line, two revisions, materially different content.

    A `resolve_line` that ignored `ref` and read the working tree would return
    the ladder-table row for both and fail the ancestor assertion. Iteration 4 of
    the plan pinned this to a line no phase committed to changing, which made the
    guarantee vacuous (ledger #571 F9).
    """
    old = pgl.EvidenceStatement(ref=ANCESTOR_REV, path=SEAL_SKILL_REL, line=250, observed="")
    new = pgl.EvidenceStatement(ref=PINNED_REV, path=SEAL_SKILL_REL, line=250, observed="")

    old_text = pgl.resolve_line(old, REPO_ROOT)
    new_text = pgl.resolve_line(new, REPO_ROOT)

    assert old_text.strip() == "### Step 4.6.5: Secret-scanning gate (Phase 56 wiring)"
    assert new_text.strip().startswith("| 4.6.14 |")
    assert old_text != new_text


def test_resolve_line_returns_none_for_an_unresolvable_path():
    s = pgl.EvidenceStatement(ref=PINNED_REV, path="qor/scripts/does_not_exist_anywhere.py",
                              line=12, observed="whatever")
    assert pgl.resolve_line(s, REPO_ROOT) is None


def test_resolve_line_returns_none_past_end_of_file():
    s = pgl.EvidenceStatement(ref=PINNED_REV, path="qor/scripts/plan_grep_lint.py",
                              line=999_999, observed="x")
    assert pgl.resolve_line(s, REPO_ROOT) is None


def test_reproduces_compares_stripped_text():
    """Indentation must not fail a true citation; a changed token must fail."""
    stmts = pgl.parse_evidence_statements(_fixture("true"))
    assert pgl.reproduces(stmts[0], REPO_ROOT) is True

    tampered = pgl.EvidenceStatement(
        ref=stmts[0].ref, path=stmts[0].path, line=stmts[0].line,
        observed='_EVIDENCE_RE = re.compile(r"grep NOT THIS")',
    )
    assert pgl.reproduces(tampered, REPO_ROOT) is False


def test_reproduces_is_false_when_the_line_number_is_wrong():
    """The Phase 222 defect, reproduced deliberately -- it was never committed."""
    stmts = pgl.parse_evidence_statements(_fixture("false_line"))
    assert len(stmts) == 1
    assert stmts[0].line == 99
    assert pgl.reproduces(stmts[0], REPO_ROOT) is False
