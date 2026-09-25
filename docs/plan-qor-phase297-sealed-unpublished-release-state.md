# Plan: Phase 297 - Distinguish sealed versions from published releases

**change_class**: hotfix

**doc_tier**: minimal

**Issue**: GH #520

**Current base**: `15729311f9f4d55d5dad2db004b972415c39432c`

## Open Questions

None.

## Problem

`tests/test_changelog_tag_coverage.py` currently exempts every dated CHANGELOG version above the highest observed Git tag. That rule was sufficient while only one release candidate was in flight, but it allows a stack of sealed-but-unpublished versions to remain implicit and therefore conflates version sealing with publication.

Qor-logic needs an explicit distinction between:

- a version stamped and sealed by `/qor-substantiate`;
- a local-only seal tag created during governed work;
- the one current release candidate that may legitimately remain untagged;
- a version actually published through the remote tag-driven release path.

The repository also carries historical untagged exceptions whose stronger publication history cannot be reconstructed safely from the retained evidence. Manufacturing remote tags for those versions would misstate history and can re-trigger release automation.

## Locked Decisions

### LD-1: exceptional release state is explicit data, not a test constant

Add `docs/release-state.json` as the machine-readable record for versions whose tag/publication history differs from the ordinary release path. The root shape is closed and versioned:

```json
{
  "schema_version": "1",
  "exceptions": []
}
```

The root object contains exactly `schema_version` and `exceptions`. `schema_version` is the string `"1"`; `exceptions` is a list. Each exception entry contains exactly:

- `version`: strict `MAJOR.MINOR.PATCH`;
- `state`: `sealed_unpublished` or `legacy_untagged`;
- `reason`: non-empty explanatory text.

The current base proves the historical exceptions are hard-coded in the test today:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE '_GRANDFATHERED_UNTAGGED_SECTIONS|def _released_orphans|Versions above the highest existing git tag'` -> `29:_GRANDFATHERED_UNTAGGED_SECTIONS = frozenset({"0.69.0", "0.70.0", "0.71.0", "0.102.2"})`, `56:def _released_orphans(versions: set[str], tags: set[str]) -> set[str]:`, `59:    Versions above the highest existing git tag are pre-release entries (about to ship`.

The exceptional record is not a release registry and does not duplicate ordinary tagged releases.

### LD-2: `[project].version` is the single implicit untagged candidate

Every observed SemVer Git tag must still have a corresponding dated CHANGELOG section.

For the inverse direction:

- read `[project].version` from `pyproject.toml`;
- require that exact version to have a dated CHANGELOG section;
- treat only that exact project version as the implicit untagged release candidate;
- require every other dated CHANGELOG version at or below the greater of the project version and highest observed tag to have ordinary tag coverage or an explicit release-state disposition.

The current base establishes the candidate and its dated section:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.0"`.

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[(Unreleased|0\.175\.0)\]'` -> `11:## [Unreleased]` and `13:## [0.175.0] - 2026-09-24`.

This replaces the broad "everything above the highest tag is pre-release" exemption. An older missing tag may not hide merely because later versions were sealed without publication.

### LD-3: local tag presence does not mint publication truth

A `sealed_unpublished` disposition remains authoritative even if the checkout contains a local-only seal tag. Unit tests must not attempt network access to infer remote publication from local Git state.

If a version is intentionally published later, its exceptional disposition must be removed or changed in the same governed release action. This phase does not push or backfill any remote tag.

### LD-4: uncertain legacy history stays uncertain

Move the existing four hard-coded historical exceptions into `docs/release-state.json` as `legacy_untagged` rather than inventing a stronger release claim:

- `0.69.0`
- `0.70.0`
- `0.71.0`
- `0.102.2`

Record the currently established sealed-but-unpublished versions as `sealed_unpublished`:

- `0.173.0`
- `0.174.0`
- `0.174.1`
- `0.174.2`
- `0.174.3`
- `0.175.0`

This phase does not rewrite any historical CHANGELOG section.

### LD-5: doctrine names the lifecycle boundary

Update `qor/references/doctrine-changelog.md` to state explicitly:

`sealed/versioned != released/published`

The base doctrine already establishes that substantiation stamps `Unreleased` into a dated version section before later staging:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/references/doctrine-changelog.md | grep -nE 'On `/qor-substantiate`|which renames'` -> `19:- **On `/qor-substantiate`**: Step 7.6 invokes \`qor/scripts/changelog_stamp.py\``, `20:  which renames \`## [Unreleased]\` to \`## [X.Y.Z] - YYYY-MM-DD\` and inserts`, `23:- **On `/qor-substantiate` Step 9.5**: the auto-stage list includes`.

The updated doctrine must distinguish that sealed/versioned state from the later remote publication transition and document the narrow exceptional-state record.

### LD-6: release-state validation has one bounded production owner

Create `qor/scripts/release_state.py` as the canonical closed-schema parser/validator rather than embedding the grammar in the already-large tag-coverage test.

Validation fails closed on:

- invalid JSON or unreadable file;
- wrong root shape, extra root fields, or unsupported `schema_version`;
- non-list `exceptions`;
- non-object or extra-field entries;
- non-SemVer versions;
- unsupported states;
- empty reasons;
- duplicate versions;
- exception versions absent from CHANGELOG.

`tests/test_release_state.py` owns malformed-state regressions. `tests/test_changelog_tag_coverage.py` owns candidate/tag coverage behavior and consumes the validator. This keeps the modified source/test files inside the Section 4 250-line file budget.

## Feature Inventory Touches

Empty. This is release-governance/test maintenance and introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Release-state contract and candidate coverage

### Affected Files

- `tests/test_changelog_tag_coverage.py` - candidate-ceiling and explicit-disposition regressions.
- `tests/test_release_state.py` - new validator regressions.
- `qor/scripts/release_state.py` - new bounded closed-schema validator.
- `docs/release-state.json` - explicit exceptional release dispositions.

### Changes

1. Before production changes, extend tag-coverage tests to require the project-version candidate rule and to catch an older unrecorded version even when it sits above the highest observed tag.
2. Add release-state validator tests covering both allowed states plus every fail-closed shape named in LD-6.
3. Observe the new tests RED against the current implementation.
4. Add `qor/scripts/release_state.py`, `docs/release-state.json`, and integrate the validator into tag coverage.
5. Remove `_GRANDFATHERED_UNTAGGED_SECTIONS` from test code.
6. Observe the focused tests GREEN.

### Unit Tests

- project version has a dated CHANGELOG section;
- project version is the only implicit untagged candidate;
- older untagged version under the candidate/tag ceiling fails;
- observed tag newer than project version extends the ceiling;
- explicit exceptional disposition exempts only the named version;
- local tag presence does not erase `sealed_unpublished` state;
- accepted `sealed_unpublished` and `legacy_untagged` entries validate;
- wrong root shape, extra root fields, unsupported schema version, duplicate, malformed, unsupported, orphaned, empty-reason, extra-entry-field, invalid-JSON, and unreadable release-state records fail closed.

## Phase 2: Doctrine and user-facing release-state disclosure

### Affected Files

- `qor/references/doctrine-changelog.md` - define sealed/versioned versus released/published state and the candidate/exception coverage rule.
- `CHANGELOG.md` - add one user-facing Unreleased note before substantiation.

### Changes

Document the new state boundary without claiming that a local tag proves publication. The Unreleased note describes the correction as release-state/tag-coverage hardening, not as a published release.

### Unit Tests

- existing changelog format/stamp/substantiate integration tests remain green;
- tag-coverage tests exercise the documented candidate and explicit-exception behavior.

## Definition of Done

### Deliverable: explicit sealed-versus-published release-state model

- **D1**: sealed/versioned state and released/published state are no longer conflated; only the current project version is an implicit untagged candidate and exceptional history is explicit.
- **D2**: `qor/scripts/release_state.py`, `docs/release-state.json`, and tag-coverage integration implement the closed state vocabulary and candidate/tag ceiling while keeping modified code/test files within Section 4 budgets.
- **D3**: doctrine states `sealed/versioned != released/published`; no historical remote tag is fabricated, no package is published, and promotion occurs only after truthful current-revision audit/substantiation evidence exists.
- **D4**: the focused release-state/tag-coverage suite is observed RED before implementation and GREEN after implementation; the changelog/substantiation regression set and full repository suite pass on the implemented revision.

## CI Commands

- `python -m pytest tests/test_changelog_tag_coverage.py tests/test_release_state.py -q` - verifies candidate coverage and exceptional-state validation.
- `python -m pytest tests/test_changelog_format.py tests/test_changelog_stamp.py tests/test_substantiate_changelog_integration.py -q` - verifies CHANGELOG/substantiation compatibility.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `ruff check qor/ tests/` - verifies the repository's configured Python lint contract.

## Non-goals

- pushing any remote Git tag;
- publishing any package;
- modifying historical CHANGELOG sections;
- changing release workflow behavior;
- inferring remote publication through network access in unit tests;
- reconstructing uncertain historical publication state from incomplete evidence;
- changing semantic-version calculation;
- broad lifecycle redesign;
- unrelated repository cleanup.
