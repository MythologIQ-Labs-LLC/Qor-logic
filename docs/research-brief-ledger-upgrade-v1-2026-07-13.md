# Research Brief

**Date**: 2026-07-13T07:19:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #271 -- META_LEDGER versioned, self-migrating, one canonical API (minimal V1 slice)
**Scope**: version marker, one-command consumer recovery, coherence proof; deferral analysis for the emission-API unification

---

## Executive Summary

GH #271 is a multi-phase roadmap by its own structure. The consumer pain it
reproduces -- a ledger that goes DAMAGED after a toolkit update with no
recovery command -- is solved by a small V1: a machine-readable schema-version
marker at the ledger head, and a `ledger_upgrade` verb that orchestrates the
existing Phase 170 migrator + verifier into one safe operation (migrate to a
sibling temp, verify the RESULT, atomically swap only on success, never touch
the original on failure). The deeper unification (all skills emitting entries
through one canonical API) is DEFERRED with new evidence: the fragment API the
issue proposes as the emission path appends fragment bodies VERBATIM
(`ledger_fragment.canonicalize_fragments`, lines 107-132 verified live) -- the
WRITER still renders hash markup by hand, so swapping the seal flow onto
fragments would not, by itself, remove the duplicated format knowledge. A real
unification needs a typed entry renderer first (the issue's own Phase-3
scope).

## Findings

### F1. No version marker exists (verified live)

- `docs/META_LEDGER.md` head: title + Chain Status + Genesis; no
  machine-readable schema marker. A `<!-- qor:meta-ledger-schema=1 -->` comment
  line is inert to every consumer verified: `ledger_hash.verify` parses
  `### Entry` blocks; `seal_entry_check` parses the latest entry;
  `governance_health._ledger_damage` keys on title/entries presence;
  the Ledger badge counts entries.

### F2. The migrator is one verb away from a recovery command

- `qor/scripts/ledger_migrate.py`: `--input/--output` required, never
  in-place (main at 155-163; `--dry-run` supported); hashes preserved verbatim
  (markup moves, math does not); mismatches reported, never corrected.
- The missing orchestration: migrate -> verify the RESULT -> atomic
  `os.replace` swap on success only -> original byte-untouched on any failure.
  Acceptance verify is `ledger_hash.verify_post_anchor` (a re-anchored ledger
  with disclosed pre-anchor failures is a legal, healthy state per GH #199).

### F3. The emission-API unification is not a fragment-swap (deferral evidence)

- `qor/scripts/ledger_fragment.py:107-132` (verified live): canonicalization
  prepends `### Entry #N: <title>` and appends the fragment BODY VERBATIM --
  "Each fragment body must be a fully-formatted SESSION SEAL entry minus the
  heading line". Hash-markup knowledge stays with the writer. Unifying
  emission therefore requires a typed entry model + renderer (issue Phase-3
  scope), not a seal-flow rewrite -- and the substantiate skill just recovered
  its byte budget (Phase 178), which a Step 7 rewrite would re-spend.

### F4. Related surfaces (not in this slice)

- #234 (reconcile deferred-tail) is an independently shippable parse fix
  (queue-next). #268 (health stderr bleed) is an output-classification fix.
  #238's residual is seed-level `.gitattributes`. None block or are blocked by
  this slice.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Issue: consumer can self-heal format drift | No one-command path exists; migrate is two-step manual with no verify/swap | DRIFT (the V1) |
| Issue: one canonical emission API | Fragment API is a transport, not a renderer (F3) | DRIFT (deferred with evidence) |

## Recommendations

1. (P0) `qor/scripts/ledger_upgrade.py`: `upgrade(ledger_path, dry_run=False)`
   -- migrate to sibling temp, `verify_post_anchor` the result, ensure the
   schema-version marker, atomic swap on success; exit 1 + original untouched
   on residual mismatch. `schema_version(text) -> int` helper (absent marker
   == 0/legacy). CLI via the generic scripts runner.
2. (P0) Add the marker to this repository's own ledger (self-application).
3. (P1) Record the deferral (typed-renderer prerequisite, F3) on GH #271.

## Updated Knowledge

F3 corrects the issue's implicit assumption that fragment integration unifies
emission -- worth quoting in the disposition.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
