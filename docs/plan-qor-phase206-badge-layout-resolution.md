# Plan: badge-layout resolution repair (GH #293 / PR #294)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: none (no new governance concept; `BadgeLayout` and
`BadgeLayoutError` are code symbols local to `qor/scripts/badge_layout.py`, not
glossary terms)

**boundaries**:
- limitations: The declared layout is supplied per invocation (one keyword
  argument or the CLI flags). No layout file, no auto-detection, no persisted
  layout config. Counting remains a filesystem walk; nothing is cached between
  calls.
- non_goals: No change to badge rendering output, README structure, or the set
  of counted badge kinds. No change to `count_tests` or `count_ledger_entries`.
  No new `qor/cli.py` subcommand. No renaming of the PR head branch.
- exclusions: The upstream package line that originated this correction is out
  of scope; this plan governs only the Qor-logic runtime and its published
  behavior. Historical ledger entries are not rewritten.

This is the second iteration. The first was VETOed at ledger entry #502 on two
grounds; both are addressed below and the changes they forced are recorded as
LD-4 and LD-5.

## Open Questions

None.

## Locked Decisions

**LD-1 — An unresolved counter root is an error; an empty declared root is a
zero.** The ported contract raises rather than returning a synthetic count when
a configured root does not resolve to a directory.

`git show HEAD:qor/scripts/badge_currency.py | grep -nE 'raise BadgeLayoutError|root not found' -> 45: raise BadgeLayoutError | 49: raise BadgeLayoutError | 50: f"{label} root not found: {configured_root} "`

This is the behavior GH #293 asks for, so the four red tests are not evidence
against the contract. They are fixtures that never declared a layout at all.

**LD-2 — The repository already has a canonical fixture idiom for a declared
default layout: create the three `qor/` roots in the temporary repo.**

`git show HEAD:tests/test_readme_badge_currency.py | grep -nE 'qor" / "(skills|agents|references)"' -> 53: (tmp_path / "qor" / "skills" / "demo").mkdir(parents=True) | 55: (tmp_path / "qor" / "agents").mkdir(parents=True) | 57: (tmp_path / "qor" / "references").mkdir(parents=True)`

The repair brings the two lagging fixtures to this shape rather than inventing
a third convention or softening LD-1.

**LD-3 — The `counts=None` fallback in `update_files` is unreachable from its
only production caller, and unusable in a synthetic repository.**

`git show HEAD:qor/scripts/seal_artifacts.py | grep -nE 'changed = update_files|counts=counts|_layout_kwargs\(args\)' -> 285: **_layout_kwargs(args), [the collect_counts call] | 287: changed = update_files( | 291: counts=counts, | 307: **_layout_kwargs(args), [the check_files call]`

`main` always supplies `counts`, so the fallback never runs. It also cannot run
usefully against a temporary repository: `collect_counts` reaches `count_tests`,
which shells out to `pytest tests/ --collect-only` and raises when there is no
`tests/` directory to collect. The fallback is therefore both dead in practice
and untestable in the fixtures available. The correct closure is deletion, not
threading a layout parameter into it. This supersedes the first iteration's
reading, which proposed forwarding a layout the fallback would never consume.

**LD-4 — One declared layout is one value, not six parameters.** (Forced by
audit entry #502 Ground 1.) Expressing the layout as six loose parameters put
four units over the Section 4 caps on repetition alone: `seal_artifacts.py`
186 -> 323 file lines, `seal_artifacts.main` 32 -> 63, `seal_artifacts.update_files`
under 30 -> 42, `badge_currency.check_currency` 38 -> 41. The layout becomes a
frozen dataclass carried as a single keyword.

**LD-5 — Layout ownership is its own module.** (Forced by LD-4.) With the value
object folded into `badge_currency`, that module reached 275 lines against a
250 cap. `BadgeLayout`, `BadgeLayoutError`, `DEFAULT_LAYOUT`, and the two CLI
helpers move to a new `qor/scripts/badge_layout.py`. `badge_currency` re-exports
them, so no import site outside the module changes. The resulting layering is
one-directional: `badge_layout` (what a layout is) <- `badge_currency` (counting)
<- `seal_artifacts` (writing).

## Phase 1: Reconcile the synthetic seal-artifact fixtures

### Unit Tests

- `tests/test_seal_artifacts.py::test_check_files_clean_after_write` -
  confirms `check_files` returns no mismatches on a repo whose declared layout
  resolves and is empty, immediately after `update_files` wrote the zero counts.
- `tests/test_seal_artifacts.py::test_check_files_reports_stale_badge_and_header` -
  confirms a stale skills badge and a behind-by-four header are both named as
  mismatches when the layout resolves.
- `tests/test_seal_artifacts.py::test_main_write_then_check_exit_codes` -
  confirms `main --write` exits 0 and the following `main --check` exits 0, then
  exits 1 with `ledger` named once a fourth ledger entry is appended.
- `tests/test_dry_run_modes.py::test_seal_artifacts_dry_run_previews_without_writing` -
  confirms `--write --dry-run` exits 0, previews exactly two writes, leaves both
  files byte-identical, and that the following wet `--write` changes README.

### Affected Files

- `tests/test_seal_artifacts.py` - `_make_repo` creates the three default
  counter roots as empty directories.
- `tests/test_dry_run_modes.py` - the inline repo in
  `test_seal_artifacts_dry_run_previews_without_writing` does the same.

### Changes

`_make_repo` gains `qor/skills`, `qor/agents`, and `qor/references` as empty
directories, so the temporary repository declares the default layout and is
explicitly empty under it. Every existing assertion in those tests already
expects zero skills, zero agents, and zero doctrines, so the expected values do
not move; only the reason for the zero changes, from "root absent" to "root
present and empty". The dry-run fixture is brought to the same shape.

## Phase 2: Carry the layout as one value

### Unit Tests

- `tests/test_badge_layout_resolution.py::test_declared_non_qor_layout_counts_actual_files` -
  extended to assert `count_by_layout` returns `{skills: 1, agents: 1, doctrines: 1}`
  for the non-`qor/` fixture, and that `check_currency` accepts the layout as one
  keyword and reports no mismatches.
- `tests/test_badge_layout_resolution.py::test_seal_write_regenerates_badges_for_declared_layout` -
  seeds a stale `Skills-99` badge into a repo that has no `qor/` roots at all,
  runs `main --write` with the non-`qor/` layout flags, and asserts exit 0 and a
  README carrying `Skills-1`. A layout that failed to reach the counters would
  abort instead of writing, so the assertion is on rendered output, not wiring.
- `tests/test_badge_layout_resolution.py::test_seal_check_propagates_declared_layout` -
  unchanged behavior, rewritten to share the flag list with the write test.

### Affected Files

- `qor/scripts/badge_layout.py` - NEW. `BadgeLayoutError`, the frozen
  `BadgeLayout` dataclass with the `qor/` defaults, `DEFAULT_LAYOUT`,
  `add_layout_args`, `layout_from_args`.
- `qor/scripts/badge_currency.py` - imports and re-exports the five names above
  via `__all__`; `check_currency` takes `layout` as one keyword; new
  `count_by_layout` returns all three filesystem-derived counts for one layout;
  `main` builds the layout with `layout_from_args`.
- `qor/scripts/seal_artifacts.py` - `collect_counts` and `check_files` take
  `layout` as one keyword; `update_files` requires `counts` and carries no
  layout; `_add_layout_args` and `_layout_kwargs` deleted in favor of the
  `badge_layout` helpers; `main` split into `_build_parser`, `_run_write`, and a
  dispatcher; `_BADGE_FORMS` derived from a suffix table rather than twenty
  literals.
- `tests/test_badge_layout_resolution.py` - layout fixtures rebuilt as a
  `BadgeLayout` value and a shared CLI flag list; the two tests above.

### Changes

The six parameters collapse to one `layout` keyword at every seam. The CLI flag
names, their defaults, and every rendered output byte are unchanged. The
`_BADGE_FORMS` table is generated from `{kind: trailing-suffix}` by a single
rule; the generated table was asserted equal to the previous literal table
before the literals were removed.

## Phase 3: Repair the pull-request governance surface

### Affected Files

- PR #294 body - rewritten to carry the plan path, ledger entry reference, and
  Merkle seal hash produced by this phase's seal.
- Issue #293 body - direct identifiers of a repository outside Qor-logic
  replaced with neutral concepts.

### Changes

Executed after the seal, because two of the three required citations do not
exist until the seal entry is written. The PR body is rewritten to the
`doctrine-governance-enforcement.md` §6 citation template. Both bodies are
swept for outside-repository identifiers per
`qor/references/doctrine-publication-boundary.md`: the upstream source is
described as an upstream package line without naming a repository, issue
number, pull-request number, or commit identifier belonging to it.

## Definition of Done

### Deliverable: resolvable-layout fixtures

- **D1**: A synthetic governance repository used by the seal-artifact tests
  declares the layout it is counted against, so a zero count in those tests
  means "declared and empty", never "unresolved".
- **D2**: `tests/test_seal_artifacts.py::_make_repo` and the inline repo in
  `tests/test_dry_run_modes.py` create `qor/skills`, `qor/agents`, and
  `qor/references`.
- **D3**: Seal entry records the fixture reconciliation and states that the
  fail-loud contract from LD-1 was preserved rather than relaxed.
- **D4**: The four previously red tests named in Phase 1 pass, and the full
  suite is green on two consecutive runs.

### Deliverable: the layout as one value

- **D1**: A declared layout is one immutable value threaded as one keyword, and
  the module that owns it is separate from the module that counts with it.
- **D2**: `qor/scripts/badge_layout.py` exports `BadgeLayout`, `DEFAULT_LAYOUT`,
  `BadgeLayoutError`, `add_layout_args`, `layout_from_args`; `check_currency`,
  `collect_counts`, and `check_files` each take a single `layout` keyword;
  `update_files` requires `counts` and takes no layout.
- **D3**: Seal entry records LD-4 and LD-5 as audit-forced, cites entry #502 as
  the ground, and reports the post-refactor Section 4 measurements.
- **D4**: `test_seal_write_regenerates_badges_for_declared_layout` asserts the
  README bytes written under a non-`qor/` layout; every unit is measured under
  its Section 4 cap by `ast` span and `splitlines` (`seal_artifacts.py` 250,
  `badge_currency.py` 249, `badge_layout.py` 62; longest function 33).

  No red-then-green claim is made for the `update_files` change: LD-3 establishes
  that the deleted fallback was unreachable from the only caller, so no test
  could observe it. Its removal is verified by the full suite staying green with
  every call site unchanged.

### Deliverable: pull-request governance surface

- **D1**: PR #294 satisfies the §6 citation contract and neither it nor issue
  #293 identifies a repository outside Qor-logic.
- **D2**: No code deliverable.
- **D3**: PR body cites `docs/plan-qor-phase206-badge-layout-resolution.md`,
  the seal ledger entry number, and the 64-character Merkle seal hash.
- **D4**: `PR Citation Lint` reports success for the rewritten body, and
  `publication_boundary_lint` reports zero findings in every file this phase
  touched.

  Amended after the PASS audit, disclosed here and in the seal entry. The
  original wording claimed the lint would report no findings "for the tracked
  surface", which is not achievable in this phase and was never in its scope:
  `main` already carries 90 tracked files with findings, 42 of them outside the
  `qor/vendor/` third-party-attribution exception (legacy `qore-*` skill names,
  identity terms in `.claude/skills/` and `qor/dist/` variants, three Phase 205
  gate artifacts, and the `docs/archive/` ingest tree). That debt predates this
  branch, is unrelated to badge-layout resolution, and needs its own phase. The
  criterion is narrowed to what this phase can honestly own and verify.

## Feature Inventory Touches

None. This plan touches `qor/scripts/` and `tests/` only; it introduces no
user-touchable feature and modifies no FEATURE_INDEX row.

## CI Commands

- `python -m pytest tests/test_seal_artifacts.py tests/test_dry_run_modes.py tests/test_badge_layout_resolution.py tests/test_readme_badge_currency.py -q` — the directly affected suites.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/scripts/badge_layout.py qor/scripts/badge_currency.py qor/scripts/seal_artifacts.py` — lint on the touched modules.
- `qor-logic scripts seal_artifacts --check --repo-root . --skip-tests` — live-repo badge and header currency under the default layout.
- `qor-logic scripts publication_boundary_lint --repo-root .` — no outside-repository identifiers on the tracked surface.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase206-badge-layout-resolution.md` — this plan asserts each path and command identically at every site.
