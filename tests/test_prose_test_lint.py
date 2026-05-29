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


# --- Phase 117 (#174): hardened heuristic + allowlist ----------------------

def _unexplained(findings):
    return [f for f in findings if not f["exempted"]]


_STDERR_FP = '''
from pathlib import Path
def test_cli():
    _ = Path("x/SKILL.md").read_text()        # function mentions SKILL.md
    proc_stderr = "WARN: boom"
    assert "WARN" in proc_stderr              # comparator is NOT the SKILL.md read
'''

_SOURCE_FP = '''
from pathlib import Path
def test_src():
    src = Path("qor/scripts/x.py").read_text()
    _ = Path("a/SKILL.md").read_text()
    assert "qor-logic install" in src         # comparator traces to x.py, not SKILL.md
'''

_DICT_FP = '''
from pathlib import Path
def test_manifest():
    _ = Path("a/SKILL.md").read_text()
    entry = {"id": 1, "sha256": "x"}
    assert "sha256" in entry                  # comparator is an emitted dict
'''

_ALLOWLISTED = '''
from pathlib import Path
def test_contract():
    text = Path("a/SKILL.md").read_text()
    assert "|| true" in text  # prose-lint: ok=documented shell-control in prompt
'''

_ALLOWLIST_EMPTY = '''
from pathlib import Path
def test_contract():
    text = Path("a/SKILL.md").read_text()
    assert "|| true" in text  # prose-lint: ok=
'''


def test_ignores_assert_on_subprocess_stderr():
    assert _unexplained(prose_test_lint.scan_source(_STDERR_FP)) == []


def test_ignores_assert_on_module_source():
    assert _unexplained(prose_test_lint.scan_source(_SOURCE_FP)) == []


def test_ignores_assert_on_emitted_dict():
    assert _unexplained(prose_test_lint.scan_source(_DICT_FP)) == []


def test_allowlist_comment_suppresses():
    findings = prose_test_lint.scan_source(_ALLOWLISTED)
    assert _unexplained(findings) == []
    assert any(f["exempted"] and "shell-control" in (f["reason"] or "") for f in findings)


def test_allowlist_requires_reason():
    assert _unexplained(prose_test_lint.scan_source(_ALLOWLIST_EMPTY))


def test_enforce_exit_nonzero_on_unexplained(tmp_path):
    (tmp_path / "test_bad.py").write_text(_PRESENCE_ONLY, encoding="utf-8")
    assert prose_test_lint.main(["--tests-dir", str(tmp_path), "--enforce"]) == 1


def test_enforce_exit_zero_when_only_exempted(tmp_path):
    (tmp_path / "test_ok.py").write_text(_ALLOWLISTED, encoding="utf-8")
    assert prose_test_lint.main(["--tests-dir", str(tmp_path), "--enforce"]) == 0


_MODULE_CONST = '''
from pathlib import Path
SKILL = Path("qor/skills/x/SKILL.md")
def test_wiring():
    text = SKILL.read_text(encoding="utf-8")
    assert "qor.scripts.dod_check" in text
'''

_MODULE_CONST_DICT = '''
from pathlib import Path
SKILL = Path("qor/skills/x/SKILL.md")
def test_emits():
    _ = SKILL.read_text(encoding="utf-8")
    entry = {"sha256": "x"}
    assert "sha256" in entry
'''


def test_flags_module_level_skill_const_read():
    # The dominant real pattern: SKILL path is a module constant, read in the fn.
    assert _unexplained(prose_test_lint.scan_source(_MODULE_CONST))


def test_module_const_does_not_reintroduce_dict_false_positive():
    # Reading the SKILL const but asserting on a dict must NOT flag.
    assert _unexplained(prose_test_lint.scan_source(_MODULE_CONST_DICT)) == []
