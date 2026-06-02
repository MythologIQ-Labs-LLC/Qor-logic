"""Behavioral tests for qor.scripts.plan_feature_tdd_lint (Phase 130; GH #159)."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import plan_feature_tdd_lint as ftl


def _fit(rows: str) -> str:
    return "# Plan\n\n## Feature Inventory Touches\n\n" + rows + "\n\n## Phase 1\n"


def _row(op: str, test_path: str, desc: str, entry: str = "n/a") -> str:
    return (f"- entry_id: `{entry}` operation: `{op}` "
            f"test_path: `{test_path}` test_descriptor: `{desc}`")


def test_parse_fit_rows_extracts_columns() -> None:
    text = _fit(_row("NEW", "tests/test_a.py", "a returns 1") + "\n"
                + _row("MODIFIED", "tests/test_b.py", "b returns 2"))
    rows = ftl.parse_fit_rows(text)
    assert len(rows) == 2
    assert rows[0]["operation"] == "NEW"
    assert rows[0]["test_path"] == "tests/test_a.py"
    assert rows[1]["test_descriptor"] == "b returns 2"


def test_new_row_with_test_clears() -> None:
    text = _fit(_row("NEW", "tests/test_a.py", "POST /x returns 200 + nonce"))
    assert ftl.check_feature_tdd(text) == []


def test_new_row_missing_test_path_flagged() -> None:
    text = _fit(_row("NEW", "n/a", "the feature works"))
    kinds = {f.kind for f in ftl.check_feature_tdd(text)}
    assert "missing-failing-test" in kinds


def test_presence_only_descriptor_flagged() -> None:
    text = _fit(_row("MODIFIED", "tests/test_a.py", "route exists"))
    kinds = {f.kind for f in ftl.check_feature_tdd(text)}
    assert "presence-only-feature-test" in kinds


def test_na_justified_row_exempt() -> None:
    text = _fit(_row("n/a-justified", "n/a", "neighbouring feature, untouched"))
    assert ftl.check_feature_tdd(text) == []


def test_src_touch_without_fit_block_flagged() -> None:
    text = ("# Plan\n\n## Phase 1\n\n### Affected Files\n\n"
            "- `src/foo.ts` - the handler\n")
    kinds = {f.kind for f in ftl.check_feature_tdd(text)}
    assert "undeclared-feature-tdd" in kinds


def test_docs_only_plan_clean() -> None:
    text = ("# Plan\n\n## Phase 1\n\n### Affected Files\n\n"
            "- `docs/x.md` - a doc\n- `qor/references/y.md` - doctrine\n")
    assert ftl.check_feature_tdd(text) == []


def test_main_exit_1_on_finding(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_fit(_row("NEW", "n/a", "the feature works")), encoding="utf-8")
    assert ftl.main(["--plan", str(p), "--repo-root", str(tmp_path)]) == 1


def test_main_exit_0_clean(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_fit(_row("NEW", "tests/test_a.py", "a returns the parsed value")),
                 encoding="utf-8")
    assert ftl.main(["--plan", str(p), "--repo-root", str(tmp_path)]) == 0


def test_audit_invokes_feature_tdd_lint() -> None:
    text = Path("qor/skills/governance/qor-audit/SKILL.md").read_text(encoding="utf-8")
    assert "plan_feature_tdd_lint" in text  # prose-lint: ok=prompt-contract
