# Phase 282: a lint that detects the defect four phases fixed by hand

**change_class**: feature
**Issues**: closes GH #469; prevents recurrence of the #467 / #468 / #477 class
**Research**: docs/research-brief-dialect-ownership-remeasure-2026-09-09.md
**Prior research**: docs/research-brief-dialect-ownership-2026-09-08.md
**Iteration**: 9
**Session**: 2026-09-09T0342-9a87f0

**Provenance**: the design, its declaration surface and its baseline key come from the Phase 276
plan, parked unimplemented after four review rounds (GH #469). Those are adopted unchanged. **The
measurements are re-taken**, because three phases landed since and the parked numbers are stale.

## Scope note

One new lint, no consumer behaviour changes. Advisory against a recorded baseline; it cannot fail an existing seal. The reviewer should attack the declaration surface and the baseline key hardest -- both were vetoed once, and the baseline key is still the piece carrying the most weight.

## What the parked design's iterations 1 and 2 got wrong

Recorded from GH #469 as provenance. These are Phase 276's iterations, not this plan's.

1. **The matching rule was unspecified, and the one used was wrong.** Iteration 1 keyed on the literal `\*\*Field\*\*`, which cannot see a reader of a suffixed label like `**Chain Hash (Merkle seal)**`. It reported "7 violations, 0 noise". The real count under the parked plan's own rule was **14**. D1n's rule yields a different figure -- D3's table is canonical for it -- and the two are not comparable, because the rule changed rather than the tree. Three modules missed entirely -- `ledger_emit.py`, `snapshot_export.py`, `ledger_base_currency.py` -- were absent from Affected Files, so the plan could not have made its own live-tree test pass.
2. **The #467 correction was itself wrong.** The claim was that 60 of 160 missed hashes were `ledger_dialect` false positives (#428), making the real count 100. Re-measured: **0** are false positives; the 60 carry the qualifier *inside* the markers (`**Content Hash (session seal)**:`, entry #137), the form `_FIELD_SUFFIX` exists to support. All 160 are real and **#467 is not blocked on #428**.
3. **Iteration 2 added emitters to scope, and that was a ghost path.** `ledger_dialect`'s public surface is entirely readers -- there is no `render`. "An emitter must import its owner" would force three modules to import something they cannot call: an import that satisfies a lint and changes nothing. Withdrawn, and filed as GH #468.

Items 1 and 2 failed the same way -- keying on a bare `**Field**` in a corpus that uses `**Field (qualifier)**` -- the failure mode the brief already named as noise cause #2. Item 3 committed the ghost-path shape this repo has an open issue about (#459). Naming a failure mode does not prevent committing it, which is the argument for the lint over further hand measurement.

## D1: the property

```
A module that parses a field owned by a declared dialect must import that dialect.
```

Decidable by AST plus **bounded normalization over two enumerated constructs**
(D1n). No general pattern semantics and no subset reasoning.

An earlier iteration claimed "no pattern semantics" outright. That is false and
is retracted: deciding whether `\*\*Chain Hash[^\n*]*\*\*` reads Chain Hash
requires interpreting the label region, for a share of the tree's label regions
large enough that a recorded gap would not be honest. The measurement and its
four shapes are stated once, in **D5 blind spot 3**, and are not restated here.
The claim is replaced by the bounded rule in D1n, which enumerates exactly what
is interpreted.

**The read-count differential is still not the verdict, and that rejection does
not rest on the retracted claim.** It rests on its own measurement: comparing
each parser's read-count against the owner's over the real ledger produces ~50%
false positives -- whole-document `DOTALL` patterns scored per entry, a wrong
denominator for `**Chain Hash (Merkle seal)**`, and `**Session Seal**` scored as
a broken `**Session**` reader. Those figures are untouched by D1n, so the
rejection stands on its own ground. Stated explicitly because an argument that
silently inherits a premise its author has withdrawn is the defect this plan
would otherwise ship.

## D1n: the classification rule, normative

One rule in four steps. Stated once, here, and referenced everywhere else --
three separately-worded rules drift apart across revisions and one cannot.

1. **Normalize** the label region to a fixpoint over exactly two constructs:
   a trailing character-class wildcard (`[^...]*` or `[^...]+`) is stripped, and
   an optional non-capturing group (`(?:X)?`) expands to both its present and
   absent forms. **Nothing else. A third construct is a new plan.**
2. **Discard** any expansion still carrying either construct. Intermediates are
   not label forms: expanding `(?:META_LEDGER )?Content Hash[^\n*]*` yields six
   strings of which four still carry constructs, and counting those mints four
   spurious `undeclared-label` findings from one site.
3. **Classify each surviving expansion independently**, applying longest-form-wins
   *within* that expansion as the containment tiebreaker. A declared form
   contributes a read of its field; otherwise, an expansion containing an owned
   field name contributes an `undeclared-label`. The two branches are mutually
   exclusive by construction, which is what stops `Previous Chain Hash` -- a
   declared form -- from also emitting an `undeclared-label` for the `Chain Hash`
   it contains.
4. **Union** the findings and report each distinct `(field, kind)` once per site.

**Longest-form-wins is a tiebreaker inside one concrete label, never a selector
over the expansion set.** Applied at step 4 instead of step 3 it picks the longer
form and silently drops the other read: `(?:Previous )?Chain Hash` would report
Previous Hash alone rather than Previous Hash *and* Chain Hash. The ordering is
the whole rule; a version of this plan that states the steps without the order
states nothing.

A region denoting more than one owned field reporting each is a **corollary** of
step 4, not a separate rule.

### The harvest, stated as a property

The rule above classifies a label region. **Which string constants are label
regions at all** is a separate question, and it is a property, not a shape:

```
A string constant that flows into a compiled pattern is a candidate label region.
```

Exact dataflow is not decidable here, so it is approximated by three sources,
each resolving **one level** of module-level name indirection:

1. arguments of an `re.*` call;
2. an assignment bound to a `_RE`, `_PATTERN` or `_PAT` name;
3. an assignment whose right-hand side contains an `re.*` call.

The one level of indirection is load-bearing rather than defensive. Without it,
`_STRIPS = (...)` followed by `_INLINE = [re.compile(p) for p in _STRIPS]`
harvests nothing -- measured -- so hoisting `ledger_migrate:83`'s tuple to its
own binding, an ordinary refactor, reopens the fourth blind spot entirely.

**Broad harvest was measured and rejected**: taking every string constant
reaches 40 labels by pulling in docstrings and error strings, the noise class
D4 already rejects for emitters, and `meta_ledger_walker`'s own docstring is the
recorded instance of that misfire.

What the approximation still misses is recorded in D5.

**Nesting bound: 2.** `Previous Hash(?:\s*\([^)]+\))?`
(`qor/reliability/ledger_base_currency.py:29`) is the one live region needing the
second level, and it is the test that pins the bound.

## D1a: the owner declares label FORMS, because structure cannot decide aliasing

Iteration 2 proposed a "component rule": the field name must open a bold label. Measured against every label shape actually present in the tree, **it is wrong on 5 of the 7 shapes below**:

| shape | site | correct | component rule |
|---|---|---|---|
| `**Content Hash**` | many | read | MATCH |
| `**Chain Hash (Merkle seal)**` | many | read | MATCH |
| `**META_LEDGER Content Hash**` | `ledger_migrate:35,86` | read (alias) | invisible |
| `**Session Seal**` | `ledger_migrate:58,93` | read (alias of Chain Hash) | invisible |
| `**Previous Chain Hash**` | `ledger_migrate:47,49,89,90` | read (alias of Previous Hash) | invisible |
| `**(?:META_LEDGER )?Content Hash**` | `ledger_migrate:79` | read (alias) | invisible |
| `**Superseded Content Hash**` | `ledger_commitment:56` | **not** a Content Hash read | invisible |

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

**Containment never implies aliasing**, and D1n step 3 is where that is decided -- not restated here. A label containing an owned name but not declared as a form of it takes the `undeclared-label` branch rather than being silently ignored, which is what keeps D2's third-silent-category defect from returning one level down.

Measured with the D1n detector: **1** such label in the tree, `**Superseded Content Hash**` at `ledger_commitment:56`. An earlier draft said 4 across 2 modules; that count came from a detector that matched declared forms as substrings and counted intermediate expansions, and it is retracted.

## D2: the declaration surface is three-valued

| value | meaning | obligation |
|---|---|---|
| `alias of <field>` | a second label form of an owned field | owner must parse it |
| `owned field` | a field the owner owns | **owner must provide the reader** |
| `undeclared` | neither, and not assumed | reported as `undeclared-label`, baseline-able |

**`Superseded Content Hash` is the third, deliberately.** It is a distinct field, not an alias -- `ledger_commitment` carries `_CONTENT_RE` and `_SUPERSEDED_RE` side by side for different purposes. But it does not get an `OWNS` row either: `ledger_dialect` has no pattern for it, so declaring it owned would make `ledger_commitment` non-compliant with no remedy except importing a module with nothing to call. That is item 3 above, repeated. It gets one baseline row with the reason recorded; a *second* reader mints a new key and fails, forcing the alias-or-distinct ruling at the moment it first matters, with two real readers to reason from rather than one.

**Fields are (document, field) pairs.** `meta_ledger_walker` parses `**Verdict**`/`**Target**` from `META_LEDGER.md` while `verdict_dialect` owns those names in `.agent/staging/AUDIT_REPORT.md` (`verdict_dialect.py:4`) -- the declared document is a **path**, and D2 cross-check (a) tests the field against that path, so the distinction is load-bearing rather than cosmetic. Phase 275 audited that and deliberately declined to touch the walker; a name-only lint would contradict a sealed decision. Modules declare what they read:

```python
READS_DOCUMENTS = ("docs/META_LEDGER.md",)
```

A module parsing an owned field name while declaring **no** documents fails as `undeclared-document`.

**Declarations are cross-checked, not trusted** -- by two checks, because one is not enough:

- **(a) the field must occur as a label in every declared document.** Catches a fabricated or empty document.
- **(b) every declared document's stem must appear as a literal in the module, outside the declaration itself.** Catches the plausible-but-wrong document, which is the shape that actually gets written.

  Two parts, both load-bearing. **The stem**, not the full path: measured, the full path occurs in 2 of the 6 in-scope modules and the stem in 5, so a path rule would report on two thirds of its own subjects. **Outside the declaration**: a `READS_DOCUMENTS` tuple contains its own paths, so counting it makes the check vacuously true and it would pass the exact document it exists to catch. That second part was found by `test_a_declaration_naming_a_document_without_the_field_fails` failing against a first implementation that omitted it, and it belongs in the specification rather than only in the code.

(a) alone does not work, and the counterexample that motivated it defeats it: **`CHANGELOG.md:281` contains `**Content Hash**`** in prose describing Phase 251, and `:31` carries it again in Phase 281's entry. A module declaring `docs/CHANGELOG.md` while parsing that field passes (a), and since owned pairs are keyed on document, `(docs/CHANGELOG.md, Content Hash)` is not an owned pair either -- so the opt-out survives with no violation raised. Many tracked files carry the label, including every archived ledger snapshot, so the material for that bypass is abundant.

(b) does **not** have material in every live case, and an earlier draft said it did while naming the pre-Phase-277 module set -- `gate_provenance` and `evidence_bundle`, both delisted by this plan's own Affected files, and omitting `meta_ledger_walker`, `ledger_migrate` and `ledger_emit`, all three in scope. Re-derived against the actual six, excluding each declaration:

| module | full path | stem |
|---|---|---|
| `meta_ledger_walker` | 0 | 1 |
| `ledger_commitment` | 0 | 1 |
| `ledger_migrate` | 0 | 5 |
| `ledger_emit` | **0** | **0** |
| `snapshot_export` | 7 | 9 |
| `ledger_base_currency` | 1 | 4 |

**2 of 6** under a path rule, **5 of 6** under the stem rule. `ledger_emit` has material under neither, and that is a true finding rather than a gap -- see blind spot 8.

That stale list survived seven iterations of sweeps because every sweep was numeric and a module list contains no digit. **A stale module list is the same defect as a stale count, and no grep for a number finds it.**

A failure of either is `false-declaration`, which fails. Both are decidable against tracked files with no intent inference.

**Residue, stated rather than closed:** a module that opens document D for an unrelated purpose, carries D's path literal, and parses an owned field belonging to a different document passes both checks. Nothing structural distinguishes that from a correct declaration.

## D3: the baseline

The reader findings plus the `undeclared-label` findings ship as a recorded baseline. **The unit is a pattern site, not a pair.**

Measured once, with the detector implementing D1n, after it was validated against all sixteen classification cases in the audit record:

| | pre-declaration | post-declaration |
|---|---|---|
| read-violation sites | 31 | 29 |
| (module, field) pairs | 10 | 8 |
| modules | 6 | 5 |
| `undeclared-label` findings | 1 | 1 |
| `false-declaration` findings | n/a | 1 |

**Both columns are measured.** Bold previously marked the measured column; it
marks nothing now and has been removed rather than left to imply a distinction
that no longer exists. The pre-declaration `false-declaration` cell is **n/a**,
not zero: with no declarations present there is nothing a declaration can be
false about, and a `0` there would read as a measurement of an absence rather
than the absence of a measurement.

**This table is canonical.** Every other count in this plan references it rather than restating a figure. That is not tidiness: the same measurement stated independently in two places is how `:197` and `:249` came to disagree about one set inside a single round, and how a corrected figure survives in the place nobody swept.

Post-declaration was a prediction when this table was written and is now a
**result**. `READS_DOCUMENTS` exists in six modules, and the lint reports
`31 baselined, 0 failing` against a baseline of 29 reads, 1 `undeclared-label`
and 1 `false-declaration`.

**D2's acceptance test is closed by execution.** D3 set it as the test of
document scoping -- if scoping works `meta_ledger_walker`'s two rows vanish, and
if they need a baseline entry then D2 is wrong. Predicted 29, returned 29, and
the walker's rows are absent from the baseline artifact. That is stronger than
the argument this paragraph previously offered, and it was the last claim in
this plan resting on reasoning rather than a run.

The caveat this paragraph used to carry -- that post-declaration was predicted
because the declarations did not exist -- was accurate when written and made
false by the work it describes. It is recorded here rather than deleted, because
it is the third instance in two rounds of the defect at `:192`: a statement that
stops describing the thing it is attached to, and that no sweep for a stale
number would find.

`ledger_migrate` holds **24 of the 31**. `ledger_migrate`'s 24 sites decompose into three disjoint groups, which is the checkable form of the claim and does not rest on any baseline rule: **9** are plain declared forms a narrow harvest both sees and classifies; **10 are harvest-blind** (`:84-93`, the `_INLINE_STRIPS` lines, invisible to a rule reading only `re.*` arguments and `_RE` bindings); **5 are normalization-blind** (`:51`, `:53`, `:56`, `:79`, `:81` -- seen by any harvest, unclassifiable without D1n step 1). Two causes, two fixes, disjoint sets summing to 24. An earlier draft credited the whole gap to the harvest, and a later one quoted a delta over a 'narrow-visible-and-classifiable' baseline that depends on which narrow rule is meant; the decomposition above avoids that ambiguity. So the module carrying most of the baseline is also where the evasion route is idiomatic.

The single `undeclared-label` is `Superseded Content Hash` at `ledger_commitment:56`, which is exactly what D2 predicts and nothing else.

These are re-measured, not inherited. The parked plan's repository-wide figures were 14 pairs / 24 sites / 9 modules -- note that its 24 and 9 count different things from the 24 and 9 in the paragraph above, which are `ledger_migrate`'s sites and its plain subset; Phase 277 has since routed `evidence_bundle` and `gate_provenance` through the dialect, and `meta_ledger_walker`'s two rows drop out under D2's document scoping rather than needing a baseline entry -- which is the acceptance test D3 sets for D2 below, now with a result. The site discriminator changed the unit and an earlier draft left the pair count in place. The lint prints the live entry count at runtime, so the table above is the document's single recorded statement of it and no other section carries a copy -- which is the discipline this plan's own subject matter is about, and which it violated in four places before iteration 6. A baseline entry reports and does not fail; anything else fails. A baseline entry that no longer applies is **stale and fails**, so the baseline can only shrink.

**One exception, and it is permanent.** Under D1n step 4 a single pattern site can mint two baseline rows sharing a normalized pattern and differing in field, when an optional group crosses fields. That is the mechanism working -- widening a group until it crosses adds a row and fails loudly. But such a row never goes stale, because the pattern is still there, so it persists for the life of the pattern. Acceptable, visible in the diff, and written here rather than left for whoever hits it.

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
| `ledger_emit` (`false-declaration`) | path-parameterised: `append(ledger_path, ...)` reads its argument, so no document declaration can be honest. One row with its reason, on the `Superseded Content Hash` precedent; a **second** path-parameterised module mints a new key and forces the ruling then, with two real cases to reason from rather than one |
| ~~`meta_ledger_walker` (2 fields)~~ | **not needed.** Different document, and D2's scoping removes it. Measured: with document scoping the two rows vanish, which is the acceptance test below returning the predicted answer |

The `meta_ledger_walker` rows were D2's acceptance test: if scoping works they vanish, and if they need a baseline entry then D2 is wrong. **They vanish.** Executed, not predicted: `meta_ledger_walker` carries no row in the baseline artifact, so D2's scoping works and this acceptance test is closed by result. The counts are the table's and are not restated here.

## D4: what this does NOT do

- **Does not fix GH #467**, and its remaining module is deliberate rather than pending. Phase 277 fixed 2 of the 3; the third, `ledger_commitment._CONTENT_RE` (`:54`), is narrow on purpose -- the comment at `:36-53` records that widening it takes on-disk stale commitments from 74 to 116 in a gate that hard-ABORTs the seal, and a test guards it. It belongs in the baseline with that reason. The PR carries no closing keyword for #467.
- **Does not fix GH #477**, which this lint cannot see. See Limitations.
- **Does not fix #428.** The owner over-reads prose hex; this is about divergence, not correctness.
- **Does not cover emitters (GH #468).** Withdrawn for the ghost-path reason above. It also needs a *different detector*: an emitted literal never reaches an `re.*` call, so writer detection needs a write-sink anchor, and without one "any literal" gives 11 findings where 3 are real -- the other 8 being 5 docstrings and 3 error strings, including `meta_ledger_walker`'s own docstring flagging a pure reader as a writer.
- **Is not wired as a seal gate.** The ladder went 12 -> 8; a ninth ABORT is not earned by a check with no track record. Promotion is a later decision resting on its false-positive record.

  **What makes it run in the meantime is `test_live_tree_matches_the_recorded_baseline`,** which executes the lint against the real tree on every suite run. An advisory CLI nobody invokes would be a check in name only; the test is the enforcement mechanism until promotion, and it is why the baseline's can-only-shrink property has teeth. Stated because "advisory" otherwise reads as "optional".

## D5: the blind spots -- eight, numbered; six open and two closed

**1. Indirection.** `ledger_dialect` builds every pattern through `_field_re("Content Hash")`, so the field name never appears inside an `re.*` call literal and the owner is invisible to its own check. A violator evades with a one-line helper. The obvious mitigation -- also match bare field-name literals -- **was measured and rejected**: 14 hits of which 7 are noise (`TargetProfile`, `_HookTarget`, `SeedTarget`, `'Verdict'` in `sdk.py`, prose in an error string). Clean only for multi-word names; a rule that works for `Content Hash` but not `Target` has an unstated exception.

**2. Unrelated label names, with a live instance.** `**Session Merkle Seal**` is a `Content Hash` label form: `ledger_migrate.py:41-43` compiles it as `content_merkle_fenced`, and `extract()` at :62-76 routes it to `content` on the `content_` name prefix, with a second site at :80. It contains **no owned field name**, so neither the component rule nor `undeclared-label` can see it -- and an alias table only covers it once someone declares it. An earlier draft called this gap hypothetical; it is not.

**3. CLOSED -- the label region, and its cost is paid in D1.** The parked plan recorded `\*\*(?:META_LEDGER )?Content Hash[^\n*]*\*\*` (`ledger_migrate:79`) as unmatchable, citing one instance, and declined to close it because a bounded pattern-structure pass would cost D1's "no pattern semantics" claim.

Re-measured, it was never one instance: **10 of 28** owned-name label regions -- 36% -- are undecidable without it, across four shapes and two modules (`Chain Hash[^\n*]*` x6, `Content Hash[^\n*]*` x2, `(?:META_LEDGER )?Content Hash[^\n*]*` x1, `Previous Hash(?:\s*\([^)]+\))?` x1). A recorded-and-accepted gap covering 36% of labels is a silent category wearing a baseline row, which D1a already rules out for containment.

So D1n takes the bounded pass, D1 retracts the claim it cost, and the read-count rejection is re-founded on its own measurement. The gap is closed rather than declared.

**4. CLOSED at one level -- the harvest.** A harvest reading only `re.*` arguments and `_RE`-suffixed bindings cannot see `_INLINE_STRIPS = [re.compile(p) for p in (...)]` (`ledger_migrate:83`), because the argument is a Name. Ten live sites were invisible, and the shape is an available evasion of D3's central argument. The harvest rule that closes it is stated in D1n, not here.

**What it still misses**, stated as a gap rather than left to be discovered: chains longer than one binding. `A = (...)`, `B = A`, `C = [re.compile(p) for p in B]` resolves `B` and stops. One level was chosen because it closes the ordinary refactor -- hoisting a collection to its own name -- and because each further level widens what counts as "flows into a pattern" without a measured case demanding it.

**5. Non-bold label forms, and an asymmetry inside the owner.** The extractor reads labels between `**...**` only. `verdict_dialect.VALUE_RE` (`:51-56`) accepts far more: an optional `#{1,6}` heading prefix and `[*_]*` around the field word, so `## Verdict:` and `_Verdict_:` are accepted verdict labels the extractor cannot see. `TARGET_RE` (`:69-72`) is bold-only, so the owner is not even internally consistent about this.

Measured: zero live instances -- `meta_ledger_walker:21-22` is the only non-owner parser of either field and it uses the bold form for both. The `OWNS` rows for `verdict_dialect` therefore under-describe what the owner accepts, and a module parsing a heading-form verdict would be invisible. Recorded rather than closed: covering it means the extractor must recognise every marker shape a declaration names, which is a wider change than the two constructs D1n enumerates.

**6. Transitive import of the owner.** The import check is direct-only: it looks for `ledger_dialect` or `verdict_dialect` in an import statement. Reach accepts consumption through a re-export -- `reconcile.py:16-22` imports the patterns from `qor.scripts.ledger_hash`, which re-exports them at `:158-160` -- so a module doing that is compliant by design and invisible to the check.

Measured: no module is affected today, because every transitive consumer also carries no label literal and so is never scanned. A module that both imported transitively **and** carried a literal would be reported as a violation wrongly -- a false positive, the class this lint has no live evidence about. Closing it means resolving re-export chains, which is a different detector.

**8. A path-parameterised module cannot honestly declare a document.** `ledger_emit.append(ledger_path: Path, ...)` (`:68`) reads whatever path it is handed (`:79`); it is deliberately document-agnostic. So `READS_DOCUMENTS` **overstates** for it under any value D2 currently offers, and its `false-declaration` finding is a **true positive**, not noise.

This is a gap in D2's declaration surface, not a detector limitation -- the detector reports exactly what is true. Recording it the other way round would have been convenient and wrong: D4 rests promotion on the false-positive record, and baselining a genuine finding as though it were false would contaminate the evidence that decision depends on.

**7. Undeclared alias labels.** Until an owner declares a form, a module reading only that form is invisible. Three live alias forms exist today and all are declared in D1a, but the next one is invisible until someone declares it. `undeclared-label` narrows this: a *label* containing an owned name is caught even when undeclared. A wholly unrelated label name for the same field is not.

Each open gap is pinned by a test, so it is recorded rather than described, and each closed one is pinned by the test that closes it.

## Tests

Written first, red before the code. Each runs twice for determinism.

| Test | Pins | Red before |
|---|---|---|
| `test_flags_a_parser_that_does_not_import_its_owner` | the core property | yes |
| `test_accepts_a_parser_that_imports_its_owner` | the clean path | yes |
| `test_a_declared_alias_label_is_a_read_of_its_field` | D1a; `**Previous Chain Hash**` -> Previous Hash | yes |
| `test_a_declared_alias_is_not_a_read_of_a_field_it_merely_contains` | `**Previous Chain Hash**` is not a `Chain Hash` read | yes |
| `test_an_undeclared_containing_label_is_reported_not_ignored` | `**Superseded Content Hash**` -> `undeclared-label` | yes |
| ~~`test_an_optional_prefix_group_is_matched_as_its_alias`~~ | **withdrawn** -- asserts behaviour an alias table cannot produce; see D5 | -- |
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
| `test_longest_form_wins_applies_within_an_expansion_not_across_the_set` | **D1n step 3 vs 4**; `(?:Previous )?Chain Hash` reports Previous Hash AND Chain Hash, not the longer form alone | yes |
| `test_an_intermediate_expansion_is_not_a_label_form` | D1n step 2; one site must not mint four spurious `undeclared-label` findings | yes |
| `test_a_declared_expansion_and_an_undeclared_sibling_both_report` | D1n step 3; `(?:Superseded )?Content Hash` yields a Content read plus one `undeclared-label` | yes |
| `test_the_nesting_bound_resolves_ledger_base_currency` | D1n's bound of 2; `Previous Hash(?:\s*\([^)]+\))?` | yes |
| `test_a_pattern_in_a_comprehension_fed_collection_is_harvested` | the `_INLINE_STRIPS` evasion of D3's key | yes |
| `test_the_canonical_qualified_label_reads_as_its_field` | `**Chain Hash (Merkle seal)**` is a Chain Hash read, not an `undeclared-label` | yes |
| `test_a_third_construct_is_not_normalized` | D1n's enumeration is closed; an unlisted construct leaves the expansion discarded | yes |
| `test_optional_group_expansion_is_order_independent` | D1n step 1; the `(?:X)?` expansion must resolve `Previous Hash(?:\s*\([^)]+\))?` WITHOUT relying on the wildcard strip running first | yes |
| `test_a_hoisted_pattern_collection_is_harvested` | D1n's one level of indirection; `_STRIPS = (...)` then `[re.compile(p) for p in _STRIPS]` must not evade | yes |
| `test_live_tree_matches_the_recorded_baseline` | the repo's actual state | no |

`test_a_second_diverging_pattern_in_a_baselined_module_fails` is the one that matters most: it is the exact case iteration 2 would have shipped green.

`test_longest_form_wins_applies_within_an_expansion_not_across_the_set` is the second. The two rules it separates are individually correct and give opposite answers on the same input, and the plan text before D1n did not say which applied first -- so an implementer following it could have shipped either. `test_the_canonical_qualified_label_reads_as_its_field` pins a defect that was live in the detector during this phase: unescaping `\*` but not `\(` misfiled `**Chain Hash (Merkle seal)**` as an unknown label, which silently removed two modules from the violation list.

## Affected files

- `qor/scripts/dialect_ownership_lint.py` (new)
- `qor/scripts/ledger_dialect.py`, `qor/scripts/verdict_dialect.py` (`OWNS` declaration only)
- `READS_DOCUMENTS` declaration only, no parser changes:
  - `qor/scripts/meta_ledger_walker.py`
  - `qor/scripts/ledger_commitment.py`
  - `qor/scripts/ledger_migrate.py`
  - `qor/scripts/ledger_emit.py` -- reads `Chain Hash` at line 19 independently of its emitter sites
  - `qor/scripts/snapshot_export.py`
  - `qor/reliability/ledger_base_currency.py`
- `.qor/dialect-ownership-baseline.json` (new, tracked -- verified not gitignored, and pinned by test)
- `tests/test_dialect_ownership_lint.py` (new)
- `CHANGELOG.md`

**`evidence_bundle.py` and `gate_provenance.py` are no longer listed.** Phase 277 routed both through the dialect; measured, neither carries a field-label literal any more, so neither is scanned and neither needs a declaration. The parked plan listed both.

**`reconcile.py` is deliberately absent, for a reason an earlier draft stated wrongly.** That draft said it "only writes". It reads: `PREV_HASH_RE.search` at `:41` and `CHAIN_HASH_RE.search` at `:71`. It scores zero in the scan for a different reason -- it carries no label literal of its own, consuming the owner's compiled patterns instead, which is the compliant shape.

It also imports them from `qor.scripts.ledger_hash` (`:16-22`), not from `ledger_dialect` directly -- which is compliant by design, since Reach accepts transitive consumption through `ledger_hash.py:158-160`. The detector does not see that, and the gap is recorded in D5 with the others.

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
- **The compliant class has no live instance, and the false-positive claim is weaker than a bare "0" suggests.** `seal_entry_check`, `ledger_hash`, `verdict_reconcile` and `reconcile` import their owner and consume its *compiled patterns*, so they carry no literal and fall outside the scan entirely. `test_accepts_a_parser_that_imports_its_owner` is therefore synthetic-only.

  What the evidence actually is: **every finding in D3's table hand-checked to a declared form or an owned name, and zero live examples of the compliant class to be wrong about.** An earlier draft cited "14 negatives", a figure inherited from the parked plan and not re-derived; it is retracted. A detector cannot demonstrate a low false-positive rate against a class with no live members, and this one does not.
- A declaration can still be wrong in the one way both cross-checks miss: a module carrying a document's path literal for an unrelated reason while parsing a field owned elsewhere.
- **A module can import the owner and still parse the field itself; the lint sees an import, not a use. GH #477 is a live instance.** `reconcile.py` imports `PREV_HASH_RE` and `CHAIN_HASH_RE`, so it is compliant under this property, and at `:44` and `:73` it reads `group(1) or group(2)` from a three-group value pattern, dropping the bare-hex form. This lint passes it. Shipping this must not be described as covering that defect; #477 is a separate fix and stays open.
- Defeatable by indirection, and by a wholly unrelated label for an owned field (D5).
- The baseline records the pattern-site entries counted in **D3's table**, plus its single `undeclared-label` entry. The figures are not restated here: D3 is canonical, and every count in this plan references it rather than carrying its own copy. If it grows, this lint has failed at its job, visibly in its own diff.
- Advisory: it cannot stop a seal.
