# Plan: Phase 91 — verify-ledger `--tolerate-known-grandfathered` flag (GH #85)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #85

**boundaries**:
- limitations: V1 ships only Option D from the GH #85 four-option menu —
  a `--tolerate-known-grandfathered` flag on `qor-logic verify-ledger`
  that accepts chain-math failures iff the failing entries' `previous_hash`
  appears in the duplicate-previous_hash set within the
  SG-ConcurrentLedgerRace-A signature AND those entries lie below the
  grandfather cutoff (default 207, the same cutoff Phase 76 used for
  `check_previous_hash_uniqueness`). This does NOT fix the ledger — it
  lowers verifier gate severity for the specifically-known failure
  pattern so consumer workspaces (e.g., Accountable-App-3.0 per GH #85)
  can ship clean `verify-ledger` results immediately. Forward-only by
  construction: no past entries are modified; no new ledger entry type
  is introduced; no operator-authorization protocol is needed because
  the operation is read-only (verifier semantics change, not ledger
  content).
- non_goals: Options A (RECONCILIATION ledger entry append), B
  (post-anchor pinning at reconciliation entry), and C (per-session
  sub-ledger merge tool) from GH #85 are NOT implemented in V1. Each
  requires real operator-authorization protocol design and a new
  schema-bearing ledger entry type; the issue itself classifies (D) as
  a stopgap that "doesn't actually fix the ledger" but unblocks consumer
  release gates. V2 (A/B) reserved for a future phase after operator
  evidence accumulates on whether (D) is sufficient. The
  `--tolerate-known-grandfathered` flag is OFF by default; existing
  release gates remain strict unless the operator opts in.
- exclusions: no changes to `verify_post_anchor` (which already has its
  own `DISCLOSED_PRE_ANCHOR` tolerance for the re-anchored consumer
  case from Phase 66); no changes to `check_previous_hash_uniqueness`
  in `qor.reliability.seal_entry_check` (still enforces uniqueness on
  new entries, preventing future grandfathered surface); no changes to
  the META_LEDGER itself; no new doctrine file (extends
  `SG-ConcurrentLedgerRace-A` per the GH #92 progressive-disclosure
  lesson).

## Open Questions

None.

## Feature Inventory Touches

Empty. This plan touches a public CLI flag (`qor-logic verify-ledger
--tolerate-known-grandfathered`) and the underlying `verify()` function
in `qor/scripts/ledger_hash.py`; it introduces no `src/` user-facing
feature. `feature_inventory_touches`: `[]`.

## Design notes

GH #85 documents a consumer-workspace blocker: `Accountable-App-3.0` has
six entries (#16a/b, #17a/b, #18a/b) from a Phase-76-era concurrent
federation race, plus an Entry #20 downstream chain-hash mismatch. The
canonical Qor-logic META_LEDGER carries the analogous pre-Phase-76
duplicates at #109/#111/#113 (sharing one `previous_hash`), though
without a downstream chain-math failure on this repo's ledger because
the operator's anchoring stayed consistent. Both cases match the
SG-ConcurrentLedgerRace-A doctrine signature and are explicitly
grandfathered as documented residual per the Phase 76 forbidden-
interpretation clause ("Past sealed entries are grandfathered").

The minimal V1 fix is a verifier flag that accepts these specifically-
known failures as `DISCLOSED_GRANDFATHERED` instead of `FAIL`. Per the
GH #85 proposed scope:

> Add `--tolerate-known-grandfathered` to `verify-ledger` that accepts
> pre-V1 failures iff every failing entry's `previous_hash` lineage
> matches the SG-ConcurrentLedgerRace-A doctrine signature. Lighter-
> weight than (A)-(C) but doesn't actually fix the ledger — it just
> lowers the gate severity.

V1 grandfather signature (operatively testable):

- An entry `E` is `grandfathered` iff `E.previous_hash` appears as the
  `Previous Hash` of two or more entries in the same ledger AND
  `E.entry_num <= cutoff` (default 207, configurable via
  `--grandfather-cutoff`).
- The duplicate-previous_hash set is computed in one pass over the
  ledger; entries below the cutoff whose `previous_hash` is in that
  set become tolerated.
- Failures on entries `>` cutoff (or entries whose `previous_hash` is
  not in the duplicate set) remain `FAIL` — the flag does not mask
  novel failures.

The flag is read-only by construction (verifier semantics change; no
ledger writes), so no operator-authorization protocol is needed — this
is what makes (D) the V1 stopgap. Real reconciliation (Options A/B)
that writes new entries to the ledger DOES need authorization
infrastructure and is reserved for a future phase.

Per `[[feedback-progressive-disclosure]]` (GH #92 corpus-bloat lesson),
the change is kept lean: one helper function + one verify() arg + two
CLI flags + a doctrine paragraph. No new script file, no new doctrine
file. Tests use fixture ledgers to construct the consumer-workspace
failure scenario from GH #85; the canonical Qor-logic ledger is also
exercised end-to-end via `test_canonical_ledger_unchanged_without_flag`
and `test_canonical_ledger_clean_with_flag` to confirm forward-only
semantics.

Per the **dogfooding pattern** established by Phases 89/90 (each phase
exercises the prior phase's countermeasure on its own plan), Phase 91's
own plan covers the full CI surface in `## CI Commands` so Phase 89's
`ci_coverage_lint` reports zero WARNs, and the new test file carries
the Environment-block discipline established in Phase 90 (the test file
doesn't invoke `python -m qor.X` so the discipline is checked vacuously,
but the convention is honored).

## Phase 1: find_grandfathered_entries + verify flag + CLI wiring + tests

### Affected Files

- `qor/scripts/ledger_hash.py` — add `find_grandfathered_entries(ledger_md, cutoff=207)` helper returning a `frozenset[int]` of entry numbers; modify `verify()` to accept `tolerate_known_grandfathered: bool = False` and `grandfather_cutoff: int = 207` kwargs.
- `qor/cli.py` — add `--tolerate-known-grandfathered` flag (default False) and `--grandfather-cutoff` arg (default 207) to the `verify-ledger` subparser; propagate to `verify()` in `_do_verify_ledger`.
- `qor/references/doctrine-shadow-genome-countermeasures.md` — extend the existing `SG-ConcurrentLedgerRace-A` section with a "V2 stopgap (Phase 91)" paragraph naming the flag, the signature, and the operator-actionable contract.
- `tests/test_ledger_hash_tolerate_grandfathered.py` — NEW. Behavior tests using fixture ledgers reconstructing the GH #85 consumer-workspace scenario.
- `docs/plan-qor-phase91-ledger-tolerate-grandfathered.md` — NEW. This plan file.

### Unit Tests

- `tests/test_ledger_hash_tolerate_grandfathered.py`

  Each test uses tmp-path fixture ledgers (no dependency on the repo's
  own META_LEDGER except for the two canonical-ledger forward-only
  guards). Per `qor/references/doctrine-test-functionality.md`, each
  assertion verifies an operative property — what the function returns
  or what verifier output line appears — not header presence.

  - `test_find_grandfathered_returns_entries_with_duplicate_previous_hash_below_cutoff`
    — fixture ledger has entries #100 / #102 / #104 all carrying the
    same `Previous Hash` value; cutoff=207; assert
    `find_grandfathered_entries` returns `{100, 102, 104}`.
  - `test_find_grandfathered_excludes_entries_above_cutoff`
    — fixture has #208 / #210 sharing one previous_hash; cutoff=207;
    assert the returned set is empty (post-cutoff entries are NOT
    grandfathered; the flag does not retroactively cover new failures).
  - `test_find_grandfathered_excludes_unique_previous_hash_entries`
    — fixture has #100 with a unique previous_hash; assert it is NOT
    in the grandfathered set even though it's below cutoff.
  - `test_find_grandfathered_handles_mixed_pre_and_post_cutoff_group`
    — fixture has #105 / #207 / #208 all sharing one previous_hash;
    cutoff=207; assert only #105 and #207 are grandfathered (#208 is
    above the cutoff and remains a FAIL candidate, preserving the
    forward-only-no-new-grandfathering invariant).
  - `test_verify_without_flag_still_fails_on_grandfathered_chain_mismatch`
    — fixture ledger has a grandfathered entry whose recorded chain
    hash deliberately mismatches the recomputed chain hash; invoke
    `verify(ledger, tolerate_known_grandfathered=False)`; assert
    return code is 1 and stderr contains `FAIL Entry #`.
  - `test_verify_with_flag_reports_disclosed_grandfathered_not_fail`
    — same fixture; invoke
    `verify(ledger, tolerate_known_grandfathered=True)`; assert return
    code is 0 and stdout contains
    `DISCLOSED_GRANDFATHERED Entry #` for the grandfathered entry.
  - `test_verify_with_flag_does_not_propagate_taint_from_grandfathered_failure`
    — fixture has a grandfathered failure followed by a clean entry
    whose chain math is valid; invoke `verify(..., True)`; assert the
    clean entry reports `OK` not `TAINTED` (the existing taint cascade
    must not fire from a tolerated failure).
  - `test_verify_with_flag_still_fails_on_post_cutoff_chain_mismatch`
    — fixture has both a grandfathered failure (tolerated) and a
    post-cutoff entry with a real chain mismatch (not in any
    duplicate-previous_hash group); invoke `verify(..., True)`;
    assert return code is 1 and the post-cutoff entry reports `FAIL`.
    This is the critical "does not mask novel failures" guard.
  - `test_verify_with_custom_cutoff_overrides_default`
    — fixture has duplicates at #150 and at #220; invoke with
    `grandfather_cutoff=250`; assert both #150 and #220 are
    grandfathered (the cutoff is a hard upper bound the operator can
    raise but defaults to the Phase 76 boundary).
  - `test_cli_flag_parses_and_propagates`
    — subprocess-invoke `qor-logic verify-ledger
    --ledger <fixture> --tolerate-known-grandfathered`; assert exit
    code 0 and stdout contains `DISCLOSED_GRANDFATHERED`. Run the
    same command WITHOUT the flag; assert exit code 1 and stderr
    contains `FAIL`.
  - `test_cli_grandfather_cutoff_arg_parses`
    — subprocess-invoke `qor-logic verify-ledger
    --ledger <fixture> --tolerate-known-grandfathered
    --grandfather-cutoff 250`; assert exit code reflects the wider
    cutoff (entries that would FAIL at the default 207 are tolerated
    at 250).
  - `test_canonical_ledger_unchanged_without_flag`
    — invoke `verify(REPO_ROOT/'docs'/'META_LEDGER.md')` with default
    args (flag OFF); assert return code is 0 (the canonical Qor-logic
    ledger currently verifies clean per Phase 76 forensics; #109/#111/#113
    duplicate-previous_hash entries each still produce valid chain
    math in isolation). This is the forward-only guard: Phase 91 must
    not change observable behavior on the canonical ledger when the
    flag is not set.
  - `test_canonical_ledger_clean_with_flag`
    — invoke `verify(REPO_ROOT/'docs'/'META_LEDGER.md',
    tolerate_known_grandfathered=True)`; assert return code is 0. The
    canonical ledger is already clean; the flag adds zero noise on a
    clean ledger.

### Changes

`qor/scripts/ledger_hash.py` — new module-level helper:

```python
def find_grandfathered_entries(
    ledger_md: Path,
    cutoff: int = 207,
) -> frozenset[int]:
    """Return entry numbers whose previous_hash appears in 2+ entries AND
    whose entry number is <= cutoff.

    These are the SG-ConcurrentLedgerRace-A documented residuals -- pre-V1
    concurrent-append duplicates explicitly grandfathered by the Phase 76
    forbidden-interpretation clause. Past these are not tolerated; the
    flag does not retroactively cover new failures, preserving the
    forward-only invariant.
    """
```

`verify()` extension: two new keyword-only args
(`tolerate_known_grandfathered: bool = False`,
`grandfather_cutoff: int = 207`). When the flag is True, chain-math
failures on entries in the grandfathered set produce a new
`DISCLOSED_GRANDFATHERED Entry #N: tolerated SG-ConcurrentLedgerRace-A
residual` line (stdout, not stderr) instead of `FAIL`; the
`last_failed = num` taint propagation does NOT fire for tolerated
entries (so downstream entries don't get marked TAINTED).

`qor/cli.py` — two new args on the `verify-ledger` subparser:

```python
sp_verify.add_argument(
    "--tolerate-known-grandfathered", action="store_true",
    help="accept chain failures on SG-ConcurrentLedgerRace-A documented residuals (Phase 91, GH #85)",
)
sp_verify.add_argument(
    "--grandfather-cutoff", type=int, default=207,
    help="entry-number upper bound for the tolerate-known-grandfathered flag (default 207; Phase 76 cutoff)",
)
```

`_do_verify_ledger` propagates the args to `verify()`.

`qor/references/doctrine-shadow-genome-countermeasures.md` — append a
"V2 stopgap (Phase 91; GH #85)" paragraph at the end of
`SG-ConcurrentLedgerRace-A`:

```markdown
**V2 stopgap** (Phase 91 wiring; GH #85): `qor-logic verify-ledger
--tolerate-known-grandfathered` accepts chain-math failures iff the
failing entries' `previous_hash` appears in the ledger's duplicate-
previous_hash set AND the failing entry numbers are `<= --grandfather-
cutoff` (default 207, matching `check_previous_hash_uniqueness`'s
`min_entry_num`). Read-only verifier semantics; no operator-
authorization protocol needed because the ledger is not modified. Lets
consumer workspaces ship clean `verify-ledger` gates immediately
without rewriting past entries. The flag is OFF by default; the strict
verifier remains the canonical gate unless the operator opts in. Real
reconciliation that writes new entries (Options A/B from GH #85 —
RECONCILIATION entry append; post-anchor pinning) is reserved for a
future phase with operator-authorization protocol design.
```

## CI Coverage Exemptions

None for this phase. Phase 91's `## CI Commands` block declares the full
Qor-logic CI surface so `ci_coverage_lint` reports zero WARNs.

## CI Commands

- `python -m pytest tests/test_ledger_hash_tolerate_grandfathered.py -q` — behavior tests for `find_grandfathered_entries`, `verify(... tolerate=True)`, taint suppression, post-cutoff failure preservation, and CLI flag propagation.
- `python -m pytest tests/ -v` — full regression suite (matches the ci.yml `test` job's `-v` form).
- `python qor/scripts/check_variant_drift.py` — ci.yml `test` job step.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ci.yml `test` job step.
- `python -m pytest tests/test_packaging_install.py -v -m integration` — ci.yml `install-smoke` job step.
- `python -m qor.reliability.gate_chain_completeness --phase-min 52` — ci.yml `gate-chain-completeness` job step.
- `python qor/scripts/pr_citation_lint.py` — pr-lint.yml `lint` job step.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase91-ledger-tolerate-grandfathered.md` — plan-internal text-consistency.
- `python -m qor.scripts.ci_coverage_lint --plan docs/plan-qor-phase91-ledger-tolerate-grandfathered.md --workflows-dir .github/workflows` — Phase 89 ci-coverage lint (self-applying to this plan, dogfooding pattern).
