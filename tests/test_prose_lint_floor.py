"""Enforce floor for prose_test_lint (Phase 117, #174).

Locks the gate: the test suite must carry ZERO unexplained presence-only
SKILL.md-substring assertions. New ones must either be converted to behavioral
assertions or carry an explicit `# prose-lint: ok=<reason>` allowlist comment.
This is what makes the `--enforce` wiring in /qor-audit safe.
"""
from __future__ import annotations

from qor.scripts import prose_test_lint


def test_no_unexplained_prose_lint_findings():
    findings = prose_test_lint.scan_dir("tests")
    unexplained = [f for f in findings if not f["exempted"]]
    assert unexplained == [], (
        f"{len(unexplained)} unexplained presence-only assertion(s); convert to "
        f"behavioral or add `# prose-lint: ok=<reason>`: "
        + "; ".join(f"{f['file']}:{f['line']}" for f in unexplained[:8])
    )
