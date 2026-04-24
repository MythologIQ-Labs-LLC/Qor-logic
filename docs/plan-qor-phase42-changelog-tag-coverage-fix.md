# Plan: Phase 42 — changelog-tag-coverage test fix (unblock phase 39/39b PRs)

**change_class**: hotfix
**target_version**: v0.28.2
**doc_tier**: minimal
**pass**: 2

**Pass 2 delta**: Added `CHANGELOG.md` backfill for `## [0.28.1]` (Phase 40 retrospective) and `## [0.28.2]` (this hotfix). Addresses audit VETO V1 (coverage-gap) documented in `.agent/staging/AUDIT_REPORT.md` (Phase 42 Pass 1) and `docs/SHADOW_GENOME.md` Entry #31. Without the backfill, Phase 42's own merge would surface a latent failure in the symmetric `test_every_tag_has_changelog_section` when v0.28.1 + v0.28.2 tags exist on origin without matching CHANGELOG sections.

**Scope**: One-function assertion relaxation in `tests/test_changelog_tag_coverage.py`. Pre-release CHANGELOG sections (version > highest existing git tag) are exempt from the "must have matching tag" rule. No production code changes.

**Rationale**: PRs #10 (phase 39 → v0.29.0) and #11 (phase 39b → v0.30.0) are blocked by `test_every_changelog_section_has_tag` failing on every CI matrix cell (ubuntu/windows × py3.11/3.12/3.13 — 6 failures each). The test asserts a bidirectional equality between `git tag -l v*` and CHANGELOG `## [X.Y.Z]` headers. CI only sees tags pushed to `origin`. Phase 40's release-workflow doctrine holds the about-to-ship tag LOCAL ONLY until the PR merges — so when a phase-seal PR adds a CHANGELOG section for the version it is about to ship, that section always looks orphaned from CI's perspective. Chicken-and-egg: PR can't merge until CI passes; CI can't pass until PR merges and the tag pushes to origin.

This is a test-semantics defect introduced by Phase 27 (when the test landed) colliding with Phase 40's LOCAL-ONLY tag doctrine. The symmetric test (`test_every_tag_has_changelog_section`) already works correctly because origin tags are a subset of local tags and the direction of the assertion is safe.

Fixing `test_every_changelog_section_has_tag` with a "sections above the highest existing tag are pre-release and exempt" rule restores the invariant for released versions (which is the test's real concern) without colliding with the LOCAL-ONLY tag doctrine.

## Open Questions

None.

## Preflight note for substantiate

The `bump_version('hotfix')` helper refuses when the computed new version (`0.28.2`) is less than the highest existing tag. Local orphan tags `v0.29.0` and `v0.30.0` exist on this repo from unmerged phase 39/39b seals; they are not pushed to origin. They must be deleted locally before `/qor-substantiate` runs the bump:

```bash
git tag -d v0.29.0 v0.30.0
```

Those tags will be recreated on the respective phase 39/39b merge commits by the operator post-merge per Phase 40's deploy protocol. No state is lost.

This is operator-executed at the start of `/qor-substantiate`, not embedded in the skill.

## Phase 1 — relax the orphan-section assertion + backfill CHANGELOG

### Affected Files

- `tests/test_changelog_tag_coverage.py` — new TDD fixtures added first; then the assertion in `test_every_changelog_section_has_tag` is narrowed to "orphan sections at or below the highest existing tag are violations; sections above are exempt."
- `CHANGELOG.md` — backfill `## [0.28.1] - 2026-04-20` (Phase 40 release-workflow guard hotfix) and add `## [0.28.2] - 2026-04-24` (this hotfix) ahead of the existing `## [0.28.0]` entry. Each section gets a single short paragraph referencing the META_LEDGER seal entry. No new tests for this file — the existing `test_every_tag_has_changelog_section` and the newly-relaxed `test_every_changelog_section_has_tag` will both enforce correctness after the sections land.

### Unit Tests

TDD order — new tests added and confirmed RED before the assertion change, then GREEN after.

- `test_changelog_section_above_highest_tag_is_exempt` — constructs a temporary repo state (via `monkeypatch` of `_git_tags` and `_changelog_versions` helpers, or via a pure-function extraction) where tags are `{v0.28.0, v0.28.1}` and CHANGELOG contains sections `{0.28.0, 0.28.1, 0.29.0}`. The pre-fix assertion reports `0.29.0` as orphan and fails; the post-fix assertion exempts it (version > highest tag 0.28.1) and passes.
- `test_changelog_section_at_or_below_highest_tag_still_enforced` — same fixture but CHANGELOG is `{0.28.0, 0.99.0}` with tags `{v0.28.0, v0.28.1}`. Section `0.99.0` is above highest tag → exempt; BUT add a second case where CHANGELOG is `{0.28.0}` and tags are `{v0.28.0, v0.28.1}` — no orphan sections at all, test passes. And a third case where CHANGELOG is `{0.28.0, 0.28.1, 0.30.0}` but tags are `{v0.28.0}` (missing v0.28.1 tag) — `0.28.1` is at-or-below-highest (highest 0.28.0) wait no, if only tag is 0.28.0 then 0.28.1 is above → exempt. Adjust: CHANGELOG `{0.27.0, 0.28.0}` with tags `{v0.28.0}` — section `0.27.0` is below highest `0.28.0` but has no tag → orphan reported, assertion fails. This is the true regression case: a section below the highest tag with no tag.

Refactor to enable testable fixtures: extract the core assertion logic from the test function into a pure helper `_released_orphans(versions, tags) -> set[str]` that takes two sets and returns the violating versions. The test function then calls the helper with `_changelog_versions()` and `_git_tags()`. New TDD tests call `_released_orphans` directly with synthetic inputs — no git or filesystem coupling.

### Changes

Extract and narrow:

```python
def _parse_semver(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".", 2)
    return int(a), int(b), int(c)


def _released_orphans(versions: set[str], tags: set[str]) -> set[str]:
    """CHANGELOG versions with no matching tag AT OR BELOW the highest existing tag.

    Versions above the highest existing tag are pre-release entries (about to ship
    in the current PR, awaiting merge-and-push per Phase 40 doctrine). They are
    exempt from the match-a-tag rule.

    If there are no tags at all, no enforcement is possible; return empty.
    """
    if not tags:
        return set()
    highest = max(_parse_semver(t) for t in tags)
    return {v for v in versions - tags if _parse_semver(v) <= highest}


def test_every_changelog_section_has_tag():
    tags = {t.lstrip("v") for t in _git_tags()}
    versions = _changelog_versions()
    orphan_sections = _released_orphans(versions, tags)
    assert not orphan_sections, (
        "CHANGELOG sections at or below the highest tag must have matching git tags:\n  "
        + "\n  ".join(sorted(orphan_sections))
    )
```

`test_every_tag_has_changelog_section` is unchanged — its assertion direction is already sound. The CHANGELOG backfill (below) brings its current-state inputs into compliance.

### CHANGELOG backfill content

`CHANGELOG.md` edit inserts two sections between the existing header block and `## [0.28.0]`:

```markdown
## [0.28.2] - 2026-04-24

### Fixed
- `test_every_changelog_section_has_tag` no longer blocks phase-seal PRs whose CHANGELOG sections are above the highest existing tag. Pre-release sections are now exempt from the match-a-tag rule, resolving the chicken-and-egg collision with Phase 40's LOCAL-ONLY tag doctrine. See META_LEDGER Entry #[N] (Phase 42 seal).

## [0.28.1] - 2026-04-20

### Fixed
- `.github/workflows/release.yml` now verifies the tag's commit is reachable from `origin/main` before publishing to PyPI; refuses publish otherwise. Closes the pre-merge-publish defect that shipped v0.24.1, v0.25.0, and v0.28.0 from unmerged PR branches. See META_LEDGER Entry #133 (Phase 40 seal).
```

Entry number for the v0.28.2 section is filled in at `/qor-substantiate` time when the seal entry is written; placeholder `#[N]` flagged here so the implementer knows to replace it.

## CI Commands

Operator must run locally before substantiate:

- `python -m pytest tests/test_changelog_tag_coverage.py -v`
- `python -m pytest tests/ -v` (full suite — catch any adjacent doctrine-test coupling)

Determinism check: the two new tests run twice in a row locally to confirm no flake (pure-function helper has no time/random/filesystem coupling, but the determinism rule applies uniformly per `qor/references/doctrine-test-discipline.md` Rule 3).
