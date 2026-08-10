"""Phase 27 Phase 3: end-to-end stamp + staging integration."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


_SAMPLE = """# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Sample pending change.

## [0.17.0] - 2026-04-17

### Added
- Earlier release.
"""


from tests.support.git_fixture import run_git, scratch_env


def _git_available() -> bool:
    try:
        subprocess.run(
            ["git", "--version"], check=True, capture_output=True, text=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def test_apply_stamp_end_to_end_preserves_newer_and_older(tmp_path):
    from qor.scripts.changelog_stamp import apply_stamp
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(_SAMPLE, encoding="utf-8")
    apply_stamp(cl, "0.18.0", "2026-05-01")
    text = cl.read_text(encoding="utf-8")
    # Fresh empty Unreleased exists above the new dated section
    unreleased_idx = text.index("## [Unreleased]")
    new_idx = text.index("## [0.18.0] - 2026-05-01")
    old_idx = text.index("## [0.17.0] - 2026-04-17")
    assert unreleased_idx < new_idx < old_idx, (
        "ordering wrong: Unreleased should come before 0.18.0 which should "
        "come before 0.17.0"
    )
    # The previous Unreleased body is under 0.18.0 now
    assert "Sample pending change" in text[new_idx:old_idx]


def test_apply_stamp_raises_on_collision(tmp_path):
    from qor.scripts.changelog_stamp import apply_stamp
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(_SAMPLE, encoding="utf-8")
    apply_stamp(cl, "0.18.0", "2026-05-01")
    with pytest.raises(ValueError, match="0\\.18\\.0.*already"):
        apply_stamp(cl, "0.18.0", "2026-05-01")


@pytest.mark.skipif(not _git_available(), reason="git not available on PATH")
def test_stamped_changelog_included_in_auto_stage(tmp_path):
    """Mirror the /qor-substantiate Step 9.5 auto-stage block and confirm
    the stamped CHANGELOG appears in ``git diff --cached --name-only``."""
    from qor.scripts.changelog_stamp import apply_stamp
    # Phase 209: hermetic git -- ambient config cannot alter this fixture.
    env = scratch_env()
    run_git(["git", "init", "-q"], cwd=tmp_path, env=env)
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text(_SAMPLE, encoding="utf-8")
    run_git(["git", "add", "CHANGELOG.md"], cwd=tmp_path, env=env)
    run_git(["git", "commit", "-m", "initial", "-q"], cwd=tmp_path, env=env)

    # Stamp in place -> CHANGELOG.md is now modified
    apply_stamp(cl, "0.18.0", "2026-05-01")

    # Mirror Step 9.5 auto-stage (just the CHANGELOG line for this test)
    run_git(["git", "add", "CHANGELOG.md"], cwd=tmp_path, env=env)

    # Assert stamped CHANGELOG is staged for the next commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        check=True, cwd=tmp_path, capture_output=True, text=True,
    )
    staged = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert "CHANGELOG.md" in staged, (
        f"stamped CHANGELOG missing from staging set: {staged}"
    )


def test_doctrine_file_exists_and_names_automation():
    doc = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-changelog.md"
    assert doc.exists(), f"missing doctrine: {doc}"
    text = doc.read_text(encoding="utf-8")
    assert "Keep a Changelog" in text
    assert "Semantic Versioning" in text
    assert "Unreleased" in text
    assert "qor/scripts/changelog_stamp.py" in text
    assert "tests/test_changelog_format.py" in text
    assert "tests/test_changelog_tag_coverage.py" in text
