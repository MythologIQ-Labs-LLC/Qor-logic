"""Phase 24 (widened Phase 25): codebase-wide ban on unsafe YAML loaders.

Scans ``qor/`` and ``tests/``. ``qor/vendor/`` and ``tests/fixtures/`` are
excluded: the former because vendored upstream may legitimately use the banned
APIs; the latter because fixtures deliberately contain unsafe content to
verify the discipline catches it elsewhere.
"""
from __future__ import annotations

import re
from pathlib import Path


_UNSAFE_API = re.compile(r"yaml\.(load|load_all|full_load|unsafe_load)\s*\(")
_ROOTS = ("qor", "tests")
_EXCLUDE_DIRS = ("vendor", "fixtures")
# Self-referential meta-test files that mention the banned API as strings
# while enforcing the discipline. They do not call the banned API.
_EXCLUDE_FILES = (
    "test_yaml_safe_load_discipline.py",
    "test_owasp_governance.py",
)


def _is_call_site(line: str, match_start: int) -> bool:
    """True if the match is a bare code call, not inside a string literal."""
    prefix = line[:match_start]
    # Count unescaped double and single quotes before the match
    double = prefix.count('"') - prefix.count('\\"')
    single = prefix.count("'") - prefix.count("\\'")
    # Odd count means we're inside an unclosed string literal
    if double % 2 == 1 or single % 2 == 1:
        return False
    # Comment before the match => string/doc reference, not a call
    if "#" in prefix:
        return False
    return True


def _scan(root: Path) -> list[str]:
    violations: list[str] = []
    for py_path in root.rglob("*.py"):
        if any(part in _EXCLUDE_DIRS for part in py_path.parts):
            continue
        if py_path.name in _EXCLUDE_FILES:
            continue
        text = py_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = _UNSAFE_API.search(line)
            if match and _is_call_site(line, match.start()):
                violations.append(f"{py_path}:{lineno}: {line.strip()}")
    return violations


def test_no_unsafe_yaml_apis_across_scope():
    repo = Path(__file__).resolve().parent.parent
    violations: list[str] = []
    for name in _ROOTS:
        violations.extend(_scan(repo / name))
    assert not violations, (
        "Unsafe YAML API usage detected (use yaml.safe_load only):\n  "
        + "\n  ".join(violations)
    )


def test_widened_scope_catches_planted_call(tmp_path):
    """Proves the scan routine flags a violation when it appears outside the
    exclusion set. Plants ``yaml.load(...)`` in a temp file at a tests-style
    path (no ``fixtures`` segment) and asserts the scanner flags it.
    """
    planted = tmp_path / "planted_call.py"
    planted.write_text("import yaml\n_ = yaml.load('a: 1')\n", encoding="utf-8")
    violations = _scan(tmp_path)
    assert any("planted_call.py" in v for v in violations), (
        f"Planted unsafe call not caught by scanner. Violations: {violations}"
    )


def test_fixtures_excluded_from_scan():
    """The deliberate unsafe fixture must NOT be flagged by the main scan
    (because ``tests/fixtures/`` is excluded). This is the bait control."""
    repo = Path(__file__).resolve().parent.parent
    tests_violations = _scan(repo / "tests")
    for v in tests_violations:
        assert "fixtures" not in v, (
            f"Fixture directory leaked into scan: {v}"
        )
