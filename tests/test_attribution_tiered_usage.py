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


def test_seal_commits_after_cutoff_have_full_canonical_trailer():
    """Seal commits for Phase 49+ MUST have the full canonical trailer."""
    seals = _git_commits(r"^seal:", limit=10)
    if not seals:
        pytest.skip("no seal commits to audit")
    failures: list[str] = []
    for sha, subj, body in seals:
        phase_num = _phase_num_from_subject(subj)
        if phase_num is None or phase_num < 49:
            continue  # grandfathered
        has_qor_line = "Qor-logic" in body and "Authored via" in body
        # GitHub squash merge normalizes trailers to canonical lowercase form
        # `Co-authored-by:`; the doctrine accepts either case per git's
        # case-insensitive trailer convention (see git-interpret-trailers).
        has_coauthor = re.search(r"^Co-authored-by:", body, re.IGNORECASE | re.MULTILINE) is not None
        if not (has_qor_line and has_coauthor):
            failures.append(f"{sha[:8]} {subj!r}")
    assert not failures, (
        "Seal commits (Phase 49+) must use full canonical trailer per "
        "doctrine-attribution.md §'Tiered usage':\n  " + "\n  ".join(failures)
    )


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
