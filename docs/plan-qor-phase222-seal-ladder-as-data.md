# Plan: Seal gate ladder as data (GH #327)

**iteration**: 2 (amends iter-1 per ledger #565 VETO)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: gate ladder row
  home: qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md
- term: ladder preamble
  home: qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md

**boundaries**:
- limitations:
  - The parser reads one table in one file. It does not validate that a declared
    command exists, that a module is importable, or that a policy is honored at
    run time. Those remain the Step Prerequisites table's job and the operator's.
  - Byte savings are projected from the current ladder, not guaranteed. The
    acceptance criterion is a slack floor, not a target figure.
- non_goals:
  - Unifying the ladder table with the Step Prerequisites table. Two tables with
    one cross-consistency check is deliberate; merging them would rewrite
    `substantiate_capability.parse_step_prerequisites` and its host-capability
    consumers, which is a separate phase.
  - Extracting anything into a second load unit. Option B (`/qor-seal-gates`) and
    option A (composition) are both declined; see Locked Decision LD-2.
  - Landing any part of GH #286. This phase creates the room; it does not spend it.
- exclusions:
  - `qor-audit/SKILL.md` (463 B slack) is untouched. Its Execution-Continuity Pass
    is prose, not a ladder, and has no analogous table.

## Open Questions

1. **Does the executor prose need to restate `ABORT` per row, or once?** The table
   carries a Policy column whose value is `ABORT`, `WARN`, or `disclose`. Stating
   the halt semantics once above the table is fewer bytes; stating it per row is
   more robust to a reader who skims. Resolve during Phase 2 by checking whether
   any retargeted assertion requires the literal `ABORT` adjacent to a specific
   step (`test_seal_ladder_order.test_relocation_preserved_the_step_body` does,
   for 4.6.12). Current expectation: Policy cell value carries it, and the 4.6.12
   assertion reads the cell.

2. **Does `doc_integrity` term-drift fire on the Policy vocabulary?** `ABORT`,
   `WARN`, `disclose`, and `disclosed-skip` become column values rather than
   prose. Per the definition-pattern gotcha, a cell reading `X is Y` would be
   parsed as a divergent glossary definition. Mitigation is to keep cells as bare
   tokens with no copula. Verify by running `doc_integrity` before audit, not at
   seal.

## Locked Decisions

**LD-1: The ladder is 6,194 B, lines 227-345.**

Executed 2026-08-12 at `6424413`:

```
$ awk '/^### Step 4\.6/{f=1} /^### Step 4\.7/{f=0} f' \
    qor/skills/governance/qor-substantiate/SKILL.md | wc -c
6194

$ grep -n "^### Step 4\.6:\|^### Step 4\.7:" \
    qor/skills/governance/qor-substantiate/SKILL.md
227:### Step 4.6: Reliability Sweep (Phase 17 wiring)
346:### Step 4.7: Documentation Integrity Check (Phase 28 wiring)
```

6,194 B includes the terminating newline of line 345. The file is 39,912 B, so
the ladder is 15%.

Ten step blocks: 4.6, 4.6.5, 4.6.6, 4.6.7, 4.6.8, 4.6.9, 4.6.10, 4.6.12, 4.6.13,
4.6.14. Each has the same shape -- heading, optional prerequisite line, one or two
sentences, a fenced bash block, a rationale pointer. The regularity is what makes
the block a table that has not been written as one.

**LD-2: Composition (option A) cannot reduce the measured artifact.**

Grep-evidence, executed 2026-08-12 in the canonical `git show` form:

```
git show 6424413:qor/scripts/skill_size_budget_lint.py | grep -nE 'rglob' -> 42:    for skill in sorted(skills_root.rglob("SKILL.md")):
git show 6424413:qor/scripts/install_drift_check.py | grep -nE 'rglob' -> 24:    return sorted((repo_root / "qor" / "skills").rglob("SKILL.md"))
```

Iter-1 of this plan cited line 39 for the first of these. Line 39 holds
`if not skills_root.is_dir():`; the number had been read off an unnumbered
`sed -n '25,50p'` window and then written in `grep -n` form. VETOed at ledger
#565 and catalogued as candidate `SG-TranscribedEvidence-A`. Every evidence block
in this iteration is pasted from a run, not recalled. The corrections also went
to `docs/research-brief-open-issue-triage-2026-08-11.md` and to GH #327.

Both controls walk `qor/skills/**/SKILL.md`. The composed output would be the
governed and measured file, so composition buys nothing; keeping the fragment
outside that file makes the harness never load it. Recorded in ledger #564 and
posted to GH #327. Option B (sub-skill) is workable but adds a second load unit
and a delegation-table row for a non-lifecycle skill; ladder-as-data keeps one
load unit and improves reachability rather than trading it.

**LD-3: A machine-readable table in this exact file already has a parser.**

Grep-evidence, executed 2026-08-12:

```
git show 6424413:qor/scripts/substantiate_capability.py | grep -nE 'def parse_step_prerequisites' -> 45:def parse_step_prerequisites(skill_md: Path) -> list[PrereqRow]:
```

The Step Prerequisites table (SKILL.md lines 60-75) is already parsed as rows and
consumed by `host_capability.check_step_prerequisites`. This phase applies an
established pattern to a second table; it does not invent one.

**LD-4: The relocation-fidelity token set is derived, never enumerated.**

Iter-1 listed 16 literals in this decision and had the Phase 2 test assert
against that list. Ledger #565 VETOed it: a hand-transcribed list fails exactly
when it matters, because the same author dropping a token from the ladder drops
it from the list in the same pass. Entry #561 recorded the rule -- a test that
greps for a literal must not be the reason the grep matches -- and Phase 221
honored it by constructing `39 * 1024` rather than writing `39936`.

The token set is therefore extracted mechanically from the ladder region of the
**pinned pre-rewrite revision** `6424413`, by
`substantiate_gates.extract_ladder_tokens(text)`: every non-comment command line
inside a fenced block, unioned with every backticked span. Executed 2026-08-12:

```
$ python - <<'EOF'
# fenced non-comment command lines + backticked spans over lines 227-345
# of git show 6424413:qor/skills/governance/qor-substantiate/SKILL.md
EOF
command lines in fenced blocks: 13
backticked tokens: 42
union size: 55
```

55 tokens, not 16. Two of the ten gate commands (`install_drift_check`,
`publication_boundary_lint`) are backticked inline rather than fenced, which is
why the union rather than either half is the correct set -- and is the kind of
detail a hand list loses.

Not every token belongs in a table cell. Rationale pointers such as
`SG-DoDImplicit-A` and `qor/references/doctrine-procedural-fidelity.md`
legitimately relocate to `references/seal-gate-ladder.md`. The fidelity property
is therefore: **every extracted token survives into the ladder table or into
`references/seal-gate-ladder.md`** -- the two files Phase 2 writes. Nothing is
lost; only its destination changes.

**Superseded**: entry #559 recorded "36 of 54 asserted strings live inside the
ladder" and that count is the constraint that made option A look expensive for
three phases. It does not reproduce. Scanning `tests/*.py` for quoted literals
of >= 12 chars within three lines of an `assert` that resolve into lines 227-345
yields 30, of which most also occur outside the ladder and resolve unchanged
after the rewrite. The exact retarget count is not load-bearing under the derived
set above, which is why this iteration stops quoting one.

**LD-5: Step 4.6.11 stays absent.**

Executed 2026-08-12 at `6424413`:

```
$ grep -c "4\.6\.11" qor/skills/governance/qor-substantiate/SKILL.md
0
```

Phase 221 (ledger #563) decided the gap is the scar of GH #314 and that closing it
would erase the record of a gate that was declared and never existed. A table
invites renumbering into a dense sequence. Phase 1 ships a test that fails if
4.6.11 appears.

---

## Phase 1: The parser and its contract

### Unit Tests

- `tests/test_substantiate_gates_parser.py` — NEW.
  - `test_parse_ladder_returns_every_declared_row`: `parse_ladder` over the live
    `SKILL.md` returns rows whose step ids are exactly
    `{4.6, 4.6.5, 4.6.6, 4.6.7, 4.6.8, 4.6.9, 4.6.10, 4.6.12, 4.6.13, 4.6.14}`.
  - `test_rows_are_returned_in_ascending_numeric_order`: compares integer tuples,
    not decimal encodings, so 4.6.9 sorts before 4.6.10. (Phase 221 shipped this
    bug in its first ladder-order key and caught it against a correct ladder.)
  - `test_a_removed_row_is_detected`: given a fixture table with the
    `merge_velocity_check` row deleted, the required-gate check reports it
    missing. Without this the parser could return `[]` forever and satisfy every
    other assertion.
  - `test_a_malformed_row_raises_rather_than_being_skipped`: a row with an empty
    Command cell raises `LadderError` naming the step id. Silent skipping would
    reproduce SG-InertControl-A -- a control wired so it cannot fire.
  - `test_policy_values_are_closed`: any Policy cell outside
    `{ABORT, WARN, disclose}` raises. Open vocabulary in a gate policy column is
    how a fail-closed gate becomes advisory by typo.
  - `test_step_4_6_11_is_absent`: `parse_ladder` returns no row numbered 4.6.11,
    and the raw file contains no `4.6.11` token. Locks LD-5. The raw-token half is
    presence-shaped by nature -- the property under test IS a textual absence --
    so it carries `# prose-lint: ok=locks LD-5, the absence is the assertion`.
  - `test_extract_ladder_tokens_returns_the_pinned_baseline_count`: over
    `git show 6424413:...SKILL.md`, `extract_ladder_tokens` returns exactly 55
    tokens (13 fenced command lines + 42 backticked spans, unioned). Without a
    count assertion the extractor could return the empty set and every fidelity
    check downstream would pass vacuously.
  - `test_removing_a_command_shrinks_the_extracted_set`: deleting one fenced
    command line from a copy of the baseline text drops the extracted count by
    one. Proves the extractor reads what it claims to read.

- `tests/test_substantiate_gates_prereq_consistency.py` — NEW.
  - `test_every_ladder_module_appears_in_the_prerequisites_table`: for each row
    naming a `module:` prerequisite, `substantiate_capability.parse_step_prerequisites`
    yields a row with the same step id and module. Proves the two tables agree
    without merging them.
  - `test_a_prerequisite_drift_is_detected`: given a fixture where the ladder
    names `module:qor.scripts.secret_scanner` and the prerequisites table names a
    deliberately-truncated variant of it, the check fails. The wrong value lives
    only in `tests/fixtures/seal_ladder_prereq_drift.md`; it is not written into
    this plan, because a non-existent module path in plan prose is
    indistinguishable from a bad citation to `plan_grep_lint` and to a reader.

### Affected Files

- `qor/scripts/substantiate_gates.py` — NEW. `GateRow` frozen dataclass
  (`step: str`, `gate: str`, `command: str`, `policy: str`, `records: str`,
  `notes: str`), `LadderError`, `POLICY_VALUES` frozenset,
  `parse_ladder(skill_md: Path) -> list[GateRow]`,
  `required_gates(rows) -> set[str]`, and
  `extract_ladder_tokens(text: str) -> set[str]` (LD-4). Pure functions over
  text; no I/O beyond the single read. Modeled on
  `substantiate_capability.parse_step_prerequisites`. A `__main__` entry point
  parses the live skill and exits non-zero on `LadderError`, so the module is
  invocable as `qor-logic scripts substantiate_gates` from the ceremony.
- `tests/fixtures/seal_ladder_*.md` — NEW. Four small fixtures: `complete`,
  `row_removed`, `malformed`, `prereq_drift`. Fixtures rather than live-file
  mutation so the negative tests do not depend on repository state.

### Changes

`parse_ladder` locates the table by its header row (`| Step | Gate | Command |
Policy | Records | Notes |`), reads until the first blank line, and returns one
`GateRow` per data row with cells stripped of surrounding backticks. Step ids are
kept as strings and ordered by `tuple(int(p) for p in step.split("."))`.

---

## Phase 2: Rewrite the ladder as the table

### Unit Tests

- `tests/test_substantiate_gates_ceremony_wiring.py` — NEW.
  - `test_ceremony_parses_the_ladder_before_executing_it`: the ladder preamble
    invokes `substantiate_gates` and the invocation precedes the table's first
    row in file order. Asserts position, not presence -- a validation that runs
    after the gates it validates is not a validation.
  - `test_a_malformed_table_fails_the_ceremony_entry_point`: running the module's
    `__main__` against the malformed fixture exits non-zero. Proves the wired
    command can actually halt a seal.

- `tests/test_seal_ladder_order.py` — MODIFIED (Phase 221 file, retargeted).
  - `test_ladder_steps_appear_in_numeric_order`: reads parsed rows instead of
    `### Step` headings; same ordering property.
  - `test_no_ladder_step_sits_after_failure_scenarios`: asserts the table itself
    begins before `## Failure Scenarios`. The property Phase 221 protected --
    reachability in reading order -- is strictly stronger under a single table,
    because one position now covers all ten gates.
  - `test_relocation_preserved_the_step_body`: retargeted to the 4.6.12 row. Same
    three literals -- `execution_continuity`, `ABORT`, `inconclusive` -- read from
    the row's Command, Policy, and Records/Notes cells. Resolves Open Question 1.

- `tests/test_seal_ladder_tokens_survived.py` — NEW. The LD-4 proof obligation,
  with no hand-authored list anywhere in it.
  - `test_every_baseline_token_survives_the_rewrite`: for each token in
    `extract_ladder_tokens(git show 6424413:...SKILL.md)`, assert it appears in
    the post-rewrite ladder table or in
    `qor-substantiate/references/seal-gate-ladder.md`. The set comes from the
    pinned revision, so shrinking it requires rewriting history rather than
    editing a list.
  - `test_the_survival_check_can_fail`: given a post-rewrite fixture with one
    Command cell blanked, the same check reports the corresponding token missing.
    Without this the survival assertion could hold over an empty token set.

- Retargeted in place, same literal, now read from a parsed row:
  `test_substantiate_skill_corpus_wiring.py` (`--scope auto`,
  `install_drift_check`, `skill_corpus`), `test_substantiate_boundary_wiring.py`
  (`boundary_scope`, `publication_boundary_lint`, `references/seal-gate-ladder.md`),
  `test_dod_substantiate_wiring.py` (`qor-logic scripts dod_check`),
  `test_merge_velocity_substantiate_wiring.py`
  (`qor-logic scripts merge_velocity_check`),
  `test_skill_size_budget_substantiate_wiring.py`
  (`qor-logic scripts skill_size_budget_lint`), `test_badge_layout_config.py` and
  `test_skill_size_budget_lint.py` (`--skills-root`),
  `test_seal_intent_lock_state.py` (`intent_lock_state`),
  `test_substantiate_secret_scan_aborts_on_finding.py` (`has_hardcoded_secrets`),
  `test_substantiate_stepz_structure.py` (`### Step 4.6`).

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` — lines 227-345 replaced by:
  a ladder preamble (one fenced bash block deriving `SESSION_ID` and `PLAN_PATH`
  once, rather than 4.6 deriving one and 4.6.7 the other, and running
  `qor-logic scripts substantiate_gates --skill <this file> || ABORT` so a
  malformed table halts the seal), the six-column table, a short executor
  paragraph stating run-in-order and halt semantics, and a four-item qualifier
  list for what does not fit a cell: 4.6.8 `--override`, 4.6.10's two escape
  comments, 4.6.14's post-Step-9.5 ordering, and 4.6.11's deliberate absence.

  The parse-before-execute line is the V2 remedy from ledger #565. Without it the
  parser's only consumer is CI, and the ceremony would execute a table nothing
  had validated -- `SG-InertControl-A` in the deliverable of a plan that cites
  that family in its own argument. Cost is roughly 80 B against a 3,000 B floor.
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` — the
  per-step rationale already lives here; append the paragraphs displaced from the
  step bodies. This file is not size-bound.

### Changes

Every gate command moves into a Command cell verbatim. No command text is
reworded, because the retargeted assertions read the same literals (LD-4) and a
reworded command would fail them -- which is the intended mechanism, not a
side effect.

The 4.6.14 post-staging constraint stays adjacent to the table as a qualifier
rather than inside the Notes cell, because it is an ordering fact about a
different step (9.5) and burying a cross-step ordering constraint in a cell is
how Phase 221's defect was introduced.

---

## Phase 3: Headroom acceptance and doc surfaces

### Unit Tests

- `tests/test_substantiate_staging_gates.py` — MODIFIED. The existing
  `HEADROOM_BYTES` assertion stays. Add
  `test_ladder_rewrite_left_usable_slack`: `HEADROOM_BYTES - size >= 3000`,
  asserting the phase produced room rather than merely fitting. A phase that
  frees 24 more bytes has not addressed #327.
- `tests/test_headroom_constant_single_source.py` — unchanged; verifies no new
  hardcoded copy of the bound appears.

### Affected Files

- `qor/references/glossary.md` — entries for `gate ladder row` and
  `ladder preamble`, each with `home:` pointing at
  `qor-substantiate/references/seal-gate-ladder.md` and `referenced_by:` listing
  the SKILL.md and the new parser. Required or `doc_integrity` orphan-check fires
  at seal.
- `docs/FEATURE_INDEX.md` — no new row. `substantiate_gates` is an internal
  parser, not a `qor-logic` CLI surface; the inventory enumerates the command
  surface.
- `docs/GOVERNANCE_INDEX.md` — advance `Last Reviewed` for the seal skill entry.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/`, `qor/skills/`, `qor/references/`, and
`tests/`; it introduces no user-touchable CLI feature. `substantiate_gates` has
two consumers, both created by this plan: the Phase 1 tests, and the
parse-before-execute line the Phase 2 ladder preamble adds to the seal ceremony.
It is not a feature an operator invokes directly, so `docs/FEATURE_INDEX.md`
gains no row.

Iter-1 claimed a seal-ceremony consumer without building one; ledger #565 VETOed
it as `specification-drift`. The claim is now backed by the Phase 2 change and by
`test_ceremony_parses_the_ladder_before_executing_it`.

## Definition of Done

### Deliverable: `qor/scripts/substantiate_gates.py`

- **D1**: The seal gate ladder is readable as ordered rows by a program, so its
  order, completeness, and policy vocabulary are checkable rather than reviewable.
- **D2**: `parse_ladder(skill_md: Path) -> list[GateRow]` in
  `qor/scripts/substantiate_gates.py`; `GateRow` frozen with six string fields;
  `LadderError` raised on empty Command cell or out-of-vocabulary Policy cell.
- **D3**: Ledger entry records the pre- and post-rewrite byte sizes and the
  resulting slack; LD-4's superseding of entry #559's 36-of-54 count is stated in
  the seal entry, not only in this plan.
- **D4**: `test_a_removed_row_is_detected` fails when the `merge_velocity_check`
  row is deleted from the fixture, `test_a_malformed_row_raises_rather_than_being_skipped`
  raises `LadderError` naming the step, and
  `test_extract_ladder_tokens_returns_the_pinned_baseline_count` observes exactly
  55. All three prove the module can report rather than return empty, which a
  presence-only assertion cannot.

### Deliverable: the rewritten ladder in `SKILL.md`

- **D1**: Ten gates run in one reading order from one load unit, with room to add
  the two GH #286 layers without a relocation round.
- **D2**: Lines 227-345 replaced by preamble + table + executor + qualifiers;
  every Command cell byte-identical to the command it replaces.
- **D3**: `references/seal-gate-ladder.md` carries the displaced rationale;
  glossary entries registered with `referenced_by`.
- **D4**: `test_every_baseline_token_survives_the_rewrite` passes over the 55
  tokens extracted from pinned revision `6424413` (no list is authored),
  `test_the_survival_check_can_fail` fails on a blanked Command cell, and
  `test_ladder_rewrite_left_usable_slack` observes at least 3,000 B of headroom
  below `HEADROOM_BYTES`.

### Deliverable: preserved Phase 221 properties

- **D1**: Nothing this phase does may re-create the defect the previous phase fixed.
- **D2**: `test_seal_ladder_order.py` retargeted, not relaxed.
- **D3**: Seal entry states that 4.6.11 remains absent by decision.
- **D4**: `test_step_4_6_11_is_absent` passes, and
  `test_no_ladder_step_sits_after_failure_scenarios` passes against the table's
  position.

## CI Commands

- `python -m pytest tests/test_substantiate_gates_parser.py tests/test_substantiate_gates_prereq_consistency.py tests/test_substantiate_gates_ceremony_wiring.py tests/test_seal_ladder_order.py tests/test_seal_ladder_tokens_survived.py -q` — the new and retargeted contract
- `python -m pytest -q` — full suite; run twice for determinism per test-discipline doctrine
- `python -m qor.scripts.prose_test_lint --tests-dir tests --enforce` — ENFORCED (Phase 117; GH #174); the two presence-shaped assertions in this plan carry `# prose-lint: ok=` reasons
- `python -m qor.scripts.doc_integrity --repo-root . --strict` — glossary, orphan, and term-drift checks over the new terms (Open Question 2)
- `python -m qor.scripts.skill_size_budget_lint --skills-root qor/skills` — confirms no EXCEEDED finding
- `python -m qor.scripts.install_drift_check --host claude --scope auto` — confirms the rewritten skill is reinstalled before any local gate observation is trusted
- `python -m qor.scripts.publication_boundary_lint --repo-root .` — structural + identity
- `ruff check .` — lint

## CI Coverage Exemptions

Standing CI steps that run on every branch and are untouched by this phase. Each
is a governance or packaging control over surfaces this plan does not modify; the
plan's own CI Commands cover everything it does modify.

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
