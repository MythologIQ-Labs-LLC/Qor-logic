# Phase 275: one definition of the audit verdict

**change_class**: feature
**Issues**: GH #424, GH #462
**Research**: docs/research-brief-verdict-definition-2026-09-08.md
**Iteration**: 6 (iterations 1-5 VETOed; 19 findings, all reproduced)
**Session**: 2026-09-08T1303-1f0903

## Scope note

Two gates read `.agent/staging/AUDIT_REPORT.md` and disagree about what its verdict is on 44% of real reports. One fails open (#424), one fails closed on valid input (#462). Gate-behaviour reach, so a full review round.

## What iterations 1 through 5 got wrong

Recorded because these are substantially the same mistake each time: a guard written against the instance in front of it rather than the class, and a number counted at a unit that flattered it.

1. **The value pattern was itself an enumeration.** `([A-Za-z]+)` anchored to `\s*$` cannot read `## VERDICT: PASS (L1)`. Such a line is not *conflicting*, it is **invisible**, so a readable `PASS` elsewhere wins uncontested and #424 survives untouched. The attack input is `## VERDICT: PASS` above `**Verdict**: VETO (finding 3 unresolved)`. Iteration 1's own test asserted that line "stays unmatched", pinning the hole open.
2. **`_TARGET_RE` was carved out in one unmeasured clause.** It has the identical trailing-text defect in the same function; 62 of 84 reports would still ABORT, changing which finding code printed and nothing else.
3. **"Nothing emits these forms" was false.** Two templates emit both forms per report (GH #464). The claim came from grepping `qor/templates/` when the emitters live under the skill's `references/`.
4. **Iteration 2's label probe was itself case-anchored**, so the #424 class survived one layer below iteration 1's instance: `verdict: VETO` in lowercase is invisible to both the value pattern and the guard, and `is_pass` returns True on a VETO report. Fixing the reader without giving the guard strictly wider reach than the reader leaves exactly this gap.
5. **"59 reconcile cleanly" counted parses, not agreements** -- after the brief had already recorded, twice, that counting matches rather than agreements overstates a fix. The same substitution recurred one level up, in the number the issue closes on, having been written down as a lesson in the same document.
6. **Iteration 3 fixed the target field's parsing and left its selection first-match**, in no clause at all -- carving out the class after fixing the instance, on the same field as item 2. D2's argument against first-match was already written in the same document and was simply not applied to the field one function away.

7. **The fix for item 6 reproduced item 6.** Adding agreement-required to the target field left `reconcile`'s message unchanged, so a report with two disagreeing `**Target**` lines is reported as "no `**Target**` line" -- factually false, and unactionable in exactly the way D3 argues a conflict message must not be. D3 had already given the verdict half a third branch for this precise reason; the field added one round later did not get one. The planned test pinned the refusal and not the message, so it would have gone green on the wrong one.

8. **The target-discrimination claim was measured over 62 and asserted over "the corpus" (204)** -- the same unit substitution as items 2 and 5, in a sentence written to summarise the correction of item 5. Measured properly it was the stronger claim: 103 pairable, 99 agree, 4 disagree, and two of the four disagreements had never been looked at (GH #465).

The pattern: the fix is scoped to the example in hand. Item 7 arrived *inside the fix for item 6*, which is the strongest available evidence that stating the rule is not sufficient -- item 6's correction was written in the same session that produced item 7. The standing guard against it, applied throughout this document: every rule states its field-agnostic form and the measurement that makes it free, every new field gets the same three-way message contract as the first, every count names the population it was measured over, and tests pin the message code rather than only the refusal.

## D1: a shared verdict dialect

New `qor/scripts/verdict_dialect.py`, following `ledger_dialect.py` -- including the part iteration 1 omitted. Import direction matches the existing `reliability -> scripts` convention: four module-level imports (`ledger_base_currency.py:26`, `seal_entry_check.py:27-29`) plus two function-local ones in `gate_chain_completeness.py`.

```
VALUE  ^(?:#{1,6}[ \t]*)?\**(?:Verdict|VERDICT)\**\s*[:\-]\s*\**([A-Z]+)\**(?:\s*\([^)]*\))?\**\s*$
LABEL  ^(?:#{1,6}[ \t]*)?[*_]*(?i:verdict)[*_]*\s*[:\-]\s*\S
TARGET ^\*\*Target\*\*\s*:\s*`?([^`\s]+)`?(?:[ \t]+.*)?$
```

**The label probe is case-insensitive; the value pattern is not.** Iteration 2 anchored both as `(?:Verdict|VERDICT)`, which left the #424 class alive one layer below where iteration 1's instance sat: an all-lowercase label matches neither pattern, so the line is invisible to the reader *and* to the guard meant to catch what the reader cannot parse.

```
## VERDICT: PASS

verdict: VETO          -> value='PASS', conflict=False, unreadable=False, is_pass=True
```

With the inline `(?i:verdict)` on the probe alone -- scoped to the label word, so the value stays case-sensitive -- that line becomes unreadable and the report refuses, while a lowercase *value* under a correct label still refuses, so the F6 restriction is unaffected. Measured over all 204 reports the change is free: newly-unreadable reports 0, `is_pass` unchanged at 190.

The property that makes this design sound is that **the probe is strictly wider than the reader at every position** (`[*_]*` includes `\**`, `(?i:verdict)` includes `(?:Verdict|VERDICT)`, and `\S` is implied by `\**[A-Z]+`). No readable verdict line can therefore escape the guard. Independently fuzzed over 60,000 inputs for a line matching the value pattern but not the probe: zero counterexamples.

**The trailing `(...)` group is what closes #424.** It reads a qualified line as its value rather than dropping it, so `**Verdict**: VETO (finding 3 unresolved)` becomes a conflicting `VETO` instead of vanishing. Measured over 204 reports: unreadable-label reports fall 3 -> 0, conflicts stay 0, `is_pass` rises 187 -> 190 -- it simultaneously closes the hole and stops wrongly refusing two genuine `PASS (L1)` reports.

**`([A-Z]+)`, not `([A-Za-z]+)`.** Lowercase is an unneeded relaxation on the path that authorizes `capture`; the corpus vocabulary is `PASS` 232 / `VETO` 14, all uppercase. `**Verdict**: pass` becomes unreadable, trips the label probe, and refuses with the format hint rather than being silently accepted. It also makes the dataclass's "uppercased" claim honest rather than load-bearing normalization.

**The label probe is the `any_hash_label_present` counterpart** (`ledger_dialect.py:60-76`, GH #363), which exists for word-for-word this failure: telling "field absent" apart from "field present but unparseable" so the latter is reported rather than silently dropped. The unreadable set is empty on today's corpus; the probe is the fail-closed guard for forms not yet written.

```python
@dataclass(frozen=True)
class Verdict:
    value: str | None       # the agreed verdict; None when absent, conflicting, or unreadable
    conflict: bool          # >1 distinct readable value
    unreadable: bool        # a verdict-labeled line the value pattern could not parse
    lines: tuple[str, ...]  # every verdict-labeled line, verbatim, for messages

@dataclass(frozen=True)
class Field:
    """The same shape for `**Target**`: agreement-required, not first-match."""
    value: str | None       # None when absent or when the lines disagree
    conflict: bool
    lines: tuple[str, ...]

def is_pass(v: Verdict) -> bool:
    return v.value == "PASS"
```

**`value` is `None` whenever `conflict` or `unreadable`.** Pinned by test, not left to the caller. This is what makes the API safe for `reconcile`, which branches on the raw string at `verdict_reconcile.py:93`: the natural conversion stays correct instead of depending on routing through `is_pass`. A predicate whose safety rests on calling the right function is a defect waiting for the next caller.

`is_pass` compares a string. It never truth-tests a container -- a predicate returning a list of problems consumed as `if not problems` inverts on a non-empty list of vetoes.

## D2: agreement-required, on both fields

A report authorizes capture only when every verdict-labeled line is readable, they state one distinct value, and it is `PASS`.

Justified by the corpus: 0 of 204 reports carry disagreeing values, so this refuses nothing ever written, while refusing both #424 shapes. First-match and last-match both close the reported instance and leave the class open -- a quoted example above, or an appendix below, silently outvotes the real verdict. Agreement-required is the only one of the three whose failure mode is a refusal rather than a wrong answer.

**The same rule applies to `**Target**`, because that argument is field-agnostic.** Iteration 3 fixed the target field's *parsing* and left its *selection* as `.search()` -- first match wins -- in no clause at all. That is a fail-open in the exact direction `verdict_reconcile` exists to prevent: its own docstring records that `.agent/staging/` is not session-scoped, so a stale report survives indefinitely and the interdiction can pass on work belonging to a different phase. A report whose first `**Target**` line is a quoted or superseded path, paired with an artifact naming that same path, reconciles clean on the target half while the report's real target is something else. Plans here routinely cite a prior phase's plan path in prose above the fields.

The cost is the same as the verdict half's: **0 of 204 reports carry more than one distinct `**Target**` value**, so agreement-required refuses nothing ever written and closes the selection hole. Taking the parsing fix without the selection fix would be another instance of this plan's own recorded mistake -- fixing the instance and leaving the class.

## D3: both call sites, both halves

- `intent_lock._audit_has_pass` -> `verdict_dialect`. `_verdict_hint` gets **three** branches: `unreadable` -> the existing "canonical form" message; `conflict` -> a new message naming the offending lines verbatim from `lines`; otherwise -> "audit not PASS". Two branches would drop a conflict into "audit not PASS", the exact unactionable message this is meant to fix.
- `verdict_reconcile._read_report` -> the same module for **both** its verdict and its target halves.

**Every field gets the same three-way message contract.** `reconcile` currently emits `report-unreadable` ("no `**Target**` line in \<path\>") whenever the target value is `None`. With agreement-required on that field, `None` now also means "two lines disagree", so the existing message would be factually false on a conflict. A `target-conflict` finding code names the disagreeing lines from `Field.lines`, mirroring the verdict half's third branch. A message that says a field is absent when it is contested is the same unactionable failure D3 exists to prevent.

**The class is enumerated, not sampled.** Given that this plan's recorded failure is fixing the instance and leaving the class, the two modules were swept for every remaining field selection rather than waiting for the next one to be found. `verdict_reconcile` defines exactly two field regexes, `_TARGET_RE` (line 22) and `_VERDICT_RE` (line 23), selected at lines 50-51; both are replaced. `intent_lock` has two `re.search` calls, the PASS predicate (line 71) and the hint probe (line 84); both are replaced. `_read_artifact` parses JSON and holds no regex, and `reconcile` compares a single artifact value. There is no third text-field selection in either module.

The existing assertions at `test_intent_lock_anchored_pass_check.py:138-148` pin `"canonical form"` for a malformed line and `"audit not PASS"` without it for a verdict-free file. The three-branch map satisfies both unchanged: `Verdict -> PASS` trips the label probe (`[:\-]` matches `-`, `\S` matches `>`) and `no verdict content here` trips neither.

## D4: what this closes, measured

`_TARGET_RE`'s qualifier tolerance alone is not enough -- **readable is not reconcilable**. 29 reports write `` **Target**: `docs/plan-x.md` ``; tolerating a qualifier makes the line match but captures the backticks into the value, turning `report-unreadable` into `target-mismatch`. Same refusal, different code. Hence the backtick stripping, which `meta_ledger_walker._TARGET` already does.

| of the 84 reports `reconcile` flags today | |
|---|---|
| target **parses to a usable path-shaped value** after this phase | **59** |
| refuse structurally: no `**Target**` field in any form | 22 |
| refuse structurally: prose target (`Phase 240 ... at <sha>`) | 3 |

**59 is a parse count, not a reconcile count, and the row says so.** Whether a parsed target *agrees with its artifact* is a different measurement, and most of the population cannot supply it. Pairing each report to `.qor/gates/<session>/audit.json` by its `**Session**` line, over the 62 with a readable target:

| | |
|---|---|
| pairable, and target agrees with the artifact | 13 |
| pairable, and target **disagrees** -- the prose-target reports | 2 |
| unpairable: report carries no `**Session**` line | 36 |
| unpairable: named artifact not recoverable at that commit | 11 |

So 47 of the 62 are **unverifiable, not verified-good**. The 2 disagreements are not failures of this phase: they are the `Phase 240 execution-context governance at <sha>` reports, whose target parses to `Phase` and correctly mismatches `docs/plan-qor-phase240-execution-context-governance.md`. That is `reconcile` doing its job.

**Measured over the whole corpus rather than over this subset**, because the sub-table above quantifies only the 84 and the discrimination claim is about the comparison itself:

| all 204 reports | |
|---|---|
| pairable with their artifact | 103 |
| target agrees | 99 |
| target disagrees | 4 |

All 4 disagreements are cases where the report and its artifact genuinely describe different things, so the target comparison demonstrably discriminates in four independent cases. Two are the `Phase 240` reports above; the other two sit outside the 84 and are a different shape -- their artifact's `target` names a gate artifact (`.qor/gates/<session>/remediate-iter1.json`) where a plan path belongs, one of them as an absolute local path. `reconcile` would flag both. That is a question about how gate artifacts are written rather than how reports are read, so it is filed (GH #465) rather than fixed here.

An earlier draft asserted these were "the only direct evidence in the corpus" while having measured only the 62 -- the same unit substitution recorded as items 2 and 5. The corrected measurement is the stronger claim, not the weaker one.

#462 closes on the parse measurement, which is the right one because #462 is a parsing defect; the agreement figure is reported separately rather than folded in.

**How these numbers were obtained is part of the finding.** A first run of this measurement reported 12 / 0 / 36 / 14. It was wrong: its `**Session**` regex captured the surrounding backticks from `` **Session**: `2026-08-28T1956-6e0074` ``, so those reports resolved to a malformed artifact path and were misfiled as "artifact not recoverable" rather than as the disagreements they are. That is the identical backtick-capture defect this section exists to document, reproduced inside the script measuring it, after it had been written down two paragraphs above. Stripping the backticks reproduces the reviewer's independent count exactly.

A close implying 84/84 would be the overclaim iteration 1 was vetoed for.

An earlier draft added "every report from 2026-08-18 onward parses cleanly" here. It was false -- the two 2026-08-30 prose-target reports are counted as structural refusals in the table directly above and as the 2 disagreements in the table below it. The sentence is deleted rather than corrected: it restated a boundary the authoritative table already carries, and a restated number cannot be caught by re-deriving the original.

## D5: what this does NOT do

- **Does not close GH #463.** A wired `|| ABORT` produced no observable effect across a continuous run of sealed phases. Fixing the parser stops this gate mis-firing and would thereby make its silence permanently invisible. The PR body must carry no closing keyword for it.
- **Does not converge the templates (GH #464).** 204 historical reports exist in both forms and these gates must read them forever, so the dialect accepts both regardless of what the templates say from today. Convergence removes no branch, no test and no fixture from this phase; the entire benefit accrues after it. Against that, the skill-tree edit forces a dist recompile, pulling in skill-size headroom, dist parity and doc_integrity term-drift -- a failure axis unrelated to gate semantics. The deferral is made safe by the conflict hint naming offending lines verbatim, and by #464 being filed over both emitters and their drift.
- **Does not touch `meta_ledger_walker`.** It reads `META_LEDGER.md`, a different document with its own owning dialect.

## Tests

Written first, red before the change. Every new test run twice for determinism.

| Test | Pins | Red before |
|---|---|---|
| `test_quoted_pass_line_inside_a_veto_report_is_not_pass` | GH #424 as reported | yes |
| `test_qualified_veto_line_conflicts_rather_than_vanishing` | **the iteration-1 hole**; the attack input | yes |
| `test_pass_beside_an_unenumerated_verdict_is_a_conflict` | the `BLOCKED` shape | yes |
| `test_qualified_pass_is_read_as_pass` | the 3 corpus reports; no wrong refusal | yes |
| `test_lowercase_verdict_value_is_unreadable_not_accepted` | F6; the value relaxation stays shut | yes |
| `test_lowercase_verdict_LABEL_is_unreadable_not_invisible` | **the iteration-2 hole**; probe case-insensitivity | yes |
| `test_mixed_case_verdict_label_is_unreadable` | the same class, `VeRdIcT:` | yes |
| `test_repeated_identical_verdicts_are_not_a_conflict` | the 39 template-produced reports | yes |
| `test_bolded_value_is_read` / `test_heading_form_is_read` | GH #462 forms | yes |
| `test_inline_prose_mention_is_not_a_verdict_line` | Phase 53 anti-prose anchors | no |
| `test_indented_verdict_is_refused` | Phase 53 anchor, explicitly re-pinned | no |
| `test_absent_verdict_reads_as_none_not_as_pass` | fail-closed on empty | no |
| `test_value_is_none_under_conflict` | the D1 contract | yes |
| `test_value_is_none_under_unreadable` | the D1 contract | yes |
| `test_hint_distinguishes_unreadable_conflict_and_not_pass` | the three branches | yes |
| `test_existing_hint_substrings_are_preserved` | the two pinned assertions | no |
| `test_reconcile_accepts_heading_and_bolded_pass_reports` | GH #462 | yes |
| `test_reconcile_reads_a_backticked_target` | the 29 | yes |
| `test_reconcile_reads_a_qualified_target` | the 40 | yes |
| `test_reconcile_still_reports_a_missing_target_field` | the 22 stay refused | no |
| `test_disagreeing_target_lines_do_not_take_the_first` | F12; the selection hole | yes |
| `test_disagreeing_targets_report_target_conflict_not_missing` | F15; pins the **code**, not just the refusal | yes |
| `test_repeated_identical_target_lines_are_not_a_conflict` | 0 of 204 disagree; refuses nothing real | yes |
| `test_a_report_quoting_the_template_placeholder_is_refused` | F14; `## VERDICT: [PASS / VETO]` refuses, documented not surprising | yes |
| `test_reconcile_still_flags_a_genuine_veto_report` | the fix does not relax the gate | no |
| `test_reconcile_still_flags_a_conflicted_report` | agreement-required reaches reconcile | yes |
| `test_malformed_qualifier_is_unreadable_not_ignored` | multi-parenthetical, nested, unbalanced both ways | yes |
| `test_a_verdict_word_inside_a_qualifier_is_not_a_value` | `PASS (VETO withdrawn)` reads PASS, no conflict; the boundary that makes the group safe rather than merely permissive | yes |
| `test_capture_refuses_a_conflicted_audit` | end to end at the gate | yes |

**Fixtures, not git history.** Committed fixtures reproduce each real shape, including a backticked target and a qualified verdict. A test walking `git log` would pass locally and fail on a shallow CI clone.

## Affected files

Corrected: iteration 1 named two files that do not exist, and its first CI command exited 4.

- `qor/scripts/verdict_dialect.py` (new)
- `qor/reliability/intent_lock.py` (`_audit_has_pass`, `_verdict_hint`)
- `qor/scripts/verdict_reconcile.py` (`_read_report`, `_VERDICT_RE` and `_TARGET_RE` removed)
- `tests/test_verdict_dialect.py` (new)
- `tests/fixtures/verdict/*.md` (new)
- `tests/test_intent_lock_anchored_pass_check.py` (additions; 11 existing assertions on `_audit_has_pass` plus 2 on the hint output, all verified to survive)
- `tests/test_verdict_reconciliation.py` (additions)
- `tests/test_security_fixes.py` (lines 168-191 assert on `_audit_has_pass`; verified to survive, listed because the phase reaches it)
- `CHANGELOG.md`

`README.md` is deliberately not touched. `doc_integrity_strict.py:192-197` (release classes at 160, WARN semantics at 175) will WARN for a release class without it; the change is an internal parser with no README-visible surface, so the warning is accepted rather than answered with a cosmetic edit.

## Reach

- **Behaviour change at two gates.** `capture` refuses a class it accepted; `reconcile` accepts a class it refused. Consumer-visible, hence `feature` -- matching Phase 194, which introduced `ledger_dialect.py` under the same class.
- A downstream consumer adopted `intent_lock.py` verbatim and carries a test pinning the present semantics as an inherited weakness; it becomes deletable once this lands. That repository is not touched from here.
- No skill or template changes, so the dist tree is untouched.

## CI Commands

```
python -m pytest tests/test_verdict_dialect.py tests/test_verdict_reconciliation.py tests/test_intent_lock_anchored_pass_check.py tests/test_security_fixes.py -q
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- **Any column-0 line beginning with a verdict label whose value is not a bare uppercase word makes the whole report unreadable, and a fenced code block does not protect it.** The `^` anchor matches inside fences; only indentation prevents the match. This is the fail-closed direction and it is correct, but the refusal surface is wider than "quotes a standalone VETO line": a report quoting the template placeholder `## VERDICT: [PASS / VETO]`, or quoting D1's own `verdict: VETO` example, refuses at `capture` with the format hint. **This phase's own audit report and any report for GH #464 will quote exactly those lines** -- indent them by four spaces. Verified: indented, they read clean; fenced, they refuse. Documented here so the operator meets a contract rather than a surprise.
- 25 of the 84 still refuse. They name no usable target, which is correct behaviour, but it means #462's headline number does not go to zero.
- Textual detection only. A report whose verdict says PASS while its findings say otherwise is not a parsing problem; GH #436 covers an auditor amending what it judges.
- The dialect defines the accepted forms; two templates still emit two of them (GH #464), so the split regenerates until that lands.
- This establishes what the gates decide, not that they run. GH #463.
