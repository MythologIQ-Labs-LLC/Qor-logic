"""Phase 240: execution-context adaptive governance tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import execution_context as ec


def _contract_file(tmp_path: Path, extra: str = "") -> Path:
    path = tmp_path / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\n"
        "name: qor-audit\n"
        "hard_execution_requirements: [repo-read, repo-search]\n"
        "advisory_quality_requirements: [high-reasoning]\n"
        "rendering_recipes: [conservative, outcome-first, explicit-checklist]\n"
        "default_rendering_recipe: conservative\n"
        f"{extra}"
        "---\n# audit\n",
        encoding="utf-8",
    )
    return path


def _legacy_file(tmp_path: Path) -> Path:
    path = tmp_path / "qor" / "skills" / "governance" / "legacy" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\n"
        "name: legacy\n"
        "model_compatibility: [claude-opus-4-7]\n"
        "min_model_capability: opus\n"
        "---\n# legacy\n",
        encoding="utf-8",
    )
    return path


def _context(**overrides) -> ec.ExecutionContext:
    values = {
        "host": "test-host",
        "declared_model_family": "unknown-model",
        "responder_model_family": "unknown",
        "reasoning_mode": "unknown",
        "capabilities": (),
        "capabilities_complete": False,
        "rendering_hint": None,
    }
    values.update(overrides)
    return ec.ExecutionContext(**values)


def test_unknown_model_identity_does_not_block_contract(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    result = ec.inspect_contract(contract, _context())
    assert result["context"]["declared_model_family"] == "unknown-model"
    assert result["missing_hard_requirements"] == []
    assert result["unverified_hard_requirements"] == ["repo-read", "repo-search"]


def test_declared_and_responder_model_are_distinct(monkeypatch):
    monkeypatch.setattr(ec, "_platform_context", lambda: ("test-host", set()))
    context = ec.detect_context({
        "QOR_MODEL_FAMILY": "declared-family",
        "QOR_RESPONDER_MODEL_FAMILY": "actual-responder",
    })
    assert context.declared_model_family == "declared-family"
    assert context.responder_model_family == "actual-responder"


def test_complete_capability_inventory_reports_real_missing_requirement(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    context = _context(capabilities=("repo-read",), capabilities_complete=True)
    result = ec.inspect_contract(contract, context)
    assert result["missing_hard_requirements"] == ["repo-search"]
    assert result["unverified_hard_requirements"] == []


def test_high_reasoning_selects_outcome_first_when_admitted(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    assert ec.select_recipe(contract, _context(reasoning_mode="high")) == "outcome-first"


def test_valid_rendering_hint_selects_only_admitted_recipe(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    context = _context(rendering_hint="explicit-checklist")
    assert ec.select_recipe(contract, context) == "explicit-checklist"


def test_unadmitted_rendering_hint_falls_back(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    context = _context(rendering_hint="skip-the-boring-bits")
    assert ec.select_recipe(contract, context) == "conservative"


def test_legacy_model_metadata_is_conservative_only(tmp_path):
    contract = ec.load_contract(_legacy_file(tmp_path))
    assert contract is not None
    assert contract.hard_requirements == ()
    assert contract.rendering_recipes == ("conservative",)
    assert "legacy-model-metadata-advisory" in contract.quality_requirements
    context = _context(reasoning_mode="high", rendering_hint="outcome-first")
    assert ec.select_recipe(contract, context) == "conservative"


def test_rendering_directives_preserve_governance_semantics(tmp_path):
    contract = ec.load_contract(_contract_file(tmp_path))
    assert contract is not None
    for recipe in ec.RENDER_RECIPES:
        result = ec.inspect_contract(contract, _context(rendering_hint=recipe))
        joined = " ".join(result["rendering_directives"]).lower()
        assert "every" in joined or "preserve" in joined
        assert "authority_note" in result
        assert "do not alter" in result["authority_note"]


def test_invalid_recipe_in_skill_contract_is_rejected(tmp_path):
    path = _contract_file(tmp_path)
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "[conservative, outcome-first, explicit-checklist]",
        "[conservative, invent-my-own-rules]",
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported rendering recipe"):
        ec.load_contract(path)


def test_scan_ignores_skills_without_execution_context_contract(tmp_path):
    path = tmp_path / "qor" / "skills" / "plain" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: plain\n---\n# plain\n", encoding="utf-8")
    assert ec.scan(tmp_path, _context()) == []
