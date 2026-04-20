"""Structural tests for the /qor-ab-run skill (Phase 39b Phase 1)."""
from __future__ import annotations

import pathlib


_SKILL = pathlib.Path("qor/skills/meta/qor-ab-run/SKILL.md")
_PROMPT = pathlib.Path("qor/skills/meta/qor-ab-run/references/ab-subagent-prompt.md")
_CORPUS_MANIFEST = pathlib.Path("tests/fixtures/ab_corpus/MANIFEST.json")
_VARIANTS_DIR = pathlib.Path("tests/fixtures/ab_corpus/variants")


def test_skill_file_exists():
    assert _SKILL.is_file()


def test_skill_declares_task_tool_orchestration():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "Task" in prose
    assert "parallel" in prose.lower()


def test_skill_references_corpus_manifest():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "MANIFEST.json" in prose


def test_skill_references_4_variant_files():
    prose = _SKILL.read_text(encoding="utf-8")
    for variant_file in (
        "qor-audit.persona.md",
        "qor-audit.stance.md",
        "qor-substantiate.persona.md",
        "qor-substantiate.stance.md",
    ):
        assert variant_file in prose, f"skill missing reference to {variant_file}"


def test_skill_declares_subagent_type_general():
    prose = _SKILL.read_text(encoding="utf-8")
    assert '"general"' in prose
    # And cites the doctrine rule
    assert "doctrine" in prose.lower() and ("§4" in prose or "section 4" in prose.lower())


def test_skill_declares_5_replications():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "5 replications" in prose or "× 5" in prose or "rep 1..5" in prose or "1..5" in prose


def test_skill_writes_results_artifact_path():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "docs/phase39-ab-results.md" in prose


def test_subagent_prompt_template_has_placeholders():
    prose = _PROMPT.read_text(encoding="utf-8")
    assert "{VARIANT_IDENTITY_ACTIVATION_BLOCK}" in prose
    assert "{FIXTURES_CONCATENATED}" in prose


def test_skill_discloses_measurement_scope():
    """O1 from Pass 1 audit: subagent receives variant block only, not full skill body."""
    prose = _SKILL.read_text(encoding="utf-8")
    assert "Measurement scope" in prose or "scope" in prose.lower()
    assert "NOT" in prose  # must declare what's NOT in the subagent prompt


def test_skill_records_model_identity():
    """O5 from Pass 1 audit: record session model in results artifact."""
    prose = _SKILL.read_text(encoding="utf-8")
    assert "model" in prose.lower()


def test_skill_has_constraints_section():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "## Constraints" in prose


def test_skill_has_next_step_section():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "## Next Step" in prose
