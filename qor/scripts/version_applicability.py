"""Early version-applicability validation (GH #282).

Moves the substantiate-time version downgrade guard earlier so a release-class
plan whose target would not exceed the current tag is rejected before audit
PASS, and adds an explicit non-release ("governance") classification that plan,
audit, and substantiate interpret identically. The computation mirrors the
existing bump-time guard exactly; it is only run sooner.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qor.scripts import governance_helpers as gh

RELEASE_CLASSES = frozenset({"hotfix", "feature", "breaking"})
NON_RELEASE_CLASSES = frozenset({"governance"})


@dataclass(frozen=True)
class VersionVerdict:
    ok: bool
    classification: str  # "release" | "version-not-applicable"
    change_class: str
    target: tuple[int, int, int] | None
    current_highest: tuple[int, int, int] | None
    reason: str


def is_release_class(change_class: str) -> bool:
    """True for a class that must produce a version bump; False for a
    non-release (version-not-applicable) governance cycle."""
    return change_class in RELEASE_CLASSES


def _current_version(repo_root: Path) -> tuple[int, int, int]:
    text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    return gh._parse_version(text)


def validate(plan_path: str | Path, repo_root: str | Path) -> VersionVerdict:
    """Validate that ``plan_path``'s version state is admissible before audit.

    ``governance`` -> version-not-applicable (ok, no bump). A release class ->
    the computed target must exceed the current highest tag (identical to the
    substantiate downgrade guard). Raises ``ValueError`` when the plan carries
    no canonical ``**change_class**:`` header.
    """
    root = Path(repo_root)
    change_class = gh.parse_change_class(Path(plan_path))
    highest = gh._highest_tag(gh._list_tags())
    if change_class in NON_RELEASE_CLASSES:
        return VersionVerdict(
            ok=True,
            classification="version-not-applicable",
            change_class=change_class,
            target=None,
            current_highest=highest,
            reason="non-release governance cycle; no version bump expected",
        )
    target = gh._compute_new(*_current_version(root), change_class)
    ok = highest is None or target > highest
    reason = (
        f"target v{target[0]}.{target[1]}.{target[2]} "
        + ("> " if ok else "<= ")
        + ("(no prior tag)" if highest is None
           else f"current highest v{highest[0]}.{highest[1]}.{highest[2]}")
    )
    return VersionVerdict(
        ok=ok,
        classification="release",
        change_class=change_class,
        target=target,
        current_highest=highest,
        reason=reason,
    )
