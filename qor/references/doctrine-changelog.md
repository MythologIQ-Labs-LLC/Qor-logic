# Doctrine: Changelog Discipline

> Every shipped version has a dated CHANGELOG section. Bullets describe
> user-facing changes, not implementation details. The file is authored by
> hand during implementation and stamped mechanically on seal.

## Format

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 1.1.0 + [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Six allowed subsection labels: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

## Authoring convention

- **During `/qor-implement`**: author populates the `## [Unreleased]` section
  with bullets describing the user-facing effect of their work. Internal
  refactors, ledger entry numbers, and hash values do NOT appear in the
  CHANGELOG -- they live in `docs/META_LEDGER.md`. Security posture shifts
  (new parser commitments, dependency additions with security implications,
  banned API rules) go under `Security`.
- **On `/qor-substantiate`**: Step 7.6 invokes `qor/scripts/changelog_stamp.py`
  which renames `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` and inserts
  a fresh empty `Unreleased` section above. No content is generated; the
  stamp is a pure rename.
- **On `/qor-substantiate` Step 9.5**: the auto-stage list includes
  `git add CHANGELOG.md`. Without this line, the stamp modifies the file
  but the seal commit does not include the change.

## Sealed/versioned state is not publication

A substantiation stamp or local seal tag records governed version state. It does
not prove that the version was published through the remote release path.
Accordingly:

- `[project].version` is the single implicit untagged release candidate;
- every older dated CHANGELOG version at or below the greater of the project
  version and the highest observed SemVer tag must have an ordinary tag or an
  explicit disposition in `docs/release-state.json`;
- `sealed_unpublished` records a governed version that was sealed/versioned but
  not published through the remote release path;
- `legacy_untagged` preserves an older exception whose stronger publication
  history cannot be reconstructed safely from retained evidence;
- a local-only tag does not convert `sealed_unpublished` into `published`;
- if an exceptional version is later intentionally published, its exceptional
  disposition is removed or changed in that same governed release action.

The governing invariant is: `sealed/versioned != released/published`.
Historical tags must never be manufactured merely to satisfy coverage checks.

## Fail-fast rules (enforced by `changelog_stamp.py`)

- Missing `## [Unreleased]` header -> `ValueError` (author forgot to
  maintain Unreleased, or CHANGELOG is misformatted).
- Empty `Unreleased` section (no bullets) -> `ValueError` (no user-facing
  changes means this is not a real release; check whether a seal is warranted).
- `## [X.Y.Z]` collision on the target version -> `ValueError` (never
  silently overwrite).
- Non-SemVer version or non-ISO date -> `ValueError` (operator typo).

The stamp never silently succeeds with malformed input.

## Enforcement

- `tests/test_changelog_format.py` -- Keep-a-Changelog structural lint
  (header, intro links, subsection allow-list, version/date formats,
  newest-first ordering, Unreleased presence and position).
- `tests/test_changelog_tag_coverage.py` -- every observed SemVer tag has a
  CHANGELOG section; the current project version is the only implicit untagged
  candidate; older untagged sections require an explicit release-state
  disposition.
- `tests/test_release_state.py` -- closed-schema validation for exceptional
  release dispositions.
- `tests/test_changelog_stamp.py` -- unit tests for the pure stamp function.
- `tests/test_substantiate_changelog_integration.py` -- end-to-end
  including a staging assertion that confirms the stamped CHANGELOG is
  included in the would-be seal commit.

## Canonical automation

`qor/scripts/changelog_stamp.py` is the single entry point for
`## [Unreleased]` -> `## [X.Y.Z] - YYYY-MM-DD` renames. No other tool
should rewrite the CHANGELOG. Historical backfill (v0.3.0 through v0.17.0)
was hand-authored as a one-time task; going forward the stamp convention
is canonical.

`qor/scripts/release_state.py` is the single parser/validator for
`docs/release-state.json`. The record is exceptional-state metadata, not a
release registry and not evidence that publication occurred.

## Exceptions

- Pre-v0.3.0 history: the repo shipped internally before going public;
  those versions are not documented in the CHANGELOG. See `git log` for
  pre-v0.3.0 pedigree.
- Documentation-only commits between releases do not require a CHANGELOG
  bullet if they do not change user-facing behavior.
