# Research brief: the audit verdict has three definitions and no owner

**Date**: 2026-09-08
**Session**: 2026-09-08T1303-1f0903
**Issues**: GH #424, GH #462 (GH #463 filed, out of scope here)

## The finding

Three modules parse "the audit verdict", each with its own regex, none shared:

| module | pattern | selection |
|---|---|---|
| `qor/reliability/intent_lock.py:72` | heading or bold label, value `PASS` only | any matching line anywhere |
| `qor/scripts/verdict_reconcile.py:23` | bold label only, unbolded value | first match |
| `qor/scripts/meta_ledger_walker.py:21` | bold label, any uppercase value | first match |

The first two read the **same file**, `.agent/staging/AUDIT_REPORT.md`, and disagree about what a PASS looks like on 44% of real reports. The third reads `META_LEDGER.md`, whose entries do use the bold form, so its pattern suits its input; it is listed for completeness and is not a defect.

## Measurement

Population: all 204 historical versions of `.agent/staging/AUDIT_REPORT.md`, recovered from git. That is the unit both gates are pointed at.

| | |
|---|---|
| audit reports | 204 |
| carrying no verdict-shaped line | 1 |
| carrying more than one verdict **line** | 39 |
| carrying more than one **distinct** verdict value | **0** (see the qualifier caveat below) |
| `intent_lock` accepts as PASS | 189 |
| of those, `verdict_reconcile` flags `verdict-not-pass` | **84 (44%)** |
| verdict vocabulary in use | `PASS` 232, `VETO` 14, all uppercase |

**Two corrections worth recording, both found by measuring again rather than by reasoning.**

*The unit.* A first pass measured over all `*.md` and found 72 of 96 files carrying conflicting verdicts, which would have made "fail closed on disagreement" reject three quarters of the corpus. That number was wrong: it counted `META_LEDGER.md` and test fixtures, which aggregate many entries by design. At the correct unit -- one audit report -- the conflicting-verdict count is zero. The wrong unit pointed the design in the opposite direction.

*The population.* "0 disagreeing" is measured only over verdict lines a reader can parse. Three reports carry a **qualified** verdict (`## VERDICT: PASS (L1)`, `*Verdict: PASS (L1)*`) that a bare `([A-Z]+)` value pattern cannot read. Such a line is not counted as disagreeing because it is invisible, and invisibility is the dangerous direction: a `**Verdict**: VETO (finding 3 unresolved)` line would drop out and let a PASS elsewhere carry the report. The corpus count is therefore only sound alongside a value pattern that tolerates a trailing parenthetical -- which reads all three as `PASS` and empties the unreadable set to **0** across all 204.

**Readable is not reconcilable.** The same trap appears on the target half: tolerating a trailing qualifier makes 62 of the 84 `**Target**` lines *match*, but 29 of them capture surrounding backticks into the value, turning `report-unreadable` into `target-mismatch` -- a different code and the same refusal. Counting matches rather than agreements overstates the fix by 29.

## What each defect is

**GH #424 -- the lock fails open.** `_audit_has_pass` returns True if a PASS-shaped line appears anywhere, with no relation to the report's verdict. Reproduced against the current tree:

```
quoted-PASS-inside-VETO  -> True
PASS + BLOCKED           -> True
genuine PASS             -> True
genuine VETO             -> False
```

The `BLOCKED` row matters: any fix that enumerates known verdict words rather than reading whatever word is present re-opens the hole for an unrecognized verdict.

**GH #462 -- the reconciler fails closed on valid input.** `^\*\*Verdict\*\*:\s*(\w+)\s*$` matches neither `## VERDICT: PASS` nor `**Verdict**: **PASS**` (the value is bolded, so `\w+` does not reach it). Demonstrated on Phase 262's own report and its own matching gate artifact, both recording PASS:

```
artifact verdict : PASS
report verdict lines: "## VERDICT: PASS", "**Verdict**: **PASS**"
findings: Finding(code='verdict-not-pass', detail='report verdict is None')
```

## Where the split comes from

The two forms are not drift by accident. Two template files instruct both of them, in the same report:

| file | lines |
|---|---|
| `qor/references/ql-audit-templates.md` (130 lines) | `## VERDICT: [PASS / VETO]` at 15; `**Verdict**: [PASS / VETO]` at 76 and 116 |
| `qor/skills/governance/qor-audit/references/qor-audit-templates.md` (203 lines) | `## VERDICT: [PASS / VETO]` at 15; `**Verdict**: [PASS / VETO]` at 123 and 163 |

That is the mechanism behind the 39 multi-line same-value reports: the template asks for the verdict twice, in two dialects. The two files have also drifted from each other, which is a second defect in its own right.

This was nearly missed. An earlier pass grepped `qor/templates/` and concluded "nothing emits them"; the emitters live under the skill's `references/`, so the search location, not the reasoning, produced the wrong answer.

## Why one phase and not two

They are one defect: there is no single answer to "what is this report's verdict", so each caller invented one. Fixing `intent_lock` alone leaves two definitions of PASS in the tree, one of which still cannot read 44% of real reports. That is the half-measure shape -- the reported symptom closed, the cause left standing.

## What the corpus permits

Because zero reports carry disagreeing verdicts, an agreement-required rule is a no-op on all 204 while closing the #424 hole. Both alternatives are worse:

- **first-match wins** -- the current reconciler behaviour; a quoted example above the real verdict silently outvotes it.
- **last-match wins** -- also a no-op on the corpus today, but a trailing appendix that quotes a verdict form silently outvotes the real one. It closes the reported instance and leaves the class open.

Agreement-required is the only one of the three whose failure mode is a refusal rather than a wrong answer.

## Out of scope

GH #463: the reconciler's `|| ABORT` wiring produced no observable effect across a continuous run of phases that sealed anyway. That is a question about whether documented gate steps execute, and no parser change answers it. Filed separately and deliberately not addressed here -- fixing the parser stops this gate mis-firing, which would also make its silence permanently invisible, so #463 must not be allowed to close as a side effect.

## Reach

- `intent_lock.capture` is the only production caller of `_audit_has_pass`; the seal path re-verifies the lock it wrote.
- `verdict_reconcile.reconcile` is called from `/qor-implement` Step 2.
- A downstream consumer adopted `intent_lock.py` verbatim and carries a test pinning the present semantics as an inherited weakness, to be deleted rather than amended once this lands.
