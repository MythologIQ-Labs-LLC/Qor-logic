"""Phase 225 (GH #336): the canonical statement is evidence on its own account.

Phase 223 resolved a statement only when a bare ``file:line`` citation elsewhere
in the block demanded it, so a plan citing solely in the mandated form indexed
its statements and never read them -- the enforcer reported zero truth-checked
citations over every recent real plan. These tests bind the first-class
adjudication contract: every parsed statement is resolved, findings carry bare
``<path>:<line>`` citation keys (the ref lives in the reason), and the reported
count is of distinct examined targets, statements and demands unioned.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import plan_grep_lint


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "sample.py").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, check=True)
    return tmp_path


def test_canonical_statement_is_truth_checked_without_bare_file_line(tmp_path):
    """A lone true statement is examined and clean; nothing needs to demand it."""
    repo = _repo(tmp_path)
    plan = ("## Infrastructure Citation Inventory\n"
            "- `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta`\n")

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert findings == []


def test_wrong_line_is_not_reproducible(tmp_path):
    """The finding's citation key is bare; the ref appears in the reason."""
    repo = _repo(tmp_path)
    plan = ("## Infrastructure Citation Inventory\n"
            "- `git show v1.0.0:sample.py | grep -nE 'beta' -> 3:beta`\n")

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert [f.kind for f in findings] == ["evidence-not-reproducible"]
    assert findings[0].citation == "sample.py:3"
    assert "v1.0.0" in findings[0].reason


def test_missing_line_is_unresolvable(tmp_path):
    repo = _repo(tmp_path)
    plan = ("## Locked Decisions\n"
            "- `git show v1.0.0:sample.py | grep -nE 'beta' -> 999:beta`\n")

    _, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert [f.kind for f in findings] == ["evidence-unresolvable"]
    assert findings[0].citation == "sample.py:999"


def test_bare_citation_and_matching_statement_count_once(tmp_path):
    """Union dedup by (path, line): one location, one examined target."""
    repo = _repo(tmp_path)
    plan = ("## Locked Decisions\n"
            "- decision anchored at `sample.py:2`\n"
            "- `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta`\n")

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert findings == []


def test_md_citation_enters_the_demand_set(tmp_path):
    """Documentation surfaces are demandable like code surfaces (F5 remedy)."""
    repo = _repo(tmp_path)
    plan = ("## Locked Decisions\n"
            "- the contract lives at `qor/skills/x/SKILL.md:405` with no statement\n")

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert [f.kind for f in findings] == ["unpaired-citation"]
    assert findings[0].citation == "qor/skills/x/SKILL.md:405"
