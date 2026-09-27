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
- `tests/test_changelog_tag_coverage.py` -- tag coverage (see "Release
  state" below): every reachable `v*` tag has a CHANGELOG section; every
  other dated section at or below the ceiling has a reachable tag or an
  explicit release-state disposition.
- `tests/test_changelog_stamp.py` -- unit tests for the pure stamp function.
- `tests/test_substantiate_changelog_integration.py` -- end-to-end
  including a staging assertion that confirms the stamped CHANGELOG is
  included in the would-be seal commit.

## Release state: sealed/versioned != released/published

A seal and a publication are different transitions:

- **sealed/versioned**: `/qor-substantiate` bumps `[project].version`, stamps
  the CHANGELOG, and creates a local seal tag. Nothing leaves the checkout.
- **released/published**: the version's tag reaches the remote and the
  tag-driven release path runs. Only this is publication.

A local tag, reachable or not, never proves publication.

Coverage rule (owner: `qor/scripts/release_state.py`):

- Only tags reachable from `HEAD` (`git tag --merged HEAD`, strict
  `vMAJOR.MINOR.PATCH`) take part. A tag on another line of history, such as
  a parallel phase's local seal tag, cannot fail the forward rule, raise the
  ceiling, or cover a version.
- Every reachable tag, and the current `[project].version`, has a dated
  section.
- The `[project].version` is the single implicit untagged release candidate.
- The ceiling is the greater of the project version and the highest reachable
  tag. Every other dated version at or below it needs a reachable tag or an
  explicit disposition. There is no blanket "above the highest tag"
  exemption, and a checkout with no reachable tags exempts nothing.

`docs/release-state.json` (`qor.release-state/v1`, closed shape: `schema` and
`exceptions`; each entry exactly `version`, `state`, `reason`) records the
exceptional dispositions. It is not a release registry. States:

- `sealed_unpublished`: sealed by `/qor-substantiate`, never published. It
  stays authoritative even if a local seal tag exists. Publishing the version
  later removes or changes the entry in the same governed release action.
- `legacy_untagged`: historical version whose publication history cannot be
  reconstructed safely; no tag is backfilled, since that could re-trigger
  release automation.
- `unreachable_tag`: a tag exists but is not reachable from `HEAD`. No claim
  about publication.

Every state is an operator-asserted disposition; the validator checks the
shape, that each version has a dated CHANGELOG section, and nothing about
remote history. An invalid record fails closed.

Enforcement point: CI, which checks out full history with tags. A shallow
checkout cannot decide reachability, so the local test skips with a named
reason. A local checkout can also hold a reachable local-only seal tag, which
covers a version locally that is an orphan in CI (CI sees only origin's
tags). The CI result is authoritative; the local result is advisory.

## Canonical automation

`qor/scripts/changelog_stamp.py` is the single entry point for
`## [Unreleased]` -> `## [X.Y.Z] - YYYY-MM-DD` renames. No other tool
should rewrite the CHANGELOG. Historical backfill (v0.3.0 through v0.17.0)
was hand-authored as a one-time task; going forward the stamp convention
is canonical.

## Exceptions

- Pre-v0.3.0 history: the repo shipped internally before going public;
  those versions are not documented in the CHANGELOG. See `git log` for
  pre-v0.3.0 pedigree.
- Documentation-only commits between releases do not require a CHANGELOG
  bullet if they do not change user-facing behavior.
