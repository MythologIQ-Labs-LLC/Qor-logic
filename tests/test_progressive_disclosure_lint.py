"""Behavioral tests for Phase 132 (GH #162): progressive-disclosure lint +
corpus consolidation report.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import progressive_disclosure_lint as pdl
from qor.scripts import corpus_consolidation_report as ccr

_BIG_PROSE = ("This is a long inline sub-pass paragraph that should live in a "
              "references file. ") * 40  # ~3000 chars, no code, no references pointer


def _section(heading: str, body: str) -> str:
    return f"{heading}\n\n{body}\n\n"


def _skill(root: Path, name: str, text: str) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / "SKILL.md"
    p.write_text(text, encoding="utf-8")
    return p


# --- AC1: progressive-disclosure lint ---

def test_oversized_inline_section_flagged() -> None:
    text = "# Skill\n\n" + _section("### Step 4: Big sub-pass", _BIG_PROSE)
    findings = pdl.scan_text("qor-x", text)
    assert findings
    assert any("Big sub-pass" in f.section for f in findings)


def test_section_with_references_pointer_cleared() -> None:
    body = _BIG_PROSE + "\n\nSee `qor/references/foo.md` for the full sub-pass."
    text = "# Skill\n\n" + _section("### Step 4: Big sub-pass", body)
    assert pdl.scan_text("qor-x", text) == []


def test_escape_comment_clears() -> None:
    body = _BIG_PROSE + "\n<!-- qor:inline-prose-ok -->"
    text = "# Skill\n\n" + _section("### Step 4: Big sub-pass", body)
    assert pdl.scan_text("qor-x", text) == []


def test_small_section_not_flagged() -> None:
    text = "# Skill\n\n" + _section("### Step 1: Tiny", "A short step.")
    assert pdl.scan_text("qor-x", text) == []


def test_fenced_code_excluded_from_prose() -> None:
    body = "Short intro.\n\n```python\n" + ("x = 1\n" * 600) + "```\n"
    text = "# Skill\n\n" + _section("### Step 2: Mostly code", body)
    assert pdl.scan_text("qor-x", text) == []


def test_scan_skills_over_tmp_root(tmp_path: Path) -> None:
    _skill(tmp_path, "qor-x", "# Skill\n\n" + _section("### Step 4: Big", _BIG_PROSE))
    findings = pdl.scan_skills(tmp_path)
    assert len(findings) == 1


def test_main_exit_codes(tmp_path: Path) -> None:
    _skill(tmp_path, "qor-x", "# Skill\n\n" + _section("### Step 4: Big", _BIG_PROSE))
    assert pdl.main(["--skills-root", str(tmp_path)]) == 1
    _skill(tmp_path, "qor-y", "# Skill\n\n### Step 1\n\nshort\n")
    # qor-x still oversized -> still 1
    assert pdl.main(["--skills-root", str(tmp_path)]) == 1


# --- AC2: consolidation report ---

def test_report_ranks_oversized_skills_first(tmp_path: Path) -> None:
    _skill(tmp_path, "qor-huge", "# Skill\n\n### Step\n\n" + ("padding line. " * 3200))  # >40KB
    _skill(tmp_path, "qor-extract", "# Skill\n\n" + _section("### Step 4: Big", _BIG_PROSE))
    report = ccr.build_report(tmp_path)
    assert report.candidates
    assert "qor-huge" in report.candidates[0]


def test_report_total_bytes_sums_corpus(tmp_path: Path) -> None:
    a = _skill(tmp_path, "qor-a", "# A\n\nshort\n")
    b = _skill(tmp_path, "qor-b", "# B\n\nshort\n")
    report = ccr.build_report(tmp_path)
    assert report.total_bytes == a.stat().st_size + b.stat().st_size


def test_report_empty_when_lean(tmp_path: Path) -> None:
    _skill(tmp_path, "qor-a", "# A\n\nshort\n")
    assert ccr.build_report(tmp_path).candidates == ()


def test_process_review_cycle_wires_consolidation_report() -> None:
    text = Path("qor/skills/governance/qor-process-review-cycle/SKILL.md").read_text(
        encoding="utf-8")
    assert "corpus_consolidation_report" in text  # prose-lint: ok=prompt-contract
