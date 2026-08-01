"""Regression tests for declarable badge-count filesystem layouts (#293)."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import badge_currency
from qor.scripts import seal_artifacts


def _write_non_qor_repo(tmp_path: Path) -> Path:
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "skills" / "demo" / "SKILL.md").write_text(
        "# demo\n", encoding="utf-8"
    )
    (tmp_path / "skills" / "bic" / "runtime" / "agents").mkdir(parents=True)
    (tmp_path / "skills" / "bic" / "runtime" / "agents" / "reviewer.md").write_text(
        "# reviewer\n", encoding="utf-8"
    )
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "doctrine-demo.md").write_text(
        "# doctrine\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "### Entry #1: SESSION SEAL -- Phase 1 test\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "SYSTEM_STATE.md").write_text(
        "# State\n\n**Snapshot**: 2026-07-30\n**Phase**: Phase 1\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        '<img src="https://img.shields.io/badge/Tests-1%20passing-green" alt="Tests: 1 passing">\n'
        '<img src="https://img.shields.io/badge/Ledger-1%20entries%20sealed-green" alt="Ledger: 1 entries sealed">\n'
        '<img src="https://img.shields.io/badge/Skills-1-blue" alt="Skills: 1">\n'
        '<img src="https://img.shields.io/badge/Agents-1-blue" alt="Agents: 1">\n'
        '<img src="https://img.shields.io/badge/Doctrines-1-blue" alt="Doctrines: 1">\n',
        encoding="utf-8",
    )
    return tmp_path


def _layout() -> badge_currency.BadgeLayout:
    """The non-`qor/` topology `_write_non_qor_repo` lays down."""
    return badge_currency.BadgeLayout(
        skills_root=Path("skills"),
        skills_pattern="**/SKILL.md",
        agents_root=Path("skills"),
        agents_pattern="**/agents/*.md",
        doctrines_root=Path("governance"),
        doctrines_pattern="doctrine-*.md",
    )


_NON_QOR_CLI_FLAGS = [
    "--skills-root", "skills",
    "--skills-pattern", "**/SKILL.md",
    "--agents-root", "skills",
    "--agents-pattern", "**/agents/*.md",
    "--doctrines-root", "governance",
    "--doctrines-pattern", "doctrine-*.md",
]


def _symlink_or_skip(
    link: Path, target: Path, *, target_is_directory: bool = False
) -> None:
    """Create a symlink when the host permits it; Linux remains binding proof."""
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"host cannot create symlinks: {exc}")


def test_missing_default_root_is_resolution_error_not_zero(tmp_path: Path) -> None:
    with pytest.raises(badge_currency.BadgeLayoutError, match="skills root not found"):
        badge_currency.count_skills(tmp_path)


def test_declared_non_qor_layout_counts_actual_files(tmp_path: Path) -> None:
    root = _write_non_qor_repo(tmp_path)
    layout = _layout()
    assert badge_currency.count_skills(
        root, layout.skills_root, layout.skills_pattern
    ) == 1
    assert badge_currency.count_agents(
        root, layout.agents_root, layout.agents_pattern
    ) == 1
    assert badge_currency.count_doctrines(
        root, layout.doctrines_root, layout.doctrines_pattern
    ) == 1
    assert badge_currency.count_by_layout(root, layout) == {
        "skills": 1,
        "agents": 1,
        "doctrines": 1,
    }
    assert badge_currency.check_currency(
        root,
        root / "docs" / "META_LEDGER.md",
        skip_tests=True,
        layout=layout,
    ) == []


def test_seal_check_propagates_declared_layout(tmp_path: Path) -> None:
    root = _write_non_qor_repo(tmp_path)
    rc = seal_artifacts.main(
        ["--check", "--repo-root", str(root), "--skip-tests", *_NON_QOR_CLI_FLAGS]
    )
    assert rc == 0


def test_seal_check_names_unresolved_default_layout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _write_non_qor_repo(tmp_path)
    rc = seal_artifacts.main(
        ["--check", "--repo-root", str(root), "--skip-tests"]
    )
    assert rc == 1
    assert "skills root not found" in capsys.readouterr().out


def test_layout_pattern_cannot_traverse_outside_root(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    with pytest.raises(badge_currency.BadgeLayoutError, match="must not traverse"):
        badge_currency.count_skills(tmp_path, Path("skills"), "../**/SKILL.md")


def test_matching_symlink_file_escaping_repo_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    skills = repo / "skills"
    skills.mkdir(parents=True)
    outside = tmp_path / "outside" / "SKILL.md"
    outside.parent.mkdir()
    outside.write_text("# external\n", encoding="utf-8")
    _symlink_or_skip(skills / "SKILL.md", outside)

    with pytest.raises(badge_currency.BadgeLayoutError, match="symlink"):
        badge_currency.count_skills(repo, Path("skills"), "**/SKILL.md")


def test_matching_symlink_file_inside_declared_root_is_rejected(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    skills = repo / "skills"
    target = skills / "real" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("# real\n", encoding="utf-8")
    alias = skills / "alias" / "SKILL.md"
    alias.parent.mkdir()
    _symlink_or_skip(alias, target)

    with pytest.raises(badge_currency.BadgeLayoutError, match="symlink"):
        badge_currency.count_skills(repo, Path("skills"), "**/SKILL.md")


def test_recursive_pattern_does_not_import_symlinked_directory(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    skills = repo / "skills"
    skills.mkdir(parents=True)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "SKILL.md").write_text("# external\n", encoding="utf-8")
    _symlink_or_skip(skills / "external", outside_dir, target_is_directory=True)

    assert badge_currency.count_skills(
        repo, Path("skills"), "**/SKILL.md"
    ) == 0


def test_seal_write_regenerates_badges_for_declared_layout(tmp_path: Path) -> None:
    """`--write` renders the DECLARED layout's truth, not the default roots'.

    The fixture repo has no `qor/` roots at all, so a layout that failed to
    reach the counters would abort rather than write these values.
    """
    root = _write_non_qor_repo(tmp_path)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        .replace("Skills-1-blue", "Skills-99-blue")
        .replace('alt="Skills: 1"', 'alt="Skills: 99"'),
        encoding="utf-8",
    )

    rc = seal_artifacts.main(
        [
            "--write", "--phase", "1", "--snapshot", "2026-07-30",
            "--repo-root", str(root), "--skip-tests", *_NON_QOR_CLI_FLAGS,
        ]
    )

    assert rc == 0
    written = readme.read_text(encoding="utf-8")
    assert "Skills-1-blue" in written
    assert 'alt="Skills: 1"' in written
    assert "Skills-99" not in written


def test_seal_cli_does_not_swallow_unrelated_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def programming_defect(*args, **kwargs):
        raise ValueError("unrelated programming defect")

    monkeypatch.setattr(seal_artifacts, "check_files", programming_defect)
    with pytest.raises(ValueError, match="unrelated programming defect"):
        seal_artifacts.main(
            ["--check", "--repo-root", str(tmp_path), "--skip-tests"]
        )
