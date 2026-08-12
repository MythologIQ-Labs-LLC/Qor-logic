# Plan: Grep-evidence truth check (GH #330)

**iteration**: 4 (amends iter-3 per ledger #572 VETO)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: evidence statement
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: unpaired citation
  home: qor/references/doctrine-shadow-genome-countermeasures.md

**boundaries**:
- limitations:
  - Only the `file:line` citation kind is truth-checked. A migration filename and
    a bare `git show <ref>:<path>` carry no line to verify, so they keep the
    existing block-level presence behavior. The CLI prints which kinds were
    truth-checked and which were only counted.
  - The check verifies that a cited line holds the quoted text. It cannot verify
    that the text supports the claim the Locked Decision draws from it. Iteration
    1 of this plan demonstrated the gap: LD-3 cited a line correctly and drew a
    conclusion the line does not carry (ledger #570, F4).
  - Pairing is scoped to the whole Locked-Decisions region, not to an individual
    LD. See non_goals.
  - Evidence resolved against the working tree (no `git show` prefix) is checked
    against the tree at lint time, not as of authoring.
- non_goals:
  - **Per-LD pairing granularity.** A citation under LD-5 can be satisfied by a
    statement under LD-1. Narrowing further requires LD-level block boundaries,
    and LD-1..LD-6 are bold spans rather than markdown headings, so
    `_ANY_HEADING_RE` yields one block for the whole region. Changing that means
    changing the LD authoring convention across every existing plan, which is a
    separate phase. Recorded as ledger #570 F15 rather than silently inherited.
  - Promoting the lint to a binding VETO. It stays WARN at `/qor-audit` Step 0.6.
  - Retroactive sweeps of sealed plans.
  - Changing the **behavior** of `check_plan`'s module-path and skill-path
    warnings. Their construction sites do change: `LintWarning.kind` is a
    required field with no default, so all three producers name their kind.
    Iteration 2 declared a blanket non-goal that collided with the required
    field and left the default undeclared (#571 V2). A required field with
    honest values beats an optional one with a meaningless default, so the
    two sites gain `kind="module-path-missing"` and `kind="skill-path-missing"`
    and emit the same findings they do today.
- exclusions:
  - `qor-audit/SKILL.md` is untouched; `--repo-root` is already passed there.
  - `main()`'s output stream is untouched. It writes to `sys.stderr` today and
    continues to; iteration 1's Definition of Done wrongly said stdout (#570 F5).

## Open Questions

1. **Does the span-based exclusion mask a legitimate prose citation?** Phase 2
   drops any citation whose character span falls inside a parsed evidence
   statement, otherwise every statement would demand a statement of its own. The
   risk is that a plan citing `foo.py:12` in prose while a statement covers
   `foo.py:97` has its prose citation silently exempted. Phase 2's
   `test_a_prose_citation_is_still_checked_when_the_same_path_appears_in_a_statement`
   resolves it by proving the exclusion is span-based rather than path-based.

2. **Does the reason wording constrain the implementation?** Yes, and the
   constraint is now known rather than discovered: the existing suite asserts
   `"evidence" in f.reason.lower()`. All three new finding kinds must keep the
   word "evidence" in their operator-facing reason, or an undeclared test breaks.
   Enumerated in Phase 2 Affected Files.

## Locked Decisions

**LD-1: The lint verifies the shape of an evidence statement, not its content.**

In-scope citation: `qor/scripts/plan_grep_lint.py:97`.

Grep-evidence, executed 2026-08-12 at `2d356ec` (pattern chosen to match exactly
one line):

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_EVIDENCE_RE = re.compile' -> 97:_EVIDENCE_RE = re.compile(r"grep\b.*->")
```

The predicate is a `grep` token and an arrow on one line. Nothing reads the path,
the line number, or the observed text.

Iteration 1 cited the bare name `_EVIDENCE_RE`, which matches two lines; the
statement showed one without marking the omission (#570 F13). Every pattern in
this iteration was checked for match count before being quoted.

**LD-2: Satisfaction is block-level, so one statement covers every citation in the
region.**

In-scope citations: `qor/scripts/plan_grep_lint.py:134`,
`qor/scripts/plan_grep_lint.py:140`.

Grep-evidence, executed 2026-08-12 at `2d356ec`:

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE 'def check_citation_evidence' -> 134:def check_citation_evidence(text: str, plan: str = "<plan>") -> list[LintWarning]:
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE 'if _EVIDENCE_RE.search' -> 140:        if _EVIDENCE_RE.search(block):
```

Line 140 guards a `continue` that skips the whole block.

Iteration 1 asserted this from an unrecorded synthetic experiment -- three
citations enumerated, four claimed extracted, nothing committed to re-run (#570
F8). The experiment is now `tests/fixtures/evidence_block_level_gap.md`, authored
in Phase 1 and asserted in Phase 2, so the claim has a subject a reader can
execute. LD-6 forbids citing an unrecorded counterfactual; iteration 1 did it
four decisions earlier in the same document.

**LD-3: The doctrine specifies per-LD pairing. This phase tightens it to
per-citation, and amends the doctrine to say so.**

Grep-evidence, executed 2026-08-12 at `2d356ec`. `grep -oE` is used so the
observation is the command's complete output rather than a fragment of a long
line.

**Two disclosures iteration 2 omitted (#571 A1).** Both patterns are ERE
literals, so `grep -oE` echoes the pattern back: the text right of the arrow
equals the text left of it, and a misquote is undetectable by inspection --
only by execution. And a `-oE` statement carries no line number, so
`_EVIDENCE_STMT_RE` does not parse it and this plan's own check never resolves
it. These statements are executable evidence, not parseable evidence, and D3
scopes accordingly.

```
git show 2d356ec:qor/references/doctrine-shadow-genome-countermeasures.md | grep -oE 'every LD citing sealed infrastructure MUST carry a paired grep-evidence statement' -> every LD citing sealed infrastructure MUST carry a paired grep-evidence statement
git show 2d356ec:qor/references/doctrine-shadow-genome-countermeasures.md | grep -oE 'whose block carries no grep-evidence statement' -> whose block carries no grep-evidence statement
```

**The contract is per-LD: one statement per LD, not one per citation.** Iteration
1 titled this decision "the doctrine already specifies per-citation pairing" and
quoted the line partially, dropping the enforcement clause that the second
statement above now quotes directly. That truncation was the binding V1 finding,
and the dropped text is exactly what disproves the claim the truncated quote was
used to support (#570 V1, F4). Iteration 2 then asserted an unpaired
character-count figure while fixing a quoting defect, and measurement showed it
wrong. Every such figure is dropped rather than repaired, because none was
load-bearing (#571 A2). Iteration 3's first draft kept the numbers inside the
sentence disclosing them, which left one unpaired assertion in the paragraph
that exists to retire unpaired assertions; caught in pre-audit verification.

So this phase does not close an implementation gap. It **changes the contract**
from per-LD to per-citation, and Phase 3 amends the doctrine paragraph
accordingly. That is a larger claim than iteration 1 made and it is the honest
one.

**LD-4: The checkable citation kind is already parsed; the others are not
checkable by construction.**

In-scope citations: `qor/scripts/plan_grep_lint.py:99`,
`qor/scripts/plan_grep_lint.py:101`.

Grep-evidence, executed 2026-08-12 at `2d356ec` (both patterns single-match):

```
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_GIT_SHOW_RE = re.compile' -> 99:_GIT_SHOW_RE = re.compile(r"git show\s+\S+:\S+")
git show 2d356ec:qor/scripts/plan_grep_lint.py | grep -nE '_FILE_LINE_RE = re.compile' -> 101:_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
```

`_FILE_LINE_RE` yields a path and a line number as one token; a caller splits on
the final colon. `_GIT_SHOW_RE` yields a revision and a path but no line, so it
is presence-only by construction rather than by choice. Note the extension set:
`.md` paths are not `file:line` citations, so a `SKILL.md:158` reference is
outside the truth-checked kind.

**LD-5: The invocation site needs no change, and the headroom claim is measured.**

Grep-evidence, executed 2026-08-12 at `2d356ec`:

```
git show 2d356ec:qor/skills/governance/qor-audit/SKILL.md | grep -nE 'plan_grep_lint' -> 158:qor-logic scripts plan_grep_lint --plan "$PLAN_PATH" --repo-root . || true
```

Measurement, executed 2026-08-12 at `2d356ec`. Not grep-evidence -- it carries no
`grep` token and no line, so neither predicate parses it, and iteration 2 filed it
under a grep-evidence header (#571 A4):

```
git show 2d356ec:qor/skills/governance/qor-audit/SKILL.md | wc -c -> 39473
```

`--repo-root` is already passed and `|| true` already declares the WARN posture,
so the skill file is untouched. At 39,473 B against the canonical
`HEADROOM_BYTES` of 39 * 1024, that leaves 463 B -- the figure iteration 1
asserted without evidence (#570 F12), now paired.

**LD-6: The counterfactual must be authored, not recovered.**

This is an observation, not a grep-evidence statement; it carries no line number
and is labelled as such rather than counted toward D3 (#570 F14).

```
$ git log --oneline --all -- docs/plan-qor-phase222-seal-ladder-as-data.md
85a9077 seal: phase 222 - seal gate ladder as data (v0.145.0)
```

One commit. The iteration-1 text carrying the false line number was never
recorded. GH #330 and ledger #569 both claimed otherwise and are corrected.

**LD-7: This plan is now in scope for the check it proposes.**

Iteration 1's Locked Decisions contained **zero** `file:line` citations -- every
one was the `git show` kind the plan itself exempts -- so the check was inert on
the document proposing it, and the CI command offered as self-validation
validated nothing (#570 V3, catalogued as candidate `SG-VacuousSelfValidation-A`).
That inertness is how V1 survived authoring.

This iteration carries **five in-scope `file:line` citations**, each paired with
a statement naming the same path and line:

| citation | paired statement in |
|---|---|
| `qor/scripts/plan_grep_lint.py:97` | LD-1 |
| `qor/scripts/plan_grep_lint.py:99` | LD-4 |
| `qor/scripts/plan_grep_lint.py:101` | LD-4 |
| `qor/scripts/plan_grep_lint.py:134` | LD-2 |
| `qor/scripts/plan_grep_lint.py:140` | LD-2 |

The count is stated so that a self-validation run producing zero findings is
distinguishable from one with nothing to check. Per the Shadow Genome remedy: a
command that exits 0 on an empty subject set is indistinguishable from one that
exits 0 on a verified one.

**Five distinct pairs, ten occurrences (#571 V1).** `_sealed_citations` uses
`finditer` and does not deduplicate, and this table restates all five citations
inside the region, so raw extraction yields ten. Phase 2 therefore **deduplicates
the demand set by `(path, line)` before pairing**, and the reported count is of
distinct pairs. Without that, the table built to make an empty run
distinguishable from a verified one would itself break the number expressing it
-- the V3 remedy reproducing the V3 pattern.

Deduplication, not span exclusion, is what reduces ten to five here. The span
rule is exercised only by `tests/fixtures/evidence_true.md`, never by this plan's
own content, which is why Open Question 1's fixture is the sole coverage for it.

---

## Phase 1: Parse and resolve an evidence statement

### Unit Tests

- `tests/test_plan_grep_evidence_parse.py` — NEW.
  - `test_parses_a_git_show_evidence_statement`: returns one `EvidenceStatement`
    with `ref="2d356ec"`, the path, `line=97`, and the observed text stripped of
    its `97:` prefix.
  - `test_parses_a_working_tree_evidence_statement`: a `grep -n <pattern> <path> -> NN:text`
    form with no `git show` prefix yields `ref=None` and the same fields.
  - `test_a_statement_without_an_observation_is_not_parsed`: `grep foo -> bar`
    with no `NN:` observation returns no statement. It satisfies the legacy shape
    predicate and must not be mistaken for a verifiable one.
  - `test_a_grep_o_statement_is_not_parsed_as_file_line`: the `grep -oE ... -> text`
    form used in LD-3 carries no line number and yields no `EvidenceStatement`.
    Without this the parser might invent a line from a substring match.
  - `test_resolve_line_reads_the_named_revision_not_head`: `resolve_line` for
    `qor/skills/governance/qor-substantiate/SKILL.md` line 250 returns
    `### Step 4.6.5: Secret-scanning gate (Phase 56 wiring)` at `6424413` and a
    ladder table row at `2d356ec`. The `2d356ec` half was verified by the independent
    reviewer; the `6424413` half by the Judge's own shell run during the
    iteration-2 audit, recorded at line 170 of
    `.agent/staging/phase223-iter1-AUDIT_REPORT.md`. The reviewer explicitly
    declined to assert the ancestor half, and iteration 3 credited it anyway
    (#572 A1). Note the structural gap this sits in (#571 A5): it is a
    `path:line:revision -> exact text` claim on a `.md` path, which is outside
    `_FILE_LINE_RE`'s extension set, so this plan's own machinery will never
    check it. The test is its only guard. Two revisions, one path, one line, materially
    different content — so a `resolve_line` that ignored `ref` and read HEAD
    would fail. Iteration 1 pinned this to a line no phase committed to changing,
    which made the guarantee vacuous (#570 F9).
  - `test_resolve_line_returns_none_for_an_unresolvable_path`: a path absent at
    the cited ref yields `None` rather than raising.
  - `test_reproduces_compares_stripped_text`: indentation differences between the
    quoted observation and the file line pass; a changed token fails.

- `tests/fixtures/evidence_*.md` — NEW. Five Locked-Decision regions: `true`
  (statement reproduces), `false_line` (right path, wrong line), `unresolvable`
  (path absent at ref), `unpaired` (citation with no statement of its own beside
  a sibling that has one), `block_level_gap` (LD-2's experiment: one true
  statement plus three citations at `:999`, `:12345`, and `:4`), and
  `duplicate_citation` (`foo.py:12` three times against one statement, plus
  `foo.py:97` once, so both the dedup and the do-not-over-merge assertions have a
  subject).

### Affected Files

- `qor/scripts/plan_grep_lint.py` — add `EvidenceStatement` frozen dataclass
  (`ref: str | None`, `path: str`, `line: int`, `observed: str`),
  `_EVIDENCE_STMT_RE`, `parse_evidence_statements(block) -> list[EvidenceStatement]`,
  `resolve_line(stmt, repo_root) -> str | None`, and
  `reproduces(stmt, repo_root) -> bool`. Pure functions plus one `git show`
  subprocess in list-form argv.

### Changes

`resolve_line` reads `git show <ref>:<path>` when `ref` is set and the working
tree otherwise, then returns the 1-indexed cited line or `None`. `reproduces`
compares `observed.strip()` against that line stripped.

---

## Phase 2: Pair each citation with its own evidence

### Unit Tests

- `tests/test_plan_grep_citation_pairing.py` — NEW.
  - `test_a_citation_whose_evidence_reproduces_passes`: the `true` fixture yields
    no findings.
  - `test_a_false_line_number_is_reported`: the `false_line` fixture yields one
    `evidence-not-reproducible` finding naming the path, the cited line, and both
    the quoted and actual text. This is iteration 1's own V1 defect reproduced
    deliberately, since it was never committed.
  - `test_an_unpaired_citation_is_reported`: the `unpaired` fixture yields one
    `unpaired-citation` finding for the citation lacking its own statement and
    none for the sibling that has one.
  - `test_the_block_level_gap_is_closed`: the `block_level_gap` fixture — which
    the legacy check passes with zero findings — now yields three
    `unpaired-citation` findings. LD-2's claim, executable.
  - `test_an_unresolvable_path_is_its_own_finding_kind`: the `unresolvable`
    fixture yields `evidence-unresolvable`, distinct from
    `evidence-not-reproducible`.
  - `test_a_citation_inside_an_evidence_statement_does_not_demand_its_own`: the
    `true` fixture's `git show <ref>:<path>` span is excluded from the demand set.
  - `test_a_prose_citation_is_still_checked_when_the_same_path_appears_in_a_statement`:
    a block citing `foo.py:12` in prose while a statement covers `foo.py:97`
    reports the prose citation as unpaired. Proves the exclusion is span-based,
    not path-based. Resolves Open Question 1.
  - `test_every_citation_evidence_reason_contains_the_word_evidence`: all three
    citation-evidence kinds keep
    "evidence" in their reason. Resolves Open Question 2 and protects
    `test_check_plan_merges_citation_findings` in the suite below.
  - `test_non_file_line_kinds_keep_block_level_behavior`: a block whose only
    citation is a migration filename, with any statement present, yields no
    finding.
  - `test_the_pairing_check_can_report_nothing_and_still_be_running`: a block with
    zero citations yields zero findings AND `parse_evidence_statements` is
    observed to have returned a non-empty list, so a parser that silently
    returned `[]` cannot satisfy the suite.
  - `test_a_repeated_citation_is_counted_once`: the `duplicate_citation` fixture
    names `foo.py:12` three times -- once in prose, twice in a restating table --
    against a single paired statement. The reported truth-checked count is **1**,
    not 3, and findings are zero. Fails if dedup is absent, which is the only
    assertion in the suite that can distinguish a correct implementation from one
    reporting the raw occurrence count (#572 V1).
  - `test_dedup_does_not_merge_distinct_lines_in_one_file`: a fixture citing
    `foo.py:12` and `foo.py:97`, each paired, reports **2**. Guards the inverse --
    a dedup keyed on path alone would collapse them and pass the test above.
  - `test_the_ceiling_names_both_truth_checked_and_presence_only_kinds`: running
    the CLI over the `false_line` fixture writes both classifications to
    `sys.stderr`. Moved here from Phase 3 because Phase 2 ships the output
    (#570 F10).

- `tests/test_plan_grep_lint_citation_evidence.py` — MODIFIED. The suite iteration
  1 omitted (#570 V2). All seven assertions survive the pairing contract; each is
  re-run and its continued validity stated rather than assumed:

  | test | under pairing | why |
  |---|---|---|
  | `test_flags_sealed_citation_without_evidence` | unchanged | migration + git-show citations, no statement — still flagged |
  | `test_no_finding_when_evidence_present` | unchanged | carries two presence-only kinds -- a migration filename and a git-show ref -- and its statement has no `NN:` observation, so survival depends on `_EVIDENCE_RE` being retained as the presence predicate (see Changes) |
  | `test_no_finding_without_ld_region` | unchanged | it does contain `qor/scripts/x.py:42`, but outside any LD region, so no block is scanned |
  | `test_file_line_citation_in_ld_flagged` | unchanged assertion, new kind | `foo.py:120` with no statement becomes `unpaired-citation`; the assertion reads `f.citation` |
  | `test_check_plan_merges_citation_findings` | unchanged | constrains reason wording — see Open Question 2 |
  | `test_attribution_12g_cross_iteration_regression` | unchanged | migration kind |
  | `test_main_warn_only_but_reports_citation` | unchanged | exit 0 preserved; WARN posture unchanged |

  Added: `test_legacy_block_satisfaction_no_longer_covers_a_file_line_citation` —
  the behavior change stated as its own assertion rather than left implicit in
  seven unchanged ones.

- `tests/test_plan_grep_lint.py` — NOT MODIFIED. It contains no citation-evidence
  assertions; iteration 1 named it in error (#570 V2).

### Affected Files

- `qor/scripts/plan_grep_lint.py` — rewrite `check_citation_evidence` to pair per
  citation, deduplicating the demand set by `(path, line)`. `LintWarning` gains a
  required `kind` field with no default; every `reason` retains the word
  "evidence". `main()` gains the ceiling line, written to `sys.stderr` alongside
  the existing output.
- `qor/scripts/plan_grep_lint.py` lines 70-74 and 85-89 — the two `check_plan`
  construction sites gain `kind="module-path-missing"` and
  `kind="skill-path-missing"`. Declared because a required field reaches every
  producer (#571 V2); both are keyword-arg constructions, so this is one added
  argument each and no behavior change. Five kinds exist in total: these two plus
  the three citation-evidence kinds.

### Changes

Citations are collected with character spans; any citation falling inside a
parsed statement's span is dropped from the demand set. **The remainder is then
deduplicated by `(path, line)`, and the deduplicated set is both what gets paired
and what the reported count counts.** Remaining `file:line`
citations are looked up by `(path, line)`: a miss is `unpaired-citation`, a hit
that does not reproduce is `evidence-not-reproducible`, a hit whose path will not
resolve is `evidence-unresolvable`. Migration and bare git-show citations keep the
block-level presence rule, **satisfied by the legacy `_EVIDENCE_RE` predicate**,
not by `parse_evidence_statements`. Iteration 2 left this unstated (#571 V3) and
the choice is decisive: `_LD_WITH_EVIDENCE` in the declared suite carries a
statement with no `NN:` observation, so the new parser returns nothing for it and
`test_no_finding_when_evidence_present` would fail. Retaining `_EVIDENCE_RE` for
the presence-only kinds is what makes that row survive.

---

## Phase 3: Doctrine and glossary

### Unit Tests

- `tests/test_doctrine_citation_pairing.py` — NEW.
  - `test_the_lint_ceiling_matches_the_doctrine_kinds`: parses the truth-checked
    and presence-only kind lists out of the amended doctrine paragraph, runs the
    CLI over the `false_line` fixture, and asserts the two agree. Behavioral on
    both sides — a doctrine edit that drifts from the shipped classification
    fails. Iteration 1's version asserted only that the paragraph contained
    certain wording, which could not fail on a behavior break (#570 F11).

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` — amend the P1
  paragraph: state that pairing is per-citation for the `file:line` kind, name
  the three citation-evidence finding kinds, and name the presence-only ceiling for the migration
  and git-show kinds.
- `qor/references/glossary.md` — entries for `evidence statement` and
  `unpaired citation`.
- `docs/GOVERNANCE_INDEX.md` — advance `Last Reviewed`.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/`, `qor/references/`, `docs/`, and `tests/`;
it introduces no user-touchable CLI feature. `plan_grep_lint` already has a
`qor-logic scripts plan_grep_lint` entry point and its surface is unchanged --
same flags, same exit codes, more findings.

## Definition of Done

### Deliverable: evidence-statement parsing and resolution

- **D1**: A grep-evidence statement becomes a value a program can resolve against
  the revision it names.
- **D2**: `EvidenceStatement`, `parse_evidence_statements`, `resolve_line`, and
  `reproduces` in `qor/scripts/plan_grep_lint.py`; `git show` invoked list-form.
- **D3**: LD-1, LD-2, LD-4 carry parseable grep-evidence -- single-match patterns
  with `NN:` observations that `_EVIDENCE_STMT_RE` resolves. LD-3 carries two
  `-oE` statements that are executable but not parseable, disclosed as such.
  LD-5 carries one parseable statement plus one measurement labelled separately.
  LD-6 is an observation. Every category is named rather than counted as one.
- **D4**: `test_resolve_line_reads_the_named_revision_not_head` observes two
  materially different lines for one path at two revisions, and
  `test_a_statement_without_an_observation_is_not_parsed` rejects a legacy-shaped
  statement carrying nothing to verify.

### Deliverable: per-citation pairing

- **D1**: Every `file:line` citation in a Locked Decision is backed by its own
  reproducible evidence.
- **D2**: `check_citation_evidence` pairs by `(path, line)`; `LintWarning.kind`
  carries one of five values -- the three citation-evidence kinds plus
  `module-path-missing` and `skill-path-missing`; every reason retains "evidence".
- **D3**: The doctrine's P1 paragraph states per-citation pairing for the checkable
  kind and the ceiling for the rest; the seal entry records the in-scope subject
  count this plan presented to its own check.
- **D4**: `test_the_block_level_gap_is_closed` turns LD-2's fixture from zero
  findings to three, `test_a_false_line_number_is_reported` fails the `false_line`
  fixture, and `test_the_pairing_check_can_report_nothing_and_still_be_running`
  prevents an empty-parser pass.

### Deliverable: the plan is in scope for its own check

- **D1**: The self-validation command has a subject, and the subject count is
  stated so an empty run is distinguishable from a verified one.
- **D2**: Five distinct `(path, line)` pairs in the Locked Decisions, each
  paired; ten raw occurrences, because LD-7's table restates each one.
- **D3**: LD-7 tabulates citation to statement; the seal entry records the count.
- **D4**: `plan_grep_lint --plan docs/plan-qor-phase223-grep-evidence-truth.md --repo-root .`
  reports **five distinct `(path, line)` pairs** truth-checked and zero findings.
  Five is the post-dedup count; raw extraction yields ten because LD-7's table
  restates each citation. A run reporting zero truth-checked citations fails this
  criterion even at exit 0.

## CI Commands

- `python -m pytest tests/test_plan_grep_evidence_parse.py tests/test_plan_grep_citation_pairing.py tests/test_plan_grep_lint_citation_evidence.py tests/test_doctrine_citation_pairing.py -q` — the new and retargeted contract
- `python -m pytest -q` — full suite; run twice for determinism
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase223-grep-evidence-truth.md --repo-root .` — this plan against its own new check; must report five distinct truth-checked `(path, line)` pairs, not zero
- `python -m qor.scripts.prose_test_lint --tests-dir tests --enforce` — ENFORCED (Phase 117)
- `python -m qor.scripts.doc_integrity --repo-root . --strict` — glossary and term-drift over the new terms
- `python -m qor.scripts.publication_boundary_lint --repo-root .` — structural + identity
- `ruff check .` — lint

## CI Coverage Exemptions

Standing branch-wide controls over surfaces this phase does not modify.

- `test_packaging_install.py` — nightly packaging smoke
- `dependency_admission_lint` — this plan adds no dependency
- `gate_chain_completeness` — sealed-phase gate-chain sweep
- `ledger_base_currency` — ledger base-ref currency
- `seal_entry_check` — post-seal entry consistency
- `gate_provenance` — provenance attestation and sidecar verification
- `github_surface` — publication boundary over the GitHub surface
- `seal_artifacts` — seal-artifact currency
- `status_json` — checker self-test
- `ruff check qor/ tests/` — covered by this plan's `ruff check .`
- `check_variant_drift.py` — per-host variant drift
- `ledger_hash.py verify` — chain verification
