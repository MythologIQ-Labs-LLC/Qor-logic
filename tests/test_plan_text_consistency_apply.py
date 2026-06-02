"""Behavioral tests for plan_text_consistency_lint --apply + --type-check (Phase 128; GH #161)."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import plan_text_consistency_lint as ptc

_DRIFT = (
    "# Plan\n\n## A\n\n`python -m qor.cli x --a`\n\n## B\n\n`python -m qor.cli x --b`\n"
)
_CLEAN = "# Plan\n\n## A\n\n`python -m qor.cli x --a`\n\n## B\n\n`python -m qor.cli x --a`\n"
_TYPE_CONFLICT = (
    "# Plan\n\n## A\n\n```python\ndef f(count: int): ...\n```\n\n"
    "## B\n\n```python\ndef g(count: str): ...\n```\n"
)
_TYPE_OK = (
    "# Plan\n\n## A\n\n```python\ndef f(count: int): ...\n```\n\n"
    "## B\n\n```python\ndef g(count: int): ...\n```\n"
)


def test_apply_rewrites_drift() -> None:
    new_text, count = ptc.apply_fixes(_DRIFT, ptc.lint(_DRIFT))
    assert count >= 1
    # both sites collapse to the canonical (earliest) raw; the divergent form is gone
    assert "`python -m qor.cli x --b`" not in new_text
    assert new_text.count("`python -m qor.cli x --a`") == 2


def test_apply_noop_when_no_drift() -> None:
    new_text, count = ptc.apply_fixes(_CLEAN, ptc.lint(_CLEAN))
    assert count == 0 and new_text == _CLEAN


def test_apply_skips_dep_name() -> None:
    # a dep_name finding must not be rewritten (it is not a plan-text fix)
    dep_finding = ptc.DriftFinding(
        operation_kind="dep_name",
        sites=(ptc.Site(line=1, section="Imports", raw_text="leftpad", normalized="leftpad"),),
        resolution_hint="dep not declared",
    )
    new_text, count = ptc.apply_fixes("# P\n\n`leftpad`\n", [dep_finding])
    assert count == 0


def test_main_dry_run_does_not_write(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_DRIFT, encoding="utf-8")
    before = p.read_bytes()
    rc = ptc.main(["--check", str(p)])
    assert rc == 1 and p.read_bytes() == before


def test_main_apply_writes_canonical(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-x.md"
    p.write_text(_DRIFT, encoding="utf-8")
    rc = ptc.main(["--check", str(p), "--apply"])
    assert rc == 0
    assert "`python -m qor.cli x --b`" not in p.read_text(encoding="utf-8")


def test_type_check_flags_conflicting_annotation() -> None:
    findings = ptc._detect_type_annotation_drift(_TYPE_CONFLICT)
    assert any(f.operation_kind == "type_annotation" for f in findings)
    assert any("count" in s.raw_text for f in findings for s in f.sites)


def test_type_check_consistent_not_flagged() -> None:
    assert ptc._detect_type_annotation_drift(_TYPE_OK) == []


def test_main_type_check_includes_type_findings(tmp_path: Path) -> None:
    p = tmp_path / "plan-qor-phase999-t.md"
    p.write_text(_TYPE_CONFLICT, encoding="utf-8")
    assert ptc.main(["--check", str(p), "--type-check"]) == 1
    # without --type-check the same plan (no command/path drift) is clean
    assert ptc.main(["--check", str(p)]) == 0
