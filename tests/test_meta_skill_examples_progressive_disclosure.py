"""Phase 98: structural countermeasure for F5+F6 meta-skill example moves.

Asserts the progressive-disclosure invariant for the two migrated meta
skills (`qor-meta-log-decision`, `qor-meta-track-shadow`): each SKILL.md
cites its examples reference file by path, the reference file exists,
and the reference file preserves the expected example identifiers.

Catches the inline-examples regression: if a future edit removes the
pointer or inlines the examples back into SKILL.md, these tests fail.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

LOG_DECISION_SKILL = REPO_ROOT / "qor" / "skills" / "meta" / "qor-meta-log-decision" / "SKILL.md"
LOG_DECISION_REF = REPO_ROOT / "qor" / "skills" / "meta" / "qor-meta-log-decision" / "references" / "example-decision-entries.md"
LOG_DECISION_POINTER = "references/example-decision-entries.md"
LOG_DECISION_EXAMPLE_IDS = (
    "Example 1: Architecture Decision (L2)",
    "Example 2: Security Decision (L3)",
    "Example 3: Scope Change (L2)",
)

TRACK_SHADOW_SKILL = REPO_ROOT / "qor" / "skills" / "meta" / "qor-meta-track-shadow" / "SKILL.md"
TRACK_SHADOW_REF = REPO_ROOT / "qor" / "skills" / "meta" / "qor-meta-track-shadow" / "references" / "example-shadow-genome-events.md"
TRACK_SHADOW_POINTER = "references/example-shadow-genome-events.md"
TRACK_SHADOW_EXAMPLE_IDS = ("SG-001", "SG-002", "SG-003")


# --- qor-meta-log-decision -------------------------------------------------

def test_qor_meta_log_decision_skill_cites_examples_reference():
    text = LOG_DECISION_SKILL.read_text(encoding="utf-8")
    assert LOG_DECISION_POINTER in text, (
        f"SKILL.md must cite {LOG_DECISION_POINTER} (progressive disclosure)"
    )


def test_qor_meta_log_decision_examples_reference_file_exists():
    assert LOG_DECISION_REF.exists(), (
        f"Reference file {LOG_DECISION_REF} must exist at HEAD"
    )


def test_qor_meta_log_decision_examples_reference_carries_all_three_examples():
    text = LOG_DECISION_REF.read_text(encoding="utf-8")
    missing = [eid for eid in LOG_DECISION_EXAMPLE_IDS if eid not in text]
    assert not missing, (
        f"Reference file must preserve all three example headings; missing: {missing}"
    )


# --- qor-meta-track-shadow -------------------------------------------------

def test_qor_meta_track_shadow_skill_cites_examples_reference():
    text = TRACK_SHADOW_SKILL.read_text(encoding="utf-8")
    assert TRACK_SHADOW_POINTER in text, (
        f"SKILL.md must cite {TRACK_SHADOW_POINTER} (progressive disclosure)"
    )


def test_qor_meta_track_shadow_examples_reference_file_exists():
    assert TRACK_SHADOW_REF.exists(), (
        f"Reference file {TRACK_SHADOW_REF} must exist at HEAD"
    )


def test_qor_meta_track_shadow_examples_reference_carries_all_three_examples():
    text = TRACK_SHADOW_REF.read_text(encoding="utf-8")
    missing = [eid for eid in TRACK_SHADOW_EXAMPLE_IDS if eid not in text]
    assert not missing, (
        f"Reference file must preserve all three example IDs; missing: {missing}"
    )
