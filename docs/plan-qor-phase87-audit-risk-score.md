# Plan: Phase 87 — Author-momentum risk auto-dispatch (GH #82)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #82

**boundaries**:
- limitations: the V1 risk score implements GH #82's two mechanically
  deterministic signals (config-file citation; high citation surface). The
  config-cite signal is a path-pattern grep over the whole plan — it can
  over-fire on a plan that merely discusses config files rather than citing
  one. Over-firing dispatches an extra independent review, which is the safe
  direction (a false positive costs one review; a false negative ships an
  unverified plan), so the grep is left deliberately broad.
- non_goals: GH #82 signals 2 (sealed-shared-module + new shared-type field)
  and 3 (analytics-emit + new state-flow logic) are NOT implemented in V1.
  Both require plan-semantic analysis a lean text heuristic cannot do
  honestly; a keyword-only version would be too noisy to anchor deterministic
  tests to. They are deferred to a follow-on phase; the `RiskAssessment.flags`
  tuple is designed open so they can be added without an API change.
- exclusions: the score does not itself dispatch a subagent — `/qor-audit` is
  an LLM-run skill; the module returns the assessment and the Step 1 prose
  directs the auditing agent. The score does not gate or VETO; it only routes
  solo-vs-Option-B.

## Open Questions

None.

## Design notes

GH #82 lists four risk signals. V1 ships the two that are deterministic and
directly testable — **signal 1** (a cited `*.config.{ts,js,yaml,toml}` file:
the config-fabrication class behind the `vitest.config.ts` instance) and
**signal 4** (>=5 grep-evidence citations: a verification surface large
enough that solo author-momentum dominates). Signals 2 and 3 are fuzzy
plan-semantic judgements; implementing them as keyword heuristics would
produce a vague check whose test is itself vague (the failure mode
`doctrine-test-functionality.md` warns against). They are declared non_goals
above. Two of four still covers the two risk classes the GH #82 empirical
table most concretely evidences, and `option_b_required` fires on ANY flag,
so the V1 score is already useful the moment either signal trips.

The score never blocks: it routes. When it flags, Option B (independent
reviewer) becomes mandatory for that audit instead of operator-optional —
making the Phase 68 Option B proactive (dispatched on the risk iteration)
rather than reactive (dispatched after a VETO).

## Phase 1: Author-momentum risk score + auto-dispatch wiring

### Affected Files

- `tests/test_audit_risk_score.py` - NEW. Behavior tests for `score_plan`
  and the CLI against fixture plans.
- `tests/test_audit_risk_score_wiring.py` - NEW. Anchored + strip-and-fail
  test for the `/qor-audit` Step 1 auto-dispatch prose.
- `qor/scripts/audit_risk_score.py` - NEW. The risk-score module.
- `qor/skills/governance/qor-audit/SKILL.md` - add the Phase 87 auto-dispatch
  paragraph to Step 1 (after the Phase 68 Option B prose).
- `qor/references/doctrine-shadow-genome-countermeasures.md` - extend the
  `SG-AuthorAuditMomentum-A` Countermeasure section with the Phase 87
  auto-dispatch wiring.

### Unit Tests

- `tests/test_audit_risk_score.py`
  - `test_config_file_cite_flags_option_b` — write a plan citing
    `vitest.config.ts`; invoke `score_plan`; assert the returned
    `RiskAssessment.flags` contains `config-file-cite` and
    `option_b_required` is `True`.
  - `test_high_citation_surface_flags_option_b` — write a plan containing
    five `git show <ref>:<path> | grep ...` grep-evidence lines; invoke
    `score_plan`; assert `flags` contains `high-citation-surface` and
    `option_b_required` is `True`.
  - `test_four_grep_evidence_below_threshold` — write a plan with exactly
    four grep-evidence lines; invoke `score_plan`; assert
    `high-citation-surface` is NOT in `flags` (boundary: 4 < 5).
  - `test_clean_plan_requires_no_option_b` — write a plan with no config
    citation and fewer than five grep-evidence lines; invoke `score_plan`;
    assert `flags` is empty and `option_b_required` is `False`.
  - `test_both_signals_fire_independently` — write a plan that both cites a
    config file and carries five grep-evidence lines; invoke `score_plan`;
    assert `flags` contains both `config-file-cite` and
    `high-citation-surface`.
  - `test_missing_plan_scores_no_risk` — invoke `score_plan` on a
    non-existent path; assert `flags` empty and `option_b_required` `False`.
  - `test_cli_reports_option_b_required_with_flags` — run
    `python -m qor.scripts.audit_risk_score --plan <risky-fixture>` as a
    subprocess; assert the output contains `option_b_required: true` and
    names the fired flag.
  - `test_cli_reports_no_risk_for_clean_plan` — run the CLI against a clean
    fixture; assert the output contains `option_b_required: false`.

- `tests/test_audit_risk_score_wiring.py`
  - `test_step_1_invokes_audit_risk_score_and_mandates_option_b` — read
    `qor/skills/governance/qor-audit/SKILL.md`; isolate the `### Step 1`
    section; assert it invokes `qor.scripts.audit_risk_score` and states
    that Option B is mandatory when `option_b_required` is reported.
  - `test_step_1_directive_fails_when_stripped` — strip-and-fail negative:
    remove the `audit_risk_score` directive lines from an in-memory copy of
    the Step 1 section; assert the auto-dispatch assertion no longer holds.

### Changes

`qor/scripts/audit_risk_score.py` — new module, structured like the existing
`qor/scripts/*_lint.py` scripts:

```python
@dataclass(frozen=True)
class RiskAssessment:
    flags: tuple[str, ...]
    option_b_required: bool

def score_plan(plan_path: Path) -> RiskAssessment: ...
def main(argv: list[str] | None = None) -> int: ...  # exit 0; prints result
```

Two module-level regexes: a `*.config.{ts,js,yaml,toml}` path matcher
(signal 1) and a `git show ... | grep` grep-evidence matcher (signal 4).
`score_plan` reads the plan text, appends `config-file-cite` when the config
matcher finds >=1 hit, appends `high-citation-surface` when the grep-evidence
matcher finds >=5 hits, and sets `option_b_required = bool(flags)`. A missing
plan returns an empty assessment. `main` prints `option_b_required: true`
(with the fired flag names) or `option_b_required: false`; exit 0 always —
the score routes, it does not gate.

`qor/skills/governance/qor-audit/SKILL.md` — insert a `**Phase 87 wiring
(GH #82) — author-momentum risk auto-dispatch**` paragraph into Step 1,
after the Phase 68 Option B operator-dispatch prose and before "Your role is
to find violations". It runs `python -m qor.scripts.audit_risk_score --plan
"$PLAN_PATH"` (argv-only, `PLAN_PATH` from `current_phase_plan_path`,
SG-Phase47-A honored) and states: when the score reports
`option_b_required: true`, Option B is **mandatory** for this audit — the
auditing agent MUST run an independent reviewer, not a solo audit,
regardless of the operator default; operator override requires explicit
written justification in the audit report.

`qor/references/doctrine-shadow-genome-countermeasures.md` — extend the
`SG-AuthorAuditMomentum-A` Countermeasure section with a paragraph: Phase 87
adds `qor.scripts.audit_risk_score`, consulted at `/qor-audit` Step 1, which
makes Option B proactive — auto-mandated on the iteration where a
config-fabrication or high-citation-surface risk signal first appears,
rather than reactively dispatched after a VETO. Cite GH #82 and its
originating consumer-repo recurrence (the `SG-AuthorMomentum*` instances).

## CI Commands

- `python -m pytest tests/test_audit_risk_score.py -q` — risk-score module behavior and CLI.
- `python -m pytest tests/test_audit_risk_score_wiring.py -q` — Step 1 auto-dispatch wiring (anchored + strip-and-fail).
- `python -m pytest tests/ -q` — full regression suite.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase87-audit-risk-score.md` — plan-internal text-consistency.
