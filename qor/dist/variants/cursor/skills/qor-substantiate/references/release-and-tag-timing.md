# Release backend + seal-tag timing — rationale

Extended rationale for the `/qor-substantiate` Step 7.5/7.6 (pluggable
version/changelog backends) and Step 9.5.4/9.5.5/9.6/9.7 (seal-tag creation and
post-merge push) steps. Held here per GH #92 progressive disclosure: SKILL.md
carries the runnable commands/code + the binding Constraints; this file carries
the history and the why.

---

## Step 7.5 — Pluggable version-bump backend (Phase 13 wiring; Phase 133 split, GH #163)

Phase 133 made the bump pluggable via `qor.scripts.version_backends`: it detects
the archetype (python/node/rust, that priority) and bumps the right manifest file
(`pyproject.toml` / `package.json` / `Cargo.toml`). Only when NONE of the three
is present does the step record SKIP + emit a `gate_skipped_prerequisite_absent`
shadow event. `version_backends.bump` delegates the python path to
`governance_helpers.bump_version` (unchanged tag-collision + downgrade
interdiction); node/rust reuse the same guards. Tag creation was moved to Step
9.5.5 after the seal commit (Phase 33 — prevents the historical off-by-one
seal-tag timing bug).

## Step 7.6 — Pluggable changelog backend (Phase 27 wiring; Phase 133, GH #163)

`changelog_backends.stamp` detects the format: a `## [Unreleased]` section
delegates to `changelog_stamp.apply_stamp` (keepachangelog — raises `ValueError`
on missing/empty Unreleased or a `[new_version]` collision; PAUSE and fix, do NOT
silently ship an unstamped CHANGELOG); otherwise the `prepend` backend inserts a
`## v<version> - <date>` section near the top. Per
`qor/references/doctrine-changelog.md`, every release gets a dated section; the
keepachangelog Unreleased convention is populated during `/qor-implement` and
mechanically renamed on seal.

## Step 9.5.4 — Seal-commit trailer verification (Phase 85 wiring; GH #96)

Phase 82/83 seal commits shipped with only the compact `Co-Authored-By:` line;
this guard makes that omission unrepeatable. On non-zero exit, ABORT before
tagging: the seal commit is missing the `Authored via [Qor-logic SDLC]` line
and/or the `Co-Authored-By:` line. Amend the seal commit so its message contains
the full `qor.scripts.attribution.commit_trailer()` output, then re-run from Step
9.5. The check delegates to `qor.scripts.attribution.message_has_full_trailer` —
the single source of truth shared with `tests/test_attribution_tiered_usage.py`.
Per `qor/references/doctrine-attribution.md` §"Tiered usage".

## Step 9.5.5 — Annotated seal-tag creation (Phase 33 wiring)

The seal commit now exists (created in Step 9.5). Capture its SHA via `git
rev-parse HEAD` and tag it. Moving tag creation to this step closes the
historical timing bug where `create_seal_tag` ran at Step 7.5 with HEAD still
pointing at the pre-seal commit, producing off-by-one tags across v0.19.0–v0.22.0.
`commit` is a required argument — there is no HEAD-default fallback; calling
`create_seal_tag` without it raises `TypeError` (verified by
`tests/test_seal_tag_timing.py::test_create_seal_tag_raises_without_commit`).

## Step 9.6 / 9.7 — Push/merge options + post-merge tag push (Phase 13 / Phase 86 wiring; GH #98)

The annotated tag from Step 9.5.5 stays local until the seal commit is on
`origin/main`. `release.yml` triggers on tag push and its `build-and-publish` job
refuses to publish a tag whose commit is not reachable from `origin/main`;
pushing the tag before the merge produces a failing `build-and-publish` check
that blocks the seal PR. Push the tag only after the seal commit reaches
`origin/main`, gated on the same reachability check `release.yml` uses
(`git merge-base --is-ancestor "$SEAL_COMMIT" origin/main`). For Step 9.6 option
3 (merge to main locally), run the tag push immediately after `git push origin
main`. For option 2 (push + PR), run it after the PR is merged. For options 1 and
4 the seal commit is not on `origin/main`; the tag stays local and the operator
pushes it after a later merge with `git push origin <tag>`. The reachability gate
mirrors `release.yml`'s own guard, so the tag push and the publish guard agree by
construction. The four push/merge options are never replaced by a continuation
menu — when work is sealable, the next decision is push/merge, not "what next
phase".
