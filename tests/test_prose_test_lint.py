"""Behavioral tests for the prose-not-behavior test-source lint (Phase 116, #170).

The lint flags tests whose only assertion is substring membership in a SKILL.md
(the #56/#58/#83 anti-pattern), without flagging genuine behavioral tests.
"""
from __future__ import annotations

from qor.scripts import prose_test_lint

_PRESENCE_ONLY = '''
from pathlib import Path
def test_thing():
    text = Path("qor/skills/x/SKILL.md").read_text(encoding="utf-8")
    assert "some required phrase" in text
'''

_BEHAVIORAL = '''
from mod import compute
def test_compute():
    result = compute(2, 3)
    assert result == 5
'''


def test_flags_presence_only_assertion():
    findings = prose_test_lint.scan_source(_PRESENCE_ONLY, filename="t.py")
    assert findings
    assert findings[0]["function"] == "test_thing"


def test_ignores_behavioral_test():
    assert prose_test_lint.scan_source(_BEHAVIORAL, filename="t.py") == []


def test_clean_dir_returns_empty(tmp_path):
    (tmp_path / "test_ok.py").write_text(_BEHAVIORAL, encoding="utf-8")
    assert prose_test_lint.scan_dir(str(tmp_path)) == []


def test_scan_dir_flags_presence_only(tmp_path):
    (tmp_path / "test_bad.py").write_text(_PRESENCE_ONLY, encoding="utf-8")
    findings = prose_test_lint.scan_dir(str(tmp_path))
    assert len(findings) == 1


def test_doctrine_defines_prose_lint_term():
    from pathlib import Path
    text = Path("qor/references/doctrine-verification-closure-integrity.md").read_text(
        encoding="utf-8").lower()
    assert "prose-behavior test lint" in text
    assert "coverage" in text and "stability" in text
