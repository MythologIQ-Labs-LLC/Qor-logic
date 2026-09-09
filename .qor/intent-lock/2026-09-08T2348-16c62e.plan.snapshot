# Phase 281: a hash label written in prose stops being read as a field

**change_class**: hotfix
**Issues**: GH #428
**Research**: docs/research-brief-dialect-prose-over-read-2026-09-08.md
**Iteration**: 9
**Session**: 2026-09-08T2348-16c62e

## Scope note

`ledger_dialect` owns the three hash-field patterns. Between a label and its
value it admits arbitrary text, so a hash label written in prose is read as a
field, and prose between a label and its value displaces the real value.

Shared verifier, five production consumers. The change is **two independent
terms** -- a line anchor and a restricted connective -- whose three separable
effects are declared individually below, each with a measured cost of zero.

## D1: two terms, three separable effects

`qor/scripts/ledger_dialect.py:42-43` currently:

```python
def _field_re(name):
    return re.compile(rf"\*\*{name}{_FIELD_SUFFIX}\*\*{_HASH_SPAN}{_HASH_VALUE}")
```

Replaced, in `_field_re` only:

```python
_FIELD_PREFIX = r"^[ \t]*"
_HASH_CONNECTIVE = r":(?:[^\S\n]|\r?\n|`|=|SHA256\([^)\n]*\))*"

def _field_re(name):
    return re.compile(
        rf"{_FIELD_PREFIX}\*\*{name}{_FIELD_SUFFIX}\*\*{_FIELD_SUFFIX}"
        rf"{_HASH_CONNECTIVE}{_HASH_VALUE}",
        re.MULTILINE,
    )
```

| # | constraint | what it is | measured cost |
|---|---|---|---|
| 1 | **anchor** | the label begins its line | 0 |
| 2 | **colon** | a literal `:` must follow the label; `_HASH_SPAN` does not require one | 0 |
| 3 | **connective** | only whitespace, backticks and fences, `SHA256(...)`, and `=` between colon and value | 0 |

`_FIELD_SUFFIX` appears twice deliberately: the qualifier occurs inside the
markers (`**Content Hash (session seal)**:`) and outside them
(`**Chain Hash** (Merkle seal):`). A single suffix loses the second, measured.

### The defect classes, and which constraint closes each

Ten shapes. `PROSE` means the reader returns a digest taken from narrative
text; `real` means it returns the entry's own field:

| shape | current | connective only | **all three** |
|---|---|---|---|
| S1 `` `**Previous Hash**` of `<h1>` `` (entry #741 verbatim) | PROSE | None | **None** |
| S2 ``Entry #109 records **Previous Hash**: `<h1>` at line 4076.`` | PROSE | **PROSE** | **None** |
| S3 ``The seal wrote **Chain Hash (Merkle seal)**: `<h1>` before...`` | PROSE | **PROSE** | **None** |
| S4 prose mention, then the entry's own field below it | PROSE | **PROSE** | **real value** |
| S5 ``- the stale **Previous Hash**: `<h1>` recorded at #109`` | PROSE | **PROSE** | **None** |
| S6 BETWEEN: ``**Content Hash**: mentions `<h1>` then `<h2>` `` | PROSE | None | **None** |
| S16 ``**Previous Hash** `<h1>` is stale, not ours.`` (line start, **no colon**) | PROSE | None | **None** |
| S12 diff lines quoting a change, then the entry's own field | PROSE | PROSE | **real value** |
| S13 a blockquote quoting another entry, then the entry's own field | PROSE | PROSE | **real value** |
| S15 ``3. **Previous Hash**: `<h1>` was superseded`` | PROSE | PROSE | **None** |

**S4 is the shape this issue is about.** It is the ordering the research brief
names as unprotected: an entry whose narrative discusses a hash before its own
field lines.

Each constraint is isolated by at least one shape that **only** it closes.
Verified two ways -- applying each constraint alone, and dropping one at a time.
The applied-alone method is the load-bearing one: drop-one always leaves two
constraints standing, so it cannot detect a shape that several close
independently, which is exactly how S1 was misread twice below.

| constraint | isolated by | with it | dropped |
|---|---|---|---|
| 1 anchor | S2, S4 | None / real | **PROSE** |
| 2 colon | **S16** | None | **PROSE** |
| 3 connective | S6 | None | **PROSE** |

**S1 isolates nothing.** Measured with each constraint applied alone, S1 is
closed by the anchor alone, by the colon alone, and by the connective alone.
An earlier iteration claimed S1 isolated the colon; a reviewer countered that
the anchor closes it. Both are true and both are incomplete: S1 is
over-determined, so it establishes the necessity of no constraint. S16 is what
establishes constraint 2, and without it the colon would be carried on exactly
the unproven necessity claim iteration 1 made about the anchor.

**Constraints 2 and 3 are one regex as currently factored.**
`_HASH_CONNECTIVE` *begins* with the mandatory colon, so "drop the colon" means
editing the connective rather than removing a separate term. They are separable
in **effect** -- S16 needs only the colon, S6 needs the restriction on what
follows it -- and they are separable in code too: `_HASH_COLON = r":"` followed
by a grammar constant concatenates byte-identically, verified. They are simply
not separated as written here.

This is stated because a three-row table with three identical costs implies
three independent knobs, and as shipped there are two named terms. An earlier
iteration said the two were "not separable in implementation", which was too
strong and is corrected here.

All six legitimate forms **present in the corpus** survive all three
constraints: plain, value on the next line, fenced `SHA256(...)` formula, bare
hex alone on its line, qualifier inside the markers, qualifier outside them.

### What iterations 1, 2 and 3 got wrong

**Iteration 1** proposed the anchor and connective as "two constraints, both
required". There were three -- the mandatory colon was undeclared -- and the
claim of joint necessity was never measured.

**Iteration 2 dropped the anchor**, on a measurement that tested exactly one
prose shape: S1 -- which, as established above, is over-determined and isolates
nothing. Generalising from the one shape that could not discriminate between
the constraints produced the false claim "the connective alone closes the prose
class", and iteration 2 was **worse than iteration 1 at the reported defect**:
under it S4 returns the prose digest while the entry's real field says
otherwise.

The `legitimate forms kept 6/6` column could not have caught this. All six
forms tested were colon-bearing and line-start, so no column in that table
could see the anchor's effect in either direction.

This is one-shape induction, which the research brief names as the trap that
made Phase 277 conclude #428 was unreproducible. It was repeated here while
the brief citing it was open.

The gains-and-losses framework cannot see it either: S2 through S5 match under
both patterns, so they are neither a gain nor a loss. **`-17 / 0` is correct
and says nothing about sufficiency.** Corpus deltas measure regression risk,
not whether a fix works.

**Iteration 3 restored the anchor but widened it** to admit list, blockquote and
ordered-list markers, justified as letting a field "legitimately written inside
a list item or blockquote still resolve". That justification was asserted, not
measured, and the measurement contradicts it: across the whole corpus the
marker class keeps **0** matches that a bare `^[ \t]*` would drop. The evidence
offered for it -- "8/8 legitimate forms kept, list item and blockquote
included" -- was fixtures written for the purpose, not forms occurring anywhere
in the repository. A constructed fixture cannot establish that a form is
legitimate; only the corpus can.

It also cost something. `-` and `+` are unified-diff markers, and this
repository quotes diffs of ledger changes routinely; `>` is markdown's
quotation marker, so admitting it means a blockquote quoting another entry's
field is read as this entry's field. S12 and S13 above are S4 re-admitted
through the prefix: the reader returns the quoted digest while the entry's own
field says otherwise.

The pattern across all three iterations is the same and worth naming: a
rationale asserted rather than measured. Iteration 1 asserted joint necessity,
iteration 2 asserted sufficiency from one shape, iteration 3 asserted a
legitimate form that does not exist here. Each was wrong in the direction that
made the change look finished.

## D1b: `_HASH_VALUE` is preserved exactly

`_HASH_VALUE` (`:35-40`) is three alternatives with **three capture groups**;
`hash_value` (`:85-90`) returns `group(1) or group(2) or group(3)`.

An earlier draft proposed `` `?([0-9a-f]{64})`? ``. Wrong three ways:

1. One capture group, so `group(2)` raises `IndexError` in every consumer.
2. Looser than production, which is deliberately strict: the third alternative
   requires a bare hex **alone on its line**, per the comment at `:31-34`,
   "to keep it from capturing inline prose hex".
3. **A net gain, not a loss.** Reported as -1; measured on `docs/META_LEDGER.md`
   it is **+6**, 7 gains against 1 loss, at `:50,84,113,145,190,224,281`, all
   `**Previous Hash**: <bare hex>`. Making them resolve moves entries
   #2,#3,#4,#5,#7,#8,#10 out of the migration-attestation rung into full chain
   math. They pass, so exit stays 0 and **no `rc == 0` test would detect it**.

The value grammar is not touched.

`re.MULTILINE` affects only `^` and `$`, whose sole occurrence in the composed
pattern is `_HASH_VALUE`'s third alternative. Proven a no-op both ways:
structurally, the positions `^` reaches under MULTILINE are exactly those the
`\n` branch of `(?:^|\n)` already reaches, so it adds a second path to the same
match rather than a new match; empirically, compiling `_HASH_VALUE` alone with
and without MULTILINE over all 16,169 files gives **139,241 matches each, with
identical spans and zero differing files**.

## D1c: the module docstring is part of this change

`qor/scripts/ledger_dialect.py:12-16` states the module's invariant:

> The forms are additive: no rejection is relaxed. A value must still be a
> 64-char lowercase hex, still bounded to its own field span (the span stops at
> the next `**Field**` marker, so prose hex and a later field's value are never
> captured) ...

Both halves are wrong after this change, and the second is wrong **today**:

1. **"no rejection is relaxed"** is the stated invariant, and this commit adds
   three rejections. Shipping a shared verifier that asserts no rejection is
   relaxed, in the same diff that adds three, is a self-contradicting artifact.
2. **"prose hex ... never captured"** is already false. Entry #741 is the
   counterexample this entire phase rests on. It becomes substantially true
   after the change, but not completely, and the residuals should be named
   rather than implied.

`change_class: hotfix` exempts this phase from the CHANGELOG currency rule
(`qor/references/doctrine-documentation-integrity.md:166`), so nothing
downstream would have caught it. No earlier iteration of this plan had a
documentation deliverable at all.

The paragraph is replaced with:

> The value forms are additive: no accepted value form is removed. What is
> narrowed is where a field is recognized. A label must begin its line, must be
> followed by a colon, and must reach its value through connective tissue only
> -- whitespace, backticks and fences, a `SHA256(...)` formula, `=`. A value
> must still be a 64-char lowercase hex, and the consumers still fail on
> content/chain mismatch, malformed hashes, post-boundary duplicate previous
> hashes, and tampering.
>
> A hash label written in prose is no longer read as a field when it appears
> mid-line, when no colon follows it, or when narrative text separates it from
> its value. Two cases remain captured and are not addressed here: a hash label
> inside a fenced or indented code block, and a field-shaped line whose value
> is a prose digest followed by trailing prose. See GH #428.

`doc_integrity`'s term-drift check aborts a seal when prose restates a glossary
term's definition. Checked with the repository's own `parse_glossary`: of the
**135** declared terms, **none** appears in the replacement text, so the check
has nothing to fire on. Verified rather than phrased around.

This is also the only user-facing statement of the dialect:
`docs/lifecycle.md:102-104` documents none of it.

## D2: the cost, measured

Population: **4,705** `*.md` excluding `.git`, plus **1,637** `.qor/**/*.json`
= **6,342** files. The population is stated rather than a bare count, because a
corpus figure is a claim about what was excluded.

| | count |
|---|---|
| current patterns | 134,766 |
| all three constraints | 134,749 |
| **net** | **-17** |
| gains | **0** |

All 17 losses are the entry #741 sentence: one in `docs/META_LEDGER.md`,
fifteen in `.agent/local-backup/governance/**`, one in this phase's research
brief, which quotes it.

Of the 134,749 surviving matches, **0** are at a non-line-start position, which
is why the anchor costs nothing.

Counts are measured with `_FIELD_SUFFIX`, `_HASH_SPAN` and `_HASH_VALUE`
imported from the module, never restated, with gains and losses counted
separately rather than netted.

## D3: the label probe is not touched

`_label_re` (`:52`) feeds the rung-3 "label present but unparseable" FAIL. It
is left alone. Anchoring a label can only make rung 3 fire **less** -- a
prose-quoted label stops being seen, moving such an entry from FAIL to skip --
so leaving it unanchored is the conservative choice, not the risky one.
Iteration 1 reasoned from the inverted assumption.

Measured per entry across **every `.md` in the repository carrying ledger
entries**, excluding the 15 `local-backup` copies: **59 files, 901 entries**.
An earlier iteration measured 795 entries across 5 hand-picked ledgers, which
was a chosen sample rather than the population.

| measure | result |
|---|---|
| entries where all-three-fields-resolvable flips | **0** |
| entries where any resolved field **value** changes | **0** |
| entries newly invisible to rung 3 | **0** |

Zero value changes is the strong form, and stronger than an exit code: no entry
resolves to a different value. The 17 lost occurrences are secondary matches
inside entries whose real field `.search()` finds first.

## D4: what this does NOT do

- **Does not rewrite entry #741.** Its prose is accurate and its fields are
  correct. The reader is wrong, not the ledger.
- **Does not touch `SESSION_SEAL_RE`**, which also uses `_HASH_SPAN`. Measured:
  it matches **0 times across every `.md` in the repository**, so there is no
  observation here on which to base a change, and narrowing it would be
  unmeasured scope. That is evidence for the exclusion rather than absence of a
  report, and it matters because `ledger_hash.py:388` and `reconcile.py:69-73`
  fall back to it for consumer ledgers, where it is not dead.
- **Does not close #467, #468, #469 or #477.**

## Tests

Written first, red before the change. Each runs twice for determinism.

| Test | Pins | Red before |
|---|---|---|
| `test_prose_quoted_label_is_not_read_as_a_field` | S1, entry #741 verbatim | yes |
| `test_prose_mention_does_not_displace_the_entrys_own_field` | **S4** | yes |
| `test_prose_label_with_colon_is_not_a_field` | S2, S3, S5 | yes |
| `test_prose_hex_between_label_and_value_is_rejected` | S6 | yes |
| `test_label_without_a_colon_is_not_a_field` | **S16**, the shape that isolates constraint 2 | yes |
| `test_every_legitimate_connective_form_still_matches` | the six forms present in the corpus | no |
| `test_hash_value_still_reads_all_three_capture_groups` | D1b | no |
| `test_live_ledger_gains_no_matches_and_loses_only_prose` | D2. **Gains**: asserted zero, independent of the fix. **Losses**: the expected count is derived by matching the prose-quoted-label shape itself, never as `old - new` | no |

S4 is the row that matters: it is the reported defect, and it is the row that
distinguishes the shipped pattern from the connective-only variant an earlier
iteration proposed.

No count is pinned to 134,766. A hardcoded total would couple the suite to live
ledger state and go red on the next seal; both halves are computed from the file
under test.

The loss half must derive its expectation from the prose shape itself.
Computing it as `old - new` asserts nothing: that identity holds for any pattern
whatsoever, so the test would pass against a pattern that matches nothing. The
gains half is already independent and non-tautological, and it is the only check
that would have caught the +6 in D1b, which was invisible to exit codes and to
every loss-only count.

## Reach

**Five** consumers import these patterns: `ledger_hash.py`,
`seal_entry_check.py`, `gate_provenance.py`, `evidence_bundle.py`,
`reconcile.py` (transitively via re-exports at `ledger_hash.py:158-160`).

`snapshot_export.py` is **not** one: it imports nothing from `ledger_dialect`
and uses its own `_CHAIN_HASH_RE` (`:34`). An earlier draft listed it because a
grep matched that private name as a substring.

### What each consumer does when a value becomes `None`

| consumer | on `None` | verdict |
|---|---|---|
| `seal_entry_check.py:95-97` | `ok=False`, "no parseable entries" | loud |
| `ledger_hash.py:356` | rung 3 FAILs | loud |
| **`gate_provenance.py:321-324`** | prints `SKIP: no sealed ledger entry with canonical hash markers`, **`return 0`** | **green skip** |
| `seal_entry_check.py:187-189` | `continue` | silent skip |
| `reconcile.py:41-42`, `ledger_hash.py:251,274` | `continue` | silent skip |
| `evidence_bundle.py:58` | writes `None` into the bundle | recorded |

**Two of six are loud; four are not.** An earlier draft put `gate_provenance`
in the loud column. It is the worst one to have been wrong about:
`attest-latest` runs in CI (`.github/workflows/ci.yml:151`) and HMACs the
content/chain pair on every push. On `None` it emits **no attestation** and
exits **0**, so provenance silently stops being recorded while CI stays green.

A **disclosure** defect, not a regression: all five consumers produce
byte-identical output patched against baseline, including `latest_seal_hashes`
and a 238-block evidence bundle with 0 null hashes. Recorded because the safety
argument rests entirely on the delta being one prose sentence with zero gains,
and `gate_provenance` is where a future loss of a real field would go unnoticed.

### A latent defect found while tracing, not fixed here

`reconcile.py:44` and `:73` read `ph.group(1) or ph.group(2)` from a
three-group value, so the bare-hex form yields `None`. Measured: 0 live matches
resolve via `group(3)`. Filed as **#477**, which also records
`snapshot_export.py:34`.

## Affected files

- `qor/scripts/ledger_dialect.py` -- `_field_re` and the module docstring
  (D1c). `_HASH_VALUE`, `_label_re` and `SESSION_SEAL_RE` unchanged.
- `tests/test_ledger_dialect.py` -- the eight rows above.
- `CHANGELOG.md`.

## CI Commands

```
python -m pytest tests/ -q -k "dialect or ledger_hash or seal_entry or evidence_bundle or reconcile"
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- **One prose shape remains, and no grammar can close it.** A field-shaped
  line whose value is a prose digest --
  ``**Content Hash**: `<prose hex>` was the stale value we found.`` -- is
  byte-for-byte identical to a real field up to and including its value, and
  differs only in trailing prose. Measured: current and proposed both return
  the prose digest. **#428 is narrowed, not eliminated**, and should be
  recorded that way rather than closed clean.

  An earlier iteration illustrated this with a **two-hex** line,
  ``**Content Hash**: `<h1>` (wrong; the real one is `<h2>`)``. That example
  was a bad one and undercut the claim: 0 of the 2,234 surviving field matches
  in `docs/META_LEDGER.md` sit on a line carrying more than one 64-hex, so a
  "at most one hex per field line" rule would have closed it at zero measured
  cost. That rule is **not** adopted here -- it is unaudited scope, and it does
  not touch the single-hex shape above, which is the one that is genuinely
  unclosable.
- **A hash label inside a fenced or indented code block is still read as a
  field**, and this change does not help. Inside a fence the label *is* at line
  start, so the anchor cannot see it, and the contents are legitimate
  connective grammar, so the connective cannot either. Measured: shapes S7
  (fenced example block above the real field), S8 (fenced block with a language
  tag) and S9 (four-space indented block) all return the prose digest under
  both the current and the proposed patterns. Live exposure is zero: of 107
  fenced blocks in `docs/META_LEDGER.md`, **0** contain both a hash label and a
  64-hex value. Closing it requires fence-awareness, which is a different
  mechanism and cannot be expressed in this grammar.

- **The anchor also rejects three shapes that are legitimate**, none of which
  occurs in this repository with a hash value:

  | shape | live occurrences |
  |---|---|
  | **T1** a markdown table row: `` \| **Content Hash** \| `<hex>` \| `` | 0 |
  | **T5** an entire entry quoted inside a blockquote (`> ### Entry #9`, `> **Content Hash**: ...`) | 0 |
  | **T6** a file with a UTF-8 BOM whose field is on line 1 | 0 |

  T1 is the one most likely to be met in practice: `qor/templates/META_LEDGER.md:8-10`
  already uses bold labels in table rows (`| **Hash Algorithm** | SHA-256 |`)
  for header metadata, so a consumer writing hash fields the same way is not
  exotic. It is rejected by the anchor and the colon together, so it appears in
  no single-constraint discussion.

  T5 is the important one to state, because it is **byte-identical to S13** and
  gets the opposite verdict. `> **Content Hash**: ...` is a defect when it
  quotes another entry's field inside your entry, and legitimate when the whole
  entry is quoted. Nothing available to the prefix can distinguish them. That,
  rather than its zero measured benefit, is the durable reason the marker class
  cannot come back: it is not a tuning choice, it is undecidable at this level.
  The anchor takes the safe side and T5 is the declared cost.

  T6 is small but real: **114** `.md` files in this repository carry a UTF-8
  BOM. A BOM can only shadow a field on line 1, and no ledger has one there,
  which is consistent with losses being exactly 17. A consumer ledger written
  by a Windows editor could.

  Shapes confirmed **unaffected**: nested-list continuation lines, deep
  indentation, CRLF line endings, a field on the first line of a file, and
  mixed space-and-tab indentation.

- **A field written inside a list item or blockquote does not resolve.**
  `- **Content Hash**: `<hex>`` and `> **Content Hash**: `<hex>`` are rejected
  by the anchor. Measured: **0 occurrences** anywhere in the corpus, and
  admitting them costs more than it buys, because the same markers are how
  diffs and quotations of other entries are written. See S12, S13, S15.

- The connective requires a literal `:`, which `_HASH_SPAN` does not. A field
  written with the value on the next line and no colon stops resolving.
  Measured: 0 occurrences.
- The grammar is induced from observed forms. A legitimate connective present
  in no file here would be rejected -- loudly rather than silently, but still a
  regression.
- `SESSION_SEAL_RE` keeps the permissive span. If the same defect exists there,
  this phase does not close it and nothing here would detect it.
- The fix is in the reader. Nothing stops an author writing a sentence shaped
  like a field; it is simply no longer misread.
