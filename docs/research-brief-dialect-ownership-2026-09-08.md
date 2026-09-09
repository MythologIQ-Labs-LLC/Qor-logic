# Research brief: who owns a document field's form

**Date**: 2026-09-08
**Session**: 2026-09-08T1717-f54e4c
**Issues**: GH #467 (paired with #428); proposes the lint that closes the class

## The class

Four sealed phases have now fixed the same defect: a document field parsed by more than one module, each with its own regex, diverging silently.

| phase | field | issue |
|---|---|---|
| 194 | ledger hash markup | #282 -- created `ledger_dialect` as the owner |
| 275 | audit verdict + target | #424, #462 -- created `verdict_dialect` as the owner |
| -- | `**Content Hash**`, three narrow readers | #467 |
| -- | two emitters of two verdict forms | #464 |

Each was found by hand, after shipping. Nothing detects the next one.

## What is actually checkable, and what is not

The obvious design -- compare each parser's pattern against the canonical owner's and fail when it reads less -- **was measured and does not work**. Regex subset relations are undecidable in general, so the test has to be empirical: run both patterns over the real ledger and compare counts. Run that way it produces roughly 50% false positives, from three causes:

- **Scope mismatch.** `governance_index.py:27` is `### Entry #\d+: SESSION SEAL.*?\*\*Timestamp\*\*` under `DOTALL` -- a whole-document pattern by design. Counted per entry it reads 0 and looks catastrophically narrow.
- **Label mismatch.** The chain field's real label is `**Chain Hash (Merkle seal)**`, so a `^\*\*Chain Hash\*\*` denominator is wrong and every reader of it appears to read 0.
- **Substring collision.** `**Session Seal**` contains `Session`, so `ledger_dialect`'s seal pattern is scored as a broken `**Session**` reader.

A lint at that noise level would be ignored, which is worse than no lint.

## What does work

Drop the subset reasoning entirely and check a structural property instead: **a module that parses a field with a declared owner must import that owner.** Decidable by AST, no pattern semantics involved.

**But "parses a field" has to be defined at the literal level, and the choice is not cosmetic.** A first pass keyed on the literal `\*\*Field\*\*` and reported 7 violations with "0 noise". That was wrong: it silently excluded every reader of a *suffixed* label such as `**Chain Hash (Merkle seal)**`, which is the same label-mismatch failure this brief names above as noise cause #2. Three rules, measured against de-facto owners (`ledger_dialect`: Content/Previous/Chain Hash; `verdict_dialect`: Verdict/Target):

| rule | pairs | false positives |
|---|---|---|
| exact `\*\*Field\*\*` | 7 | 0, but a large false-negative class |
| substring | 14 | 2 -- `\*\*Previous Chain Hash\*\*` scores as a `Chain Hash` read |
| **component**: `\*\*Field(?:\*\*|[^A-Za-z*])` | **14** | **0** |

The component rule admits a suffixed label and rejects a longer field name that merely contains a shorter one. It is the rule the lint must specify, and the count is **14**, not 7:

```
ledger_base_currency.py   **Chain Hash**, **Previous Hash**
evidence_bundle.py        **Chain Hash**, **Content Hash**     <- Content Hash: GH #467
gate_provenance.py        **Chain Hash**, **Content Hash**     <- Content Hash: GH #467
ledger_commitment.py      **Content Hash**                     <- GH #467
ledger_emit.py            **Chain Hash**
ledger_migrate.py         **Chain Hash**, **Content Hash**, **Previous Hash**   <- migration tool
meta_ledger_walker.py     **Target**, **Verdict**              <- different document
snapshot_export.py        **Chain Hash**
```

Every finding is real under the component rule. Two categories need handling rather than fixing, and the measurement surfaced both without being told about them:

- **Fields are `(document, field)` pairs, not names.** `meta_ledger_walker` reads `**Verdict**` from `META_LEDGER.md`; `verdict_dialect` owns that name in `AUDIT_REPORT.md`. Different documents, legitimately different dialects -- Phase 275 examined this and deliberately declined to touch the walker. A name-only lint contradicts a decision already made and audited.
- **Migration tools need raw access.** `ledger_migrate` rewrites markup between dialects; requiring it to read through the dialect it is migrating away from is incoherent.

## A retracted correction, and the error that produced it

An earlier revision of this brief claimed that of the 160 hashes the narrow readers miss, 60 were `ledger_dialect` false positives (GH #428) and the real count was 100. **That was wrong and is withdrawn.** Re-measured:

| | count |
|---|---|
| real field, suffix **inside** the markers -- `**Content Hash (session seal)**:` (entry #137) | 60 |
| real field, suffix outside the markers or a non-backtick value form | 100 |
| **genuinely unlabelled, i.e. a true #428 false positive** | **0** |

**All 160 are real misses.** Each narrow reader reads 581 of 741.

The probe used to decide "does this entry carry the label at all" was `^\*\*Content Hash\*\*`, which cannot match a label whose qualifier sits inside the bold markers -- and `ledger_dialect` builds its label as `\*\*{name}{_FIELD_SUFFIX}\*\*`, so the suffixed form is exactly what it supports. Every suffixed entry was therefore filed as "no label present, therefore an owner false positive".

Consequence: **#467 is not blocked on #428.** Consolidation imports no prose false positives, because there are none.

Two measurements in this cluster have now failed the same way -- the 7-vs-14 undercount above and this one -- both by keying on a bare `**Field**` label in a corpus that uses `**Field (qualifier)**`, and both after this brief had already named that failure mode in writing. Naming a failure mode does not prevent committing it, which is the argument for a lint over further hand measurement.

## Scope consequence

The lint and the consolidation separate cleanly, and should:

- The **lint** depends on nothing. It records the 14 findings as a baseline, fails on any *new* violation, and gives the eventual consolidation a red test.
- The **consolidation** (#467) is a separate phase. It is *not* blocked on #428, that claim having been retracted above -- it is simply different work with a different blast radius.

Shipping a lint that fails on 14 pre-existing violations would put CI red on merge, so the baseline is part of the contract rather than a compromise: it makes existing debt explicit and countable, and it can only shrink.

## Two blind spots found by testing the instrument rather than trusting it

**The owner is invisible to its own check.** `ledger_dialect` builds every field pattern through `_field_re("Content Hash")`, so the field name never appears inside an `re.*` call literal. None of the three rules above can see it. This is not an exotic evasion: it is the idiom the canonical owner uses, so any module can defeat the lint with a one-line helper. The lint must state this as a real gap rather than as a theoretical one about "runtime-assembled patterns".

**Emitters are an uncovered category.** `ledger_emit.py:39` and `reconcile.py:135` write `f"**Content Hash**: \`{content}\`"` without importing the dialect that defines the form. Both currently emit a readable form, so nothing is broken today -- but nothing holds them to it. This is the shape of GH #404 (a template emitting markup every reader rejects) and GH #464 (two templates emitting two dialects). A writer that emits an unreadable form creates permanently unreadable data, which is worse than a narrow reader that skips it.

## What the lint cannot catch

- Patterns assembled at runtime from non-literal parts.
- A field with exactly one parser that is simply wrong -- this is about divergence, not correctness (#428 is that shape and needs its own fix).
- Whether a compliant importer then *uses* the owner correctly.
- Emitters. #464 is two templates emitting two dialects; nothing here reads templates.
