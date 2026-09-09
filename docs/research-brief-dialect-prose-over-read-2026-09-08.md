# Research brief: the hash-field owner matches a label written in prose

**Date**: 2026-09-08
**Session**: 2026-09-08T2348-16c62e
**Issues**: GH #428

## The correction this brief exists to make

Phase 277 examined GH #428 and placed it out of scope with this finding:

> **#428** -- whether the owner over-reads. Not reproducible against the current
> dialect except in the BETWEEN ordering, which the corpus does not contain.

The first half is wrong. The over-read **is** reproducible against the current
dialect and it **is** in the corpus. `docs/META_LEDGER.md` entry #741 contains:

```
Entries #109, #111 and #113 carry an identical `**Previous Hash**` of
`1cc74e892f2cab70e161cfbad195579d874d7a94bad20cb322f3d21cb876169e` at lines ...
```

`ledger_dialect.PREV_HASH_RE` matches that sentence and `hash_value` returns the
prose digest. This is exactly the shape #428 reports: a 64-hex string in entry
prose read as the entry's own field.

Phase 277's measurement was not wrong about what it measured. It measured
whether the dialect returns a value *differing from the label line* across the
640 entries carrying an inline value, and got zero. A label written inside
backticks in a narrative sentence is not one of those 640, so the probe could
not see it. The conclusion was broader than the measurement.

## It is harmless today, and only by accident

Entry #741 carries its own real `**Previous Hash**:` field, and that field
appears **before** the prose sentence. Readers use `.search()`, which returns
the first match, so the correct value is returned:

| match order in entry #741 | value |
|---|---|
| 1. the real field line | `75a6b901...` correct |
| 2. the prose sentence | `1cc74e89...` wrong, never reached |

Nothing structural produces that ordering. An entry whose narrative discusses a
hash before its own field lines would return the prose digest. The protection is
the order somebody happened to write two paragraphs in.

This is the ordering-sensitivity trap on record: one shape cannot measure an
ordering-dependent property. The corpus is safe in the ordering it happens to
have, and that is not the same as the reader being correct.

## The second half, which Phase 277 got right

Prose hex **between** a label and its value on the same line returns the prose
value, because `_HASH_SPAN` is lazy and the first value form after the label
wins. Reconfirmed independently:

| ordering | current result |
|---|---|
| prose hex before the field | real value |
| prose hex after the field | real value |
| prose hex between label and value | **prose value** |

No corpus entry exhibits BETWEEN. Both halves are the same root cause: the span
between a label and its value admits arbitrary text.

## Why the span cannot simply be tightened

The obvious remedy is to require the value immediately after the colon. Measured
against the live ledger, the connective text between label and value is:

| form | count |
|---|---|
| `: ` plain | 2019 |
| code-fenced `SHA256(...)` formula, then `= ` | ~120 |
| bare newline, qualifier forms, `SHA256(...) = ` inline | ~96 |

So roughly 216 real entries put something between the label and the value.
Tightening to "value immediately follows the colon" would break all of them.
The permissiveness is load-bearing and the fix has to preserve it.

## What the corpus says the connective actually is

Every one of those forms is structural: a colon, whitespace, backticks or a code
fence, a `SHA256(...)` formula, and `=`. None contains prose words. That is a
grammar, not an accident, and it is narrow enough to exclude both defect shapes
while admitting every legitimate form.

Two independent constraints follow:

1. **Anchor the label to line start.** A field label begins its line. A label
   quoted inside a sentence does not.
2. **Constrain the connective to the structural grammar.** Colon, whitespace,
   fences, `SHA256(...)`, `=`, and nothing else.

Anchoring alone does not close BETWEEN, since a BETWEEN line starts with a real
label. The grammar alone does not close the prose case cleanly. Both are needed.

## Cost, measured at repository scale

Across **6,342 files** and **134,766** current field matches:

| | count |
|---|---|
| matches under the current patterns | 134,766 |
| matches under anchor + connective | 134,749 |
| **delta** | **17** |

All 17 are the same entry #741 sentence: one in `docs/META_LEDGER.md`, fifteen
in its `.agent/local-backup/governance/**` copies, and one in this brief, which
quotes it. **No legitimate match is lost anywhere in the repository.**

Measured with `_FIELD_SUFFIX`, `_HASH_SPAN` and `_HASH_VALUE` imported from
`ledger_dialect` rather than restated. A first pass used a looser single-group
value pattern and reported 135,276 -> 135,260; that baseline was inflated by
roughly 510 matches and did not correspond to any pattern production compiles.

BETWEEN returns `None` rather than a wrong value. That is the intended outcome
and matches the direction Phase 249 set for this reader: a labeled field whose
value cannot be resolved fails loudly rather than being guessed.

## Out of scope

- **#467** -- the remaining narrow-regex consumer. Phase 277 fixed two of three.
- **#468** -- the emitter half. **#469** -- the lint, designed and parked.
- Rewriting entry #741. Its prose is accurate and its own field is correct; the
  reader is what is wrong.
- The 187 historical attestations, untouched here.
