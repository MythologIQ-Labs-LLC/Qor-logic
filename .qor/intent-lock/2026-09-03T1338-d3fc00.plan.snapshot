# Plan: resolve qor/references citations in plans (closes the 2026-08-12 hallucination event)

**change_class**: hotfix

**doc_tier**: standard

**terms**: []

No new domain vocabulary.

**boundaries**:
- limitations: [does not edit any sealed plan document; the two genuine bad citations this surfaces in Phase 28 and Phase 244 plans stay as historical record, and the lint reports them without rewriting them]
- non_goals: [does not widen `plan_grep_lint` to other path families; does not change the lint's WARN posture at the audit site, which is shared with its working siblings]
- exclusions: [no change to `check_citation_evidence` or the truth-checked/presence-only kind split]

## Problem

The Process Shadow Genome carries an unaddressed severity-4 `hallucination`
event from 2026-08-12:

```
pattern:        invented-artifact-path
artifact:       qor/references/doctrine-citation-pairing.md  <!-- grep-lint: ok=discussing-not-citing -->
why_undetected: plan_grep_lint.py:37 defines _REFERENCE_PATH_RE and never uses
                it, so qor/references/*.md citations are resolved by no check.
remedy:         Resolve Affected Files paths before writing them; wire
                _REFERENCE_PATH_RE or delete it.
```

A doctrine path that does not exist was asserted to the operator as fact and
written into a plan as an Affected File. The recorded remedy has been open since
August and is still open: `_REFERENCE_PATH_RE` is defined at
`plan_grep_lint.py:55` and appears exactly once in the file.

Its two siblings are wired. `_MODULE_RE` drives a loop emitting
`module-path-missing`; `_SKILL_PATH_RE` drives one emitting
`skill-path-missing`. Both carry a `new_paths` exemption for files the plan
declares it will create, and both skip placeholder tokens. The reference family
has neither loop nor exemption -- it has a regex and nothing else.

## Fix

`plan_grep_lint.check_plan` gains a `_REFERENCE_PATH_RE` loop symmetric to the
skill-path loop, emitting `reference-path-missing`:

- a path the plan declares as NEW is exempt, via the existing `_new_paths`
- placeholder citations are skipped, extending the sibling's token list to cover
  the `foo` convention the reference family actually uses
- anything else that does not resolve on disk is reported with its line number

### The allow marker (tribunal ground V-1, entry #715)

A plan that *discusses* an unresolvable path is indistinguishable from one that
*cites* it, and this plan quotes ten such paths. Without an exemption the phase
introducing the check would emit ten findings from it, and every future plan
discussing a broken citation would inherit the same noise -- a check whose
loudest output is its own documentation is the kind operators learn to skim.

`plan_grep_lint` gains `_ALLOW_RE` accepting `grep-lint: ok=<reason>`, matching
the two markers this repository already uses: `boundary-lint: ok=<reason>` in
`publication_boundary_lint` and `# prose-lint: ok=<reason>` in
`prose_test_lint`. Two properties make it evidence rather than a mute button,
and both are inherited from those siblings:

- **the reason is required and non-empty** -- an empty marker cannot silence the
  control
- **scope is per line** -- there is no file-level or directory-level suppression

The discussion lines in this plan carry the marker with the reason
`discussing-not-citing`.

### On the WARN posture, since a severity-4 closure invites the question

`plan_grep_lint` is invoked `|| true` at `/qor-audit` Step 0.6, so this check
reports rather than aborts -- the same posture as the module-path and skill-path
checks that do work. That is deliberate parity, not a half measure: the binding
force lives in the Infrastructure Alignment Pass, where an unresolvable citation
is a VETO with `infrastructure-mismatch`. The lint's job is to put the finding in
front of the Judge before an audit cycle is spent; the Judge's job is to refuse.

Closing the hallucination event on a check with no teeth would be the
closing-on-prose failure this repository rejects. Closing it on the same
mechanism that already catches invented module paths and invented skill paths is
closing it on a working enforcer.

## Measured effect

Run prospectively over all 277 plan documents in `docs/`:

| | count |
|---|---|
| plans scanned | 277 |
| plans with an unresolvable `qor/references` citation | 4 |
| total unresolvable citations | 4 |

Two are placeholders by convention and will be skipped:
`qor/references/foo.md` (Phase 132) and `qor/references/doctrine-foo.md`  <!-- grep-lint: ok=discussing-not-citing -->
(Phase 53).

Two are genuine and will be reported:

- `plan-qor-phase244-qor-harden.md:24` cites
  `qor/references/doctrine-implementation-quality.md`. No such file; the real  <!-- grep-lint: ok=discussing-not-citing -->
  one is `qor/references/implementation-quality-sweep.md`, which carries no
  `doctrine-` prefix. This is the same invented-path class as the event being
  closed, sitting undetected in a sealed plan.
- `plan-qor-phase28-documentation-integrity.md:69` cites
  `qor/references/README.md`, which does not exist.  <!-- grep-lint: ok=discussing-not-citing -->

Both stay as historical record. The lint reports them; nothing rewrites a sealed
plan to make a number clean.

The event's own artifact, `qor/references/doctrine-citation-pairing.md`, is  <!-- grep-lint: ok=discussing-not-citing -->
absent and no plan still cites it -- that plan was corrected at the time. The
defect was never the single bad path but the absence of any check.

## Tests (written first)

- `tests/test_reference_path_resolution.py::test_unresolvable_reference_is_reported`
  -- a plan citing `qor/references/doctrine-citation-pairing.md`, the exact path  <!-- grep-lint: ok=discussing-not-citing -->
  from the event, yields a `reference-path-missing` warning with its line
  number. Red before the fix, and red for the reason the event records: no check
  reads that family.
- `::test_resolvable_reference_is_silent`
  -- a plan citing a doctrine that exists yields nothing, so the check does not
  become noise.
- `::test_new_declared_reference_is_exempt`
  -- a plan that declares `qor/references/doctrine-new-thing.md` as a NEW  <!-- grep-lint: ok=discussing-not-citing -->
  Affected File is not warned about it. Without this the check would fire on
  every phase that introduces a doctrine, including the three that did so this
  week.
- `::test_placeholder_reference_is_skipped`
  -- `qor/references/foo.md` and `qor/references/doctrine-foo.md` are skipped,  <!-- grep-lint: ok=discussing-not-citing -->
  matching how the skill-path sibling treats its own placeholders.
- `::test_live_plan_corpus_has_exactly_the_known_findings`
  -- over `docs/plan-*.md`, the check reports the Phase 244 and Phase 28
  citations and nothing else. The anti-recurrence binding: a future doctrine
  rename that orphans a citation makes this fail.

Every test invokes `check_plan` and asserts on the returned warnings.

## Validation

- `python -m pytest tests/test_reference_path_resolution.py -q` -- run twice for determinism
- `python -m pytest -q` (full suite)
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
- `python -m qor.scripts.publication_boundary_lint`
- `qor-logic-plus scripts plan_grep_lint --plan docs/plan-qor-phase255-reference-path-resolution.md --repo-root .` -- this plan's own reference citations must either resolve or carry the marker; no unmarked unresolved citation may remain

## CI Commands

- `python -m pytest -q`
- `python -m ruff check qor/ tests/`
- `python -m qor.scripts.check_variant_drift`
