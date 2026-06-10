# Plan: Phase 154 -- seed --target help text (GH #219)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Closes GH #219. `qor-logic seed --target <name>` is a footgun: `--target` carries no `help=`, so it
reads like "the artifact to seed" when it is the **destination workspace directory**. The natural wrong
invocation (`seed --target GOVERNANCE_INDEX`) scaffolds a whole fresh workspace into `./GOVERNANCE_INDEX/`
instead of creating the one artifact. The issue's primary fix ("this alone prevents the misuse") is a
clarifying `help=` string. Verified against current code (v0.109.1): the issue's secondary "exit-1 with
success output" (fix #3) is ALREADY resolved -- `_do_seed` returns 0 unconditionally and `seed --target`
exits 0 from both a clean and an already-seeded workspace. The optional fix #2 (warn/skip when `--target`
resolves inside an initialized workspace) is deferred as a separate, deeper change.

## Phase 1: clarifying help on the path `--target` arguments

### Affected Files

- `qor/cli.py` - add `help=` to the `seed` `--target` argument (and the sibling path `--target`s on `install` / `uninstall` / `init`, which share the same no-help footgun class).
- `tests/test_cli_target_help.py` (NEW).

### Changes

`sp_seed.add_argument("--target", ...)` gains:
`help="destination workspace directory to scaffold into (default: current directory); this is a PATH, not an artifact name"`.
The `install` / `uninstall` / `init` `--target` arguments gain a concise help
(`"custom destination directory (overrides the host default)"`), so the whole `--target` family is
self-documenting. No behavior change -- help text only.

### Unit Tests

- `tests/test_cli_target_help.py`:
  - `test_seed_target_help_clarifies_directory` - build the real parser via `_build_parser`, locate the `seed` subparser's `--target` action, assert its `help` is non-empty, mentions a directory, and disambiguates from an artifact name.
  - `test_all_path_targets_have_help` - the `--target` action on each of `install` / `uninstall` / `init` / `seed` has non-empty help (no silent footgun remains in the family).
  - `test_seed_exit_zero_regression` - `_do_seed` returns 0 for a fresh tmp workspace AND when `--target` points at a sub-path of an already-seeded workspace (pins the now-resolved fix-#3 behavior so it can't regress).

## Definition of Done

### Deliverable: D-seed-target-help

- **D1**: `qor-logic seed --help` makes clear that `--target` is a destination directory, not an artifact name; the footgun no longer reads ambiguously.
- **D2**: the `seed` (and sibling install/uninstall/init) `--target` arguments carry `help=`; no behavior change.
- **D3**: ledger SEAL records GH #219 closed; fix #3 noted already-resolved, fix #2 deferred.
- **D4**: `test_seed_target_help_clarifies_directory` (help present + "director" + disambiguation) + `test_all_path_targets_have_help` + `test_seed_exit_zero_regression`.

## CI Commands

- `python -m pytest tests/test_cli_target_help.py -q` -- new tests (run twice).
- `python -m pytest -q` -- full suite green.
