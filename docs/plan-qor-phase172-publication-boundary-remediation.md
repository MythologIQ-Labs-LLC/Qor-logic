# Plan: Phase 172 - Publication-boundary retroactive remediation

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: Git history is NOT rewritten (separately gated by operator authorization); recorded ledger hash fields are NOT touched (they attest pre-remediation bytes); behavior is preserved everywhere -- code changes are docstrings/comments plus the intent-lock relative-path seam. Closed/historical GitHub items are inventoried, not edited, this phase.
- non_goals: No Lessons-Learned records (nothing requires identifying context after anonymization; relocation-to-evade is prohibited); no hash rebinding or chain recompute; no lint hard-enforcement (WARN-only V1 in the audit ladder).
- exclusions: The operator-local terms file (`.qor/private/boundary-terms.txt`) is gitignored and never tracked.

## Open Questions

(none -- both Governor decisions recorded in research entry #407)

## Origin

Research brief docs/research-brief-publication-boundary-remediation-2026-07-04.md (ledger entry #407, session `2026-07-04T1840-46e4d9`); mandated follow-on to the publication-boundary policy baseline (root AGENTS.md, doctrine, host instructions, 3 policy tests -- carried uncommitted in this phase's tree per requirement 7).

## Locked Decisions

- **LD-1: binding reality drives the surface treatment.** `grep -nE 'def (chain_hash|verify)' qor/scripts/ledger_hash.py -> chain math consumes recorded fields`; `qor/reliability/seal_entry_check.py check_latest -> latest-seal plan binding only`; `qor/scripts/gate_provenance.py verify_sidecar -> keyless payload_sha256 over artifact bytes`. Therefore: ledger bodies edit freely; edited gate artifacts get regenerated sidecars; recorded hash fields stay verbatim.
- **LD-2: the tracked lint is structural-only.** Patterns: absolute local path shapes (`[A-Z]:[/\\]`, `/home/`, `/Users/`) outside fenced code that legitimately needs them; `github.com/<owner>/<repo>` URLs whose owner/repo differ from this repository's own; a cross-repo issue shape (`<Name>#<digits>`). An optional operator-local terms file (`.qor/private/boundary-terms.txt`, gitignored) supplies identity terms for local/CI-private runs. A tracked denylist would itself violate the boundary.
- **LD-3: intent-lock code seam.** `qor/reliability/intent_lock.py` capture writes absolute `plan_path`/`audit_path`; the fix stores repo-relative paths (verify resolves against the repo root), and the 7 TRACKED lock records are rewritten to relative form. Existing verify behavior preserved (round-trip tested).
- **LD-4: anonymization conventions (uniform).** `a sibling governance repository` / synthetic `External Repo A/B` where actors must stay distinct; `an external QA exemplar`; `an external agent-governance toolkit`; absolute external paths deleted or `an external workspace path`; cross-repo issue pointers -> `an external repository's issue`. Self-references (own org/repo URL, own `#N` issues) untouched. Legally required attribution text preserved minus repository-location detail.
- **LD-5: disclosure lives in the seal.** The SESSION SEAL entry for this phase carries the remediation disclosure (classes, counts, the statement that recorded hashes attest pre-remediation bytes retrievable in git history). No new ceremony artifact (SCHEMA_REGISTRY untouched; the Phase 169 freeze lint stays at 0).
- **LD-6: audit SKILL.md ladder headroom.** The file sits ~40934/40960 bytes; the new ladder line costs ~60 -- an equivalent trim inside Step 0.6 commentary is budgeted in the same edit.

## Phase 1: Structural lint + intent-lock seam (TDD first)

### Affected Files

- tests/test_publication_boundary_lint.py - NEW; behavioral tests for each structural pattern class, the self-reference allowance, the local-terms-file overlay, and exit codes
- qor/scripts/publication_boundary_lint.py - NEW (<160 lines, stdlib): walks tracked text files (git ls-files), applies LD-2 patterns + optional local terms; WARN lines + summary; exit 1 on findings (ladder wraps `|| true`)
- tests/test_intent_lock*.py (existing) - round-trip updated for relative paths
- qor/reliability/intent_lock.py - capture stores repo-relative paths; verify resolves both forms (grandfathers absolute historical records)
- .gitignore - `.qor/private/` entry
- qor/skills/governance/qor-audit/SKILL.md - Step 0.6 gains `qor-logic scripts publication_boundary_lint || true` with LD-6 trim

### Unit Tests

- tests/test_publication_boundary_lint.py::test_flags_absolute_local_paths - synthetic tracked file with a drive-letter path and a `/Users/` path -> both flagged with file:line
- tests/test_publication_boundary_lint.py::test_flags_foreign_github_urls_not_self - own-repo URL passes; a different owner/repo URL is flagged
- tests/test_publication_boundary_lint.py::test_flags_cross_repo_issue_shape - `SomeRepo#123` flagged; own `#123` bare reference passes
- tests/test_publication_boundary_lint.py::test_local_terms_file_overlay - with a tmp terms file, listed identity terms are flagged; without it, only structural findings appear
- tests/test_publication_boundary_lint.py::test_exit_codes - clean tree fixture exits 0; any finding exits 1
- (existing intent-lock suite) - capture writes relative paths; verify passes on both relative and legacy-absolute records

## Phase 2: Tree sweep

### Affected Files

- docs/META_LEDGER.md - 23 sealed entry BODIES anonymized per LD-4 (recorded hash fields verbatim)
- CHANGELOG.md, docs/SYSTEM_STATE.md, docs/CONCEPT.md, docs/BACKLOG.md, docs/operations.md - prose anonymized
- docs/research-brief-*.md (today's three estate-referencing briefs) and docs/plan-qor-phase170-estate-consolidation.md + any legacy plan hits - anonymized
- qor/references/doctrine-shadow-genome-countermeasures.md, qor/references/doctrine-attribution.md, qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md - incident narratives anonymized
- qor/scripts/{seal_artifacts,ledger_migrate,evidence_bundle,status_json,session_tool}.py + .github/workflows/nightly-health.yml - docstring/comment mentions anonymized (zero behavior change)
- .qor/gates/<7 sessions>/*.json + regenerated *.provenance sidecars (LD-1)
- .qor/intent-lock/<7 tracked>.json - rewritten relative (LD-3)
- qor/dist/** - recompiled from cleaned canonical sources

## Phase 3: Published GitHub surfaces

All OPEN issues plus every issue/PR body/comment created 2026-07-04 edited per LD-4; a closed/historical-item inventory is recorded as the follow-on worklist in the seal disclosure.

## Feature Inventory Touches

(empty -- governance/documentation remediation; no user-touchable `src/` feature)

## Definition of Done

### Deliverable: clean tracked tree

- **D1**: No tracked or generated surface identifies an outside repository; the doctrine's retroactive clause is satisfied at tip-of-tree.
- **D2**: Structural lint + local-terms overlay report ZERO findings over the tracked tree (terms file populated locally for verification); policy tests + full suite green; every ledger/provenance/completeness gate green after sidecar regeneration.
- **D3**: Seal entry carries the LD-5 disclosure; dist regenerated; Codex baseline files committed intact.
- **D4**: `test_local_terms_file_overlay` + the lint's live zero-finding run (recorded in the seal) observe the clean baseline; the full gate ladder observes binding integrity.

### Deliverable: boundary lint

- **D1**: Future violations surface at every audit without the lint itself naming any outside identity.
- **D2**: `publication_boundary_lint.py` <160 lines, structural + overlay design per LD-2.
- **D3**: Wired WARN-only in the audit Step 0.6 ladder within the size budget (LD-6).
- **D4**: The five behavioral tests observe each pattern class and both exit codes.

## CI Commands

- `python -m pytest tests/test_publication_boundary_lint.py tests/test_publication_boundary_policy.py -q` -- new-lint determinism + policy baseline (run twice)
- `python -m pytest -q` -- full suite regression
- `qor-logic scripts publication_boundary_lint` -- live zero-finding verification
- `qor-logic scripts plan_text_consistency_lint --check docs/plan-qor-phase172-publication-boundary-remediation.md` -- plan-text consistency
