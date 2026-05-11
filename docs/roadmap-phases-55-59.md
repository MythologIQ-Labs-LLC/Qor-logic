# Roadmap: Phases 55–59 (post-GH-#48-#52 work-stream)

Sequences the 5 unsealed plans authored from GH issues #48–#52 plus operator-raised governance-capability-surface work. Renumbering note: Phase 59 was originally authored as Phase 54 and collided with the in-flight compiler-evaluation-loop seal (v0.54.0, META_LEDGER #157); renumbered 2026-05-11 to the next free slot after Phase 58.

Doctrine: each phase carries its own plan top-matter and CI commands; this roadmap is the cross-phase sequence map.

## Phase table

| Order | Phase | Plan file | Closes | Class | Status | Why this order |
|---|---|---|---|---|---|---|
| 1 | 59 | plan-qor-phase59-seal-hash-integrity.md | GH #48 | hotfix | QUEUED | **CRITICAL** chain-integrity bug. Hash-guard gate must exist before any further substantiate cycles so subsequent seals fail closed on fabricated hashes. No structural dependency on other queued phases. |
| 2 | 55 | plan-qor-phase55-implement-documentation-lifecycle.md | GH #52 | feature | QUEUED | Self-contained: `qor-implement` skill + `implement.schema.json` only. Independent of all other queued phases; ships cleanly any time after 59. |
| 3 | 57 | plan-qor-phase57-audit-adversary-and-sdk-alignment.md | GH #50, #49, #47 follow-up | feature | QUEUED | Closes 3 issues in one bundle — highest leverage. Touches `qor-audit` Step 3 + doctrine SG entries. Doesn't depend on 55/56/58 surfaces. |
| 4 | 56 | plan-qor-phase56-federated-ledger-entry-identity.md | GH #51 | feature | QUEUED | Touches ledger entry shape (new `ledger_entry_id.py` + `ledger_fragment.py` + canonicalization). **Must land AFTER 59** so the seal-hash integrity gate is enforcing when the ledger format evolves; fabricated UUIDs/UIDs would otherwise enter the chain. |
| 5 | 58 | plan-qor-phase58-governance-capability-surface.md | operator-raised | feature | QUEUED | Plan top-matter explicitly notes "after GH #47-#52 triage." Depends on 55-57 patterns stabilizing because the capability surface aggregates evidence from the audit / implement / substantiate gates those phases mature. Last in queue. |

## Cross-phase invariants the roadmap protects

1. **Chain-integrity-first**: Phase 59 ships before any feature that mutates ledger entry shape (Phase 56). Failure to enforce this ordering recreates GH #48's failure mode at the new entry shape.
2. **One issue → one canonical phase**: Phase 57 bundles three issues by design (all share the `qor-audit` Step 3 surface). No issue is split across phases. Coverage verified by the 2026-05-11T14:30Z audit at `.qor/gates/2026-05-11T1430-issue-coverage-audit/audit.json`.
3. **No phase regression**: each plan declares `originating_remediation` cross-referencing a sealed phase's invariants when applicable. Phases 56 and 59 both touch ledger-side surfaces; the Step 6.8 hash-integrity gate (Phase 59) covers Phase 56's entry-UID emission.
4. **Self-application discipline**: every phase plan is lint-clean under `plan_text_consistency_lint` V2 default (verified 2026-05-11T14:30Z). Phase 49 pipeline-inversion lint applies to any new helper module landing in Phases 55-59.

## Version sequence (recommended; bump_version determines at seal time)

| Phase | Class | Pre-seal version | Post-seal version |
|---|---|---|---|
| 59 | hotfix | 0.54.0 | 0.54.1 |
| 55 | feature | 0.54.1 | 0.55.0 |
| 57 | feature | 0.55.0 | 0.56.0 |
| 56 | feature | 0.56.0 | 0.57.0 |
| 58 | feature | 0.57.0 | 0.58.0 |

Phase-number to version-number alignment was already broken at v0.45.0 (worktree-tag collision skipped 0.32-0.44); this roadmap honors SemVer over phase-number cosmetics. Each plan's CI commands and ledger entry use the post-seal version explicitly.

## Per-phase acceptance digest

Pulled from each plan's top-matter `boundaries` block. Operator should re-read each plan in full before invoking `/qor-audit` for it.

### Phase 59 — seal hash integrity (GH #48 CRITICAL)
- New `qor/scripts/hash_guard.py` with `HashEvidence`, `validate_sha256`, `require_toolkit_modules`.
- New `qor-substantiate` Step 6.8 Seal Hash Integrity Gate; ABORTs on missing toolkit OR placeholder/short/uppercase hash strings.
- `ledger_hash.verify` validates parsed hash fields before chain comparison.
- 14 unit tests across 3 new test files.

### Phase 55 — implement documentation lifecycle (GH #52)
- `qor-implement` SKILL gains a documentation implementation step (no longer back-loaded to substantiate).
- `implement.schema.json` gains `documentation_touches` array field.
- Plan-declared doc tier + affected files drive accounting; semantic inference is V2.
- `qor-substantiate` retains documentation-currency check as final verifier.

### Phase 57 — audit adversary + SDK alignment (GH #50, #49, #47 follow-up)
- `qor-audit` SKILL codifies independent adversarial reviewer contract (Option B → Option A protocol).
- New "third-party SDK alignment" pass in Step 3 covers SDK surfaces, lockfiles, generated client types, source references; evidence-based, no network lookup.
- New "behavioral semantics claim" SG entry — distinct from SG-040 (structural ordering).
- Phase 49 Python pipeline-inversion lint helper unchanged; its findings feed the reviewer checklist.

### Phase 56 — federated ledger entry identity (GH #51)
- `qor/scripts/ledger_entry_id.py` (UID derivation; canonical form).
- `qor/scripts/ledger_fragment.py` (worker writes fragments; final ledger materialization is a single canonicalization step).
- `Entry #N` human-readable headings preserved AFTER canonicalization.
- Out of scope: distributed consensus, cross-repository replication, removing `docs/META_LEDGER.md`.

### Phase 58 — governance capability surface (operator-raised)
- New `qor/capabilities/` package: `types.py`, `context.py`, `risk.py`.
- New `qor/gates/schema/verification_request.schema.json`.
- Local-only V1: Python APIs, CLI output, gate artifacts. No network service. No remote documentation fetch.
- Depends on Phases 55-57 patterns stabilizing (capability surface aggregates evidence those phases mature).

## When NOT to follow this order

The roadmap is advisory. Skip-ahead is allowed when:

- An incident escalates a later phase to CRITICAL (Phase 56 federation becomes urgent if a federated worker breaks against the current ledger format).
- A SEALED phase needs an unplanned hotfix (those go at the front of the queue regardless of this roadmap).
- The operator chooses to split a planned phase further (e.g., shipping Phase 57's reviewer codification separately from its SDK alignment).

In any such case: update this file's `Order` column with the new sequencing and the rationale, before re-invoking `/qor-plan` against the affected plan.
