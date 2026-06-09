# Plan: Phase 144 -- author FEATURE_INDEX.md + README "Latest release" currency

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations:
  - V1 FEATURE_INDEX enumerates the user-touchable `qor-logic` CLI command surface (the primary
    product features). Skills and internal scripts are out of V1 scope; rows append over time.
  - Status is assigned honestly from real tests: `verified` only where a behavioral test exists and
    passes; `unverified` where no dedicated test exists yet (no false `verified`).
- non_goals:
  - No new feature behavior; this phase authors a governance artifact + a doc-currency edit.
  - No FEATURE_INDEX deep-verification engine (the seal pass already tallies + guards regression).
- exclusions: none new.

## Open Questions

None. FEATURE_INDEX format grep-verified from `qor/references/doctrine-feature-inventory.md` (Format
section: `ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status`)
and `qor/scripts/feature_index_verify.py:49-75` (`parse_index_rows` column order;
`STATUS_VALUES = ("verified","unverified","n/a")`).

## Phase 1: author the index + fix the stale README block

### Affected Files

- `tests/test_feature_index_present_and_verifies.py` (NEW) - the artifact parses + is recognized.
- `docs/FEATURE_INDEX.md` (NEW) - the feature index over the CLI command surface.
- `README.md` - delete the stale `v0.19+` "Highlights" block from `## Latest release`.

### Changes

`docs/FEATURE_INDEX.md`: a markdown table per `doctrine-feature-inventory.md` enumerating the
`qor-logic` CLI commands as rows. Each row: `ID | Name | Source-of-truth file:line | Doc citation |
Test path | Verification status`. Source cited to `qor/cli.py` `add_parser` lines (e.g. `install`
cli.py:151, `verify-ledger` cli.py:184, `governance-health` cli.py:207, `compliance enforce`
`qor/cli_handlers/compliance.py` + `qor/compliance/enforce.py`) or the handler module. `verified`
rows cite a real behavioral test (e.g. `install` -> `tests/test_cli_install_gemini.py`; `seed` ->
`tests/test_cli_seed.py`; `governance-health` -> `tests/test_cli_governance_health.py`; `compliance
enforce` -> `tests/test_compliance_enforce.py::test_cli_enforce_runs_pre_commit`). Commands with no
dedicated test (`uninstall`, `list`, `info`) are `unverified` with an empty Test path -- honest, not
backfilled.

`README.md`: remove the `Highlights of the v0.19+ documentation-integrity arc:` paragraph and its
five bullets (and the trailing "Full details" duplicate) from `## Latest release`, leaving the
evergreen CHANGELOG-as-single-source-of-truth pointer the section already declares. This makes the
section match its own stated intent ("avoids version-specific content to prevent README drift").

### Unit Tests

- `tests/test_feature_index_present_and_verifies.py`:
  - `test_feature_index_is_recognized_and_parses` - `feature_index_verify.tally(REPO)` returns
    `missing_index == False` and `total > 0`, and `governance_health._classify_one(REPO,
    "docs/FEATURE_INDEX.md", True).status` is `OK` (the artifact exists, parses, and clears the
    health gate -- invoking both units, asserting their output).
  - `test_feature_index_rows_use_valid_status` - every parsed row's verification status is in
    `feature_index_verify.STATUS_VALUES` (invoke `parse_index_rows`, assert membership).
  - `test_readme_latest_release_has_no_stale_version_pin` - `README.md` `## Latest release` section
    contains no `v0.19` version-pin (assert the stale block is gone; guards regression of the drift).

## Definition of Done

### Deliverable: D-feature-index

- **D1**: the absent required `FEATURE_INDEX.md` now exists, enumerates the user-touchable CLI
  surface, and clears the governance-health gate.
- **D2**: `docs/FEATURE_INDEX.md` in the doctrine table format; rows statused from real tests.
- **D3**: ledger SEAL records the index (Total/verified/unverified/n-a counts per the seal pass).
- **D4**: `test_feature_index_is_recognized_and_parses` + `test_feature_index_rows_use_valid_status`.

### Deliverable: D-readme-currency

- **D1**: the README "Latest release" section no longer ships an ~87-release-stale `v0.19+` block.
- **D2**: the `v0.19+` Highlights block removed from `README.md`.
- **D3**: ledger entry notes the doc-currency fix.
- **D4**: `test_readme_latest_release_has_no_stale_version_pin`.

## Feature Inventory Touches

None. This phase authors a governance doc + a README edit; it touches no `src/` feature surface (the
CLI commands it *indexes* are pre-existing, not modified here).

## CI Commands

- `python -m pytest tests/test_feature_index_present_and_verifies.py -q` -- the new suite.
- `python -m pytest -q` -- full suite green.
- `qor-logic governance-health --profile skill-entry` -- FEATURE_INDEX now OK (was MISSING).
