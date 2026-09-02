# Plan: bootstrap seed correctness (GH #404, #405)

**change_class**: hotfix

**doc_tier**: standard

**terms**: []

This phase introduces no new domain vocabulary; it corrects seed templates so
existing vocabulary is emitted in the form the gates already accept.

**boundaries**:
- limitations: [does not migrate any already-seeded consumer workspace; a workspace bootstrapped before this phase keeps its existing artifacts and is corrected by re-running `qor-logic-plus seed` or by hand. Does not alter sealed artifacts in this repository.]
- non_goals: [does not make the layout-bound gates configurable (GH #406 -- separate phase, since it is a path refactor plus a new typed-skip failure semantics); does not close the plan-artifact `terms` omission route (GH #414); does not add an amendment-hash enforcement gate (GH #408)]
- exclusions: [no change to `ledger_dialect`'s three accepted hash-value forms -- the templates are corrected to emit the strictest accepted form rather than the parser being widened]

## Problem

Two live defects share one cause: `/qor-bootstrap` seeds a workspace whose
artifacts the governance gates cannot read. A third reported defect (GH #407)
turns out to be already closed and is recorded below with its evidence. All
three were reported from a consumer workspace running a full governed cycle.

### GH #404 -- the seeded ledger is not machine-verifiable

`qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md:128-131`
emits:

```markdown
**Content Hash**:
SHA256(CONCEPT.md + ARCHITECTURE_PLAN.md) = [calculated hash]

**Previous Hash**: GENESIS (no predecessor)
```

`qor/scripts/ledger_dialect.py:35-40` accepts exactly three value forms:
inline backtick, `= <hex>`, and a bare hex **alone on its own line**. An
inline unbackticked hex on a `**Previous Hash**:` line matches none of them,
so `PREV_HASH_RE` misses and `ledger_hash.verify` classifies the entry as
non-verifiable.

The reporter observed 7 of 8 entries skipped with exit status 0. Two of the
three root causes they named are already closed by GH #282 (the shared
`ledger_dialect` module reconciled `seal_entry_check` with `ledger_hash`, and
the `Phase <N>` header requirement is gone). What remains live is the template
itself, plus an amplifier the report did not identify:
`ledger_dialect.py:26` sets `MARKUP_COMPAT_BOUNDARY = 123`, and
`ledger_hash.verify` fails an unparseable entry only at or above that number.
123 is an absolute entry number from **this** repository's history, so no
entry in a fresh workspace ever reaches it and every unparseable entry
degrades to a silent skip with exit 0.

### GH #405 -- the seeded FEATURE_INDEX misaligns against its parser

Seed template (`qor-bootstrap-templates.md:184`):

```
| ID | Feature | Doc | Code | Test | Status | Notes |
```

Canonical (`qor/templates/FEATURE_INDEX.example.md:6`):

```
| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |
```

GH #365 already added a `status` alias, so rows are no longer dropped
wholesale -- which makes the residual quieter, not smaller. Rows parse, but
`name`, `source-of-truth`, `doc citation`, `test path` and `surface` all
resolve to absent keys. The coverage tally is correct and everything it is
supposed to substantiate is empty.

Separately, `parse_index_rows` returns `[]` for a table whose header declares
no recognized status column, so "no rows" and "rows I could not read" are
still the same result.

### GH #407 -- verified already closed; no change in this phase

Recorded because the research brief got this one wrong twice and the record
should say so.

The literal `_PLAN_PATH_RE` the issue quotes is gone; GH #282 replaced it with
`governance_paths.resolve_governance_plan_path`. The brief then claimed the
residual was that `/qor-plan` writes no per-plan registration row. That is also
wrong: `docs/GOVERNANCE_INDEX.md` Tier 4 carries a glob row
`` `docs/plan-*.md` ``, `governance_index._is_registered` resolves globs
(`governance_index.py:72`), and `qor/templates/GOVERNANCE_INDEX.md:47` seeds
that same row into every bootstrapped workspace. Per-plan registration is
unnecessary.

Verified by execution rather than by reading:

```
resolve_governance_plan_path("docs/plan-sprint1-install-correctness.md", ".")
-> <repo-root>/docs/plan-sprint1-install-correctness.md   (resolved, not rejected)
```

A plan named for its work, in the exact shape the reporter said was rejected,
resolves. #407 closes on this evidence with no code change.

## Fix

1. **`qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md`**:
   emit the strictest accepted hash form -- `` **Content Hash**: `<hex>` ``,
   `` **Previous Hash**: `<hex>` ``, `` **Chain Hash (Merkle seal)**: `<hex>` ``
   -- so a seeded ledger parses under `ledger_dialect` without the operator
   editing markup by hand.
2. **`qor/scripts/ledger_hash.py`**: apply the GH #363 marked-but-unparseable
   rule inside `verify`, where it was missing. `MARKUP_COMPAT_BOUNDARY` is
   untouched.

   **Design revised during implementation** (amendment recorded in the ledger).
   The audited design keyed the tightening on the boundary: fail the skips when
   no entry reaches `MARKUP_COMPAT_BOUNDARY`. Implementation showed that
   condition is both too broad and aimed at the wrong thing. It broke
   `test_low6_verify_reports_skipped_entries`, whose fixture entries name no
   hash field at all -- a genuinely pre-convention entry that claims nothing and
   should stay a tolerated skip at any entry number.

   The correct line already exists in this codebase. GH #363 drew it in
   `verify_post_anchor` (`ledger_hash.py:655`): an entry that NAMES a hash field
   is making an integrity claim, and a value the dialect cannot read is a broken
   claim; an entry with no hash label claims nothing.
   `ledger_dialect.any_hash_label_present` exists for exactly this test. That
   rule was simply never applied in `verify`, which is the function
   `qor-logic-plus verify-ledger` calls -- so the consumer saw silent skips
   where the post-anchor path would have failed.

   So: in `verify`, an unresolvable entry whose body carries a hash label FAILS
   regardless of entry number; an unlabeled one stays a tolerated skip. This is
   narrower than the audited design, needs no new constant, and fixes the
   consumer's "7 of 8 skipped, exit 0" at its actual cause -- those entries all
   carried labeled `**Content Hash**` / `**Previous Hash**` fields.
3. **`qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md`**:
   emit the canonical FEATURE_INDEX header from
   `qor/templates/FEATURE_INDEX.example.md`. One vocabulary, one source.
4. **`qor/scripts/feature_index_verify.py`**: `parse_index_rows` gains a
   companion that reports an unreadable header, and `tally` surfaces it, so
   "no rows" and "rows I could not read" stop being the same result.
5. **`tests/test_qor_bootstrap_feature_index_template.py`**: convert, do not
   string-swap (tribunal ground V-1, entry #680). Every assertion in that file
   is substring-presence against the template, and line 27 asserts the
   DEFECTIVE header is "the canonical 7-column table header" -- which is why
   GH #405 survived a test positioned to catch it. The rewritten test extracts
   the header from the template region and drives it through
   `feature_index_verify.parse_index_rows`, asserting the canonical columns
   resolve, so a future template edit that breaks parsing fails regardless of
   which strings happen to be present.
6. Recompile `qor/dist/variants/**`.

No `/qor-plan` or `/qor-bootstrap` change: the Tier 4 glob row already
registers every plan, in this repository and in every seeded workspace.

## Tests (written first)

- `tests/test_bootstrap_seed_correctness.py::test_seeded_ledger_entry_parses_under_ledger_dialect`
  -- build an entry from the bootstrap template's hash lines with real
  digests substituted; `ledger_dialect.PREV_HASH_RE` must match. Red before
  fix 1: the template's unbackticked form matches none of the three accepted
  value forms.
- `::test_verify_fails_when_every_entry_is_below_the_compat_boundary`
  -- a ledger whose entries are all below `MARKUP_COMPAT_BOUNDARY` and all
  unparseable must make `ledger_hash.verify` report failure, not exit 0 with
  an informational skip line. Red before fix 2.
- `::test_verify_still_grandfathers_entries_that_claim_no_hash`
  -- an entry naming no hash field stays a tolerated skip. Guards fix 2 against
  becoming a blanket tightening. Re-aimed with the fix-2 revision: the line is
  the presence of an integrity claim, not the entry number.

### Pre-existing tests corrected by fix 2

Fix 2 changes a real contract in `verify`, and five existing tests encoded the
old one. Each is updated with its rationale in the docstring; none is deleted.

The contract: an entry that NAMES a hash field makes an integrity claim, so a
value the dialect cannot read is a broken claim and fails. An entry that names
no hash field claims nothing and stays a tolerated skip. This is what
`verify_post_anchor` has done since GH #363; `verify` -- the function
`qor-logic-plus verify-ledger` actually calls -- never got the rule, which is
why the consumer saw "7 of 8 skipped, exit 0".

- `test_ledger_hash_validation.py::test_verify_skips_entries_with_placeholder_content_hash`
  asserted that `**Content Hash**: TBD000...` skips with rc 0. Renamed to
  `test_verify_fails_...` and asserts rc != 0. A verifier exiting clean on a
  ledger entry whose content hash reads `TBD` is precisely the failure GH #404
  reports.
- `::test_verify_skips_entries_with_uppercase_hash` and
  `::test_verify_skips_entries_with_short_hash` -- same change, same reason
  (uppercase hex and a 32-character value are unreadable claims).
- `test_ledger_hash.py::test_verify_skips_entries_without_required_markers`
  bundled both cases in one fixture and called them both "skipped quietly". Split:
  the unmarked entry keeps its skip; the labeled-but-unreadable entry moves to a
  new companion test asserting failure.
- `test_ledger_hash.py::test_verify_bounded_span_stops_at_next_field` asserted
  `rc == 0` and `"FAIL Entry #1" not in out`. Its actual purpose -- proving the
  bounded span does not sweep the next field's value into Content Hash and
  "verify" on it -- is preserved by the retained `"OK Entry #1:" not in out`
  assertion; only the disposition of the unreadable claim changed.

This repository's own 677-entry ledger verifies clean under the new contract
(`verify` exit 0), because its genuinely pre-convention entries name no hash
field rather than naming one badly.

### Vacuously-passing tests corrected

Two more were passing without testing anything, and fix 2 exposed both:

- `tests/test_security_fixes.py::test_low1_verify_handles_both_formats` wrote
  its chain hashes unbolded (`Chain Hash = <hex>`), which `CHAIN_HASH_RE` does
  not match, so BOTH entries were silently skipped and the test never verified
  a chain hash in either format it names. Bolded, and its placeholder digests
  (`"a"*64`) replaced with real ones -- once the entries actually verify, the
  placeholder-pattern detector correctly rejects repeated-character hex.
- `tests/test_qor_bootstrap_feature_index_template.py` -- see fix 5.
- `::test_seeded_feature_index_header_parses_every_canonical_column`
  -- rows written under the bootstrap seed header must resolve `name`,
  `source-of-truth file:line`, `doc citation`, `test path` and `surface`, not
  just `status`. Red before fix 3.
- `::test_parse_index_rows_reports_unreadable_header`
  -- a table with no recognized status column must be distinguishable from an
  empty table. Red before fix 4.
- `tests/test_qor_bootstrap_feature_index_template.py::test_template_header_parses_every_canonical_column`
  -- the converted test (fix 5). Extracts the header from the template's
  FEATURE_INDEX region, feeds a synthetic row under it to `parse_index_rows`,
  and asserts every canonical column resolves. Red before fix 3: the seeded
  header yields absent `name` / `source-of-truth file:line` / `doc citation` /
  `test path` / `surface`. Replaces the presence-only assertion at line 27; the
  remaining structural assertions in that file (placeholder, Coverage Summary,
  Gaps Surfaced, `/qor-implement` reference) are legitimate template-shape
  checks and stay.
- `::test_work_named_plan_resolves_through_the_tier4_glob_row`
  -- `resolve_governance_plan_path` must admit a plan named for its work rather
  than only the `plan-qor-phase*` family. This one passes before any change in
  this phase; it is permanent regression coverage pinning the GH #407 closure
  so a future index edit that drops the Tier 4 glob row fails loudly instead of
  silently re-breaking consumer plans.

Every test invokes the unit and asserts on its return value or raised error;
none asserts artifact presence or substring membership in a template file.

## Validation

- `python -m pytest tests/test_bootstrap_seed_correctness.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` -- this repository's own ledger must stay clean under fix 2

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
