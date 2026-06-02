"""Behavioral tests for plan_grep_lint citation-evidence check (Phase 125; GH #152).

Each test invokes check_citation_evidence / check_plan / main and asserts on the
emitted findings, not on file presence. LD-region scoping is guarded by the
no-over-flag test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import plan_grep_lint as pgl

_LD_NO_EVIDENCE = """# Plan: thing

## Locked Decisions

- LD-1: reads `20240101_init.sql` for the items table.
- LD-2: cites `git show abc123:src/x.py` for the handler.
"""

_LD_WITH_EVIDENCE = """# Plan: thing

## Locked Decisions

- LD-1: migration `20240101_init.sql`.
  Evidence: `git show abc123:supabase/migrations/20240101_init.sql | grep -nE 'create table' -> create table items (id int)`
"""

_NO_LD_REGION = """# Plan: thing

## Phase 1

### Affected Files
- `qor/scripts/x.py:42` - touch the handler at line 42.
"""


def test_flags_sealed_citation_without_evidence() -> None:
    findings = pgl.check_citation_evidence(_LD_NO_EVIDENCE)
    assert findings, "evidence-less sealed citations in an LD block must be flagged"
    cited = " ".join(f.citation for f in findings)
    assert "20240101_init.sql" in cited or "git show abc123" in cited


def test_no_finding_when_evidence_present() -> None:
    assert pgl.check_citation_evidence(_LD_WITH_EVIDENCE) == []


def test_no_finding_without_ld_region() -> None:
    # file:line outside any Locked-Decision heading must NOT be flagged (no over-flag).
    assert pgl.check_citation_evidence(_NO_LD_REGION) == []


def test_file_line_citation_in_ld_flagged() -> None:
    text = "## Citation Inventory\n\n- LD-1: see `qor/scripts/foo.py:120`.\n"
    findings = pgl.check_citation_evidence(text)
    assert any("foo.py:120" in f.citation for f in findings)


def test_check_plan_merges_citation_findings(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_LD_NO_EVIDENCE, encoding="utf-8")
    findings = pgl.check_plan(p, tmp_path)
    assert any("evidence" in f.reason.lower() for f in findings)


def test_attribution_12g_cross_iteration_regression() -> None:
    # SG-CitationDrift-A: a sealed migration cited in an LD with no grep-evidence,
    # the citation that historically survived across audit iterations. The lint is
    # stateless over plan text, so it fires regardless of "iteration".
    plan = (
        "## Locked Decisions\n\n"
        "- LD-7: the attribution backfill relies on migration "
        "`20240612_attribution_12g.sql` being applied.\n"
    )
    findings = pgl.check_citation_evidence(plan)
    assert any("20240612_attribution_12g.sql" in f.citation for f in findings)


def test_main_warn_only_but_reports_citation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_LD_NO_EVIDENCE, encoding="utf-8")
    rc = pgl.main(["--plan", str(p), "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()
    text = captured.out + captured.err
    assert rc == 0  # WARN-only contract preserved
    assert "20240101_init.sql" in text or "evidence" in text.lower()
