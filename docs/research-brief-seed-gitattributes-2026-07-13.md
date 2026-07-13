# Research Brief

**Date**: 2026-07-13T07:59:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #238 residual -- `.gitattributes` in seed (autocrlf drift, architecture-level defense)
**Scope**: what already shipped, the seed mechanics, the scaffold-owned pinning constraint

---

## Executive Summary

GH #238's verification-layer half already shipped: every seal-relevant digest
is LF-canonical (Phases 156-158: `ledger_hash.content_hash`,
`gate_provenance._normalize`, `hash_guard.hash_file(normalize_newlines=...)`),
and the acceptance criterion "verify-ledger passes under autocrlf=true" holds.
The residual is the ARCHITECTURE-level defense: `qor-logic seed` does not emit
a `.gitattributes` pinning governance artifacts to LF, so consumer repos'
canonical bytes still drift with host autocrlf settings. Verified live: no
template exists (`qor/templates/`), no repo-root `.gitattributes`, and the
seed machinery (`qor/seed.py` SEED_TARGETS, `_write_file_if_missing` -- never
overwrites) is one entry away. One constraint the prior scout missed:
`scaffold_file_targets()` derives governance-health's SCAFFOLD_OWNED from
file-mode SEED_TARGETS, and a pinning test locks that set -- the addition is a
deliberate amendment of both.

## Findings

### F1. Already shipped (no action)

- LF-canonical hashing across ledger/provenance/hash-guard (Phases 156-158,
  file:line evidence in the prior dossier); prior scout classified every other
  raw-bytes digest as CRLF-immune (non-committed or in-memory).

### F2. Seed mechanics (verified live)

- `qor/seed.py:25-35`: SEED_TARGETS tuple; modes `file` (via
  `_write_file_if_missing`, line 55 -- idempotent, never overwrites),
  `gitkeep`, `gitignore_append`. Templates live in `qor/templates/` (8 files,
  no `.gitattributes`). Adding `SeedTarget(".gitattributes", "gitattributes.tpl", "file")`
  + the template is the whole mechanism. (Template filename avoids a leading-dot
  file inside the package data dir; content is the stanza.)
- `qor/seed.py:47` (`scaffold_file_targets`): file-mode targets BECOME
  governance-health's SCAFFOLD_OWNED -- a missing `.gitattributes` in an
  initialized workspace would route to `qor-logic seed` (correct semantics:
  it IS seed-recoverable). `tests/test_governance_health.py`'s
  scaffold-owned pinning test locks the set and must be amended deliberately.

### F3. Stanza content

- Pin the governance surfaces the hashes bind: `docs/*.md`, `docs/**/*.md`,
  `.qor/**` as `text eol=lf`. This makes canonical AND working-tree bytes LF
  for those paths regardless of host autocrlf -- the drift class disappears at
  the infrastructure level instead of being tolerated at verify time.

### F4. Self-application

- This repository's root carries no `.gitattributes` (verified). Adding the
  same stanza here mirrors Phase 179's marker self-application. Existing
  committed blobs are already LF (git normalizes at check-in); the file
  changes future checkouts only -- no renormalization commit needed, and the
  LF-canonical hashing (F1) is indifferent either way.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| GH #238 AC-1: verify under autocrlf | Holds since Phases 156-158 | MATCH (already resolved) |
| GH #238 AC-2: seeded repos carry the stanza | No template, no target | DRIFT (this residual) |

## Recommendations

1. (P0) `qor/templates/gitattributes.tpl` + `SeedTarget(".gitattributes", ...)`;
   amend the scaffold-owned pinning test deliberately.
2. (P0) Repo-root `.gitattributes` (self-application) + doctrine line in the
   governance-enforcement durability/hashing area noting the two-layer defense
   (normalize-at-verify + pin-at-checkout).
3. Tests: seeded tree contains the stanza; re-seed never overwrites an
   operator-customized `.gitattributes`.

## Updated Knowledge

None; completes GH #238's recorded residual.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
