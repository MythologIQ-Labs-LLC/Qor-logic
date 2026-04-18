"""Phase 31 Phase 1: /qor-substantiate Step 6.5 Documentation Currency Check.

Heuristic: if implement.json files_touched contains any file matching
SKILL.md / doctrine-*.md / qor/gates/schema/*.json / qor/scripts/*.py AND
none of docs/architecture.md / lifecycle.md / operations.md / policies.md
are in files_touched -> return warning list.

Else return empty list.

Lives in doc_integrity_strict.py (not doc_integrity.py; Razor budget
preserved per SG-Phase30-A countermeasure).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity_strict as dis  # noqa: E402


def _payload(files_touched: list[str]) -> dict:
    return {
        "phase": "implement",
        "session_id": "sess-test",
        "ts": "2026-04-18T10:00:00Z",
        "files_touched": files_touched,
    }


def test_currency_passes_when_no_doc_affecting_change(tmp_path):
    """Test-only edits don't trigger the currency check."""
    warnings = dis.check_documentation_currency(
        _payload(["tests/test_foo.py"]),
        repo_root=str(tmp_path),
    )
    assert warnings == []


def test_currency_warns_when_skill_touched_but_no_system_doc(tmp_path):
    warnings = dis.check_documentation_currency(
        _payload(["qor/skills/sdlc/qor-plan/SKILL.md"]),
        repo_root=str(tmp_path),
    )
    assert warnings, "Expected warning when SKILL.md touched without system-tier doc"
    assert any("SKILL.md" in w for w in warnings)


def test_currency_passes_when_skill_and_system_doc_both_touched(tmp_path):
    warnings = dis.check_documentation_currency(
        _payload(["qor/skills/sdlc/qor-plan/SKILL.md", "docs/architecture.md"]),
        repo_root=str(tmp_path),
    )
    assert warnings == []


@pytest.mark.parametrize(
    "trigger_file",
    [
        "qor/skills/meta/qor-help/SKILL.md",
        "qor/references/doctrine-test-discipline.md",
        "qor/gates/schema/plan.schema.json",
        "qor/scripts/shadow_process.py",
    ],
)
def test_currency_matches_all_trigger_categories(tmp_path, trigger_file):
    warnings = dis.check_documentation_currency(
        _payload([trigger_file]),
        repo_root=str(tmp_path),
    )
    assert warnings, f"Expected warning when {trigger_file} touched without system-tier doc"
