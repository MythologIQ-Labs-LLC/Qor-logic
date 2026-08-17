# Plan: The evidence statement is checked on its own account

**iteration**: 3

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: `reproduces` compares full stripped-line equality, so lines too long to quote verbatim cannot be cited in the mandated form; anchor a short line instead. Backtick characters are stripped from Locked-Decision block text before statement parsing, so a grep pattern containing a literal backtick cannot appear in a parseable statement. Normalization stays confined to `parse_evidence_statements`: `_demand_set`'s exclusion spans are computed over the raw block, so a `file:line` token inside a two-span statement's quoted observed text would register as a demand (iteration-2 audit O1); no artifact in the corpus exhibits this, and it is accepted as a documented asymmetry rather than widened normalization scope.
- non_goals: No change to `/qor-audit` P2 (the binding full-re-walk pass), to the PR Citation Lint workflow, or to `check_plan`'s module/skill-path checks. Statements in the pre-amendment doctrine form (no `NN:` prefix) remain presence-only; they are not guessed into truth checks.
- exclusions: GH #333, GH #332, GH #337, GH #320, GH #286. Disposition of PR #338 is an operator decision at the Review Boundary, outside this plan.

## Open Questions

None. The citation-key contract (findings report `<path>:<line>`; the ref appears in the reason text) and the doctrine's amended mandated form (`-> NN:<exact observed text>`) are Locked Decisions below, not open.

## Iteration 3 disposition of the iteration-2 VETO (F1 razor-overage)

The iteration-2 audit verified every other pass clean and vetoed on one finding: the declared extraction (grammar region only, 82 lines of 366) could not land `plan_grep_lint.py` at the 250-line ceiling. Iteration 3 closes the arithmetic by moving the citation-scanning and demand machinery into `plan_evidence.py` alongside the grammar. Shown work, measured against the current module: 366 lines total; the grammar region (lines 116-197) is 82 lines; the citation regex block (`_EVIDENCE_RE` through `_ANY_HEADING_RE`, lines 105-113) is 9; the block/demand machinery (`_ld_blocks` at 200 through `_statement_index` ending at 258, minus the kind constants and their comment at 226-231 which stay) is 50. Moves total 141; roughly 5 import lines return; `plan_grep_lint.py` lands near 230 and `plan_evidence.py` near 155 including its own docstring and imports -- both under 250 with headroom for Phase 2's net additions (about -2 and +8 respectively). No comment is deleted to reach either number.

## Iteration 2 disposition of the iteration-1 VETO (F1-F6)

- **F1/F2 (phantom targets)**: this iteration names only verified targets. The binding doctrine text is the SG-CitationDrift-A P1 paragraph in `qor/references/doctrine-shadow-genome-countermeasures.md` (section heading at line 279, paragraph at line 285 of v0.146.1); the binding contract test is `test_the_lint_ceiling_matches_the_doctrine_kinds` with companion `test_the_two_kind_sets_are_disjoint_and_non_empty` (LD-6 anchors the parser those tests share).
- **F3 (dominant defect)**: promoted to Phase 1, the primary deliverable. The two-span markdown styling parses to zero statements and the one-span styling corrupts `observed` with the closing backtick; normalization fixes both with one mechanism.
- **F4 (fake-satisfiable acceptance)**: D4 of deliverable 5 self-verifies over this plan's Locked Decisions, which are written in the fenced `NN:` form that parses both before and after the change; no illustrative citation appears anywhere in a Locked-Decision region.
- **F5 (extension disagreement)**: both path regexes are rebuilt from one shared alternation constant, and the agreement test is behavioral (each admitted extension resolves through both paths), not a parse of regex source.
- **F6 (razor)**: the statement grammar moves to a new module; `qor/scripts/plan_grep_lint.py` lands under 250 lines and `check_citation_evidence` under 40.

## Locked Decisions

**LD-1: The statement regex is the single parse point and is not rewritten; parsing is fixed by normalizing markdown span delimiters out of the block text before matching.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE '^_EVIDENCE_STMT_RE = ' -> 125:_EVIDENCE_STMT_RE = re.compile(
```

**LD-2: The demand regex admits no documentation extension today; parity is achieved by deriving both path regexes from one shared extension alternation.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE '^_FILE_LINE_RE = ' -> 109:_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
```

**LD-3: The working-tree fallback regex is the second derivation site of that constant.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE '^_WT_PATH_RE = ' -> 131:_WT_PATH_RE = re.compile(r"([\w./-]+\.(?:py|ts|tsx|sql|rs|go|js|md|json|toml))")
```

**LD-4: The reported count today is the demand set's size alone; it becomes the size of the union of parsed statements and demanded citations, per block, deduplicated by path and line.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE 'total = sum\(len\(_demand_set' -> 323:    total = sum(len(_demand_set(block)) for _, block in _ld_blocks(text))
```

**LD-5: The kind ceiling changes only in Phase 3, in the same commit as the doctrine amendment, so the ceiling contract test is green at every phase boundary.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE '^TRUTH_CHECKED_KINDS' -> 229:TRUTH_CHECKED_KINDS = ("file:line",)
```

**LD-6: The doctrine amendment must satisfy the ceiling test's parser: kind names are comma-or-and separated, backtick-stripped, and terminate at the first period, so no kind name may contain a period or comma.**

```
git show v0.146.1:tests/test_doctrine_citation_pairing.py | grep -nE '^_TRUTH_RE = ' -> 23:_TRUTH_RE = re.compile(r"truth-checked kinds?:\s*(?P<kinds>[^.\n]+)", re.IGNORECASE)
```

**LD-7: `reproduces` compares stripped full-line equality; the trailing-backtick corruption lives in the captured `observed`, not in the comparison, which is why normalization is sufficient.**

```
git show v0.146.1:qor/scripts/plan_grep_lint.py | grep -nE '^def reproduces' -> 194:def reproduces(stmt: EvidenceStatement, repo_root: Path | None = None) -> bool:
```

**LD-8: Findings report their citation as `<path>:<line>` in every code path -- one key space for demands, statements, and dedup. A statement's ref is stated in the finding's reason, never in its citation key.** (Decides the contract that PR #338 left implicit; the iteration-1 VETO's O8 two-keys-for-one-location hazard is dissolved by construction.)

**LD-9: A statement whose ref does not resolve is `evidence-unresolvable` even when nothing demands it.** The Phase 223 distinction (an environment that cannot answer is not an answer that is wrong) extends unchanged to statement-initiated adjudication; legacy test fixtures carrying illustrative fake refs are updated deliberately in Phase 2, with the updated expectations named in that phase.

## Phase 1: Normalize the markdown span stylings out of the grammar

### Affected Files

- `tests/test_plan_evidence_grammar.py` - NEW; behavioral coverage of the grammar over all three observed stylings.
- `tests/test_plan_grep_evidence_parse.py` - imports re-pointed to the new module where they name grammar internals; assertions unchanged.
- `qor/scripts/plan_evidence.py` - NEW; receives the statement grammar (`_PATH_EXT` shared extension alternation, `_EVIDENCE_STMT_RE`, `_WT_PATH_RE`, `EvidenceStatement`, `parse_evidence_statements`, `resolve_line`, `reproduces`) AND the citation-scanning and demand machinery (`_EVIDENCE_RE`, `_GIT_SHOW_RE`, `_MIGRATION_RE`, `_FILE_LINE_RE`, `_LD_HEADING_RE`, `_ANY_HEADING_RE`, `_ld_blocks`, `_sealed_citations`, `_file_line_citations`, `_demand_set`, `_statement_index`) from `plan_grep_lint.py`, unchanged except as stated below.
- `qor/scripts/plan_grep_lint.py` - retains policy only (`check_plan`, `check_citation_evidence`, `count_truth_checked`, the kind constants, `main`); everything moved is imported from `plan_evidence`.
- `qor/references/glossary.md` - the `parse_evidence_statements` home reference (line 1501) re-pointed to `qor.scripts.plan_evidence` (iteration-2 audit O2).

### Changes

`parse_evidence_statements` removes every backtick character from the block text before running `_EVIDENCE_STMT_RE.finditer`. Backticks are markdown formatting, not statement content: with them gone, the two-span styling (`` `git show ...` -> `NN:text` ``) matches the same regex the bare fenced styling already matches, and the one-span styling stops capturing its closing delimiter into `observed`. The regex itself is unchanged (LD-1). Statements without a `NN:` prefix remain unparsed and presence-only.

### Unit Tests

- `tests/test_plan_evidence_grammar.py::test_two_span_statement_parses_to_one_statement` - the styling every recent real plan uses yields one parsed statement (today: zero).
- `tests/test_plan_evidence_grammar.py::test_one_span_true_statement_reproduces` - against a tmp-git-repo fixture, a one-span statement whose line holds the quoted text reproduces (today: fails on the captured trailing backtick).
- `tests/test_plan_evidence_grammar.py::test_bare_fenced_statement_still_parses` - the styling Phase 223's fixtures use is unchanged.
- `tests/test_plan_evidence_grammar.py::test_statement_without_line_prefix_is_not_parsed` - the pre-amendment doctrine form yields zero parsed statements.
- `tests/test_plan_evidence_grammar.py::test_unresolvable_ref_is_distinct_from_wrong_text` - a fake ref resolves to None while a wrong line resolves and mismatches, preserving the Phase 223 kind distinction at the grammar layer.

## Phase 2: Adjudicate every statement and count what was examined

### Affected Files

- `tests/test_plan_grep_canonical_truth.py` - NEW; the four behaviors PR #338 specified, with LD-8 bare citation keys.
- `tests/test_plan_grep_citation_pairing.py` - the fixture reading the live module's line 97 against a pinned ref (line 92 of v0.146.1) is rewritten onto a tmp-git-repo fixture; the span-vs-path exclusion contract it guards is unchanged.
- `tests/test_plan_grep_lint_citation_evidence.py` - `test_legacy_block_satisfaction_no_longer_covers_a_file_line_citation` now expects two findings per LD-9: `evidence-unresolvable` for the fake-ref statement (`x/20240101_init.sql:1`) plus the existing `unpaired-citation` (`qor/scripts/foo.py:120`).
- `tests/test_plan_grep_lint.py`, `tests/test_doctrine_citation_pairing.py`, `tests/test_plan_text_consistency_lint_audit_wiring.py`, `qor/scripts/ci_coverage_lint.py` - caller sweep per SG-AffectedFilesContract-A; no behavioral change expected, verified by running each.
- `qor/scripts/plan_grep_lint.py` - first-class adjudication; examined-target counting; extension parity.

### Changes

In `check_citation_evidence`, every parsed statement is adjudicated on its own account: `resolve_line` None yields `evidence-unresolvable`, failed `reproduces` yields `evidence-not-reproducible`, and a reproducing statement yields nothing. The bare-citation demand loop then reports `unpaired-citation` only for demands with no statement at the same `(path, line)`; a demand whose statement exists was already adjudicated, so no duplicate finding. All findings carry `<path>:<line>` citations (LD-8). The function is restructured around a single `_adjudicate(stmt)` helper and lands under 40 lines.

`count_truth_checked` returns the per-block size of {statement targets} union {demanded citations}, deduplicated by `(path, line)` (LD-4).

`_FILE_LINE_RE` and `_WT_PATH_RE` are both built from `plan_evidence._PATH_EXT`, extended to `py|ts|tsx|sql|rs|go|js|md|json|toml|yml|yaml`. The iteration-1 audit's regression sweep (O7) verified no existing test fixture cites a documentation extension with a line number, so the widening turns no green gate red.

### Unit Tests

- `tests/test_plan_grep_canonical_truth.py::test_canonical_statement_is_truth_checked_without_bare_file_line` - a lone true statement reports count 1, zero findings.
- `tests/test_plan_grep_canonical_truth.py::test_wrong_line_is_not_reproducible` - citation key is `sample.py:3`, not `v1.0.0:sample.py:3` (LD-8).
- `tests/test_plan_grep_canonical_truth.py::test_missing_line_is_unresolvable` - line 999 of a 3-line file.
- `tests/test_plan_grep_canonical_truth.py::test_bare_citation_and_matching_statement_count_once` - union dedup, count 1, zero findings.
- `tests/test_plan_grep_canonical_truth.py::test_md_citation_enters_the_demand_set` - a bare `SKILL.md`-style citation with no statement reports `unpaired-citation` (today: invisible).
- `tests/test_plan_evidence_grammar.py::test_every_admitted_extension_resolves_through_both_paths` - parametrized over the alternation: for each extension, a tmp-repo file citation is demanded by `_FILE_LINE_RE` and its statement path is captured by `_WT_PATH_RE`; behavioral, not a parse of regex source (F5 remedy).

## Phase 3: The doctrine and the ceiling agree

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` - SG-CitationDrift-A P1 paragraph: the mandated form becomes `git show <sealed-ref>:<path> | grep -nE '<pattern>' -> NN:<exact observed text>` (the `grep -n` output line, which is what makes the statement mechanically resolvable); the kind sentences become "Truth-checked kinds: `file:line`, `grep-n evidence`. Presence-only kinds: `migration filename`, `bare git show ref-path`."
- `qor/scripts/plan_grep_lint.py` - `TRUTH_CHECKED_KINDS = ("file:line", "grep-n evidence")`, `PRESENCE_ONLY_KINDS = ("migration filename", "bare git show ref-path")`, same commit (LD-5); kind names contain no period or comma (LD-6).

### Changes

Doctrine and constants move together so `test_the_lint_ceiling_matches_the_doctrine_kinds` is green in the same commit that changes either side. No test file changes: the contract test is behavioral on both sides and simply passes once the two agree.

### Unit Tests

- `tests/test_doctrine_citation_pairing.py::test_the_lint_ceiling_matches_the_doctrine_kinds` - existing, unmodified; green is the acceptance.
- `tests/test_doctrine_citation_pairing.py::test_the_two_kind_sets_are_disjoint_and_non_empty` - existing, unmodified; guards the amendment against vacuous agreement.

## Feature Inventory Touches

None. This plan touches governance tooling (`qor/scripts/`), tests, and one doctrine; no user-touchable feature surface.

## Definition of Done

### Deliverable 1: Grammar normalization (`plan_evidence.py`)

- **D1**: One statement grammar parses all three observed markdown stylings identically; the enforcer checks the form plans actually write.
- **D2**: `parse_evidence_statements(block: str) -> list[EvidenceStatement]` in `qor/scripts/plan_evidence.py`, backtick-normalizing, regex unchanged.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file.
- **D4**: `test_two_span_statement_parses_to_one_statement` and `test_one_span_true_statement_reproduces` observed passing (both fail against v0.146.1 behavior).

### Deliverable 2: First-class statement adjudication

- **D1**: A statement is evidence on its own account; nothing needs to demand it.
- **D2**: `check_citation_evidence` adjudicates `_statement_index` entries before the demand loop; under 40 lines.
- **D3**: `docs/META_LEDGER.md` implement entry names the adjudication change.
- **D4**: `test_canonical_statement_is_truth_checked_without_bare_file_line` observed passing.

### Deliverable 3: Extension parity

- **D1**: Documentation surfaces (md, json, toml, yml, yaml) can be demanded and truth-checked like code surfaces.
- **D2**: Both regexes derive from `plan_evidence._PATH_EXT`.
- **D4**: `test_every_admitted_extension_resolves_through_both_paths` observed passing.

### Deliverable 4: Doctrine parity

- **D1**: The written contract and the shipped classification agree.
- **D2**: Doctrine P1 paragraph and both kind constants amended in one commit.
- **D4**: `test_the_lint_ceiling_matches_the_doctrine_kinds` observed passing.

### Deliverable 5: Self-verification (F4 remedy)

- **D1**: The enforcer verifies the plan that shipped it.
- **D4**: `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase225-citation-truth-driver.md --repo-root .` reports a truth-checked count of at least 7 (LD-1 through LD-7 statements) with zero findings.

### Deliverable 6: Razor compliance (F6 remedy)

- **D1**: The module the razor flagged is structurally reduced, not comment-stripped; the reduction mechanism is the Phase 1 grammar-plus-machinery move whose arithmetic is shown in the iteration-3 disposition (landing near 218 and 170 lines).
- **D2**: `qor/scripts/plan_grep_lint.py` at or under 250 lines; `qor/scripts/plan_evidence.py` at or under 250 lines; `check_citation_evidence` at or under 40 lines.
- **D4**: line counts observed in the substantiate sweep.

## CI Commands

- `python -m pytest tests/ -q` -- full suite; the new grammar, adjudication, parity, and doctrine tests plus the deliberately updated legacy expectations all green.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase225-citation-truth-driver.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase225-citation-truth-driver.md --repo-root .` -- Deliverable 5 self-verification.
