# Plan: override records collapse to one signature instead of one per reason

**change_class**: hotfix

**doc_tier**: standard

**iteration**: 2 (after VETO, ledger entry #782, 6 violations; the design is replaced, not amended)

**boundaries**:
- limitations: This takes the threshold from 47 to 41 and stops further declines
  raising it. It does not lower the threshold constant, does not work the debt,
  and does not make the gate quiet. The residual 41 across 25 signatures is
  genuine process debt and the gate is correct to keep firing on it.
- non_goals: The codex-plugin cluster is untouched -- its emission stopped
  2026-07-13 and its events age out under the existing stale-expiry rule. No
  attempt to make repeated deferral *more* visible: collapse deliberately counts
  a recurring condition once, which is what `collapsed_severity` does for every
  other recurring condition.
- exclusions: No change to `collapsed_severity`'s arithmetic, the stale-expiry
  rule, the escalation rule, the threshold constant, `permanent_skips`, or
  `orchestration_override.record`. No retroactive edit of any recorded event.
  Nothing is removed from the sum.

## Open Questions

None.

## Locked Decisions

### LD-1: the defect is a known one, recorded and unfixed

> `grep -n 'interpolated-reason defect' docs/META_LEDGER.md`
> -> `21964:...The interpolated-reason defect in \`orchestration_override.record\` that prevents signature collapse under \`collapsed_severity\` remains unfixed and unfiled separately.`

That is the Phase 266 seal. Iteration 1 of this plan neither cited nor superseded
it and was vetoed for that among five other grounds (entry #782, V6). This
iteration implements it.

The mechanism: `_signature` resolves a collapsing key from `gate`, `capability`
or `pattern`, and falls back to a digest over the whole `details` object when it
finds none.

> `git show HEAD:qor/scripts/check_shadow_threshold.py | grep -n 'key = details.get'`
> -> `113:    key = details.get("gate") or details.get("capability") or details.get("pattern")`

> `git show HEAD:qor/scripts/orchestration_override.py | grep -n '"details"'`
> -> `45:        "details": {"recommended_skill": recommended_skill, "reason": reason},`

An override carries neither `gate`, `capability` nor `pattern`, so it takes the
digest branch, and `reason` is free text that differs per event. Four records of
one condition therefore produce four signatures and four contributions.

### LD-2: the fix is a fourth positive-evidence key, not a special case

`recommended_skill` is exactly the kind of key `_signature` already resolves: it
is positive evidence that two events describe the same condition, which is the
standard the function's own docstring sets.

> `git show HEAD:qor/scripts/check_shadow_threshold.py | grep -n 'positive evidence\|Differing details mean'`
> -> `96:    Phase 254: collapse requires positive evidence that two events describe the`
> -> `98:    evidence; absent all three, identical details are. Differing details mean we`

Adding it is not the Phase 253 direction that docstring warns against. Phase 253
collapsed by `event_type` alone when no key was present; this adds a key, so
events that carry no `recommended_skill` still reach the digest branch unchanged.

**Measured by simulating the patched resolution against the live log and against
the existing tests' event shape:**

| input | signature under the change |
|---|---|
| live override (`recommended_skill` present) | `('orchestration_override', '/qor-remediate')` |
| `tests/test_signature_discrimination.py:50-51` shape (`reason` only) | `('orchestration_override', 'details:89841f4b9865')` -- unchanged |

The second row is why the existing discrimination tests are unaffected: their
fixture carries no `recommended_skill` and still takes the digest branch.

### LD-3: the writer-side alternative was measured and rejected

Putting the route into `details["pattern"]` inside `orchestration_override.record`
would need no reader change at all, since `_signature` already resolves `pattern`.
It was rejected on measurement, not taste:

| | threshold today | after a 5th decline | after a 6th |
|---|---|---|---|
| writer-side | **47** | **49** | 49 |
| this plan | **41** | 41 | 41 |

The writer-side fix cannot touch the four existing records -- they were written
before it -- so it lets the number rise once more before it takes hold, and
leaves the four historical signatures standing until they age out around
2026-11-10. The reader-side change corrects the existing records and every future
one in the same edit, without rewriting anything recorded.

### LD-4: nothing leaves the sum

Iteration 1 excluded these records from the threshold and was vetoed because the
compensating signal it named cannot fire (#782, V3):
`remediate_read_context.py:27` groups on `(event_type, skill, session_id)`, the
four events occupy four groups of one, and `remediate_pattern_match.py:34-37`
fires `gate-loop` only at `>= 2` in a group.

This iteration removes nothing. All four records stay in the sum, stay
unaddressed, and stay visible; they are counted once as one condition rather than
four times as four. The first decline still contributes 2, because the fact that
the route has been declined is real process information. What stops is the
multiplication -- a fifth decline adds 0.

> measured: threshold **47 -> 41**; override contribution **8 -> 2**; override
> signatures **4 -> 1**; a simulated fifth decline adds **0**

### LD-5: the docstring is the documentation surface

Iteration 1 proposed a paragraph in `doctrine-governance-enforcement.md` and was
vetoed because that file documents a different mechanism (#782, V4): its Section
10 covers the remediation lifecycle, cycle-count escalation and override
suppression, and the severity-sum threshold is documented in the
`qor-shadow-process` skill instead.

`_signature`'s own docstring already carries this calibration history -- the
Phase 253 over-collapse and the Phase 254 correction are both recorded there in
the file a reader of `_signature` is already looking at. The fourth key is
recorded in the same place, which needs no new section, no cross-file lookup, and
does not touch a `doctrine-` path that would pull in the documentation-currency
ladder at `doc_integrity_strict.py:149`.

## Phase 1: pin the collapse behavior

### Affected Files

- `tests/test_check_shadow_threshold_override_collapse.py` - NEW. Tests that
  build event lists and call `collapsed_severity`.

### Changes

The change is inside `_signature`, which `collapsed_severity` calls, so tests
calling `collapsed_severity` directly observe it. Iteration 1's tests called
`collapsed_severity` while the change lived in its caller, and could never have
gone green (#782, V2); this iteration's unit and change are the same unit.

Fixtures are built from the shape `orchestration_override.record` actually
writes -- `details` carrying `recommended_skill` and `reason` -- rather than from
a hand-chosen literal. Iteration 1's predicate matched a string no wired caller
emits (#782, V1), so the route value used here is taken from
`cycle_count_escalator`, which is what populates it.

### Unit Tests

- `test_two_declines_of_one_route_collapse_to_a_single_contribution` - two
  override events, same `recommended_skill`, different free-text `reason`; the
  sum is that of one. Red before: the differing reasons produce two digests and
  the sum doubles.
- `test_declines_of_different_routes_do_not_collapse` - two overrides with
  different `recommended_skill`; the sum is that of two. The negative control,
  and the one that fails if the key degenerates to `event_type`.
- `test_an_override_without_a_recommended_skill_still_uses_the_details_digest` -
  the shape `tests/test_signature_discrimination.py:50-51` uses; two such events
  with identical details collapse and with differing details do not. Green
  before and after by design -- it exists to prove the change does not disturb
  the existing discrimination contract, and it is declared here as a guard
  rather than as a red-first driver.
- `test_the_route_value_is_the_one_the_escalator_emits` - imports
  `cycle_count_escalator` and asserts the value it puts in `suggested_skill` is
  the value this collapse keys on, so the fixture cannot drift from the
  producer. Iteration 1 was vetoed for exactly that drift.
- `test_the_live_log_override_contribution_is_a_single_signature` - over the real
  log, asserts every unaddressed `orchestration_override` shares one signature
  and their combined contribution equals that of one. Red before: four
  signatures, contribution 8.

## Phase 2: resolve a fourth collapsing key

### Affected Files

- `qor/scripts/check_shadow_threshold.py` - `_signature` key resolution and its
  docstring.

### Changes

```python
    key = (
        details.get("gate")
        or details.get("capability")
        or details.get("pattern")
        or details.get("recommended_skill")
    )
```

and the docstring gains, beside the Phase 253/254 history it already carries:

> Phase 284: ``recommended_skill`` joins the resolved keys. An operator declining
> a route records the route and a free-text reason, so absent a key the digest
> branch made one condition into one signature per decline -- and because the
> threshold recommends a route, each decline raised the number that produced the
> next prompt. The route is the positive evidence that two declines describe the
> same condition; the reason varies by construction and is not.

### Unit Tests

The Phase 1 tests go green. No new tests.

## Feature Inventory Touches

Empty. This plan touches `qor/scripts/` and `tests/` only.

## Definition of Done

### Deliverable: declines of one route count once

- **D1**: An operator declining the remediation route repeatedly raises the
  threshold once, not once per decline.
- **D2**: `_signature` resolves `details.get("recommended_skill")` after `pattern`,
  and its docstring records why.
- **D3**: Plan gate artifact; audit verdict; seal entry citing this plan by
  content hash; the research brief retracting the superseded proposal and the
  VETO at #782 are both in the chain behind it.
- **D4**: `test_two_declines_of_one_route_collapse_to_a_single_contribution` --
  two overrides differing only in `reason` sum to one contribution. Observed
  before the change: the sum doubles.

### Deliverable: the change disturbs nothing that already collapses

- **D1**: Events carrying no `recommended_skill` keep the digest branch and the
  existing discrimination contract.
- **D2**: The digest fallback is unchanged and still reached when all four keys
  are absent.
- **D3**: LD-2 records the measurement showing the existing tests' fixture shape
  is unaffected.
- **D4**: `test_an_override_without_a_recommended_skill_still_uses_the_details_digest`,
  plus `tests/test_signature_discrimination.py` and
  `tests/test_remediation_closure_states.py` staying green -- both are in the CI
  commands because both exercise `collapsed_severity` directly.

### Deliverable: the fixture cannot drift from the producer

- **D1**: The route value the collapse keys on is the value the wired path emits.
- **D2**: The test imports `cycle_count_escalator` rather than hardcoding a string.
- **D3**: LD-1 and the VETO at #782 record the drift this replaces.
- **D4**: `test_the_route_value_is_the_one_the_escalator_emits` -- fails if the
  escalator's emitted value and the test fixture diverge.

## CI Commands

- `python -m pytest tests/test_check_shadow_threshold_override_collapse.py -q` — the collapse rule and its negative controls.
- `python -m pytest tests/test_signature_discrimination.py tests/test_remediation_closure_states.py tests/test_shadow_residue_disposition.py -q` — the existing signature contracts this must not disturb.
- `python -m qor.scripts.check_shadow_threshold` — the live sum; expected to drop from 47 to 41 and to remain in breach.
- `python -m qor.scripts.publication_boundary_lint` — this plan and its artifacts introduce no boundary finding.
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` — chain integrity across the phase's entries.
- `python -m pytest -q` — full suite; the seal writes badges and header state that freshness tests read.
