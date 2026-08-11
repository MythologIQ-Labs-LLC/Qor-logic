# Plan: seal-ladder structure (Phase 221, GH #314 residual)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: none

**boundaries**:
- limitations: Three structural defects in the seal ladder. This phase does not
  address the size pressure on `qor-substantiate`; entry #559 records why that
  remedy is larger than one phase and what it must decide.
- non_goals: No ladder extraction. No composition mechanism. No renumbering of
  the absent 4.6.11 -- that gap is the scar of GH #314 and reads as history.
  No change to any gate's semantics; only where a step sits, whether its
  declaration is checked, and where a constant is defined.
- exclusions: #320 (self-gated, entry criteria unmet -- four seals all report
  `drift_count=0`), #286, and the size remedy are out of scope.

## Open Questions

None.

## Locked Decisions

**LD-1 — Relocate 4.6.12; the move is safe because placement is unpinned.**

`git show HEAD:tests/test_substantiate_boundary_wiring.py | grep -n '4\.6\.12' -> 69:    assert "Step 4.6.12 execution-continuity" in ladder`

That assertion checks the **reference file** carries the relocated rationale, not
the step's position in the skill. No test pins where 4.6.12 sits, so the move
touches no assertion.

The defect it fixes is real and latent: the step is a fail-closed receipt gate
sitting inside `## Failure Scenarios` at 92% of the file, after the templates and
before `## Constraints`. An operator executing the ladder in order reaches 4.6.14
then 4.7 and never sees it. It has not fired only because no plan since Phase 216
has declared `execution_continuity`.

Destination is between 4.6.10 and 4.6.13, restoring numeric order.

**LD-2 — The sweep asserts resolvability, not a fixed list.**

`git show HEAD:qor/skills/governance/qor-substantiate/SKILL.md | grep -oE 'module:[A-Za-z_][A-Za-z0-9_.]*' | sort -u | wc -l -> 12`

Phase 217 measured 12 declarations resolving 12 and used that to disprove GH
#314's premise. The check was never made standing.

It must assert **every declared prerequisite imports**, derived from the skill
text at run time. A hardcoded list of expected modules would pass while the skill
declared something new and absent -- the failure this closes, reintroduced in the
test.

**LD-3 — One definition for the headroom bound.**

`git show HEAD:tests/test_substantiate_staging_gates.py | grep -n 'HEADROOM_BYTES' -> 52:HEADROOM_BYTES = 39 * 1024  # Phase 178 (GH #266): keep >= 1 KB under EXCEEDED`

Three test files hardcode `39936`, all three added by me in Phases 217, 219, and
220 while wiring a step into the constrained file. Tuning `HEADROOM_BYTES` would
leave three copies silently disagreeing.

They import the canonical constant instead. This is `SG-SingleEntryPointGuard-A`
in its simplest form and the cheapest possible instance to fix.

**LD-4 — The size remedy is deferred, not forgotten.**

Entry #558 predicted a structural remedy would be needed. Entry #559 records that
the extraction is blocked by 36 in-ladder assertions and the absence of any
composition mechanism, and names the three options a future phase must choose
between.

Deferring with the analysis recorded is the honest outcome of investigating a
prediction and finding the remedy larger than expected. Shipping a partial
extraction under time pressure would be the half-measure this repository has
spent five phases removing.

**Tracked at GH #327**, filed before re-audit rather than named as an intention.
It carries the three options with their tradeoffs and entry criteria that
explicitly refuse to open it in response to a size breach -- because three phases
have now each resolved a breach under time pressure and each resolution made the
next one harder.

A ledger entry records what was decided; it is not a worklist. The Judge
sustained exactly this ground against Phase 217, and that VETO was cleared by
filing GH #320 before re-audit. The same standard applies here, and applying a
weaker one because this deferral is well-argued would make the rule depend on how
good the prose is.

**LD-5 — Counterfactual tests.**

Per Phase 218 LD-5, 219 LD-6, 220 LD-5. Each fix ships a test that fails against
`HEAD`: the ladder must be in order, every declared module must import, and the
constant must have one definition.

## Phase 1: Ladder order

### Unit Tests

- `tests/test_seal_ladder_order.py::test_ladder_steps_appear_in_numeric_order` -
  the counterfactual. Extracts `### Step 4.6.x` headings in file order and
  asserts the numeric sequence is non-decreasing. Fails at HEAD, where 4.6.12
  follows 4.6.14.
- `::test_no_ladder_step_sits_after_failure_scenarios` - the sharper assertion.
  A gate positioned after `## Failure Scenarios` is unreachable to a reader
  following the ladder, whatever its number.
- `::test_relocation_preserved_the_step_body` - the moved step keeps its
  fail-closed language, so a move cannot silently become a rewrite.

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - 4.6.12 moved between
  4.6.10 and 4.6.13. Size measured before and after; a pure move is size-neutral
  and any delta is a mistake.
- `tests/test_seal_ladder_order.py` - NEW.

## Phase 2: Prerequisite sweep

### Unit Tests

- `tests/test_step_prerequisites_resolve.py::test_every_declared_module_imports` -
  the counterfactual against the defect GH #314 was filed about. Parses
  `module:<dotted.path>` from the skill and asserts each imports. Would have
  failed when `instruction_hygiene_lint` was declared.
- `::test_declarations_are_discovered_not_hardcoded` - asserts the parse finds
  the declarations actually present, so the test cannot pass by checking a stale
  list while the skill declares something new.
- `::test_a_fabricated_declaration_is_caught` - feeds the parser a skill body
  naming a nonexistent module and asserts it reports. Proves the check can fail.

### Affected Files

- `tests/test_step_prerequisites_resolve.py` - NEW.

### Changes

A test rather than a lint module: the declarations live in skill text, the
assertion is a repository invariant, and the suite already runs on every seal and
every CI job. A separate CLI would add a surface with no second caller.

## Phase 3: One constant

### Unit Tests

- `tests/test_headroom_constant_single_source.py::test_no_hardcoded_headroom_literals` -
  the counterfactual. Greps the test tree for the literal and asserts only the
  canonical definition contains it. Fails at HEAD with three occurrences.

### Affected Files

- `tests/test_substantiate_skill_corpus_wiring.py`,
  `tests/test_substantiate_boundary_wiring.py`,
  `tests/test_seal_intent_lock_state.py` - import `HEADROOM_BYTES`.
- `tests/test_headroom_constant_single_source.py` - NEW.

## Phase 4: Verification

### Unit Tests

- The three new modules, run twice.
- The full suite.
- `skill_size_budget_lint`; `qor-substantiate` unchanged in size by a pure move.
- `dist_compile` zero-drift.

## Definition of Done

### Deliverable: the ladder is reachable and checked

- **D1**: An operator reading the ladder in order encounters every gate,
  including the execution-continuity receipt gate.
- **D2**: 4.6.12 sits between 4.6.10 and 4.6.13; a standing test asserts every
  `module:` declaration imports.
- **D3**: Seal entry records that 4.6.12 was stranded by my own Phase 216 edit
  and that the sweep was proposed in Phase 217 and never shipped.
- **D4**: `test_ladder_steps_appear_in_numeric_order` and
  `test_every_declared_module_imports` both fail against `HEAD`.

### Deliverable: one definition for one bound

- **D1**: Tuning the headroom bound changes it everywhere.
- **D2**: Three files import `HEADROOM_BYTES`; no test hardcodes the literal.
- **D3**: Seal entry records that all three copies were introduced by me while
  wiring steps under size pressure.
- **D4**: `test_no_hardcoded_headroom_literals` fails against `HEAD`.

### Deliverable: nothing is weakened

- **D1**: No gate changes semantics; a move is a move.
- **D2**: `qor-substantiate` byte size is unchanged by Phase 1.
- **D3**: Seal entry records the deferred size remedy, its three options, and
  the issue tracking it (GH #327).
- **D4**: Full suite green; no existing assertion edited except the three
  literal-to-import substitutions, which assert the same bound.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Seal-ladder order invariant | NEW | `tests/test_seal_ladder_order.py` | `test_ladder_steps_appear_in_numeric_order` asserts ladder headings are non-decreasing |
| Step-prerequisite resolvability | NEW | `tests/test_step_prerequisites_resolve.py` | `test_every_declared_module_imports` asserts each declared module imports |

## CI Commands

- `python -m pytest tests/test_seal_ladder_order.py tests/test_step_prerequisites_resolve.py tests/test_headroom_constant_single_source.py -q` — the counterfactual tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new tests are lint clean.
- `qor-logic scripts skill_size_budget_lint --skills-root qor/skills` — `qor-substantiate` stays under the lock.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase221-seal-ladder-structure.md` — this plan asserts each path and command identically at every site.
