# Doctrine: Test Functionality (not Presence)

**Source**: Phase 45 v1 lesson — attribution-trailer doc-consistency tests asserted only `<string> in <file_text>`. Cross-references SG-035 (doctrine-content test unanchored) in `qor/references/doctrine-shadow-genome-countermeasures.md`.

**Goal**: A test means something only when it would catch the unit under test silently breaking. Presence-only assertions pass vacuously when the artifact survives but the behavior decays.

## Principle

A test must verify the unit under test does the right thing. Asserting only that a file exists, a string appears in a file, a function is defined, or a configuration key is set is insufficient on its own — the test passes vacuously if the artifact survives but the behavior breaks.

## Definitions

- **Presence-only test**: an assertion that is solely about the existence or textual presence of an artifact (file path, substring, attribute, declaration). The unit under test is not invoked; no output is compared to an expected value.
- **Functionality test**: a test that invokes the unit (function call, CLI subprocess, helper rendering, parser pass) and asserts the call's return value or observable side-effect against an expected value computed from the inputs.

## Rule

Every test of a unit's behavior MUST invoke that unit and assert against its output. Drift-guards (output-vs-documentation surface checks) are acceptable as auxiliary tests, but the primary test of the unit's behavior MUST be a functionality test, not a presence check.

Acceptance question, applied to every new test: *"If the unit's behavior were silently broken but the artifact still existed, would this test fail?"* If no, the test is presence-only and must be rewritten.

## Inverse-coverage discipline for closed-enum taxonomies

**Source**: GH #84 — a sealed taxonomy plan defined a `referral` canonical bucket that the normalization function could never produce; the round-trip test passed and the gap reached operator pre-commit review before it was caught.

A **closed-enum taxonomy** is a `CANONICAL_*_VALUES` constant tuple paired with a `normalize*` function that maps arbitrary input onto that closed set via an alias map. Its test list MUST assert BOTH directions:

- **Forward (round-trip)**: every alias-map key normalizes to a value in the canonical set. This is the direction the standard test discipline already covers.
- **Inverse (coverage)**: every canonical value — except explicitly gated buckets — is reachable via at least one identity-mapping in the alias map. Without this assertion a canonical bucket can be declared in the type union yet be unreachable through `normalize*`; data writes never produce it and downstream `WHERE bucket = 'X'` queries return zero rows even though `'X'` is a valid type.

Standard inverse-coverage test pattern:

```typescript
const aliasOutputs = new Set(Object.values(__ALIAS_MAP_FOR_TEST));
const expectedReachable = CANONICAL_SOURCE_VALUES.filter(
  (v) => v !== 'partner' && v !== 'unknown',  // gated / fallback buckets exempt
);
for (const bucket of expectedReachable) {
  expect(aliasOutputs).toContain(bucket);
}
```

The gated-bucket exemption is explicit: a canonical value is exempt from inverse coverage only when it is a documented fallback (e.g. `unknown`) or a runtime-checked allowlist value (e.g. `partner`), never simply because no alias happens to map to it. An unexplained unreachable bucket is the defect this discipline catches. Cross-reference `SG-InverseCoverageGapTaxonomy-A` in `qor/references/doctrine-shadow-genome-countermeasures.md`.

## Anti-patterns (verified instances)

| Anti-pattern | Where seen | Lesson |
|---|---|---|
| Substring-only doc-consistency check | Phase 45 attribution-trailer tests | A `Co-Authored-By:` substring presence check passes even if `git interpret-trailers --parse` would reject the rendered output. The behavioral test must run `git interpret-trailers --parse` (or the equivalent parser the runtime relies on) and assert the parsed output. |
| Doctrine-content test unanchored | SG-035 (Phase 15 v1, Entry #36 V-2) | Same family: substring presence with no anchor passes when the doctrine section is absent but the keyword co-occurs elsewhere. Anchor every keyword check to a section header and pair it with a strip-and-fail negative-path test. |
| Skill-prompt enforcement landed without anchor | Phase 46 (this doctrine) | A naive lock like `assert "presence-only" in body` would pass even after the section was deleted, as long as the keyword occurred anywhere else in the file. Mitigation: every Phase 46 doctrine assertion is paired with a strip-and-fail test that proves the assertion fails when the named section is removed. |
| Closed-enum taxonomy with forward-only coverage | GH #84 (attribution source taxonomy) | A `CANONICAL_*_VALUES` bucket can be declared yet unreachable through `normalize*` when only the round-trip direction is tested. The forward test iterates alias-map keys and passes; the unreachable bucket survives. Mitigation: assert inverse coverage — every non-gated canonical value is reachable via an identity-mapping. See the Inverse-coverage discipline section above. |

## Verification mechanisms

- `tests/test_doctrine_test_functionality.py` locks each gate skill's enforcement language to its section header. Every positive proximity-anchor assertion is paired with a strip-and-fail negative-path test, so the doctrine test cannot itself decay into a presence-only check.
- `/qor-plan` Step 4 forbids presence-only test descriptions in plan files; Step 5 reviews behavior-naming on every described test.
- `/qor-audit` Test Functionality Pass vetoes any plan whose described tests do not invoke the unit under test.
- `/qor-implement` Step 5 (TDD-Light) requires the failing test invoke the unit; Step 9 scans newly-added tests for the `assert <substring> in <file_text>` family.
- `/qor-substantiate` Step 4 Test Audit refuses to seal if a phase-added test is presence-only for the unit it claims to cover.
- `qor/scripts/plan_test_lint.py` flags a plan that declares a closed-enum taxonomy (`CANONICAL_*_VALUES` + `normalize*`) with no inverse-coverage test bullet (WARN-only at `/qor-audit` Step 0.6); `/qor-audit` Step 3 Test Functionality Pass issues the binding `coverage-gap` VETO.

## Update protocol

When a new presence-only failure mode emerges, append to the Anti-patterns table with a where-seen citation. The doctrine grows with the project's failure history; it does not shrink.
