# Plan: config-backed badge-layout resolution (Phase 210, GH #299)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Resolution reads one repository-local file. No org scope, no
  inheritance, no environment variable, no auto-detection of a layout. A key
  the config does not declare keeps its `qor/`-rooted default.
- non_goals: No change to the counting, confinement, or fail-loud semantics
  themselves. No change to CLI flag names. No new CLI subcommand. No change to
  which badge kinds exist.
- exclusions: Org-scoped or multi-repository layout policy is out of scope for
  the public line by design.

## Open Questions

None.

## Locked Decisions

**LD-1 — The declarable layout is unreachable from the governed flow.**

`git show HEAD:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE "seal_artifacts --check" -> 422:   qor-logic scripts seal_artifacts --check --repo-root . \`

`git show HEAD:.github/workflows/ci.yml | grep -nE "seal_artifacts --check" -> 102:        run: python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .`

Neither invocation passes a layout flag, and flags are the only channel. Phase
206 closed the dangerous half of GH #293 (a missing root raises instead of
reporting a synthetic zero) but left the remedy unreachable: a repository whose
skills are not under `qor/` fails the release-class seal gate on every
feature/breaking phase, and the abort message instructs the operator to declare
the layout explicitly while the governed path offers no way to do so.

**LD-2 — Every flag arrives populated, so no lower-precedence source could ever
win.**

`git show HEAD:qor/scripts/badge_layout.py | grep -nE 'add_argument\("--skills-root' -> 41:    parser.add_argument("--skills-root", type=Path, default=DEFAULT_LAYOUT.skills_root)`

An unset flag is indistinguishable from one explicitly set to the default. Any
configuration channel added while the defaults remain would be dead on arrival,
so the defaults must become `None` in the same change that introduces the
channel; doing one without the other produces a config surface that silently
never applies.

**LD-3 — Declaring a root is not trusting it.**

`_count_matching` and `_resolve_count_root` enforce repository containment,
reject absolute and parent-traversing patterns, and reject symlinked matches.
Routing a new input channel into an already-validated function inherits those
guarantees but does not test them: every existing negative test drives the flag
channel. A later change that resolved config roots eagerly would move resolution
outside the guard with nothing to notice. The config channel therefore gets its
own negative tests rather than relying on inheritance.

**LD-4 — One tolerant reader, not two.**

`grep -rn "CONFIG_RELPATH" qor/scripts/*.py -> qor/scripts/attribution_policy.py:23:CONFIG_RELPATH = Path(".qorlogic") / "config.json"`

Phase 207 already reads `.qorlogic/config.json` for `attribution.model_coauthor`
with its own tolerant parse. Adding a second independent parse of the same file
guarantees the two degrade differently under the same malformed input. A single
shared section loader is extracted and both consumers use it.

## Phase 1: One tolerant config reader

### Unit Tests

- `tests/test_qorlogic_config.py::test_load_section_returns_declared_mapping` -
  writes a config with two sections and asserts the requested one is returned
  as a mapping and the other is not.
- `::test_load_section_degrades_on_every_malformed_shape` - parametrized over
  absent file, unreadable path, invalid JSON, a non-object document, and a
  non-object section value; asserts each returns the empty mapping and none
  raises.
- `::test_attribution_policy_still_resolves_through_the_shared_reader` -
  asserts `resolve_policy` returns False for a declared `false`, True for an
  absent file, and True for each malformed shape, so Phase 207's contract is
  unchanged by the extraction.

### Affected Files

- `qor/scripts/qorlogic_config.py` - NEW. `CONFIG_RELPATH` and
  `load_section(repo_root, name) -> dict`, tolerant: any failure yields `{}`.
- `qor/scripts/attribution_policy.py` - delegates its read to the shared loader;
  its public surface and semantics are unchanged.

## Phase 2: Config-backed, per-key layout resolution

### Unit Tests

- `tests/test_badge_layout_config.py::test_config_declared_layout_resolves_without_flags` -
  writes a config declaring a non-`qor/` `skills_root`, resolves a layout with
  no flags set, and asserts the resolved `skills_root` is the declared value.
- `::test_flag_beats_config_and_config_beats_default` - asserts the three-way
  precedence on one key by resolving the same key under all three conditions
  and comparing the returned values.
- `::test_resolution_is_per_key_not_all_or_nothing` - a config declaring only
  `skills_root` leaves the other five equal to their defaults.
- `::test_unset_flag_is_distinguishable_from_flag_set_to_default` - parses argv
  with and without an explicit `--skills-root qor/skills`, and asserts config
  loses to the explicit flag but wins over the unset one, which is the behavior
  LD-2 says is impossible today.
- `::test_malformed_and_wrong_typed_layout_values_degrade_to_defaults` -
  parametrized over a non-object `layout`, a non-string value, an empty string,
  and a whitespace-only string; asserts each key falls back to its default and
  nothing raises.
- `::test_config_declared_root_escaping_the_repository_is_rejected` - drives the
  CONFIG channel (no flags) with a parent-traversing root, an absolute root
  outside the repository, and a root reached through a symlinked directory;
  asserts each raises `BadgeLayoutError`. This is the LD-3 guarantee proven
  through the new channel rather than inherited.
- `::test_both_entry_points_resolve_identical_layouts` - builds the parsers of
  `badge_currency` and `seal_artifacts` and asserts they produce equal resolved
  layouts for identical argv and identical config, so the check path and the
  write path cannot drift.

### Affected Files

- `qor/scripts/badge_layout.py` - `add_layout_args` defaults every flag to
  `None`; `layout_from_args(args)` resolves each of the six keys as
  flag > config > default, reading `layout` via the shared loader and the
  `--repo-root` already present on both CLIs.
- `tests/test_badge_layout_config.py` - the tests above.
- `tests/test_badge_layout_resolution.py` - existing flag-channel tests keep
  passing unchanged; the CLI-flag list they share is reused.

### Changes

Resolution moves into `layout_from_args`, which both CLIs already call, so no
call site changes. Confinement stays inside `_resolve_count_root` and
`_count_matching`; config supplies a candidate value and nothing more.

## Phase 3: Prove the governed flow reaches it

### Unit Tests

- `tests/test_badge_layout_config.py::test_governed_check_invocation_honors_config` -
  builds a repository whose skills live outside `qor/`, writes the declaring
  config, and runs `seal_artifacts main` with EXACTLY the argv the governed flow
  uses (`--check --repo-root <path> --skip-tests`, no layout flags), asserting
  exit 0. Without the config the same argv exits 1. This is GH #299's first
  acceptance criterion executed as a test.
- `::test_governed_write_invocation_honors_config` - the same for the `--write`
  argv the seal ceremony uses.

### Affected Files

- `qor/references/doctrine-governance-enforcement.md` - the badge-currency
  section documents the config channel and the precedence order.

### Changes

No skill or workflow edit is required: the governed invocations already pass
`--repo-root`, which is the only input resolution needs. That is the point of
resolving inside `layout_from_args` rather than at the call sites.

## Definition of Done

### Deliverable: reachable declared layout

- **D1**: A repository whose skills are not under `qor/` passes the
  release-class seal gate through the normal governed flow, passing no CLI flags.
- **D2**: `layout_from_args` resolves flag > config > default per key; flag
  defaults are `None`; `qorlogic_config.load_section` is the single reader.
- **D3**: Seal entry records that Phase 206 shipped an unreachable capability,
  names both invocation sites, and states that the flag-default change is
  required for the channel to apply at all.
- **D4**: `test_governed_check_invocation_honors_config` runs the governed argv
  verbatim and asserts exit 0 with the config and exit 1 without it.

### Deliverable: unchanged behavior without configuration

- **D1**: A repository declaring nothing resolves exactly as it does today.
- **D2**: Absent file, absent section, and every malformed shape yield defaults.
- **D3**: Seal entry records that this repository declares no `layout` section
  and its own seal is therefore resolved by the default path.
- **D4**: `test_malformed_and_wrong_typed_layout_values_degrade_to_defaults`
  and the existing Phase 206 suite pass unchanged.

### Deliverable: containment through the config channel

- **D1**: A hostile configuration cannot reach outside the repository and cannot
  turn a failing seal into a passing one.
- **D2**: Confinement remains in `_resolve_count_root` / `_count_matching`;
  config supplies candidates only.
- **D3**: Seal entry records that the negative tests enter through the config
  channel because inheritance is not evidence.
- **D4**: `test_config_declared_root_escaping_the_repository_is_rejected`
  asserts `BadgeLayoutError` for traversal, absolute-outside, and symlinked-root
  cases driven with no flags set.

## Feature Inventory Touches

None. This plan touches `qor/scripts/`, `qor/references/`, and `tests/`; it
introduces no user-touchable feature and modifies no FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_qorlogic_config.py tests/test_badge_layout_config.py -q` — the new reader and the resolution contract.
- `python -m pytest tests/test_badge_layout_resolution.py tests/test_seal_artifacts.py tests/test_attribution_coauthor_policy.py -q` — the Phase 206 and Phase 207 contracts stay unchanged.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `qor-logic scripts publication_boundary_lint --repo-root .` — the new files keep the tracked surface clean.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase210-config-backed-layout-resolution.md` — this plan asserts each path and command identically at every site.
