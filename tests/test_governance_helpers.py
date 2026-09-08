"""Governance helpers tests (Phase 13 v4).

Covers the 7 functions + InterdictionError in qor/scripts/governance_helpers.py.
Tests before code per doctrine-test-discipline.md.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import governance_helpers as gh


def _write_plan(path: Path, change_class: str | None, bold: bool = True) -> None:
    if change_class is None:
        body = "# Plan\n\n**Status**: Active\n"
    elif bold:
        body = f"# Plan\n\n**change_class**: {change_class}\n**Status**: Active\n"
    else:
        body = f"# Plan\n\nchange_class: {change_class}\n**Status**: Active\n"
    path.write_text(body, encoding="utf-8")


def _write_pyproject(path: Path, version: str) -> None:
    path.write_text(
        f'[project]\nname = "qor-logic"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def test_derive_phase_metadata_from_digit_filename():
    path = Path("docs/plan-qor-phase13-governance-enforcement.md")
    assert gh.derive_phase_metadata(path) == (13, "governance-enforcement")


def test_derive_phase_metadata_rejects_letter_suffix():
    path = Path("docs/plan-qor-phase11d-doctrine-tests.md")
    with pytest.raises(ValueError):
        gh.derive_phase_metadata(path)


def test_current_phase_plan_path_prefers_highest_suffix(tmp_path, monkeypatch):
    (tmp_path / "plan-qor-phase13-governance-enforcement.md").write_text("x", encoding="utf-8")
    (tmp_path / "plan-qor-phase13-v2.md").write_text("x", encoding="utf-8")
    (tmp_path / "plan-qor-phase13-v3.md").write_text("x", encoding="utf-8")
    (tmp_path / "plan-qor-phase13-v4.md").write_text("x", encoding="utf-8")
    monkeypatch.setattr(gh, "_current_branch", lambda: "phase/13-x")
    result = gh.current_phase_plan_path(docs_dir=tmp_path)
    assert result.name == "plan-qor-phase13-v4.md"


def test_parse_change_class_feature(tmp_path):
    p = tmp_path / "plan.md"
    _write_plan(p, "feature")
    assert gh.parse_change_class(p) == "feature"


def test_parse_change_class_invalid_raises(tmp_path):
    p = tmp_path / "plan.md"
    _write_plan(p, "xyz")
    with pytest.raises(ValueError):
        gh.parse_change_class(p)


def test_parse_change_class_rejects_non_bold(tmp_path):
    p = tmp_path / "plan.md"
    _write_plan(p, "feature", bold=False)
    with pytest.raises(ValueError):
        gh.parse_change_class(p)


def test_bump_version_hotfix(tmp_path, monkeypatch):
    py = tmp_path / "pyproject.toml"
    _write_pyproject(py, "0.2.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: [])
    assert gh.bump_version("hotfix", pyproject_path=py) == "0.2.1"
    assert 'version = "0.2.1"' in py.read_text(encoding="utf-8")


def test_bump_version_feature(tmp_path, monkeypatch):
    py = tmp_path / "pyproject.toml"
    _write_pyproject(py, "0.2.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: [])
    assert gh.bump_version("feature", pyproject_path=py) == "0.3.0"


def test_bump_version_breaking(tmp_path, monkeypatch):
    py = tmp_path / "pyproject.toml"
    _write_pyproject(py, "0.2.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: [])
    assert gh.bump_version("breaking", pyproject_path=py) == "1.0.0"


def test_bump_version_raises_on_tag_collision(tmp_path, monkeypatch):
    py = tmp_path / "pyproject.toml"
    _write_pyproject(py, "0.2.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.3.0"])
    with pytest.raises(gh.InterdictionError):
        gh.bump_version("feature", pyproject_path=py)


def test_bump_version_raises_on_downgrade(tmp_path, monkeypatch):
    py = tmp_path / "pyproject.toml"
    _write_pyproject(py, "0.2.0")
    monkeypatch.setattr(gh, "_list_tags", lambda: ["v0.5.0"])
    with pytest.raises(gh.InterdictionError):
        gh.bump_version("hotfix", pyproject_path=py)


# ----- Phase 272 (GH #433): two messages, and the guard they describe -----

def test_parse_change_class_error_names_every_accepted_class(tmp_path):
    """The error listed three classes while the regex accepts four, so a plan
    declaring the fourth was told the class does not exist."""
    from qor.scripts import governance_helpers as gh

    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\nchange_class: governance\n", encoding="utf-8")  # not bold: rejected
    try:
        gh.parse_change_class(plan)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected a rejection for the non-bold form")

    for accepted in ("hotfix", "feature", "breaking", "governance"):
        assert accepted in message, f"{accepted} is accepted by the regex but absent from the error"


def test_compute_new_names_governance_as_non_release():
    """`unknown change_class` was wrong for a value the schema declares valid.
    The refusal now says why, so a caller that arrived here wrongly is told
    what to do rather than that its class does not exist."""
    from qor.scripts import governance_helpers as gh

    try:
        gh._compute_new(0, 170, 0, "governance")
    except ValueError as exc:
        message = str(exc).lower()
    else:
        raise AssertionError("governance must not compute a version")

    assert "non-release" in message
    assert "unknown" not in message


def test_every_declared_class_is_classified_and_computes_iff_release():
    """The partition, not the instance.

    Asserts what GH #282 established -- every declared class is classified, and
    computes a version if and only if it is a release class -- rather than the
    rejected proposition that every class can compute one. Goes red if a fifth
    class is added to the schema without being classified, which today would
    silently ship as version-not-applicable with no version and no tag.
    """
    from qor.scripts import governance_helpers as gh
    from qor.scripts import validate_gate_artifact as vga
    from qor.scripts import version_applicability as va

    enum = vga.load_schema("plan")["properties"]["change_class"]["enum"]
    assert enum, "the schema must declare a change_class enum"

    for change_class in enum:
        assert change_class in (va.RELEASE_CLASSES | va.NON_RELEASE_CLASSES), (
            f"{change_class!r} is declared in the schema but classified by neither set; "
            "it would be silently treated as version-not-applicable"
        )
        if va.is_release_class(change_class):
            assert isinstance(gh._compute_new(0, 1, 0, change_class), tuple)
        else:
            try:
                gh._compute_new(0, 1, 0, change_class)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{change_class!r} is non-release and must not compute a version")
