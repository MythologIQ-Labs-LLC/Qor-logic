"""Phase 49: tiered attribution-trailer usage policy (G-3).

Walks recent commits + CHANGELOG version sections, asserts the right
attribution form is used at each surface per doctrine-attribution.md
§"Tiered usage". Functionality tests; positive proximity-anchored
assertions paired with strip-and-fail negative-paths per Phase 46
doctrine.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from qor.scripts.attribution import message_has_full_trailer

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-attribution.md"
ATTRIBUTION_MD = REPO_ROOT / "ATTRIBUTION.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# Commits authored after this Phase-49 cutoff (pyproject 0.36.0+) are subject
# to the tiered policy. Older commits grandfathered.
CUTOFF_VERSION = (0, 36, 0)


def _git_commits(pattern: str, limit: int = 20) -> list[tuple[str, str, str]]:
    """Return [(sha, subject, body)] for commits matching subject regex."""
    result = subprocess.run(
        ["git", "log", "--format=%H%x1f%s%x1f%b%x1e", f"-n{limit*5}"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    out = []
    for record in result.stdout.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 3:
            continue
        sha, subj, body = parts[0], parts[1], "\x1f".join(parts[2:])
        if re.match(pattern, subj):
            out.append((sha, subj, body))
        if len(out) >= limit:
            break
    return out


def _proximity(body: str, header_pattern: str, phrase_pattern: str, span: int = 1500) -> bool:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_pattern, window, re.IGNORECASE | re.DOTALL) is not None


def _strip_section(body: str, header_pattern: str, span: int = 4000) -> str:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return body
    start = m.end()
    end = min(len(body), start + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    return body[:start] + filler[: end - start] + body[end:]


# -------- Doctrine surface --------

def test_doctrine_attribution_documents_tier_table():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert _proximity(body, r"^## Tiered usage\b", r"seal commit", span=2500)
    assert _proximity(body, r"^## Tiered usage\b", r"plan/audit/implement|plan, audit, implement", span=2500)
    assert _proximity(body, r"^## Tiered usage\b", r"CHANGELOG", span=2500)
    assert _proximity(body, r"^## Tiered usage\b", r"PR description|PR-body footer", span=2500)


def test_doctrine_attribution_tier_table_negative_path():
    body = DOCTRINE.read_text(encoding="utf-8")
    mutated = _strip_section(body, r"^## Tiered usage\b")
    assert not _proximity(mutated, r"^## Tiered usage\b", r"seal commit", span=2500)


def test_attribution_md_has_quickref_block():
    body = ATTRIBUTION_MD.read_text(encoding="utf-8")
    assert _proximity(body, r"^## Tiered usage\b", r"Seal commit", span=1500)


def test_attribution_md_quickref_negative_path():
    body = ATTRIBUTION_MD.read_text(encoding="utf-8")
    mutated = _strip_section(body, r"^## Tiered usage\b", span=2000)
    assert not _proximity(mutated, r"^## Tiered usage\b", r"Seal commit", span=1500)


# -------- Helper API --------

def test_attribution_helper_returns_canonical_strings_for_each_tier():
    from qor.scripts.attribution import commit_trailer, commit_trailer_compact

    full = commit_trailer("Claude Opus 4.7 (1M context)")
    assert "Authored via" in full and "Qor-logic" in full
    assert "Co-Authored-By: Claude Opus 4.7 (1M context)" in full
    assert full.count("\n") >= 1, "full canonical trailer must be multi-line"

    compact = commit_trailer_compact("Claude Opus 4.7 (1M context)")
    assert compact == "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    assert "Qor-logic" not in compact, "compact form is the Co-Authored-By line ONLY"
    assert "\n" not in compact.strip(), "compact form is single line"


# -------- Commit-walking tests (cutoff-aware) --------

def _phase_num_from_subject(subject: str) -> int | None:
    m = re.search(r"phase\s+(\d+)", subject, re.IGNORECASE)
    return int(m.group(1)) if m else None


# Phase 82-83 seal commits (ce138b2, fb052e4) were authored locally with only
# the compact `Co-Authored-By:` line, missing the `Authored via [Qor-logic SDLC]`
# line. They predate the /qor-substantiate Step 9.5.4 seal-trailer guard
# (Phase 85, GH #96). Rewriting published main history to backfill the line is
# rejected as disproportionate; they are disclosed-grandfathered here. See
# qor/references/doctrine-attribution.md §"Tiered usage".
_GRANDFATHERED_SEAL_PHASES = frozenset({82, 83})


def _seal_phase_in_scope(phase_num: int | None) -> bool:
    """True if a seal commit at `phase_num` is subject to the full-trailer rule.

    Phase >= 49 is the enforcement boundary (the same Phase-49 boundary the
    CHANGELOG check expresses as `CUTOFF_VERSION` 0.36.0, here represented as a
    phase number for commit-subject walks). Disclosed-grandfathered phases are
    excluded.
    """
    return (
        phase_num is not None
        and phase_num >= 49
        and phase_num not in _GRANDFATHERED_SEAL_PHASES
    )


def test_seal_commits_after_cutoff_have_full_canonical_trailer():
    """Seal commits in scope (Phase 49+, non-grandfathered) MUST carry the
    full canonical trailer."""
    seals = _git_commits(r"^seal:", limit=10)
    if not seals:
        pytest.skip("no seal commits to audit")
    failures: list[str] = []
    for sha, subj, body in seals:
        if not _seal_phase_in_scope(_phase_num_from_subject(subj)):
            continue
        # message_has_full_trailer is the single source of truth, shared with
        # the /qor-substantiate Step 9.5.4 seal-trailer guard. Its co-author
        # match is case-insensitive: git trailer keys are case-insensitive and
        # a GitHub-merged commit may render `Co-authored-by:` lowercase.
        if not message_has_full_trailer(body):
            failures.append(f"{sha[:8]} {subj!r}")
    assert not failures, (
        "Seal commits (Phase 49+) must use full canonical trailer per "
        "doctrine-attribution.md §'Tiered usage':\n  " + "\n  ".join(failures)
    )


def test_seal_phase_in_scope_excludes_grandfathered():
    assert _seal_phase_in_scope(82) is False
    assert _seal_phase_in_scope(83) is False


def test_seal_phase_in_scope_includes_recent_compliant_phases():
    # A precise exception set must NOT blanket-disable checking.
    assert _seal_phase_in_scope(84) is True
    assert _seal_phase_in_scope(85) is True


def test_seal_phase_in_scope_excludes_below_floor():
    assert _seal_phase_in_scope(48) is False
    assert _seal_phase_in_scope(None) is False


def test_plan_audit_implement_commits_after_cutoff_have_coauthor_line():
    commits = _git_commits(r"^(plan|audit|implement):", limit=15)
    if not commits:
        pytest.skip("no plan/audit/implement commits to audit")
    failures: list[str] = []
    for sha, subj, body in commits:
        phase_num = _phase_num_from_subject(subj)
        if phase_num is None or phase_num < 49:
            continue  # grandfathered
        if "Co-Authored-By:" not in body:
            failures.append(f"{sha[:8]} {subj!r}")
    assert not failures, (
        "Plan/audit/implement commits (Phase 49+) must include 'Co-Authored-By:' "
        "(full canonical permitted but not required):\n  " + "\n  ".join(failures)
    )


# -------- CHANGELOG attribution-line check --------

_VERSION_HEADER_RE = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)\]", re.MULTILINE)


def _changelog_versions_with_bodies(text: str) -> list[tuple[tuple[int, int, int], str]]:
    out = []
    matches = list(_VERSION_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        version = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end]
        out.append((version, body))
    return out


def test_changelog_post_cutoff_versions_have_attribution_line():
    text = CHANGELOG.read_text(encoding="utf-8")
    sections = _changelog_versions_with_bodies(text)
    failures: list[str] = []
    for version, body in sections:
        if version < CUTOFF_VERSION:
            continue
        # Look for the canonical line within the first ~10 lines under header.
        head_window = "\n".join(body.splitlines()[:15])
        if "_Built via [Qor-logic SDLC]" not in head_window:
            failures.append(f"v{'.'.join(map(str, version))}")
    assert not failures, (
        "CHANGELOG versions ≥ 0.36.0 must include '_Built via [Qor-logic SDLC](...)._'"
        f" within 15 lines of the version header:\n  " + "\n  ".join(failures)
    )


def test_changelog_attribution_negative_path():
    """Synthetic CHANGELOG body without the attribution line — assertion fails."""
    text = "## [0.36.0] - 2026-04-29\n\n### Added\n- Some feature.\n\n## [0.35.0] - 2026-04-29\n"
    sections = _changelog_versions_with_bodies(text)
    cutoff_versions = [v for v, _ in sections if v >= CUTOFF_VERSION]
    assert cutoff_versions, "negative-path test must produce at least one cutoff-version row"
    # The synthetic body lacks the canonical line; the same check that PASSES on
    # real CHANGELOG must FAIL here (proves the assertion is anchored, not vacuous).
    found = False
    for version, body in sections:
        if version >= CUTOFF_VERSION and "_Built via [Qor-logic SDLC]" in body:
            found = True
    assert not found, "synthetic CHANGELOG without attribution must not pass"
