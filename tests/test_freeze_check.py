"""Phase 304: the maintenance-freeze conformance check.

The contract (LD-2 of docs/plan-qor-phase304-maintenance-freeze.md, K0 to K6)
is stated over this repository's own files: a copy of them is frozen, and each
regression that would undo the freeze, applied to the copy, is reported against
the file it regressed.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from qor.scripts import freeze_check

REPO_ROOT = Path(__file__).resolve().parents[1]
NIGHTLY = ".github/workflows/nightly-health.yml"
SCHEDULE_LINES = "  schedule:\n    - cron: '0 9 * * *'\n"


@pytest.fixture
def copy(tmp_path: Path) -> Path:
    for name in ("pyproject.toml", "README.md", "AGENTS.md"):
        shutil.copy2(REPO_ROOT / name, tmp_path / name)
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    for path in (REPO_ROOT / ".github" / "workflows").glob("*.yml"):
        shutil.copy2(path, workflows / path.name)
    return tmp_path


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _write(root: Path, rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding="utf-8")


def _all_name(violations: list[str], rel: str) -> None:
    assert violations, "the regression was not reported"
    assert all(v.startswith(f"{rel}: ") for v in violations), violations


def test_the_repository_is_frozen():  # K0
    assert freeze_check.check(REPO_ROOT) == []


def test_an_unmodified_copy_is_frozen(copy):  # K0
    assert freeze_check.check(copy) == []


def test_restoring_the_beta_classifier_is_reported(copy):  # K1
    text = _read(copy, "pyproject.toml")
    assert freeze_check.FROZEN_CLASSIFIER in text
    _write(copy, "pyproject.toml", text.replace(
        freeze_check.FROZEN_CLASSIFIER, "Development Status :: 4 - Beta",
    ))
    assert freeze_check.FROZEN_CLASSIFIER not in _read(copy, "pyproject.toml")
    _all_name(freeze_check.check(copy), "pyproject.toml")


def test_committing_a_dependabot_config_is_reported(copy):  # K2
    _write(copy, ".github/dependabot.yml", "version: 2\nupdates: []\n")
    assert (copy / ".github/dependabot.yml").is_file()
    _all_name(freeze_check.check(copy), ".github/dependabot.yml")


def test_restoring_the_nightly_schedule_is_reported(copy):  # K3
    text = _read(copy, NIGHTLY)
    assert "\non:\n" in text and "schedule:" not in text
    _write(copy, NIGHTLY, text.replace("\non:\n", "\non:\n" + SCHEDULE_LINES, 1))
    assert SCHEDULE_LINES in _read(copy, NIGHTLY)
    _all_name(freeze_check.check(copy), NIGHTLY)


def _without_freeze_section(text: str) -> str:
    lines = text.splitlines(keepends=True)
    start = lines.index(freeze_check.FREEZE_HEADING + "\n")
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines)
    )
    return "".join(lines[:start] + lines[end:])


@pytest.mark.parametrize("name", ["README.md", "AGENTS.md"])
def test_removing_a_freeze_section_is_reported(copy, name):  # K4, K5
    _write(copy, name, _without_freeze_section(_read(copy, name)))
    assert freeze_check.FREEZE_HEADING not in _read(copy, name)
    _all_name(freeze_check.check(copy), name)


def test_main_prints_ok_and_returns_zero_on_a_frozen_copy(copy, capsys):  # K6
    assert freeze_check.main(["--repo-root", str(copy)]) == 0
    assert capsys.readouterr().out.splitlines() == ["freeze_check: OK"]


def test_main_prints_each_violation_and_returns_one(copy, capsys):  # K6
    _write(copy, ".github/dependabot.yml", "version: 2\nupdates: []\n")
    assert freeze_check.main(["--repo-root", str(copy)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines == [*freeze_check.check(copy), "freeze_check: 1 violation(s)"]
