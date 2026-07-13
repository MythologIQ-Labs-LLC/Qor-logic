# Plan: Phase 181 - Seed emits .gitattributes (GH #238 residual)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-seed-gitattributes-2026-07-13.md (ledger entry #442, session `2026-07-13T0758-7f394f`); GH #238 residual (the verify-layer half shipped in Phases 156-158).

## Locked Decisions

- **LD-1: one seed target + one template.**
  `grep -nE 'SEED_TARGETS' qor/seed.py -> 25`; `grep -nE 'def _write_file_if_missing' qor/seed.py -> 55` (never overwrites -- operator customizations survive re-seed by construction). New `SeedTarget(".gitattributes", "gitattributes.tpl", "file")`; template at `qor/templates/gitattributes.tpl` (non-dotted name inside package data) with the stanza pinning `docs/*.md`, `docs/**/*.md`, `.qor/**` to `text eol=lf`.
- **LD-2: scaffold-owned routing is correct and self-consistent.**
  `grep -nE 'def scaffold_file_targets|scaffold_file_targets' qor/seed.py -> 47`; SCAFFOLD_OWNED derives from file-mode SEED_TARGETS, so a missing `.gitattributes` in an initialized workspace routes to `qor-logic seed` (it IS seed-recoverable). The pinning test locks EQUALITY derived from SEED_TARGETS (`grep -nE 'seed_files = frozenset' tests/test_governance_health.py -> 117`), so it stays green by construction -- no test amendment.
- **LD-3: self-application at the repo root.**
  This repository gains the identical `.gitattributes`; committed blobs are already LF (git check-in normalization), the LF-canonical hashing (Phases 156-158) is byte-order-indifferent, and no renormalization commit is needed.

## Phase 1: Template + target + self-application (TDD first)

### Affected Files

- tests/test_seed_gitattributes.py - NEW; behavioral tests for the seeded stanza, no-overwrite idempotency, and the repo-root self-application
- qor/templates/gitattributes.tpl - NEW; the LF-pinning stanza
- qor/seed.py - SEED_TARGETS gains the `.gitattributes` entry
- .gitattributes - NEW at repo root (self-application)

### Changes

Template content: `docs/*.md text eol=lf`, `docs/**/*.md text eol=lf`, `.qor/** text eol=lf` with a one-line comment naming Phase 181 / GH #238. Seed target appended before the `.gitignore` append entry. Repo root copy identical to the template body.

### Unit Tests

- tests/test_seed_gitattributes.py::test_seed_creates_gitattributes_with_lf_stanza - `seed.run(tmp_path)` (the real entrypoint; verify exact name at implement) creates `.gitattributes` whose content pins `docs/*.md` and `.qor/**` to `eol=lf`
- tests/test_seed_gitattributes.py::test_reseed_never_overwrites_operator_customization - pre-write a customized `.gitattributes`, re-run seed, bytes unchanged
- tests/test_seed_gitattributes.py::test_repo_root_carries_the_stanza - the repository's own `.gitattributes` parses to the same LF-pinning rules as the template (self-application lock)

## Feature Inventory Touches

(empty -- governance scaffolding)

## Definition of Done

### Deliverable: architecture-level line-ending pinning

- **D1**: Seed-created repos carry the `.gitattributes` stanza so governance-artifact canonical bytes never drift with host autocrlf -- completing GH #238's second acceptance criterion (the first shipped in Phases 156-158).
- **D2**: Template + SeedTarget per LD-1; repo-root self-application per LD-3.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #238 disposition records completion of both criteria.
- **D4**: `test_seed_creates_gitattributes_with_lf_stanza` (red until the target exists) and `test_reseed_never_overwrites_operator_customization` observe the behaviors.

## CI Commands

- `python -m pytest tests/test_seed_gitattributes.py tests/test_governance_health.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
