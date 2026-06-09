# Research Brief

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: GH #199, #200, #201 -- governance-health preflight + ledger-seal robustness defects
**Scope**: `qor/scripts/governance_health.py`, `qor/scripts/ledger_hash.py`, `qor/scripts/ledger_fragment.py`

---

## Executive Summary

All three issues are genuine, currently-unfixed defects in qor-logic's own tooling (no PR
addresses them; the May-2026 search hits are coincidental number-substring matches). They were
filed from a downstream FailSafe remediation, so the local ledger is clean -- but the code paths
are shared, so the defects are reproducible here by construction. The three are a coherent
**governance-health + ledger-seal robustness** cluster touching two files. They interact:
a #201-corrupted ledger fails `governance_health` at the UTF-8 read (DAMAGED/unreadable) *before*
chain verification, so #199's tolerance logic is never reached. Prevention (#201) precedes
tolerance (#199); #200 is independent.

## Findings

### #201 -- Ledger seal admits non-UTF-8 bytes (highest blast radius)

- **Corruption signature**: 19 codepoint-truncated punctuation bytes in a DELIVER-seal entry --
  em-dash U+2014 -> `0x14` (x12), en-dash U+2013 -> `0x13` (x4), right-quote U+2019 -> `0x19`
  (x1), arrow U+2192 -> `0x92` (x2). The two `0x92` bytes are **invalid UTF-8**.
- **Load-bearing**: SHA-256 of the corrupted body equals the stored Content Hash, i.e. the bad
  bytes were present at seal time and the recorded hashes commit to them.
- **Read sites that break**: every UTF-8 reader of the ledger raises `UnicodeDecodeError` at the
  first invalid byte:
  - `ledger_hash.read_text(encoding="utf-8")` -- `qor/scripts/ledger_hash.py:195,286,407,473`
    (powers `verify`, `verify_post_anchor`, `find_grandfathered_entries`, `extract_ssdf_practices`).
  - `governance_health._classify_one` -- `qor/scripts/governance_health.py:157`; the `except
    (OSError, UnicodeDecodeError)` at `:158-159` then classifies the ledger `DAMAGED`
    ("unreadable") and **never reaches chain verification**.
- **Root cause**: the seal step computes the content hash over **raw bytes** and writes them
  without asserting UTF-8 (let alone ASCII) validity. The hashing primitive is
  `ledger_hash.content_hash(path)` -- `qor/scripts/ledger_hash.py:25-30` -- which reads bytes
  directly (`open(path, "rb")`) with no decode/validation. The fragment path
  `ledger_fragment._body_hash(body)` (`qor/scripts/ledger_fragment.py:36-37`) re-encodes a Python
  `str`, which is always valid UTF-8 on re-encode -- so the `0x92` invalid bytes implicate a
  raw-bytes / cp1252 writer, not `str.encode`. `write_fragment` (`:40-50`) only checks that
  `content_hash == _body_hash(body)`; it does not validate the bytes are ASCII/UTF-8.
- **Doctrine tie-in**: `CLAUDE.md` already mandates "No em-dashes, smart quotes, or non-ASCII
  chars in code/data." The ledger write boundary does not enforce this doctrine, so the doctrine
  is advisory-only at exactly the point where violation is permanent.

### #200 -- Placeholder check false-positives on the bare substring 'TODO'

- **Root cause**: `governance_health._PLACEHOLDER_MARKERS` (`qor/scripts/governance_health.py:63-72`)
  contains the bare strings `"TODO"` and `"FIXME"`, matched by `if marker in text`
  (`:146-148`) -- a raw substring test. Any prose containing the letters T-O-D-O trips
  `INCOMPLETE` (e.g. "TODO stubs", "cosmetic TODOs", "a TODO list disguised as code").
- **Blast surface**: the non-ledger `_incomplete_reason` path (`:143-149`) applies to every
  required artifact except the ledger: CONCEPT, ARCHITECTURE_PLAN, SYSTEM_STATE, **SHADOW_GENOME**
  (narrative archaeology, most prose-dense), BACKLOG, FEATURE_INDEX, GOVERNANCE_INDEX.
- **Asymmetry already solved on the ledger path**: `_ledger_incomplete` (`:132-140`) only flags an
  *unfilled scaffold* ("### Entry" present => complete), explicitly so historical grounding-tag
  mentions inside sealed entries are not read as live placeholders. The non-ledger path lacks that
  discipline.
- **Latent locally**: `governance-health --profile skill-entry` reports SHADOW_GENOME `OK` here
  today (no "TODO" prose currently), so the bug is latent in this repo but root-caused and
  reproducible -- inject "TODO stubs" prose into any non-ledger artifact and it flips to INCOMPLETE.
- **Note**: the other markers (`INSTRUCTION:`, `[Your `, `{{verify`, `[ISO 8601`, `[Why `) carry a
  structural cue and are far less prone; `FIXME` shares TODO's bare-substring fragility.

### #199 -- Skill-entry gate has no disclosed-pre-anchor tolerance

- **Strict call**: `governance_health._verify_ledger_chain` (`qor/scripts/governance_health.py:118-121`)
  calls `ledger_hash.verify(ledger_path)` with **no tolerance flags**.
- **`verify()` tolerance paths both require duplicate-`previous_hash`**:
  - Grandfather (`qor/scripts/ledger_hash.py:281-285`, `find_grandfathered_entries` `:180-219`):
    only active when `tolerate_known_grandfathered=True` -- which `governance_health` does **not**
    pass, so `grandfathered = frozenset()` here. Requires shared `previous_hash` AND `num <= 207`.
  - Reconciliation (`:294-297`): `reconciled = _attested_reconciled(entries) &
    _duplicate_previous_hash_members(entries)`. The `&` is a deliberate security gate (`:222-237`)
    so a unique-`previous_hash` tampered entry cannot be laundered by attestation.
- **Single-lineage residuals match neither**: manual-era entries with a *unique* `previous_hash`
  (downstream report: #330/#331/#338/#339) fail strict math, are not in
  `_duplicate_previous_hash_members` (`{397,401}` only), and so hard-FAIL -- then every later entry
  is `TAINTED` by descent (`:337-342`).
- **The asymmetry**: `verify_post_anchor` (`:390-465`) **does** tolerate disclosed pre-anchor
  failures, emitting `DISCLOSED_PRE_ANCHOR` for entries `<= boundary` (`:449-450`); the docstring
  states "the post-anchor surface is what release gates check; pre-anchor failures are tolerated"
  (`:396-398`). `governance_health` never calls it. **Net: release gates tolerate the band while
  the skill-entry preflight hard-fails on it**, blocking every `/qor-*` skill (including
  `/qor-auto-dev-1`) that runs the preflight.
- **Proposal A** (lower risk, reuses tolerated surface): for the `skill-entry` profile,
  `governance_health` consults `verify_post_anchor` (or a `disclosed_residual=True` mode of
  `verify`) and classifies pre-boundary failures as `DISCLOSED_PRE_ANCHOR` rather than `DAMAGED`.
- **Proposal B** (stronger provenance): a reconciliation variant for single-lineage manual-era
  entries gated on an explicit operator-signed attestation entry instead of the
  dup-`previous_hash` heuristic.
- **Security note on A**: `verify_post_anchor` auto-detects boundary as the highest entry that
  classifies `ok` (`:440-443`), so tolerating everything pre-boundary could mask tampering of an
  old entry. This is already the accepted release-gate posture; skill-entry is a softer gate than
  release, so adopting the same tolerance is defensible. B trades convenience for an explicit
  human signature and avoids the auto-boundary blind spot.

## Blueprint Alignment

| Blueprint Claim (doctrine/intent) | Actual Finding | Status |
|---|---|---|
| Ledger never contains non-ASCII / always UTF-8 readable (`CLAUDE.md` ASCII rule) | Seal write boundary asserts nothing; raw-byte hash commits invalid UTF-8 permanently (#201) | DRIFT |
| Placeholder detection flags template scaffolds, not prose (ledger path `:132-140` does this) | Non-ledger path uses bare-substring `"TODO"`/`"FIXME"` (#200) | DRIFT |
| Skill-entry preflight gates genuine damage, parity with release-gate tolerance (`doctrine-governance-enforcement`) | Strict `verify()` rejects disclosed pre-anchor residuals that `verify_post_anchor` tolerates (#199) | DRIFT |
| `verify_post_anchor` exists to tolerate disclosed pre-anchor band (`:396-398`) | Correct, but `governance_health` never consults it | DRIFT (wiring gap) |

## Recommendations

1. **#201 first (P0 / ~L2)** -- add a UTF-8/ASCII validity assertion at the ledger write boundary
   *before* the content hash is computed (`ledger_fragment.write_fragment` and/or a guard around
   `ledger_hash.content_hash` for ledger writes). Reject or normalize smart punctuation
   (`-- - ' ->`). Aligns with the existing `CLAUDE.md` ASCII doctrine; makes this corruption class
   impossible by construction. Highest blast radius (an invalid-UTF-8 ledger is unreadable and
   requires restoring original bytes + re-chaining every downstream entry to repair).
2. **#199 next (P1 / ~L2)** -- prefer **Option A**: route the `skill-entry` profile through the
   already-tested `verify_post_anchor` tolerated surface (classify pre-boundary as
   `DISCLOSED_PRE_ANCHOR`, not `DAMAGED`). Lower risk than B and reuses shipped logic. Document the
   auto-boundary security caveat; offer B as the stronger opt-in if operators want explicit
   attestation. Sequence after #201 (a corrupted ledger fails the read before tolerance is reached).
3. **#200 last (P2 / ~L1)** -- tighten `_PLACEHOLDER_MARKERS` matching to **template form**:
   word-boundary plus structural cue (`TODO:`/`FIXME:` at line start, `<!-- TODO`, `{{...}}`,
   `[Your ...]`), not a bare substring. Mirror the discipline already in `_ledger_incomplete`.
   Independent of the other two.

**Phasing**: one cohesive plan (`change_class: feature`) covering all three is reasonable -- they
share the `governance_health.py` / `ledger_hash.py` / `ledger_fragment.py` surface and a common
theme (make the governance health/seal boundary robust to real-world byte/prose input). Each lands
as its own test-first commit. Alternatively split #201 (prevention, urgent) from the #199/#200
hardening pair. TDD mandatory per `CLAUDE.md`: red test per defect (corrupt-byte fixture for #201,
prose-with-TODO fixture for #200, single-lineage-residual ledger fixture for #199), then green.

## Updated Knowledge

Candidate Shadow Genome residual to record on implementation: **SG-LedgerByteIntegrity** -- the seal
boundary trusted writer encoding and committed non-UTF-8 bytes into a hash-sealed entry, and the
skill-entry preflight applied stricter chain tolerance than the release gate. Lesson: validity must
be asserted at the *write* boundary (prevention), and tolerance surfaces must be consistent between
preflight and release gates (no gate stricter than the one that actually ships).

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
