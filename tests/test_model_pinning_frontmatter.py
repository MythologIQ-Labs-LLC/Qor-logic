"""Phase 240: legacy model pinning is provenance, not execution authority."""
from __future__ import annotations

from pathlib import Path

from qor.scripts.model_pinning_lint import (
    _CAPABILITY_ORDER,
    check,
    extract_capability_tier,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_repo(tmp_path: Path, frontmatter: str, *, name: str = "test") -> Path:
    skill = tmp_path / "qor" / "skills" / "test" / name / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        f"---\nname: {name}\n{frontmatter}\n---\nbody\n",
        encoding="utf-8",
    )
    return tmp_path


def test_model_family_mismatch_no_longer_creates_authority_warning(tmp_path):
    repo = _make_repo(
        tmp_path,
        "model_compatibility: [claude-opus-4-7]\nmin_model_capability: opus",
    )
    assert check(repo, current_model="totally-different-model") == []


def test_unknown_model_family_is_not_rejected(tmp_path):
    repo = _make_repo(tmp_path, "min_model_capability: opus")
    assert check(repo, current_model="unknown") == []


def test_capability_tier_helper_remains_for_historical_callers():
    assert extract_capability_tier("claude-opus-4-7") == "opus"
    assert extract_capability_tier("claude-sonnet-4-6") == "sonnet"
    assert extract_capability_tier("claude-haiku-4-5") == "haiku"
    assert extract_capability_tier("new-vendor-model") is None


def test_legacy_capability_order_export_is_stable_but_non_authoritative():
    assert _CAPABILITY_ORDER == ("haiku", "sonnet", "opus")


def test_fabrication_guard_warns_when_pointer_missing(tmp_path):
    repo = _make_repo(
        tmp_path,
        "min_model_capability: opus",
        name="qor-audit",
    )
    warnings = check(repo, current_model="any-model")
    guard = [warning for warning in warnings if "fabrication" in warning.reason]
    assert len(guard) == 1
    assert guard[0].skill == "qor-audit"


def test_fabrication_guard_silent_when_pointer_present(tmp_path):
    skill = tmp_path / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: qor-audit\nmin_model_capability: opus\n---\n"
        "Negative constraints: qor/references/doctrine-negative-constraints.md\n",
        encoding="utf-8",
    )
    warnings = check(tmp_path, current_model="any-model")
    assert not [warning for warning in warnings if "fabrication" in warning.reason]


def test_fabrication_guard_ignores_non_risk_skills(tmp_path):
    repo = _make_repo(tmp_path, "min_model_capability: opus", name="qor-ideate")
    warnings = check(repo, current_model="any-model")
    assert not [warning for warning in warnings if "fabrication" in warning.reason]


def test_risk_set_matches_dist_compile():
    from qor.scripts.dist_compile import _FABRICATION_RISK_SKILLS as compile_set
    from qor.scripts.model_pinning_lint import _FABRICATION_RISK_SKILLS as lint_set
    assert compile_set == lint_set


def test_fabrication_guard_scan_clean_on_live_corpus():
    warnings = check(REPO_ROOT, current_model="non-claude-model")
    guard = [warning for warning in warnings if "fabrication" in warning.reason]
    assert not guard, f"risk skills missing doctrine pointer: {guard}"
