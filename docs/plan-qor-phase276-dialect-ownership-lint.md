# Phase 276: a lint that detects the defect four phases fixed by hand

**change_class**: feature
**Issues**: closes none; makes GH #467 measurable and prevents its recurrence
**Research**: docs/research-brief-dialect-ownership-2026-09-08.md
**Iteration**: 3 (iterations 1 and 2 VETOed)
**Session**: 2026-09-08T1717-f54e4c

## Scope note

One new lint, no consumer behaviour changes. Advisory against a recorded baseline; it cannot fail an existing seal. The reviewer should attack the declaration surface and the baseline key hardest -- both were vetoed once, and the baseline key is still the piece carrying the most weight.

## What iterations 1 and 2 got wrong

1. **The matching rule was unspecified, and the one used was wrong.** Iteration 1 keyed on the literal `\*\*Field\*\*`, which cannot see a reader of a suffixed label like `**Chain Hash (Merkle seal)**`. It reported "7 violations, 0 noise". The real count is **14**. Three modules missed entirely -- `ledger_emit.py`, `snapshot_export.py`, `ledger_base_currency.py` -- were absent from Affected Files, so the plan could not have made its own live-tree test pass.
2. **The #467 correction was itself wrong.** The claim was that 60 of 160 missed hashes were `ledger_dialect` false positives (#428), making the real count 100. Re-measured: **0** are false positives; the 60 carry the qualifier *inside* the markers (`**Content Hash (session seal)**:`, entry #137), the form `_FIELD_SUFFIX` exists to support. All 160 are real and **#467 is not blocked on #428**.
3. **Iteration 2 added emitters to scope, and that was a ghost path.** `ledger_dialect`'s public surface is entirely readers -- there is no `render`. "An emitter must import its owner" would force three modules to import something they cannot call: an import that satisfies a lint and changes nothing. Withdrawn, and filed as GH #468.

Items 1 and 2 failed the same way -- keying on a bare `**Field**` in a corpus that uses `**Field (qualifier)**` -- the failure mode the brief already named as noise cause #2. Item 3 committed the ghost-path shape this repo has an open issue about (#459). Naming a failure mode does not prevent committing it, which is the argument for the lint over further hand measurement.

## D1: the property

```
A module that parses a field owned by a declared dialect must import that dialect.
```

Decidable by AST. No pattern semantics, no subset reasoning.

**The read-count differential is not the verdict.** Comparing each parser's read-count against the owner's over the real ledger produces ~50% false positives -- whole-document `DOTALL` patterns scored per entry, a wrong denominator for `**Chain Hash (Merkle seal)**`, and `**Session Seal**` scored as a broken `**Session**` reader. Read-counts stay a research tool.

## D1a: the owner declares label FORMS, because structure cannot decide aliasing

Iteration 2 proposed a "component rule": the field name must open a bold label. Measured against every label shape actually present in the tree, **it is wrong on 4 of 7**:

| shape | site | correct | component rule |
|---|---|---|---|
| `**Content Hash**` | many | read | MATCH |
| `**Chain Hash (Merkle seal)**` | many | read | MATCH |
| `**META_LEDGER Content Hash**` | `ledger_migrate:35,86` | read (alias) | invisible |
| `**Session Seal**` | `ledger_migrate:58` | read (alias of Chain Hash) | invisible |
| `**Previous Chain Hash**` | `ledger_migrate:47,49,89,90` | read (alias of Previous Hash) | invisible |
| `**(?:META_LEDGER )?Content Hash**` | `ledger_migrate:79` | read (alias) | invisible |
| `**Superseded Content Hash**` | `ledger_commitment:38` | **not** a Content Hash read | invisible |

The last two rows are the argument. `**Previous Chain Hash**` and `**Superseded Content Hash**` are structurally identical -- a bold label containing an owned field name but not opening with it -- and their correct answers are opposite. **No regex can separate them.** The component rule's advertised "0 false positives" comes from not seeing `Previous Chain Hash` at all: right about `Chain Hash` by accident, silently wrong about `Previous Hash`.

So the owner declares its label forms, and the component rule is demoted to a fallback that reports rather than decides:

```python
# qor/scripts/ledger_dialect.py
OWNS = {
    ("docs/META_LEDGER.md", "Content Hash"):  ("Content Hash", "META_LEDGER Content Hash"),
    ("docs/META_LEDGER.md", "Previous Hash"): ("Previous Hash", "Previous Chain Hash"),
    ("docs/META_LEDGER.md", "Chain Hash"):    ("Chain Hash", "Session Seal"),
}
```

This also removes the substring rule's 2 false positives structurally rather than by regex trick: `Previous Chain Hash` scores as `Previous Hash` because it is *declared* as one.

**Containment never implies aliasing.** A label containing an owned name but not declared as a form of it is reported as `undeclared-label` -- not silently ignored, or D2's third-silent-category defect returns one level down. Measured cost: 4 such labels across 2 modules, plus 2 corpus forms (`**Superseded Content Hash**` x5 and `**Superseded Content Hash (RETRACTED)**` x2 -- a suffixed form of a prefixed label, which is the corpus restating the case for declaring forms rather than names).

## D2: the declaration surface is three-valued

| value | meaning | obligation |
|---|---|---|
| `alias of <field>` | a second label form of an owned field | owner must parse it |
| `owned field` | a field the owner owns | **owner must provide the reader** |
| `undeclared` | neither, and not assumed | reported as `undeclared-label`, baseline-able |

**`Superseded Content Hash` is the third, deliberately.** It is a distinct field, not an alias -- `ledger_commitment` carries `_CONTENT_RE` and `_SUPERSEDED_RE` side by side for different purposes. But it does not get an `OWNS` row either: `ledger_dialect` has no pattern for it, so declaring it owned would make `ledger_commitment` non-compliant with no remedy except importing a module with nothing to call. That is item 3 above, repeated. It gets one baseline row with the reason recorded; a *second* reader mints a new key and fails, forcing the alias-or-distinct ruling at the moment it first matters, with two real readers to reason from rather than one.

**Fields are (document, field) pairs.** `meta_ledger_walker` parses `**Verdict**`/`**Target**` from `META_LEDGER.md` while `verdict_dialect` owns those names in `AUDIT_REPORT.md`. Phase 275 audited that and deliberately declined to touch the walker; a name-only lint would contradict a sealed decision. Modules declare what they read:

```python
READS_DOCUMENTS = ("docs/META_LEDGER.md",)
```

A module parsing an owned field name while declaring **no** documents fails as `undeclared-document`.

**Declarations are cross-checked, not trusted** -- by two checks, because one is not enough:

- **(a) the field must occur as a label in every declared document.** Catches a fabricated or empty document.
- **(b) every declared document must appear as a path literal in the module.** Catches the plausible-but-wrong document, which is the shape that actually gets written.

(a) alone does not work, and the counterexample that motivated it defeats it: **`CHANGELOG.md:211` contains `**Content Hash**`** in prose describing Phase 251. A module declaring `docs/CHANGELOG.md` while parsing that field passes (a), and since owned pairs are keyed on document, `(docs/CHANGELOG.md, Content Hash)` is not an owned pair either -- so the opt-out survives with no violation raised. Many tracked files carry the label, including every archived ledger snapshot, so the material for that bypass is abundant.

(b) has material in every live case: `snapshot_export.py`, `ledger_base_currency.py`, `gate_provenance.py`, `evidence_bundle.py` and `ledger_commitment.py` all carry `META_LEDGER` as a literal already.

A failure of either is `false-declaration`, which fails. Both are decidable against tracked files with no intent inference.

**Residue, stated rather than closed:** a module that opens document D for an unrelated purpose, carries D's path literal, and parses an owned field belonging to a different document passes both checks. Nothing structural distinguishes that from a correct declaration.

## D3: the baseline

The 14 reader findings plus the `undeclared-label` findings ship as a recorded baseline. A baseline entry reports and does not fail; anything else fails. A baseline entry that no longer applies is **stale and fails**, so the baseline can only shrink.

**Keyed on `(module, document, field, kind, normalized-pattern)`.** Iteration 2 keyed on `(module, document, field, kind)`, which is line-blind: adding

```python
_CONTENT_ALT = re.compile(r"\*\*Content Hash\*\*:\s*([0-9a-f]{64})")   # no backticks, diverges
```

to `ledger_commitment` produces the same key, byte-identical lint output, and a green live-tree test -- while being the *defining* instance of the class this lint exists to catch. Worse, the permanent rows pre-authorise it: `ledger_migrate` holds 3 keys covering a 183-line module, so every future parse of those fields inside it would be free, including the alias forms D1a just made visible.

Normalized pattern text is the discriminator: stable across reformatting, and it distinguishes a genuinely new pattern from a moved one. A per-identity occurrence count is the fallback if normalization proves brittle -- a count *scoped to an identity* is not the count-keyed baseline this rejects.

**A test asserts the baseline file is tracked by git.** `.qor/` is only partially gitignored -- `.qor/session/` and `.qor/intent-lock/` are ignored while `.qor/gates/` is tracked. GH #457 is exactly a lint whose term list sat at a gitignored path, so CI silently ran a reduced check for months. The property gets a test, not a one-time check.

**Permanent entries, recorded with reasons rather than as pending work:**

| entry | reason |
|---|---|
| `ledger_migrate` (3 fields) | migrates markup *between* dialects; reading through the dialect it is migrating away from is incoherent |
| `ledger_commitment` (`Superseded Content Hash`) | `undeclared-label`; deliberately not owned, per D2 |
| `meta_ledger_walker` (2 fields) | different document; resolved by D2's scoping, so these should not appear once documents are declared |

The `meta_ledger_walker` rows are D2's acceptance test: if scoping works they vanish, and if they need a baseline entry then D2 is wrong.

## D4: what this does NOT do

- **Does not fix GH #467.** Separate phase. Not blocked on #428 -- that claim is retracted. The PR carries no closing keyword for it.
- **Does not fix #428.** The owner over-reads prose hex; this is about divergence, not correctness.
- **Does not cover emitters (GH #468).** Withdrawn for the ghost-path reason above. It also needs a *different detector*: an emitted literal never reaches an `re.*` call, so writer detection needs a write-sink anchor, and without one "any literal" gives 11 findings where 3 are real -- the other 8 being 5 docstrings and 3 error strings, including `meta_ledger_walker`'s own docstring flagging a pure reader as a writer.
- **Is not wired as a seal gate.** The ladder went 12 -> 8; a ninth ABORT is not earned by a check with no track record. Promotion is a later decision resting on its false-positive record.

## D5: two blind spots, both measured

**Indirection.** `ledger_dialect` builds every pattern through `_field_re("Content Hash")`, so the field name never appears inside an `re.*` call literal and the owner is invisible to its own check. A violator evades with a one-line helper. The obvious mitigation -- also match bare field-name literals -- **was measured and rejected**: 14 hits of which 7 are noise (`TargetProfile`, `_HookTarget`, `SeedTarget`, `'Verdict'` in `sdk.py`, prose in an error string). Clean only for multi-word names; a rule that works for `Content Hash` but not `Target` has an unstated exception.

**Undeclared alias labels.** Until an owner declares a form, a module reading only that form is invisible. Three live alias forms exist today and all are declared in D1a, but the next one is invisible until someone declares it. `undeclared-label` narrows this: a *label* containing an owned name is caught even when undeclared. A wholly unrelated label name for the same field is not.

Both are pinned by tests so the gaps are recorded rather than described.

## Tests

Written first, red before the code. Each runs twice for determinism.

| Test | Pins | Red before |
|---|---|---|
| `test_flags_a_parser_that_does_not_import_its_owner` | the core property | yes |
| `test_accepts_a_parser_that_imports_its_owner` | the clean path | yes |
| `test_a_declared_alias_label_is_a_read_of_its_field` | D1a; `**Previous Chain Hash**` -> Previous Hash | yes |
| `test_a_declared_alias_is_not_a_read_of_a_field_it_merely_contains` | `**Previous Chain Hash**` is not a `Chain Hash` read | yes |
| `test_an_undeclared_containing_label_is_reported_not_ignored` | `**Superseded Content Hash**` -> `undeclared-label` | yes |
| `test_an_optional_prefix_group_is_matched_as_its_alias` | the fifth shape, `ledger_migrate:79` | yes |
| `test_same_field_name_in_another_document_is_not_a_violation` | D2; the `meta_ledger_walker` case | yes |
| `test_a_module_declaring_no_documents_fails` | silence is not compliance | yes |
| `test_a_declaration_naming_a_document_without_the_field_fails` | D2; the false-declaration opt-out | yes |
| `test_owner_parsing_its_own_field_is_not_a_violation` | no self-report | yes |
| `test_baseline_entry_reports_without_failing` | D3 advisory path | yes |
| `test_a_second_diverging_pattern_in_a_baselined_module_fails` | **D3's key**; the line-blind hole | yes |
| `test_a_reformatted_pattern_does_not_mint_a_new_key` | normalization is stable | yes |
| `test_a_new_violation_fails_even_when_the_baseline_is_full` | the baseline's failure mode | yes |
| `test_a_stale_baseline_entry_fails` | the baseline can only shrink | yes |
| `test_the_baseline_file_is_tracked_by_git` | GH #457's failure mode | yes |
| `test_a_helper_built_pattern_is_not_claimed_as_checked` | D5; the blind spot is real | yes |
| `test_live_tree_matches_the_recorded_baseline` | the repo's actual state | no |

`test_a_second_diverging_pattern_in_a_baselined_module_fails` is the one that matters most: it is the exact case iteration 2 would have shipped green.

## Affected files

- `qor/scripts/dialect_ownership_lint.py` (new)
- `qor/scripts/ledger_dialect.py`, `qor/scripts/verdict_dialect.py` (`OWNS` declaration only)
- `READS_DOCUMENTS` declaration only, no parser changes:
  - `qor/scripts/meta_ledger_walker.py`
  - `qor/scripts/evidence_bundle.py`
  - `qor/scripts/gate_provenance.py`
  - `qor/scripts/ledger_commitment.py`
  - `qor/scripts/ledger_migrate.py`
  - `qor/scripts/ledger_emit.py` -- reads `Chain Hash` at line 19 independently of its emitter sites
  - `qor/scripts/snapshot_export.py`
  - `qor/reliability/ledger_base_currency.py`
- `.qor/dialect-ownership-baseline.json` (new, tracked -- verified not gitignored, and pinned by test)
- `tests/test_dialect_ownership_lint.py` (new)
- `CHANGELOG.md`

**`reconcile.py` is deliberately absent.** It scores 0 reader pairs -- it only writes -- so with emitters out of scope it has nothing to declare, and a `READS_DOCUMENTS` on it would be exactly the false declaration D2 guards against.

## Reach

- Nothing that runs today changes its verdict. The lint is new and advisory.
- Adds a declaration convention future dialect owners must follow, which is the point.
- No skill or template changes, so the dist tree is untouched.

## CI Commands

```
python -m pytest tests/test_dialect_ownership_lint.py -q
python -m qor.scripts.dialect_ownership_lint --repo-root .
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- Detects that a module bypasses an owner, never that it bypasses it *harmfully*. The read-count evidence that would distinguish those is too noisy to gate on.
- **The compliant class has no live instance.** `seal_entry_check`, `ledger_hash` and `verdict_reconcile` import their owner and consume its *compiled patterns*, so they carry no literal and fall outside the scan entirely. `test_accepts_a_parser_that_imports_its_owner` is therefore synthetic-only, and the "0 false positives" claim rests on 14 negatives with zero live positives. The claim should not be read as stronger than that evidence.
- A declaration can still be wrong in the one way both cross-checks miss: a module carrying a document's path literal for an unrelated reason while parsing a field owned elsewhere.
- A module can import the owner and still parse the field itself; the lint sees an import, not a use.
- Defeatable by indirection, and by a wholly unrelated label for an owned field (D5).
- The baseline records 14 reader entries plus the `undeclared-label` entries. If it grows, this lint has failed at its job, visibly in its own diff.
- Advisory: it cannot stop a seal.
