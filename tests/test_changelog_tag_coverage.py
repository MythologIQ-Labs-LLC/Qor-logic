"""Phase 27 Phase 1: every git tag has a CHANGELOG section and vice versa.

Phase 42 (hotfix): pre-release CHANGELOG sections -- those with versions above
the highest existing git tag -- are exempt from the tag-match requirement. This
resolves the chicken-and-egg collision with Phase 40's LOCAL-ONLY tag doctrine,
where a phase-seal PR adds a CHANGELOG section for the version it is about to
ship but the tag does not exist on origin at CI time.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
_VERSION_HEADER = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\] -", re.MULTILINE)


def _git_tags() -> list[str]:
    """Return sorted SemVer-prefixed tags; skip non-SemVer historical tags."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*"],
            check=True, capture_output=True, text=True, cwd=REPO,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("git not available; tag-coverage test skipped")
    tags = [t.strip() for t in result.stdout.splitlines() if t.strip()]
    # Keep only strict vMAJOR.MINOR.PATCH; drop migration/non-SemVer tags.
    return sorted(t for t in tags if re.match(r"^v[0-9]+\.[0-9]+\.[0-9]+$", t))


def _changelog_versions() -> set[str]:
    text = CHANGELOG.read_text(encoding="utf-8")
    return set(_VERSION_HEADER.findall(text))


def _parse_semver(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".", 2)
    return int(a), int(b), int(c)


def _released_orphans(versions: set[str], tags: set[str]) -> set[str]:
    """CHANGELOG versions with no matching tag at or below the highest existing tag.

    Versions above the highest existing tag are pre-release entries (about to ship
    in the current PR, awaiting merge-and-push per Phase 40 doctrine). They are
    exempt from the match-a-tag rule.

    If there are no tags at all, no enforcement is possible; return empty set.
    """
    if not tags:
        return set()
    highest = max(_parse_semver(t) for t in tags)
    return {v for v in versions - tags if _parse_semver(v) <= highest}


def test_every_tag_has_changelog_section():
    tags = _git_tags()
    versions = _changelog_versions()
    missing_sections: list[str] = []
    for tag in tags:
        version = tag.lstrip("v")
        if version not in versions:
            missing_sections.append(tag)
    assert not missing_sections, (
        "Git tags without CHANGELOG entries:\n  " + "\n  ".join(missing_sections)
    )


def test_every_changelog_section_has_tag():
    tags = {t.lstrip("v") for t in _git_tags()}
    versions = _changelog_versions()
    orphan_sections = _released_orphans(versions, tags)
    assert not orphan_sections, (
        "CHANGELOG sections at or below the highest tag must have matching git tags:\n  "
        + "\n  ".join(sorted(orphan_sections))
    )


# ----- Phase 42 regression tests for _released_orphans helper -----

def test_changelog_section_above_highest_tag_is_exempt():
    """Pre-release sections (above highest tag) are exempt from the match-a-tag rule."""
    tags = {"0.28.0", "0.28.1"}
    versions = {"0.28.0", "0.28.1", "0.29.0"}
    assert _released_orphans(versions, tags) == set()


def test_changelog_section_at_or_below_highest_tag_still_enforced():
    """Sections at or below the highest existing tag without matching tags are violations."""
    # Missing below-highest section → orphan reported.
    tags = {"0.28.0"}
    versions = {"0.27.0", "0.28.0"}
    assert _released_orphans(versions, tags) == {"0.27.0"}

    # All sections tagged → no orphans.
    tags = {"0.28.0", "0.28.1"}
    versions = {"0.28.0", "0.28.1"}
    assert _released_orphans(versions, tags) == set()

    # Mixed: one below-highest orphan + one exempt pre-release → only the below reported.
    tags = {"0.28.0", "0.28.1"}
    versions = {"0.27.0", "0.28.0", "0.28.1", "0.29.0"}
    assert _released_orphans(versions, tags) == {"0.27.0"}


def test_released_orphans_no_tags_returns_empty():
    """With no tags, no enforcement is possible; helper returns empty."""
    assert _released_orphans({"0.1.0", "0.2.0"}, set()) == set()
