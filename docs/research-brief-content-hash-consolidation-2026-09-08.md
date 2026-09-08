# Research brief: gate_provenance attests hash pairs that never coexisted

**Date**: 2026-09-08
**Session**: 2026-09-08T1751-c84a39
**Issues**: GH #467 (partially; the issue's own remedy is corrected below)

> **Revision note.** An earlier version of this brief asserted three things the phase's audit
> refuted: that `ledger_commitment`'s fix had no observable effect, that the 160-of-741 gap applied
> to all three modules, and that `gate_provenance`'s wrong-answer was latent. All three are wrong and
> are corrected here. The brief is rewritten rather than patched, because a partially-updated
> research artifact reads as current and is worse than a stale one.

## The defect

`gate_provenance.latest_seal_hashes` has a docstring promising the hash pair of

> "the last ledger entry that carries **both** canonical hash markers"

and an implementation that takes two independent whole-file last matches:

```python
content = re.findall(r"\*\*Content Hash\*\*:\s*`([0-9a-f]{64})`", text)
chain   = re.findall(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`", text)
if not content or not chain:
    return None
return content[-1], chain[-1]
```

Nothing constrains those to the same entry. **128 entries carry a backticked Content Hash without a backticked Chain Hash; 70 the reverse.** The `if not content or not chain` guard cannot detect a mismatch, because both lists are non-empty.

## It is realized, not latent

Replaying the ledger at each historical state -- the text truncated at the end of entry N -- and asking which entry owned each last match:

| | |
|---|---|
| states where both lists are non-empty | 640 |
| states where the two came from **different entries** | **187** (29% of 640; 24% of 765 entries) |
| span | entry #127 through #631 |

At the state ending in entry #631, the function returned `(content_of_630, chain_of_631)`. `ci_attest` (`gate_provenance.py:166`) HMACs `f"{content_hash}|{chain_hash}"`, and `.github/workflows/ci.yml:151` runs `attest-latest` on every push. Those attestations did not fail; they bound two unrelated entries, and nothing reported it.

**The most reachable trigger needs no unusual markup at all.** A ledger truncated after a new entry's content hash but before its chain hash -- an interrupted append -- makes the function return `(content_of_the_new_entry, chain_of_the_previous_one)`. Verified across five truncation shapes; the entry-anchored read returns `None` for all of them.

## The fix is strictly more available

| | |
|---|---|
| entry-anchored returns `None` where the current code returned a pair | **0** of 765 |
| entry-anchored returns a pair where the current code returned `None` | **100** |

The regression case requires the final entry to lack a parseable pair while an earlier entry has one. The 25 entries with no content+chain pair are all at or below **#122**, and `ledger_dialect.MARKUP_COMPAT_BOUNDARY = 123` makes markup mandatory at or above #123 -- so such a state is one `ledger_hash verify` rejects before `attest-latest` runs. Bounded by that boundary rather than proven impossible: the empirical 0 and the constant's contract are verified; every enforcement path for an unmarked entry appended above the cutoff is not.

No gate verdict moves either way -- `main()` prints `SKIP` and returns 0 on `None`.

## Per-module scope: the 160-of-741 figure is not portable

That is a whole-ledger count, and only `gate_provenance` scans the whole file.

| module | population it actually reads | narrow | dialect |
|---|---|---|---|
| `gate_provenance` | whole ledger | 581 | 741 |
| `evidence_bundle` | `### Entry #N: SESSION SEAL` blocks only | **168** | **235** |
| `ledger_commitment` | committing kinds carrying a citation | **256** | **337** |

All three narrow readers use `` `([0-9a-f]{64})` `` with no field suffix and only the inline-backtick value form. The gaps are real; the earlier attribution of one number to all three was not.

## `ledger_commitment` must NOT be consolidated

This is the correction that matters most, because #467's own "Fix" section recommends the opposite.

Its citation pattern is not `**Artifact**` alone:

```python
_ARTIFACT_RE = re.compile(r"^\*\*(?:Artifact|Plan|Brief)\*\*:\s*`?([\w./-]+\.md)`?", re.MULTILINE)
```

**491 entries match it.** Widening the hash pattern admits 81 new commitments (108 before `_COMMITTING_KINDS` filters at `:89`), of which **45 are SESSION SEAL entries labelled `**Content Hash (session seal)**` citing a `**Plan**`** -- a value that binds the seal digest, not the plan file:

| | entries | value equals the cited file's live hash |
|---|---|---|
| suffixed session-seal form | 45 | **0** |
| plain `**Content Hash**` form (control) | 147 | 99 |

Zero of 45 against 99 of 147. On-disk stale commitments would go 74 -> 116: **42 artifacts newly stale**, all `docs/plan-qor-phase*.md`, in a hard ABORT gate.

The module documents this at `ledger_commitment.py:27-31` and records how it was learned:

> A GATE TRIBUNAL entry cites `**Plan**` but its content hash binds the AUDIT REPORT, so treating that citation as a commitment would compare the plan's bytes against the report's digest -- a false stale reading. Found by running this gate against its own phase.

An earlier version of this brief asserted the opposite, having measured `**Artifact**` alone and not read the comment.

## `evidence_bundle` is a restructure, not a pattern swap

`_FIELD_RES` (`:25-32`) is a dict consumed by a generic loop at `:40-42`:

```python
block[key] = found.group(1) if found else None
```

`CONTENT_HASH_RE.groups == 3` -- one group per value form. Substituting it into that dict calls `.group(1)`, which is `None` for two of the three forms. Over the 235 seal blocks:

| field | narrow | dialect + `hash_value` | dialect + `.group(1)` |
|---|---|---|---|
| content_hash | 168 | 235 | 234 -- loses one silently |
| chain_hash | 219 | 235 | **219 -- zero gain** |

It also has **no production consumer**: nothing in `qor/skills/`, `.github/workflows/`, or any non-test module invokes it. The release workflow's "evidence bundle" is an unrelated inline heredoc producing `dist/evidence.json`.

## What the dialect does and does not guarantee

The obvious objection to consolidation is that importing the owner imports its over-reading (GH #428). Tested:

- prose hex **before** the field -- the real value is returned
- prose hex **after** the field -- the real value is returned
- prose hex **between** the label and its value -- **the prose value is returned**

`_HASH_SPAN` is lazy, so the first value form after the label wins. An earlier draft generalized from before/after only and claimed prose cannot displace the field; that is false as stated.

The load-bearing evidence is empirical rather than structural: across the **640** entries carrying an inline value on a label line, the dialect returns a value differing from that line **0 times**. No corpus entry exhibits the BETWEEN ordering. Entry #605, #428's own reproduction, no longer contains the shadow-event id and now reads correctly.

## The 160, broken down

| | count |
|---|---|
| real field, qualifier inside the markers (`**Content Hash (session seal)**:`, entry #137) | 60 |
| real field, qualifier outside, or a non-backtick value form | 100 |
| genuinely unlabelled, i.e. a true #428 false positive | **0** |

An earlier correction to #467 claimed 60 were #428 false positives and was itself retracted: the probe used was `^\*\*Content Hash\*\*`, which cannot match a qualifier inside the markers -- the form `_FIELD_SUFFIX` exists to support.

## Out of scope

- **#428** -- whether the owner over-reads. Not reproducible against the current dialect except in the BETWEEN ordering, which the corpus does not contain.
- **#461** -- the commitment gate's scope and its "N checked" reporting.
- **#468** -- the emitter half. **#469** -- the lint that would prevent recurrence, designed and parked.
