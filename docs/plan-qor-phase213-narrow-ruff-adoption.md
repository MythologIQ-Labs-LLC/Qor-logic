# Plan: narrow ruff adoption (Phase 213, GH #304)

**change_class**: hotfix

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Pyflakes (`F`) rules only. No style (`E`), import-sorting (`I`),
  complexity (`C901`), or bugbear (`B`) rules. No formatter. The Section 4
  Razor stays where it is -- the Judge's manual pass and the existing
  length-lock tests -- because ruff cannot express a file-line cap.
- non_goals: No baseline file and no blanket `# noqa` sweep. The adoption lands
  at zero findings or it does not land. No reformatting. No change to the
  project's own `# noqa: secret-scan` suppression convention.
- exclusions: `tests/fixtures/ab_corpus/` holds deliberately defective code used
  as detector fixtures; it is excluded by path, not by suppression comments.

## Open Questions

None.

## Locked Decisions

**LD-1 — The empirical yield is zero, so the case rests on rot and on one rule.**

Measured with `--statistics` over `qor/` and `tests/`: 195 F401 unused-import,
19 F841, 15 E402, 11 F541, 6 E741, 2 F821, remainder trivial -- 254 total.

`F821` is the only class that can indicate a live `NameError`. Both hits are in
`tests/fixtures/ab_corpus/owasp-violation/`, whose files are headed
"SEEDED TEST DEFECT -- NOT EXECUTABLE". No real defect exists in a 2776-test
codebase. Adoption is therefore justified by two narrower claims: 195 unused
imports are genuine rot, and nothing else in this repository reads Python for
correctness -- every existing lint is governance-semantic.

**LD-2 — Land at zero, never at a baseline.**

An uncleaned baseline becomes a permanently-red control, which is precisely the
failure mode repaired twice in this session: `publication_boundary_lint` could
not express its own doctrine's exceptions and was therefore wired to no gate,
and `sg_closure_lint` carried ten uncited entries for a generation. Introducing
a third instance of a pattern already diagnosed twice would be poor judgment.

Narrow scope makes zero reachable. Measured with the narrowing supplied as
flags, before any configuration exists to carry it: 207 auto-fixable and 19
needing judgment. Once Phase 1 lands the configuration, the bare invocation
cited below IS the narrow scope, which is why every non-evidence site states
the same command.

**LD-3 — The `# noqa: secret-scan` warnings are a tool collision, not a defect.**

`grep -rn "# noqa: secret-scan" qor/ tests/ | wc -l -> 14`

`grep -n "noqa" qor/scripts/secret_scanner.py -> 84:    "noqa: secret-scan",`

These 14 directives are this project's own secret-scanner suppressions; the
scanner matches that literal token. Ruff warns only because it parses any
`# noqa:` as its own directive. They suppress real findings and must not be
edited. Resolved by declaring the code external to ruff, which is what the
`external` setting exists for. An earlier characterization of these as
"malformed directives suppressing nothing" was wrong and is corrected here.

**LD-4 — Auto-fixing 195 imports is safe only because the suite proves it.**

Removing an import is inert unless the import has a side effect or is a
re-export. Ruff honors `__all__`, so deliberate re-exports (for example
`badge_currency`'s layout re-exports) are not flagged. The remaining risk is an
import kept for its side effect, which no static rule can see. The full suite,
green before and after, is the evidence -- not the auto-fixer's confidence.

## Phase 1: Declare the tool and its scope

### Affected Files

- `pyproject.toml` - `ruff` added to the `dev` extra; a `[tool.ruff]` section
  selecting `F` only, excluding `tests/fixtures/ab_corpus`, and declaring
  `secret-scan` external so the project's own suppressions do not warn.

### Changes

Configuration only; no source is touched in this phase. Selecting `F` rather
than accepting ruff's default set is the deliberate narrowing: the default
includes `E` style rules that produced 24 of the 254 findings and no defects.

## Phase 2: Land at zero

### Affected Files

- Source files across `qor/` and `tests/` - unused imports removed, unused
  variables resolved, placeholder-free f-strings de-marked. Mechanical.

### Changes

`ruff check --fix` for the 207 auto-fixable, then the 19 judgment items by
hand. An unused variable is resolved by removing it, or by naming it `_` where
the binding documents a tuple shape, never by suppressing it.

### Verification

`python -m ruff check qor/ tests/` reports zero, and the full suite is green
before and after so the removals are proven inert rather than assumed so.

## Phase 3: Gate it

### Unit Tests

- `tests/test_ruff_adoption.py::test_ruff_is_a_declared_dev_dependency` -
  parses `pyproject.toml` and asserts `ruff` appears in the `dev` extra, so the
  CI step cannot depend on a tool the project does not install.
- `::test_ruff_config_selects_pyflakes_only` - asserts the configured `select`
  is exactly `["F"]` and that `tests/fixtures/ab_corpus` is excluded, so a
  later broadening is a deliberate edit rather than a drift.
- `::test_live_tree_is_ruff_clean` - runs ruff over the repository and asserts
  zero findings, which is the regression lock that keeps the adoption at zero.

### Affected Files

- `.github/workflows/ci.yml` - a `ruff` step in the `gate-chain-completeness`
  job, adjacent to the other fail-closed checks.
- `docs/plan-qor-phase89-ci-commands-reconciliation.md` - the new command
  registered in the CI-surface list.
- `tests/test_ruff_adoption.py` - NEW, the three tests above.

## Definition of Done

### Deliverable: ruff adopted narrowly and landed at zero

- **D1**: The project declares whether it lints with ruff, and the answer is
  enforced rather than asserted in review.
- **D2**: `ruff` in the `dev` extra; `[tool.ruff]` selecting `F`, excluding the
  fixture corpus, declaring `secret-scan` external; CI runs it fail-closed.
- **D3**: Seal entry records the zero-defect yield honestly, states that
  adoption rests on rot and orthogonality rather than on bugs found, and
  corrects the earlier "malformed noqa" characterization.
- **D4**: `test_live_tree_is_ruff_clean` asserts zero findings; the full suite
  is green before and after the auto-fix, proving the import removals inert.

### Deliverable: the narrowing cannot drift

- **D1**: Broadening the rule set later is a visible, deliberate decision.
- **D2**: `select = ["F"]` and the fixture exclusion are both asserted.
- **D3**: Seal entry records why `E` rules were excluded (24 findings, zero
  defects) and why the Razor stays outside ruff.
- **D4**: `test_ruff_config_selects_pyflakes_only` fails if `select` changes.

## Feature Inventory Touches

None. This plan touches `pyproject.toml`, `.github/workflows/`, `docs/`,
`qor/`, and `tests/`; it introduces no user-touchable feature and modifies no
FEATURE_INDEX row.

## CI Commands

- `python -m ruff check qor/ tests/` — ci.yml `gate-chain-completeness` job step: the tree is ruff clean.
- `python -m pytest tests/test_ruff_adoption.py -q` — the adoption contract and the narrowing lock.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `qor-logic scripts publication_boundary_lint --repo-root .` — the tracked surface stays clean.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase213-narrow-ruff-adoption.md` — this plan asserts each path and command identically at every site.
