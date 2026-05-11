# Doctrine: Feature Inventory

A FEATURE_INDEX is a tracked governance artifact enumerating every user-touchable feature of the product. Cross-referenced against the test surface, it answers a question that per-plan Reality-vs-Promise checks structurally cannot: "is the entire product, not just this plan's slice, covered?"

Source incident: FailSafe v5 (2026-05-06) — a single-phase plan sealed cleanly under `/qor-substantiate` while the wider product surface (commands, routes, UI panels, services, voice substrate) silently shipped without feature-level tests. The seal verdict was "Reality matches Promise" for the plan's subset; framing it as "everything works" was deception by omission. The discipline below closes that gap structurally.

## Format

One row per feature. Markdown table with these columns:

```
| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |
```

- **ID**: stable identifier (e.g., `FX091`). Never reassigned; deprecated features keep their ID with `status: deprecated` (V2 extension).
- **Name**: short human-readable name.
- **Source-of-truth file:line**: the file (and approximate line) where the feature is implemented. Operator-maintained; doctrine does not auto-generate.
- **Doc citation**: link or path to the documentation entry that introduces the feature to users. Empty when the feature is internal.
- **Test path**: file path containing the test that exercises the feature. Empty when status is `unverified` (no test) or `n/a` (no test by design).
- **Verification status**: one of `verified` / `unverified` / `n/a` (see below).

## Status enum

- **`verified`** — test at the cited path exists, exercises the feature (not presence-only), currently passes.
- **`unverified`** — no test, OR test is presence-only, OR test currently fails. Counts toward outside-scope regression at substantiate.
- **`n/a`** — intentionally untested with rationale (e.g., human-judgment surface, deprecated, gated behind a feature flag the test environment cannot reach). The `n/a_rationale` cell must be populated.

## Lifecycle hooks

`/qor-plan` Step 7
: Declare every feature touched by the plan as `feature_inventory_touches` entries in plan top-matter and `plan.json`. Operations: `NEW` (entry not yet in FEATURE_INDEX), `MODIFIED` (entry exists, plan changes the surface), `n/a-justified` (declared for traceability, no behavior change).

`/qor-audit` Step 3 Feature Test Coverage Pass
: Verify every `feature_inventory_touches` entry names a test path AND a test descriptor naming the assertion that proves the feature works. Descriptors that cannot answer "yes" to the SG-035 acceptance question route to VETO with category `feature-test-undeclared`.

`/qor-implement` Step 5 per-feature TDD-Light
: For every entry in `feature_inventory_touches`, author the failing test FIRST at the declared path with the declared assertion; run it red; implement; run it green. Per `doctrine-feature-tdd.md`.

`/qor-implement` Step 12.5 FEATURE_INDEX update
: For each declared touch:
- `NEW`: append a row to FEATURE_INDEX with status `verified` (feature ships with green test in same commit).
- `MODIFIED`: update existing row's `Source-of-truth file:line` and/or `Test path`.
- `n/a-justified`: no row change.

Block staging on any entry that does not resolve to a green test in this commit.

`/qor-substantiate` Step 6 verification pass
: Invoke `feature_index_verify.tally()`. Surface counts in the SEAL ledger body: `Total: N / verified: V / unverified: U / n/a: A`. **Fail the seal** when any feature OUTSIDE the current plan's `feature_inventory_touches` regressed from `verified` to `unverified` since the last seal — this prevents silent rot.

## Repos without a FEATURE_INDEX

The artifact is optional at the framework level (a host repo may not have adopted the discipline yet). `feature_index_verify.tally()` returns `missing_index=True` and the seal proceeds with a single-line note in the SEAL entry. Once a repo creates FEATURE_INDEX.md (at any path the operator chooses; doctrine specifies format, not location), the verification pass becomes active for that repo.

## Why this beats stricter change-time enforcement alone

A "every src/ change needs a `.spec.ts`" CI rule catches *change-time* gaps. It does not catch *baseline* gaps: features that shipped in earlier releases without a test, or features whose tests rotted into presence-only. The feature index is the canonical surface against which baseline gaps become visible at every seal.

Source incidents: GH #40 (FailSafe v5 baseline coverage gap) and GH #41 (per-feature TDD upstream of #40).
