# Plan: Phase 84 — Audit-readiness guards (pre-audit short-circuit + inverse-coverage discipline)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #81 + GH #84

**terms_introduced**:
- term: SG-PreAuditDraftSubmission-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: SG-InverseCoverageGapTaxonomy-A
  home: qor/references/doctrine-shadow-genome-countermeasures.md
- term: inverse-coverage discipline
  home: qor/references/doctrine-test-functionality.md

**boundaries**:
- limitations: the `plan_test_lint` inverse-coverage check is a keyword
  heuristic over plan prose, not an AST analysis of taxonomy source. It
  flags a plan that declares a closed-enum taxonomy yet carries no
  inverse-coverage test language; it does not parse the actual alias map.
  WARN-only at the lint layer — the binding VETO is `/qor-audit` Step 3.
  The `plan_iteration_status_lint` detection is likewise text-pattern based.
- non_goals: not adding an `iteration` field to `qor/gates/schema/plan.schema.json`
  (this repo's plans do not carry one; the lint tolerates its absence and
  still fires on the two markdown-section signals); not mechanically
  parsing taxonomy source files; not changing `plan_test_lint`'s WARN-only
  exit posture.
- exclusions: the `plan_iteration_status_lint` and `plan_test_lint` checks
  run against plan markdown only, not arbitrary repository files.

## Open Questions

None. Build shape settled from the issue bodies: two pre-audit lint
scripts plus thin skill-prose wiring, detailed prose in doctrine
references per the progressive-disclosure rule (GH #92).

## Feature Inventory Touches

Empty. This plan touches governance skills, doctrine references, and
pre-audit lint scripts under `qor/scripts/`; it introduces no `src/`
user-facing feature. `feature_inventory_touches`: `[]`.

## Design notes

Both issues target the same surface — a plan reaching `/qor-audit` in a
state that wastes an audit-iteration slot. #81 catches a plan that
declares itself not-ready; #84 catches a plan whose closed-enum taxonomy
test list is half-covered. Each is realized as a pre-audit lint script
plus skill-prose wiring. Per GH #92 progressive disclosure, detailed
detection semantics live in the lint scripts and in doctrine reference
files; the `SKILL.md` files gain only short pointers.

`plan_iteration_status_lint` is a **hard short-circuit** (exits non-zero;
`/qor-audit` aborts). `plan_test_lint`'s inverse-coverage addition is
**WARN-only**, matching the existing posture of that file — the binding
VETO is the `/qor-audit` Step 3 Test Functionality Pass.

## Phase 1: Pre-audit readiness short-circuit (GH #81)

A plan can carry an explicit pre-audit self-declaration — an
`**iteration**:` value of `draft` / `pre-audit`, an "Operator Decisions
Required Before Audit" section, or an Open Questions bullet ending
"Operator confirms before audit" — and still trigger `/qor-audit` under
the autonomous cycle, producing a foregone VETO and burning an
audit-iteration slot on a structurally not-ready plan.

### Affected Files

- `tests/test_plan_iteration_status_lint.py` - NEW. Behavior tests for the
  readiness detector and its CLI exit codes.
- `tests/test_audit_skill_iteration_lint_wiring.py` - NEW. Anchored +
  strip-and-fail test for the `/qor-audit` Step 0.3 wiring prose.
- `qor/scripts/plan_iteration_status_lint.py` - NEW. Reads a plan;
  detects the three pre-audit signals; exits non-zero on any hit.
- `qor/skills/governance/qor-audit/SKILL.md` - add Step 0.3 prose that
  runs the lint and short-circuits the audit on non-zero exit.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - add the
  `SG-PreAuditDraftSubmission-A` countermeasure entry.

### Unit Tests

- `tests/test_plan_iteration_status_lint.py`
  - `test_detects_draft_iteration_field` — write a plan with
    `**iteration**: draft (pre-audit)`; invoke `check_plan`; assert the
    returned findings list has one entry whose `signal` is
    `draft-iteration` and whose `excerpt` quotes the iteration line.
  - `test_detects_preaudit_iteration_field` — write a plan with
    `**iteration**: iter-1 (pre-audit)`; invoke `check_plan`; assert one
    finding with `signal` `draft-iteration` (the `pre-audit` substring
    triggers even when `iter-1` is present).
  - `test_detects_operator_decisions_section` — write a plan containing a
    `## Operator Decisions Required Before Audit` heading; invoke
    `check_plan`; assert one finding with `signal`
    `operator-decisions-section`.
  - `test_detects_operator_confirms_open_question` — write a plan whose
    Open Questions bullet ends `Operator confirms before audit.`; invoke
    `check_plan`; assert one finding with `signal` `operator-confirms-oq`.
  - `test_clean_plan_returns_no_findings` — write a plan with
    `**iteration**: iter-2`, `## Open Questions` body `None`, and no
    decisions section; invoke `check_plan`; assert the returned list is
    empty.
  - `test_main_exits_nonzero_and_prints_guidance_on_detection` — run
    `python -m qor.scripts.plan_iteration_status_lint --plan <draft-plan>`
    as a subprocess; assert `returncode == 1` and that stderr names the
    resolve-decisions-and-rerun guidance. This is the exit contract the
    `/qor-audit` Step 0.3 abort depends on.
  - `test_main_exits_zero_on_clean_plan` — run the CLI against a clean
    plan; assert `returncode == 0` and empty stderr.
  - `test_missing_plan_returns_empty_and_exits_zero` — invoke `check_plan`
    on a non-existent path (assert empty list) and run the CLI (assert
    `returncode == 0`): an absent plan is not a readiness failure.

- `tests/test_audit_skill_iteration_lint_wiring.py`
  - `test_step_0_3_invokes_iteration_lint_and_aborts` — read
    `qor/skills/governance/qor-audit/SKILL.md`; isolate the text under the
    `Step 0.3` section header; assert that section both invokes
    `qor.scripts.plan_iteration_status_lint` and carries the abort
    directive (`|| ABORT` and the "do NOT emit an audit gate artifact"
    clause). Pattern: anchored to the section header per
    `qor/references/doctrine-test-functionality.md`.
  - `test_step_0_3_assertion_fails_when_section_removed` — strip-and-fail
    negative: delete the `Step 0.3` section from an in-memory copy of the
    skill text; assert the Step 0.3 wiring assertion now fails, proving
    the positive test is anchored and cannot pass on a stray keyword.

### Changes

`qor/scripts/plan_iteration_status_lint.py` — new module, structured like
`qor/scripts/plan_grep_lint.py`:

```python
@dataclass(frozen=True)
class ReadinessFinding:
    plan: str
    line: int
    signal: str   # draft-iteration | operator-decisions-section | operator-confirms-oq
    excerpt: str

def check_plan(plan_path: Path) -> list[ReadinessFinding]: ...
def main(argv: list[str] | None = None) -> int:  # 0 clean, 1 on any finding
```

Detection (case-insensitive, line-scanned):
- `draft-iteration`: a line matching `**iteration**:` whose value contains
  `draft` or `pre-audit`.
- `operator-decisions-section`: a markdown heading line whose text matches
  `Operator Decisions Required Before Audit`.
- `operator-confirms-oq`: a bullet line ending `Operator confirms before
  audit` (optional trailing punctuation/whitespace).

`main` prints each finding to stderr plus a one-line guidance
("Resolve the operator-decision items, bump the plan past its pre-audit
state, then re-run /qor-audit.") and returns `1` when findings exist,
`0` otherwise. A missing plan returns `0`.

`qor/skills/governance/qor-audit/SKILL.md` — insert `Step 0.3: Pre-audit
readiness short-circuit` after Step 0 (Gate Check), before Step 0.4. The
prose runs the lint via an argv-only invocation (consistent with the
Step 0.6 lint block) and, on non-zero exit, aborts before Step 1 identity
activation: print the lint guidance, skip remaining steps, emit no audit
gate artifact (no cycle consumed). The prose states the contrast with the
WARN-only Step 0.6 lints and cites `SG-PreAuditDraftSubmission-A`.

`qor/references/doctrine-shadow-genome-countermeasures.md` — append
`## SG-PreAuditDraftSubmission-A` with Pattern / Originating recurrence /
Countermeasure / Cross-reference, matching the existing entry format.

## Phase 2: Inverse-coverage discipline for closed-enum taxonomies (GH #84)

When a plan defines a closed-enum taxonomy — a `CANONICAL_*_VALUES`
constant plus a `normalize*` function — the standard test list covers the
forward direction (every alias-map key normalizes into the canonical set)
but not the inverse (every non-gated canonical value is reachable via at
least one identity-mapping). A canonical bucket can then be unreachable
through `normalize*`, and downstream consumers querying that bucket get
zero rows.

### Affected Files

- `tests/test_plan_test_lint.py` - add inverse-coverage cases (the file
  already covers presence-only detection).
- `tests/test_inverse_coverage_skill_wiring.py` - NEW. Anchored +
  strip-and-fail tests for the doctrine section and the two skill
  pointers.
- `qor/scripts/plan_test_lint.py` - add an inverse-coverage check to
  `check_plan`.
- `qor/references/doctrine-test-functionality.md` - add the
  inverse-coverage discipline section, an Anti-patterns row, and a
  Verification-mechanisms bullet.
- `qor/skills/sdlc/qor-plan/SKILL.md` - add one Step 5 checklist item
  pointing to the doctrine section.
- `qor/skills/governance/qor-audit/SKILL.md` - add a closed-enum-taxonomy
  sub-rule to the Step 3 Test Functionality Pass.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - add the
  `SG-InverseCoverageGapTaxonomy-A` countermeasure entry.

### Unit Tests

- `tests/test_plan_test_lint.py` (additions)
  - `test_inverse_coverage_flags_taxonomy_missing_inverse` — write a plan
    that declares `CANONICAL_SOURCE_VALUES` and `normalizeSource` and has
    a forward round-trip test bullet but no inverse bullet; invoke
    `check_plan`; assert the result contains a warning whose `pattern` is
    `inverse-coverage-missing`.
  - `test_inverse_coverage_silent_when_both_directions_present` — write a
    plan declaring the same taxonomy with BOTH a forward round-trip
    bullet and an inverse coverage bullet ("every canonical value is
    reachable"); invoke `check_plan`; assert no `inverse-coverage-missing`
    warning is in the result.
  - `test_inverse_coverage_silent_when_no_taxonomy_declared` — write a
    plan with ordinary test bullets and no `CANONICAL_*_VALUES` /
    `normalize*` tokens; invoke `check_plan`; assert no
    `inverse-coverage-missing` warning fires.
  - `test_presence_only_detection_unaffected_by_inverse_check` —
    regression: re-run the existing substring-presence fixture through
    `check_plan`; assert exactly one warning still returns and its
    `pattern` is `substring-presence` (the inverse-coverage addition does
    not perturb presence-only behavior).

- `tests/test_inverse_coverage_skill_wiring.py`
  - `test_doctrine_defines_inverse_coverage_section` — read
    `qor/references/doctrine-test-functionality.md`; isolate the text
    under the inverse-coverage discipline section header; assert it
    defines both the forward and the inverse assertion and the
    gated-bucket exemption.
  - `test_doctrine_assertion_fails_when_section_removed` — strip-and-fail
    negative for the section above.
  - `test_plan_step5_and_audit_pass_cite_inverse_coverage` — read
    `qor/skills/sdlc/qor-plan/SKILL.md` and
    `qor/skills/governance/qor-audit/SKILL.md`; assert the qor-plan
    Step 5 checklist and the qor-audit Test Functionality Pass each carry
    the closed-enum-taxonomy directive anchored to their respective
    section headers.
  - `test_skill_citations_fail_when_directives_removed` — strip-and-fail
    negative for the two skill pointers above.

### Changes

`qor/scripts/plan_test_lint.py` — `check_plan` gains an inverse-coverage
pass after the presence-only scan. When the plan text contains both a
`CANONICAL_[A-Z_]*VALUES` token and a `normalize[A-Za-z_]*` token, the
plan declares a closed-enum taxonomy. The pass then scans test-description
bullets for a forward signal (round-trip / "every alias" + "canonical")
and an inverse signal ("inverse" / "every canonical value" + "reachable").
If the taxonomy is declared and the inverse signal is absent, append a
`LintWarning` with `pattern="inverse-coverage-missing"`, `line` set to the
`CANONICAL_*_VALUES` declaration line. `main` keeps its WARN-only exit
(`return 0`); the new warning prints through the existing stderr path.

`qor/references/doctrine-test-functionality.md` — add an "Inverse-coverage
discipline for closed-enum taxonomies" section: the forward and inverse
assertions, the gated-bucket exemption (fallback / runtime-checked
buckets), and the standard test pattern. Add an Anti-patterns table row
(taxonomy bucket unreachable via `normalize*`) and a Verification-
mechanisms bullet naming `plan_test_lint` + the `/qor-audit` Step 3
sub-rule.

`qor/skills/sdlc/qor-plan/SKILL.md` — add one Step 5 ("Review Plan")
checklist item: when the plan declares a closed-enum taxonomy
(`CANONICAL_*_VALUES` + `normalize*`), the test list includes BOTH the
forward round-trip and the inverse coverage assertion; cite
`qor/references/doctrine-test-functionality.md`.

`qor/skills/governance/qor-audit/SKILL.md` — add a closed-enum-taxonomy
sub-rule to the Step 3 Test Functionality Pass: a plan declaring such a
taxonomy whose test list omits the inverse-coverage assertion VETOs with
`coverage-gap` category; cite the doctrine section and
`SG-InverseCoverageGapTaxonomy-A`.

`qor/references/doctrine-shadow-genome-countermeasures.md` — append
`## SG-InverseCoverageGapTaxonomy-A` with Pattern / Originating
recurrence / Countermeasure / Cross-reference.

## CI Commands

- `python -m pytest tests/test_plan_iteration_status_lint.py -q` — Phase 1
  readiness detector behavior and CLI exit codes.
- `python -m pytest tests/test_plan_test_lint.py -q` — Phase 2
  inverse-coverage detection plus the presence-only regression.
- `python -m pytest tests/test_audit_skill_iteration_lint_wiring.py tests/test_inverse_coverage_skill_wiring.py -q` — skill-prose and doctrine wiring (anchored + strip-and-fail).
- `python -m pytest tests/ -q` — full regression suite.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase84-audit-readiness-guards.md` — plan-internal text-consistency.
