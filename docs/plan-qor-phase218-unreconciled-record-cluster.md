# Plan: unreconciled-record cluster (Phase 218, GH #319: #313/#316/#318/#321)

**change_class**: feature

**doc_tier**: system

**terms_introduced**: ledger sequence assertion, verdict reconciliation

**boundaries**:
- limitations: Four checks are corrected to reject input they currently accept.
  None of them gains new authority, and none becomes able to detect a class it
  was not already responsible for. The ledger sequence assertion detects a
  deleted entry within one file; it cannot detect a ledger truncated at the tail,
  because nothing downstream of the last entry exists to contradict it.
- non_goals: No rewrite of historical entries. No renumbering to close the
  existing `#531 -> #533` gap -- doing so would invalidate every downstream chain
  hash. No change to `qor-substantiate`, which sits at 28 bytes of slack.
- exclusions: #309, #314, #320 are out of scope. #320 in particular is gated on
  observed drift data and must not be pulled forward.

## Open Questions

None.

## Locked Decisions

**LD-1 — #316 is a sequence assertion; numbering is the weaker symptom.**

`git show HEAD:qor/scripts/ledger_hash.py | grep -n 'def chain_hash' -> 46:def chain_hash(content: str, prev: str) -> str:`

Verified by counterfactual, not by reading. Corrupting an entry's
`previous_hash` already returns rc=1, because `chain_hash` is a function of it.
Excising entry #544 entirely returns rc=0 with `OK Entry #545: chain hash
verified` -- every survivor stays internally consistent.

The fix is therefore to assert that each entry's `previous_hash` equals the
`chain_hash` of the entry **physically preceding it in the file**, which is a
cross-entry claim the current per-entry arithmetic never makes.

**File order, explicitly -- not number order.** The two are not equivalent here,
and the difference decides whether the check works at all:

```
file-order   (#533.prev == #531.chain): True
number-order (#533.prev == #532.chain): #532 absent -> FAIL
```

Number order fails this repository's own ledger at every gap. File order is also
the correct semantics on the merits: the chain is built by appending, so the
sequence claim is about adjacency in the artifact, and entry numbers are labels
rather than load-bearing structure. That is precisely why deletion is the
detectable case and renumbering the weaker one.

Entry-number contiguity is a separate, weaker signal and ships as WARN.

**The exception list is measured, not asserted.** Enumerated from the ledger
rather than recalled:

```
gaps in numbering: [510, 532]
```

Both are verified absent from every commit (`git log --all -S "Entry #510"`
returns nothing; #532 was allocated in an abandoned session during Phase 215 and
never committed). Neither can be closed: renumbering would invalidate every
downstream chain hash. `KNOWN_ENTRY_GAPS = frozenset({510, 532})`.

An earlier draft of this plan seeded the list with 532 alone, from memory. The
second gap surfaced only when the file-order question above was tested against
real data. The list must be derived by measurement in the test as well, so a
future gap cannot be silently normalized by editing a constant.

**LD-2 — #318 applies an existing lesson to a second site.**

`git show HEAD:qor/scripts/ledger_hash.py | grep -n 'replace(b' -> 37:    data = Path(path).read_bytes().replace(b"\r\n", b"\n")`

`ledger_hash.content_hash` normalizes CRLF before hashing and its docstring names
GAP-GOV-03 as the reason. `intent_lock._hash_file` does not. The fix is the same
two-line treatment, not a new design.

The normalization must not swallow real drift: a test asserts that a genuine
content change is still detected after the change, or the fix trades a false
ABORT for a false PASS -- the strictly worse direction.

**LD-3 — #313 compares digests, not paths.**

`git show HEAD:qor/skills/sdlc/qor-implement/SKILL.md | grep -n 'AUDIT_REPORT' -> 134:Read: .agent/staging/AUDIT_REPORT.md`

The gate artifact already carries `target` and `target_content_hash`. Comparing
only the path would catch this session's three stale-report occurrences but would
still accept a report written against a since-amended plan. The digest comparison
catches both and costs nothing extra.

`.agent/staging/` is not session-scoped, which is why the stale window is
unbounded rather than a race. The reconciler treats an absent artifact as a
finding, not as permission.

**LD-4 — #321 separates the completeness list from the verification scope.**

`git show HEAD:qor/scripts/gate_provenance.py | grep -n '_REQUIRED_PHASES =' -> 44:_REQUIRED_PHASES = ("plan", "audit", "implement", "substantiate")`

`_REQUIRED_PHASES` answers "which artifacts must exist for a phase to be
complete." It is reused at `:226` to answer "which artifacts do we verify," and
those are different questions. Iteration artifacts must exist for nothing, but
they are evidence and must verify.

The scope becomes "every `*.json` in the session directory that has a sidecar."
`_REQUIRED_PHASES` keeps its original meaning.

**LD-5 — Every fix ships a counterfactual test.**

Each of these four checks passes today on input it should reject. A test
exercising the good path would pass before the change and prove nothing.

Every fix therefore ships a test that constructs the input the check currently
accepts and asserts rejection. That test must fail against `HEAD` and pass after.
Where a check already catches a neighbouring case, a second test pins that it
still does -- the risk of a sequence assertion is that it replaces per-entry
arithmetic rather than adding to it.

## Phase 1: Ledger sequence assertion (#316)

### Unit Tests

- `tests/test_ledger_sequence.py::test_deleted_entry_is_detected` - the
  counterfactual. Builds a ledger, excises a middle entry leaving every survivor
  internally consistent, asserts non-zero exit naming the break. Fails at HEAD.
- `::test_tampered_previous_hash_still_detected` - regression. The existing
  per-entry arithmetic must survive the addition.
- `::test_intact_ledger_verifies_clean` - no false positives on a good chain.
- `::test_number_gap_warns_without_failing` - a numbering gap is reported and
  exits 0.
- `::test_declared_gap_exceptions_are_silent` - parametrized over BOTH declared
  gaps (510 and 532); each produces no finding.
- `::test_live_ledger_gap_set_matches_declared_exceptions` - enumerates gaps from
  `docs/META_LEDGER.md` and asserts the set equals `KNOWN_ENTRY_GAPS`. Goes red
  if a new gap appears OR if someone widens the constant to silence one, which
  is the failure mode that let 510 go unnoticed.

### Affected Files

- `qor/scripts/ledger_hash.py` - add the cross-entry sequence assertion (file
  order) and the contiguity WARN with `KNOWN_ENTRY_GAPS = frozenset({510, 532})`.
- `tests/test_ledger_sequence.py` - NEW.

### Changes

The sequence check runs alongside the per-entry arithmetic, never instead of it.
`KNOWN_ENTRY_GAPS` carries a comment naming why each number is absent -- both
were allocated in sessions whose entries were never committed -- so the exception
is self-documenting rather than a pair of magic numbers.

## Phase 2: Intent-lock line-ending invariance (#318)

### Unit Tests

- `tests/test_intent_lock_lf_invariance.py::test_hash_is_line_ending_invariant` -
  the counterfactual. Same content as CRLF and as LF hashes identically. Fails at
  HEAD.
- `::test_real_content_drift_still_detected` - a genuine edit still changes the
  hash. Guards against trading a false ABORT for a false PASS.
- `::test_verify_survives_line_ending_conversion` - end to end: capture, convert
  the audit report's line endings, verify still passes.

### Affected Files

- `qor/reliability/intent_lock.py` - `_hash_file` normalizes CRLF to LF.
- `tests/test_intent_lock_lf_invariance.py` - NEW.

## Phase 3: Verdict reconciliation (#313)

### Unit Tests

- `tests/test_verdict_reconciliation.py::test_mismatched_target_is_rejected` - the
  counterfactual. A PASS report naming one plan and a gate artifact naming
  another yields a finding.
- `::test_matching_target_and_digest_accepted` - the good path.
- `::test_stale_content_hash_is_rejected` - matching paths but a report bound to a
  since-amended plan is rejected.
- `::test_absent_artifact_is_a_finding_not_permission` - a missing gate artifact
  does not silently pass.
- `::test_implement_step_invokes_the_reconciler` - the wiring coupling. Asserts
  `/qor-implement` Step 2 text names `verdict_reconcile`. Step 2 is prose, so
  nothing mechanical fails if the call is dropped and the module would sit in the
  tree looking like coverage. Precedent:
  `test_substantiate_skill_corpus_wiring.py::test_seal_step_invokes_the_check`,
  shipped one phase earlier for this exact reason.

### Affected Files

- `qor/scripts/verdict_reconcile.py` - NEW. `reconcile(report_path, artifact)`
  returning findings.
- `qor/skills/sdlc/qor-implement/SKILL.md` - Step 2 calls it before the
  interdiction. 20,087 bytes of slack; measured before and after regardless.
- `tests/test_verdict_reconciliation.py` - NEW.

## Phase 4: Provenance verification scope (#321)

### Unit Tests

- `tests/test_provenance_iteration_scope.py::test_corrupted_iteration_sidecar_is_detected` -
  the counterfactual. An `-iter1` sidecar whose digest does not recompute is
  reported. Fails at HEAD, where it returns OK.
- `::test_required_phase_artifacts_still_verified` - regression; the original
  scope is not lost.
- `::test_artifact_without_sidecar_is_skipped_not_failed` - absence of a sidecar
  is not corruption.

### Affected Files

- `qor/scripts/gate_provenance.py` - verification walks every `*.json` with a
  sidecar; `_REQUIRED_PHASES` keeps its completeness meaning.
- `tests/test_provenance_iteration_scope.py` - NEW.

## Phase 5: Documentation and record

### Affected Files

- `qor/references/doctrine-provenance-binding.md` - iteration artifacts are in
  scope for Layer B, and why.
- `docs/architecture.md`, `docs/operations.md` - the four corrected checks.
- `docs/SHADOW_GENOME.md` - the pattern: a control validated only against inputs
  it was built to accept, so its silence means "not asked" rather than
  "verified". `closure_enforcer` cites
  `tests/test_ledger_sequence.py::test_deleted_entry_is_detected`.

## Phase 6: Verification

### Unit Tests

- The four new test modules, run twice for determinism.
- The full suite.
- `dist_compile` zero-drift.
- `qor-logic scripts ledger_hash verify docs/META_LEDGER.md` against the live
  ledger, which must stay clean including the real 532 gap.

## Definition of Done

### Deliverable: the four checks reject what they accept

- **D1**: A deleted ledger entry, a line-ending-only change, a stale audit
  report, and a corrupted iteration sidecar each produce a finding.
- **D2**: `ledger_hash`, `intent_lock`, `verdict_reconcile`, `gate_provenance`
  ship the corrections.
- **D3**: Seal entry records that #316 was sharpened from the filed text --
  linkage was already verified; deletion was not -- that the correction came from
  a counterfactual rather than a re-read, and that a second ledger gap (510) was
  found only by enumerating rather than recalling.
- **D4**: Each fix has a test that FAILS against `HEAD` and passes after. Named
  explicitly per phase above.

### Deliverable: nothing existing is weakened

- **D1**: No check loses a class it already detected.
- **D2**: Regression tests pin tampered-`previous_hash` detection, required-phase
  provenance coverage, and real-content drift detection.
- **D3**: Seal entry states the live ledger still verifies clean with the real
  532 gap present, so the exceptions mechanism is exercised on real data rather
  than only in fixtures.
- **D4**: Full suite green; no existing test edited to accommodate a change.
- **D5**: The exceptions list is derived from the ledger by a test, not trusted
  as a constant, and the new module is coupled to its wiring by a test.

## Feature Inventory Touches

| Feature | Touch | Source-of-truth | test_descriptor |
|---|---|---|---|
| Ledger sequence assertion | NEW | `qor/scripts/ledger_hash.py` | `test_ledger_sequence.py::test_deleted_entry_is_detected` asserts a deleted entry yields non-zero exit |
| Verdict reconciliation | NEW | `qor/scripts/verdict_reconcile.py` | `test_verdict_reconciliation.py::test_mismatched_target_is_rejected` asserts a cross-phase report yields a finding |

## CI Commands

- `python -m pytest tests/test_ledger_sequence.py tests/test_intent_lock_lf_invariance.py tests/test_verdict_reconciliation.py tests/test_provenance_iteration_scope.py -q` — the counterfactual tests.
- `python -m pytest tests/ -q` — full suite; the definition of done for this plan.
- `python -m ruff check qor/ tests/` — the new modules are lint clean.
- `qor-logic scripts ledger_hash verify docs/META_LEDGER.md` — the live ledger stays clean with the real 532 gap.
- `qor-logic scripts dist_compile` — variants rebuilt with zero drift.
- `qor-logic scripts sg_closure_lint` — the new Shadow Genome entry carries an enforcer citation.
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase218-unreconciled-record-cluster.md` — this plan asserts each path and command identically at every site.
