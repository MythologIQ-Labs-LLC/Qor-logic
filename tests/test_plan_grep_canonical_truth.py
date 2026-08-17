from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import plan_grep_lint


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    target = tmp_path / "sample.py"
    target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    subprocess.run(["git", "add", "sample.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "tag", "v1.0.0"], cwd=tmp_path, check=True)
    return tmp_path


def test_canonical_grep_statement_is_truth_checked_without_bare_file_line(tmp_path):
    repo = _repo(tmp_path)
    plan = """## Infrastructure Citation Inventory
- `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta`
"""

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert findings == []


def test_canonical_grep_statement_wrong_line_is_detected(tmp_path):
    repo = _repo(tmp_path)
    plan = """## Infrastructure Citation Inventory
- `git show v1.0.0:sample.py | grep -nE 'beta' -> 3:beta`
"""

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert len(findings) == 1
    assert findings[0].kind == "evidence-not-reproducible"
    assert findings[0].citation == "v1.0.0:sample.py:3"


def test_canonical_grep_statement_missing_line_is_unresolvable(tmp_path):
    repo = _repo(tmp_path)
    plan = """## Locked Decisions
- `git show v1.0.0:sample.py | grep -nE 'beta' -> 999:beta`
"""

    _, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert len(findings) == 1
    assert findings[0].kind == "evidence-unresolvable"


def test_bare_file_line_and_matching_statement_count_once(tmp_path):
    repo = _repo(tmp_path)
    plan = """## Locked Decisions
- decision anchored at `sample.py:2`
- `git show v1.0.0:sample.py | grep -nE 'beta' -> 2:beta`
"""

    checked, findings = plan_grep_lint.count_truth_checked(plan, repo)

    assert checked == 1
    assert findings == []
