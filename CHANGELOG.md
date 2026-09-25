# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Merkle seal hashes for each release are recorded in `docs/META_LEDGER.md`; this
file is the user-facing narrative.

## [Unreleased]

### Fixed
- **Phase 297 (hotfix; truthful sealed-versus-published release state)**: release/tag coverage now treats the current project version as the only implicit untagged candidate and records older sealed-but-unpublished or legacy untagged versions explicitly, without manufacturing release tags or treating local seal tags as proof of publication.

## [0.175.0] - 2026-09-24

_Built via [Qor-logic SDLC](https://github.com/MythologIQ-Labs-LLC/qor-logic)._

### Added
- **Phase 296 (feature; governed re-attestation of sealed intent-lock evidence)**: the publication-boundary doctrine applies retroactively, but a sealed plan could not be corrected: CI's `intent_lock_committed` binds a sealed session's plan file and plan snapshot to its lock record, so any edit failed, and rewriting the record would erase the evidence. A walked session's plan hash can now be superseded by an append-only chain of `.qor/intent-lock/<session>.reattest-<k>.json` records (exactly four string fields, contiguous from 1), each committed by a META_LEDGER AMENDMENT whose line-leading `**Artifact**` names it. The checker folds the chain into an effective plan hash; the audit side is never superseded; uncommitted, edited-after-commit, non-chaining, malformed, and unwalked-session records fail as `reattestation-invalid`, and a malformed ledger becomes a failure rather than an exception. `ledger_commitment` now attributes `.json` artifacts.

  Used once: the two sealed plans that carried an outside-repository identity term are anonymized (one line each), their plan snapshots regenerated, the walked session re-attested and the unwalked one disclosed. The identity-aware seal-time boundary gate is clear again. Stated limits: the lock record itself is still hash-bound by nothing, so a coordinated direct edit remains undetected as before; AMENDMENT review is not machine-enforced; phase numbers must stay unique for a session to remain walked. See `qor/references/doctrine-publication-boundary.md` and `docs/operations.md`.
