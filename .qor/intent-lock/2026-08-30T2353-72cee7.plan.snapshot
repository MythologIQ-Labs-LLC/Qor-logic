# Plan: Governed promotion of completed relay hotfixes (GH #389)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #389

**boundaries**:
- limitations: this phase promotes already-reviewed, already-integrated fixes; it introduces no new capability beyond the eight underlying issues' scopes.
- non_goals: does not resolve GH #366's third ask (a phase-optional selection path for consumers keying ledger entries by feature/issue id) -- that residual is split to GH #395 rather than erased by this promotion.
- exclusions: the individual relay branches' missing pre-implementation ceremonies are not retroactively fabricated; this phase's own ceremony governs the integrated head per the Phase 235 precedent.

## Open Questions

None.

## Locked Decisions

**LD-1: One integration branch, eight fixes, merge-integrated.** The completed relay fixes for GH #357, #359, #361, #362, #363, #364, #365, #366 (former PRs #367/#368/#369/#370/#371/#372/#386/#387) are consolidated on one branch based on post-#360 main. The two known overlap surfaces resolved through normal merges: `qor/scripts/ledger_hash.py` (#368/#370) and `tests/test_remediate.py` (#369/#371); neither change overwrote the other.

**LD-2: Ledger-fork enforcement (GH #361).** `qor/scripts/ledger_hash.py` gains a duplicate-entry-number check and gates the sequence-break tolerance. Verified: `grep -n "duplicate" qor/scripts/ledger_hash.py` -> duplicate-number detection present; regression suite `tests/test_ledger_hash_duplicate_entry.py` (176 lines) passes.

**LD-3: Honest zero-population reporting (GH #366, first two asks).** `qor/reliability/gate_chain_completeness.py` gains `zero_population` and WARNs on an empty inspected set instead of claiming completeness; seal-entry behavior pinned by `tests/test_seal_entry_check.py` regression coverage. The third ask (phase-optional selection) is split to a follow-up issue.

**LD-4: Consumer-extensible secret-scanner allowlist (GH #359).** `qor/scripts/secret_scanner.py` exposes a declaration surface for consumer allowlists with disclosure. Verified by `tests/test_secret_scanner.py` (122 new lines) behavioral coverage.

**LD-5: Remediation classifier closure (GH #362, #364).** `repeated_veto_pattern` gains a classifier rule and proposal mapping; `closure_enforcer` module/gate-step forms validate behavior beyond importability. Verified by tests/test_remediate*.py + tests/test_sg_closure_enforcement.py. Iteration 2 (independent-audit V1+V2): the batch-blocking test stages a real Step heading under its tmp repo_root so the raise fires on the invalid member (red-proved by neutering the four-forms rejection), and `_validate_gate_step` falls back to disclosed shape-only acceptance when the repo_root carries no qor/skills corpus (consumer-shaped trees), with a regression test covering fallback, shape rejection, and corpus-present enforcement. The semantic-relevance residual is split to GH #396.

**LD-6: FEATURE_INDEX Status alias (GH #365) + qor-audit headroom (GH #357).** `qor/scripts/feature_index_verify.py` accepts the `Status` column alias; qor-audit SKILL.md recovers size-budget headroom via progressive disclosure into `references/phase37-subpasses.md`.

## Phase 1: Integrated verification (work pre-existing)

### Affected Files

(as merged on this branch; 22 product files plus the 17-file dist recompile relative to main)

- tests/test_ledger_hash_duplicate_entry.py, tests/test_post_anchor_verify.py, tests/test_seal_entry_check.py, tests/test_secret_scanner.py, tests/test_gate_chain_completeness.py, tests/test_feature_index_verify_helper.py, tests/test_remediate.py, tests/test_remediate_enforcer_edges.py, tests/test_remediate_per_event_enforcers.py, tests/test_sg_closure_enforcement.py, tests/test_substantiate_staging_gates.py, tests/test_ledger_hash.py - regression coverage for the eight fixes.
- qor/scripts/ledger_hash.py, qor/scripts/ledger_dialect.py, qor/reliability/gate_chain_completeness.py, qor/scripts/feature_index_verify.py, qor/scripts/secret_scanner.py, qor/scripts/remediate_attestation.py, qor/scripts/remediate_pattern_match.py, qor/scripts/remediate_propose.py - the fixes.
- qor/skills/governance/qor-audit/SKILL.md + references/phase37-subpasses.md - headroom recovery.
- qor/dist/manifest.json + qor/dist/variants/** - recompiled qor-audit variants (the relay branch edited qor-audit source without regenerating; check_variant_drift reported stale content across all six targets on the integrated head).
- qor/scripts/seal_artifacts.py + tests/test_seal_artifacts.py - discovered at seal time: the header-currency check compared SYSTEM_STATE against max(sealed phase), assuming phases seal in ascending numeric order; Phase 244 merged before Phase 243, so the truthful header for this seal was reported as drift. Fixed red-then-green to file-order-last (the ledger is append-only, so the last SESSION SEAL entry is the most recent), which preserves the invariant's meaning and strengthens it for out-of-order seals.
- qor/references/glossary.md - registered qor/skills/governance/qor-audit/references/phase37-subpasses.md as a referenced_by consumer of the Doctrine term (the strict doc-integrity gate ABORTed on the relocated binding-VETO citations section until registered).

### Unit Tests

- The ten focused suites above: 141 tests, all invoking the changed units and asserting behavior (duplicate-number rejection, zero-population WARN, allowlist declaration honored, classifier rule closes the event, Status alias parsed, post-anchor unparseable-hash FAIL).

## Definition of Done

### Deliverable: promoted relay-hotfix set

- **D1**: The eight completed relay fixes reach main through one governed promotion, per GH #389.
- **D2**: The 22-file integrated delta as described in the Locked Decisions.
- **D3**: This phase's plan/tribunal/implement/seal ledger entries; PR #390 cites this plan and the Merkle seal; GH #366 residual split to GH #395 before closure.
- **D4**: Focused suites 141/141 green; full suite green twice for determinism.

## CI Commands

- `python -m pytest tests/test_ledger_hash_duplicate_entry.py tests/test_post_anchor_verify.py tests/test_seal_entry_check.py tests/test_secret_scanner.py tests/test_gate_chain_completeness.py tests/test_feature_index_verify_helper.py tests/test_remediate.py tests/test_remediate_enforcer_edges.py tests/test_sg_closure_enforcement.py tests/test_substantiate_staging_gates.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

**ci_commands**:
- `python -m pytest tests/test_ledger_hash_duplicate_entry.py tests/test_post_anchor_verify.py tests/test_seal_entry_check.py tests/test_secret_scanner.py tests/test_gate_chain_completeness.py tests/test_feature_index_verify_helper.py tests/test_remediate.py tests/test_remediate_enforcer_edges.py tests/test_sg_closure_enforcement.py tests/test_substantiate_staging_gates.py -q`
- `python -m qor.scripts.publication_boundary_lint`
- `python -m pytest tests/ -q`

## Governance note

The eight fixes were implemented and tested on relay branches whose PRs disclosed that no valid plan/ledger/Merkle evidence existed; those artifacts are not fabricated retroactively. This plan and its audit/implement/substantiate artifacts govern the integrated head, authored after the code was complete and verified green, per the Phase 235 precedent: every fact recorded is a true, independently-verifiable description of already-completed work, and the citation gate is satisfied because the artifacts it demands are real.
