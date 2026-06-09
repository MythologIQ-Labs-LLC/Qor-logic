# Research Brief

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: Residual-cleanup triage -- items 4-6 (FEATURE_INDEX MISSING, shadow-genome test pollution, v0.102.2 tag gap) + phase/117 stash status
**Scope**: `docs/META_LEDGER.md`, `qor/scripts/governance_health.py`, `qor/scripts/feature_index_verify.py`, `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`, `tests/test_override_friction_escalator.py`, `tests/test_changelog_tag_coverage.py`, PyPI

---

## Executive Summary

Of the four residuals, **one is already fully in main and needs nothing** (phase 117), **one needs no
cycle** (the v0.102.2 gap is a permanent grandfather), and **two are real and need governed work**:
the absent `FEATURE_INDEX.md` (a substantive artifact-authoring cycle) and a test that pollutes the
tracked `PROCESS_SHADOW_GENOME_UPSTREAM.md` with 78 accumulated `sess-1` events (a small hotfix-class
cycle including cleanup). Direct answer to the question: phase 117 is incorporated; items 4 and 5
require a cycle; item 6 does not.

## Findings

### Phase 117 -- ALREADY IN MAIN (no cycle)

`docs/META_LEDGER.md` Entry #310 is the Phase 117 SESSION SEAL (v0.84.0, prose_test_lint
harden+enforce; `CHANGELOG.md:195`). The work shipped. The `stash@{2}` ("phase/117 ...
pre-pyproject-fix") is **not unincorporated work** -- `git stash show -p stash@{2}` is leftover
working-tree churn from that session: appended `sess-1` shadow-genome lines (the item-5 pollution)
plus `qor/dist/manifest.json` timestamp drift. The stash is droppable; nothing to merge.

### Item 4 -- FEATURE_INDEX.md MISSING -- NEEDS A FULL CYCLE

`docs/FEATURE_INDEX.md` is a declared required governance artifact
(`governance_health.REQUIRED_ARTIFACTS`) consumed by `qor/scripts/feature_index_verify.py`,
`qor/scripts/governance_health.py`, and `qor/scripts/qa_evidence.py`; its format is specified in
`qor/references/doctrine-feature-inventory.md` ("a tracked governance artifact enumerating every
user-touchable feature of the product ... is the entire product covered?"). The file genuinely does
not exist -- the preflight `MISSING` is real, not noise. Authoring it means enumerating every
user-touchable feature (CLI subcommands, skills, gates) and cross-referencing each to a proving test
per the doctrine. That is substantive artifact authoring + per-feature verification, not a
mechanical edit -> **a full governance cycle** (plan -> audit -> implement -> seal). It also unlocks
the per-plan `feature_inventory_touches` discipline that is currently skipped because the index is
absent.

### Item 5 -- shadow-genome test pollution -- NEEDS A (SMALL) CYCLE

`tests/test_override_friction_escalator.py` emits `gate_override` events with `session_id: "sess-1"`
and reason "user override: hotfix scope" against the **real repo root**, so they land in the tracked
`docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`. `git show HEAD:docs/PROCESS_SHADOW_GENOME_UPSTREAM.md | grep
-c sess-1` = **78** -- the events have been accumulating into main across many runs (each test run
appends more; this session discarded the fresh line at each seal). Root cause: the test exercises the
real emit path without redirecting the write to a `tmp_path` (contrast the same file's hygienic tests
in `tests/test_shadow_attribution.py:96+`, which use `tmp_path`). Fix = point the offending test at a
tmp root (monkeypatch/`repo_root`) **and** prune the 78 polluted lines from the committed file. Touches
a governance doc + a test -> a small governed cycle (hotfix class), not a bare edit.

### Item 6 -- v0.102.2 tag/release gap -- NO CYCLE (permanent grandfather)

PyPI has no `0.102.2` release (`pypi.org/pypi/qor-logic/json` -> `0.102.2` absent); the tag exists
locally but never reached origin (origin holds `v0.102.0`/`v0.102.1`, then `v0.103.0`). The
`CHANGELOG.md` `[0.102.2]` section therefore corresponds to no shipped release, and it is already
grandfathered in `tests/test_changelog_tag_coverage.py::_GRANDFATHERED_UNTAGGED_SECTIONS` (added
Phase 140). Pushing the tag now would fire `release.yml` to publish `0.102.2` **after** `0.106.0` --
out-of-order and wrong. The correct state is the current one: a permanent grandfather. **No cycle.**
Optional trivial doc nicety: annotate the `[0.102.2]` CHANGELOG heading as a local-only/unreleased
band -- cosmetic, not required.

## Blueprint Alignment

| Item | In main? | Needs a governance cycle? |
|---|---|---|
| Phase 117 | YES (Entry #310, v0.84.0) | NO -- done; stash is droppable cruft |
| 4. FEATURE_INDEX.md | NO (genuinely absent) | YES -- full cycle (artifact authoring + per-feature tests) |
| 5. shadow-genome test pollution | bug IS in main (78 lines) | YES -- small/hotfix cycle (test fix + prune) |
| 6. v0.102.2 tag gap | n/a (never released) | NO -- permanent grandfather; optional cosmetic note |

## Recommendations

1. **Phase 117 / stashes**: drop `stash@{0}`/`stash@{1}` (this session's cruft) and `stash@{2}`
   (phase-117 cruft); delete the three merged `phase/14x` branches. Housekeeping, no cycle.
2. **Item 5 first (small cycle, P1)**: redirect `test_override_friction_escalator.py` to a tmp root
   and prune the 78 `sess-1` lines from `PROCESS_SHADOW_GENOME_UPSTREAM.md`. Self-contained; stops the
   bleed before it grows. Add a guard test asserting no test writes to the real upstream file.
3. **Item 4 (full cycle, P2)**: author `docs/FEATURE_INDEX.md` per `doctrine-feature-inventory.md` --
   enumerate user-touchable features (CLI subcommands incl. the new `compliance enforce`, skills,
   gates) with a proving test each; this also re-activates the `feature_inventory_touches` plan gate.
4. **Item 6**: accept the grandfather; optionally annotate the CHANGELOG section. No cycle.

## Updated Knowledge

The "pending issues" reduce to **two governed work items** (item 5 small, item 4 full) plus
housekeeping. Phase 117 and item 6 are resolved/closed by construction. Candidate doctrine note: a
test that emits real shadow-genome / ledger events MUST redirect writes to a tmp root; writing to a
tracked governance doc from a test is a hygiene defect (the item-5 pattern) -- pairs with the saved
`feedback_full_suite_after_seal` discipline.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
