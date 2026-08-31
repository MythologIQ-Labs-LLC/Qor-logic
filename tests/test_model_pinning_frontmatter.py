"""Phase 240: model identity is provenance, not execution authority."""
from __future__ import annotations

from pathlib import Path

from qor.scripts.model_pinning_lint import (
    RETIRED_MODEL_FIELDS,
    check,
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


def test_retired_model_admission_fields_are_detected(tmp_path):
    repo = _make_repo(
        tmp_path,
        "model_compatibility: [legacy-model]\nmin_model_capability: legacy-tier",
    )
    warnings = check(repo, current_model="unrelated-runtime")
    assert len(warnings) == 1
    assert "retired named-model admission metadata" in warnings[0].reason
    assert all(field in warnings[0].reason for field in RETIRED_MODEL_FIELDS)


def test_model_identity_does_not_change_clean_skill_result(tmp_path):
    repo = _make_repo(tmp_path, "rendering_recipes: [conservative]")
    assert check(repo, current_model="runtime-a") == []
    assert check(repo, current_model="runtime-b") == []
    assert check(repo, current_model=None) == []


def test_retired_field_inventory_is_generic():
    assert RETIRED_MODEL_FIELDS == (
        "model_compatibility",
        "min_model_capability",
    )


def test_fabrication_guard_warns_when_pointer_missing(tmp_path):
    repo = _make_repo(
        tmp_path,
        "rendering_recipes: [conservative]",
        name="qor-audit",
    )
    warnings = check(repo, current_model="any-runtime")
    guard = [warning for warning in warnings if "fabrication" in warning.reason]
    assert len(guard) == 1
    assert guard[0].skill == "qor-audit"


def test_fabrication_guard_silent_when_pointer_present(tmp_path):
    skill = tmp_path / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: qor-audit\nrendering_recipes: [conservative]\n---\n"
        "Negative constraints: qor/references/doctrine-negative-constraints.md\n",
        encoding="utf-8",
    )
    warnings = check(tmp_path, current_model="any-runtime")
    assert not [warning for warning in warnings if "fabrication" in warning.reason]


def test_fabrication_guard_ignores_non_risk_skills(tmp_path):
    repo = _make_repo(
        tmp_path,
        "rendering_recipes: [conservative]",
        name="qor-ideate",
    )
    warnings = check(repo, current_model="any-runtime")
    assert not [warning for warning in warnings if "fabrication" in warning.reason]


def test_risk_set_matches_dist_compile():
    from qor.scripts.dist_compile import _FABRICATION_RISK_SKILLS as compile_set
    from qor.scripts.model_pinning_lint import _FABRICATION_RISK_SKILLS as lint_set

    assert compile_set == lint_set


def test_fabrication_guard_scan_clean_on_live_corpus():
    warnings = check(REPO_ROOT, current_model="arbitrary-runtime")
    guard = [warning for warning in warnings if "fabrication" in warning.reason]
    assert not guard, f"risk skills missing doctrine pointer: {guard}"


def test_no_retired_admission_fields_in_live_corpus():
    """Plan Phase 2 completion requirement (Phase 240 iteration-2 audit V1):
    the corpus test that fails if either legacy admission field reappears in
    a live skill. Detection behavior is proven against fixtures above; this
    binds the real corpus so a reintroduced field turns CI red instead of a
    stderr WARN nobody reads."""
    retired = [
        w for w in check(REPO_ROOT)
        if "retired named-model admission metadata" in w.reason
    ]
    assert retired == [], (
        "live skill(s) carry retired named-model admission metadata: "
        + ", ".join(w.skill for w in retired)
    )


def test_scan_reports_malformed_contract_without_suppressing_the_rest(tmp_path):
    """Phase 240 iteration-2 audit V2: one malformed execution contract must
    not abort inspection of every remaining skill (the prior lint path caught
    the first ValueError and returned, failing open corpus-wide)."""
    from qor.scripts import model_pinning_lint as execution_context

    good = tmp_path / "qor" / "skills" / "test" / "good" / "SKILL.md"
    good.parent.mkdir(parents=True)
    good.write_text(
        "---\nname: good\nrendering_recipes: [conservative]\n"
        "default_rendering_recipe: conservative\n---\nbody\n",
        encoding="utf-8",
    )
    bad = tmp_path / "qor" / "skills" / "test" / "bad" / "SKILL.md"
    bad.parent.mkdir(parents=True)
    bad.write_text(
        "---\nname: bad\nrendering_recipes: [conservative]\n"
        "default_rendering_recipe: not-an-admitted-recipe\n---\nbody\n",
        encoding="utf-8",
    )

    results, errors = execution_context.scan_with_errors(tmp_path)
    assert [row["skill"] for row in results] == ["good"], (
        "the well-formed contract must still be inspected"
    )
    assert len(errors) == 1 and "bad" in errors[0], (
        "the malformed contract must be reported, not swallowed"
    )
