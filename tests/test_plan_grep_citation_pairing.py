"""Phase 223 (GH #330): each citation is backed by its own reproducible evidence.

`check_citation_evidence` satisfied an entire Locked-Decision region whenever any
single statement appeared in it, so one true statement covered every citation
beside it. Demonstrated: a region with one true statement and three citations at
`:999`, `:12345` and `:4` produced zero findings.

The doctrine has said "paired" since Phase 72; the implementation said "block".
These tests hold the gap closed.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from qor.scripts import plan_grep_lint as pgl

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _fx(name: str) -> str:
    return (FIXTURES / f"evidence_{name}.md").read_text(encoding="utf-8")


def _kinds(findings) -> list[str]:
    return [f.kind for f in findings]


def _git_ok() -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", "2d356ec"],
                          cwd=REPO_ROOT, capture_output=True).returncode == 0


pytestmark = pytest.mark.skipif(not _git_ok(), reason="pinned revision unreachable")


def test_a_citation_whose_evidence_reproduces_passes():
    assert pgl.check_citation_evidence(_fx("true"), repo_root=REPO_ROOT) == []


def test_a_false_line_number_is_reported():
    """The Phase 222 defect, reproduced deliberately -- it was never committed."""
    findings = pgl.check_citation_evidence(_fx("false_line"), repo_root=REPO_ROOT)
    assert _kinds(findings) == ["evidence-not-reproducible"]
    assert "99" in findings[0].citation
    assert "evidence" in findings[0].reason.lower()


def test_an_unpaired_citation_is_reported():
    """One citation paired, its sibling riding on the first's statement."""
    findings = pgl.check_citation_evidence(_fx("unpaired"), repo_root=REPO_ROOT)
    assert _kinds(findings) == ["unpaired-citation"]
    assert findings[0].citation.endswith(":101")


def test_the_block_level_gap_is_closed():
    """THE COUNTERFACTUAL for the whole phase.

    The legacy check passes this fixture with zero findings, because one true
    statement sits in the region. Three citations there are backed by nothing.
    """
    findings = pgl.check_citation_evidence(_fx("block_level_gap"), repo_root=REPO_ROOT)
    assert len(findings) == 3
    assert set(_kinds(findings)) == {"unpaired-citation"}


def test_an_unresolvable_path_is_its_own_finding_kind():
    """An environment that cannot answer is not an answer that is wrong."""
    findings = pgl.check_citation_evidence(_fx("unresolvable"), repo_root=REPO_ROOT)
    assert _kinds(findings) == ["evidence-unresolvable"]


def test_a_citation_inside_an_evidence_statement_does_not_demand_its_own():
    """Otherwise every statement would demand a statement, without end."""
    assert pgl.check_citation_evidence(_fx("true"), repo_root=REPO_ROOT) == []


def test_a_prose_citation_is_still_checked_when_the_same_path_appears_in_a_statement(tmp_path):
    """The exclusion is span-based, not path-based.

    A block citing `sample.py:1` in prose while a statement covers `sample.py:2`
    must still report the prose citation. A path-based exclusion would silently
    exempt it, which is exactly what Open Question 1 exists to prevent.

    Phase 225: rebuilt on a tmp-repo fixture. The prior form read the live
    module's line 97 against a pinned ref, so it broke whenever the module's
    lines moved -- a live-state coupling, not a contract.
    """
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "sample.py").write_text("alpha\nbeta\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "f"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, check=True)

    text = (
        "## Locked Decisions\n\n"
        "**LD-1**: prose cites `sample.py:1` with no statement.\n\n"
        "git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta\n"
    )
    findings = pgl.check_citation_evidence(text, repo_root=tmp_path)
    assert [f.citation for f in findings] == ["sample.py:1"]
    assert _kinds(findings) == ["unpaired-citation"]


def test_a_repeated_citation_is_counted_once():
    """Dedup by `(path, line)`.

    `_sealed_citations` uses `finditer` with no dedup, so a restating table
    multiplies one location into several. The reported count is of distinct
    pairs; without this, a correct implementation is indistinguishable from one
    reporting the raw occurrence count.
    """
    n, findings = pgl.count_truth_checked(_fx("duplicate_citation"), repo_root=REPO_ROOT)
    assert n == 1
    assert findings == []


def test_dedup_does_not_merge_distinct_lines_in_one_file():
    """Guards the inverse: a dedup keyed on path alone collapses these to 1."""
    n, findings = pgl.count_truth_checked(_fx("distinct_lines_same_file"), repo_root=REPO_ROOT)
    assert n == 2
    assert findings == []


def test_every_citation_evidence_reason_contains_the_word_evidence():
    """The existing suite asserts `"evidence" in f.reason.lower()`.

    All three citation-evidence kinds must keep it or an undeclared test breaks.
    """
    seen = set()
    for name in ("false_line", "unpaired", "unresolvable"):
        for f in pgl.check_citation_evidence(_fx(name), repo_root=REPO_ROOT):
            seen.add(f.kind)
            assert "evidence" in f.reason.lower(), f.kind
    assert seen == {"evidence-not-reproducible", "unpaired-citation", "evidence-unresolvable"}


def test_non_file_line_kinds_keep_block_level_behavior():
    """Migration and bare git-show citations have no line to verify.

    They keep the legacy `_EVIDENCE_RE` presence rule -- which is what makes
    `test_no_finding_when_evidence_present` in the existing suite survive.
    """
    text = ("## Locked Decisions\n\n"
            "- LD-1: migration `20240101_init.sql`.\n"
            "  Evidence: `git show abc123:x/20240101_init.sql | grep -nE 'create' -> create table items`\n")
    assert pgl.check_citation_evidence(text, repo_root=REPO_ROOT) == []


def test_the_pairing_check_can_report_nothing_and_still_be_running():
    """A block with zero citations yields zero findings AND the parser is
    observed to have returned a non-empty list, so a parser that silently
    returned `[]` cannot satisfy this suite."""
    text = _fx("true")
    assert pgl.check_citation_evidence(text, repo_root=REPO_ROOT) == []
    assert pgl.parse_evidence_statements(text) != []


def test_the_ceiling_names_both_truth_checked_and_presence_only_kinds(tmp_path, capsys):
    """The stated ceiling must be visible where the lint reports, not only in a
    doctrine nobody reads at the moment of use."""
    plan = tmp_path / "plan-x.md"
    plan.write_text(_fx("false_line"), encoding="utf-8")
    rc = pgl.main(["--plan", str(plan), "--repo-root", str(REPO_ROOT)])
    err = capsys.readouterr().err
    assert rc == 0, "WARN-only contract preserved"
    assert "truth-checked" in err
    assert "presence-only" in err
