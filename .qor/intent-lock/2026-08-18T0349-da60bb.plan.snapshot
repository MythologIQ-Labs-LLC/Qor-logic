# Plan: The corpus ceiling becomes a wall

**iteration**: 2

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: WARN-band findings remain advisory forever under this flip; only EXCEEDED (over 40 KB) aborts the seal, which is already the lint's sole exit-1 condition. An operator facing a legitimate deliberate breach uses the progressive-disclosure refactor the WARN has been recommending since Phase 95, not an override -- no override path is added.
- non_goals: No threshold changes (25 KB WARN / 40 KB EXCEEDED stand). No new lint behavior; the flip is pure posture. No changes to the dogfooding anchors or the per-skill headroom tests.
- exclusions: GH #351, GH #286.

## Open Questions

None. The entry condition is measured in the research brief (ledger #628) and the flip aborts nothing today.

## Locked Decisions

**LD-1: The flip surface is exactly the Step 4.6.9 row of the ladder table whose header line anchors here** (the row itself carries backticks and cannot be quoted in the mandated evidence form -- the Phase 228 research's normalization limitation; the parsed-policy test in Phase 1 is the row's behavioral anchor instead):

```
git show v0.154.0:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'Step . Gate . Command . Policy . Records . Notes' -> 239:| Step | Gate | Command | Policy | Records | Notes |
```

The 4.6.9 row (seven lines below the header at v0.154.0) currently declares policy WARN with a true-suffixed command; it becomes: command suffix `|| ABORT`, Policy `ABORT`, Notes `WARN at 25 KB; EXCEEDED at 40 KB aborts the seal (V2, Phase 234; GH #320)`.

**LD-2: The ladder parser already admits the target posture; no parser change.**

```
git show v0.154.0:qor/scripts/substantiate_gates.py | grep -nE '^POLICY_VALUES' -> 33:POLICY_VALUES = frozenset({"ABORT", "WARN", "disclose"})
```

**LD-3: The byte delta must respect the substantiate skill's own slack floor** (2,727 bytes against a 2,700 floor at v0.154.0): the row edit is held within 27 net bytes, verified in the substantiate sweep by the existing `test_ladder_rewrite_left_usable_slack`. Measured delta of the declared row text: +1 (command suffix true to ABORT) +1 (Policy WARN to ABORT) +16 (Notes, 57 to 73 characters) = +18 net, landing slack at 2,709.

## Phase 1: Bind the posture (test first)

### Affected Files

- `tests/test_skill_size_budget_substantiate_wiring.py` - extended with one test.

### Unit Tests

- `test_step_4_6_9_policy_is_abort` - the parsed 4.6.9 row's policy field equals `ABORT` and its command carries no `|| true` suffix (via the shipped `substantiate_gates` parser, not string matching). Red at v0.154.0 (policy is WARN).

## Phase 2: The one-row flip

### Affected Files

- `qor/skills/governance/qor-substantiate/SKILL.md` - the LD-1 row edit; nothing else in the file.
- `tests/test_skill_size_budget_substantiate_wiring.py` - the invocation test's posture assertion flips from the `|| true` literal to the `|| ABORT` literal (line 23; Phase 222 exact-literal guardrail convention), in the same commit as the row edit. Deliberate consumer update per audit F1 (entry #629); the parsed-policy test from Phase 1 remains the behavioral anchor, this assertion stays the exact-literal guardrail.

### Changes

Phase 1's test goes green; the remaining two existing wiring tests (removal, order), the ladder order/token suites, the dogfooding anchors, and the slack-floor test all stay green. The invocation test stays green via its declared assertion flip above.

### Unit Tests

- Phase 1's test observed red-then-green.
- `qor-logic-plus scripts skill_size_budget_lint --skills-root qor/skills` observed exit 0 with three WARN findings in the substantiate sweep -- the flip aborts nothing on the current corpus, by measurement.

## Feature Inventory Touches

None. One skill-table row and one test.

## Definition of Done

### Deliverable 1: EXCEEDED is a wall

- **D1**: A governance skill crossing 40 KB can no longer seal; the drift class that consumed hard-constraint incidents at Phases 222 and 229 is structurally closed at the source.
- **D2**: Row 4.6.9 at policy ABORT, command without the true-suffix.
- **D3**: Implement-phase ledger entry cites this plan; seal binds this plan file; this phase's own seal runs the flipped gate live.
- **D4**: `test_step_4_6_9_policy_is_abort` observed red at v0.154.0 and green after Phase 2; the live lint observed exit 0 at seal.

## CI Commands

- `python -m pytest tests/ -q` -- full suite.
- `qor-logic-plus scripts plan_text_consistency_lint --check docs/plan-qor-phase234-size-budget-v2.md` -- plan-internal consistency.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase234-size-budget-v2.md --repo-root .` -- citation truth check.
