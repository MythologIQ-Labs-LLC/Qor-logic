# Plan: Surface the post-anchor disagreement

**change_class**: hotfix

**doc_tier**: minimal

**iteration**: 1

**originating_remediation**: GH #430

**boundaries**:
- limitations:
  - This closes the operator-visible half of GH #430. It does not change any exit code, so a consumer whose strict verifier fails and whose post-anchor surface is clean still releases; they are now told what they are releasing over.
  - The counts reported are the strict verifier's own FAIL and TAINTED line counts. Because taint propagates unconditionally from the first failure, the tainted count is a distance-to-first-failure measure, not an independent defect count, and the disclosure says so rather than implying otherwise.
- non_goals:
  - Changing what `verify_post_anchor` returns for any input. Every exit code in this phase is byte-identical to today's.
  - GH #430's suggestions 1 and 2. Both were measured contract-breaking at the Phase 263 tribunal and are refused here with the measurement recorded, not silently dropped.
- exclusions:
  - GH #443 and GH #425.
  - Attestation parity between the two modes. Measured below as not fixing GH #430; it belongs to its own phase and its own issue.
  - Phase 263's declared-anchor design, VETOed at META_LEDGER entry #741.

## Scoping

Phase 263 proposed a declared-anchor contract for the same issue and was VETOed on five grounds, the fifth being that its premise was false. This is a new phase rather than a Phase 263 iteration because the design shares nothing with it: no config key, no resolution order, no migration, and no exit-code change at all. Phase 263's plan and tribunal stand as the record of the refused approach. The attempt cap is not being evaded; the scope that consumed one attempt no longer exists.

Every rule below was executed against the failing fixture and against this repository before being written down.

## Open Questions

None.

## Phase 1: Report what was tolerated

### Affected Files

- `tests/test_post_anchor_disagreement_disclosure.py` NEW - the coverage line, the strict-count note, and the invariant that no exit code moves
- `qor/scripts/ledger_hash.py` - `verify_post_anchor` summary line reports coverage
- `qor/scripts/governance_health.py` - the OK note names the strict verifier's finding instead of discarding it

Callers of `verify_post_anchor`, enumerated per SG-AffectedFilesContract-A. No signature changes, so none require amendment: `qor/cli.py:70`, `qor/reliability/seal_entry_check.py:149`, `qor/scripts/governance_health.py:167`, `qor/scripts/ledger_upgrade.py:71`.

### Locked Decisions

**LD-1. The reported harm is that the stricter finding is discarded, and it is discarded at a known line.** `governance_health._ledger_damage` runs the strict verifier, keeps only its return code, and throws its output away:

- `git show d07daac3:qor/scripts/governance_health.py | grep -nE 'rc = _verify_ledger_chain' -> 140:            rc = _verify_ledger_chain(base / _LEDGER)`

On non-zero it falls back to the post-anchor surface and, when that passes, returns a fixed note:

- `git show d07daac3:qor/scripts/governance_health.py | grep -nE 'disclosed pre-anchor residuals tolerated' -> 153:                "disclosed pre-anchor residuals tolerated; post-anchor band clean"`

The strict result is therefore already computed at the moment the note is written. Nothing new needs running; a buffer that is currently discarded needs reading.

**LD-2. The change is additive, and that is a measured constraint rather than a preference.** Every assertion that reads either surface is a substring test:

- `git show d07daac3:tests/test_verify_ledger_cli.py | grep -nE 'assert "post-anchor clean" in out' -> 55:    assert "post-anchor clean" in out`
- `git show d07daac3:tests/test_governance_health_post_anchor_tolerance.py | grep -nE 'assert "disclosed pre-anchor residuals tolerated" in finding.reason' -> 119:    assert "disclosed pre-anchor residuals tolerated" in finding.reason`

Appending to either string preserves both. Replacing or reordering either phrase would not. The four contract tests that the Phase 263 design broke assert `status is OK`, the absence of FAIL and TAINTED lines, and that substring; none is disturbed by an append, because no status and no exit code moves.

**LD-3. The summary line already has the boundary and needs the coverage beside it.** The line is:

- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'print\(f"post-anchor clean' -> 719:        print(f"post-anchor clean (boundary=#{boundary_entry})")`

"The post-boundary band is clean" and "the post-boundary band is empty" print identically today, which is the sentence GH #430 asks to be made distinguishable. The counts that distinguish them are already in hand at that point: the classification loop has produced the OK and disclosed tallies, and the boundary is resolved.

**LD-4. Coverage separates the two consumer shapes that currently look alike.** Measured on the two fixtures plus this repository:

| shape | strict | post-anchor | OK | disclosed |
|---|---|---|---|---|
| GH #430 reporter | rc=1, 1 FAIL, 7 TAINTED | rc=0 | 1 | 7 |
| GH #55 consumer | rc=1, 1 FAIL, 5 TAINTED | rc=0 | 6 | 2 |
| this repository, live | rc=0 | rc=0 | 707 | 10 |

The reporter's ledger verifies one entry and tolerates seven; the GH #55 consumer verifies six and tolerates two. Both print the identical `post-anchor clean` line today. The ratio is the operator-legible difference and it costs two integers to report.

**LD-5. This repository is unaffected, and the reason matters.** Strict `verify()` returns 0 here, with 738 OK lines and zero FAIL or TAINTED. `_ledger_damage` therefore never reaches its fallback, so no note is emitted today and none will be after. The ten `DISCLOSED_PRE_ANCHOR` lines `verify_post_anchor` prints are an artifact of that classifier lacking the four attestation paths `verify()` has, which is a separate defect recorded at the Phase 263 tribunal and excluded here.

**LD-6. Attestation parity would not close this issue, so it is excluded rather than bundled.** Measured against the two fixtures: `find_grandfathered_entries` returns an empty set for both, and `verify(tolerate_known_grandfathered=True)` still returns 1 for both. The reporter's entries fail as unparseable markup, not as an attested residual, so no tolerance channel reaches them.

### Changes

`verify_post_anchor` appends the verified count, the disclosed count, and the count above the boundary to both its clean and its dirty summary lines. The existing `post-anchor clean` and `boundary=#N` substrings are left in place at the front of the line.

`governance_health._ledger_damage` captures the strict verifier's output buffer it currently discards, counts its FAIL and TAINTED lines, and appends them to the OK note after the existing phrase.

### Unit Tests

- `tests/test_post_anchor_disagreement_disclosure.py::test_summary_line_reports_verified_and_disclosed_counts` - builds a ledger with a known number of valid entries and one pre-boundary failure, calls `verify_post_anchor`, and asserts the printed line carries both counts matching the fixture's composition. Red before: the line carries only the boundary.
- `tests/test_post_anchor_disagreement_disclosure.py::test_summary_line_distinguishes_an_empty_band_from_a_verified_one` - two fixtures with the same boundary, one where entries exist above it and one where none do, asserting the printed lines differ. This is the sentence GH #430 names; it fails today because the two are identical.
- `tests/test_post_anchor_disagreement_disclosure.py::test_exit_codes_are_unchanged_for_every_fixture_shape` - runs `verify_post_anchor` over the clean, pre-anchor-failure, post-anchor-failure and empty-ledger shapes and asserts each return equals the value recorded before the change. The phase's central promise is that no verdict moves; this is the assertion that would catch it if one did.
- `tests/test_post_anchor_disagreement_disclosure.py::test_ok_note_names_the_strict_failure_count` - constructs a ledger where strict fails and post-anchor passes, invokes `governance_health._classify_one`, and asserts the reason reports the strict FAIL and TAINTED counts. Red before: the reason is a fixed string that names neither.
- `tests/test_post_anchor_disagreement_disclosure.py::test_ok_note_keeps_the_existing_tolerance_phrase` - the same call, asserting the original substring still appears. This is the assertion that protects the three GH #199 contract tests from a future edit that rewrites the note instead of appending to it.
- `tests/test_post_anchor_disagreement_disclosure.py::test_status_stays_ok_when_only_the_strict_verifier_fails` - the same ledger, asserting `ArtifactStatus.OK`. The GH #199 contract is that this shape is not damaged; the phase must not change that while making it legible.
- `tests/test_post_anchor_disagreement_disclosure.py::test_a_ledger_that_passes_strict_gets_no_disagreement_note` - a fully valid ledger, asserting the reason names no strict count, because there is no disagreement to report. Guards against the note becoming unconditional noise.

## Definition of Done

### Deliverable: post-anchor disagreement disclosure

- **D1**: An operator whose strict verifier fails and whose post-anchor surface passes is told what the strict verifier found, instead of receiving a bare OK that discards it.
- **D2**: `verify_post_anchor` prints verified, disclosed and above-boundary counts on its summary lines; `governance_health._ledger_damage` appends the strict FAIL and TAINTED counts to its OK note. No signature, no return value and no status changes.
- **D3**: No doctrine or glossary change. Section 14 constrains the two modes' verdicts, not their diagnostics, and this phase changes only diagnostics. The seal entry records that GH #430's suggestions 1 and 2 were refused on measurement, so a future reader does not re-propose them.
- **D4**: The seven tests above pass, each red beforehand for its own stated reason, and the full suite stays green with no existing test amended -- verified by running it, not by enumerating call sites.

## Feature Inventory Touches

None. No user-facing command surface in `FEATURE_INDEX.md` changes; two diagnostic strings gain content.

## CI Commands

- `python -m pytest tests/test_post_anchor_disagreement_disclosure.py -v` - the new suite; run twice to confirm determinism
- `python -m pytest tests/test_post_anchor_verify.py tests/test_ledger_hash_duplicate_entry.py tests/test_ledger_hash.py tests/test_verify_ledger_cli.py tests/test_seal_entry_check.py tests/test_ledger_upgrade.py tests/test_governance_health.py tests/test_governance_health_post_anchor_tolerance.py tests/test_governance_health_json.py tests/test_cli_governance_health.py tests/test_qor_status_governance_health.py tests/test_variant_drift_governance_health.py -v` - every suite that reads either changed surface, including all six governance-health files
- `python -m pytest -q` - full suite; no regression
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity, run without a truncating pipe
- `ruff check .` - lint
