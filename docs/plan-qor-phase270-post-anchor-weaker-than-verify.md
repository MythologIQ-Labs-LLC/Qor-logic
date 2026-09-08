# Phase 270: the gate mode is weaker than the mode it replaced

**change_class**: feature
**Issues**: GH #443, GH #425, GH #430
**Research**: docs/research-brief-post-anchor-weaker-2026-09-07.md
**Iteration**: 4 (iterations 1, 2 and 3 VETOed)
**Session**: 2026-09-07T2035-2f4c25

## Problem

`verify_post_anchor()` is the mode both governance gates consume, and it is weaker than `verify()` in four ways rather than the three the issues name. Mechanisms and fixtures are in the research brief.

## What iteration 1 got wrong

Recorded because the corrections are the design.

- **D1 closed neither issue it claimed.** `_sequence_breaks` resets continuity across an unresolvable entry, so it returns nothing on the #430 fixture and the tainted entry still becomes the anchor. Measured.
- **D1 reproduced the very window it diagnosed.** Routing linkage results into `max(ok_entries)` means one honest append after a fork moves the boundary past it and the fork prints as tolerated. Measured: the #443 fixture is DIRTY at the tail and CLEAN with a single valid entry appended. The plan carried an `..._after_later_appends` row for duplicates and none for linkage; the lesson was applied to the smaller symptom.
- **The root defect is `boundary_entry = max(ok_entries)`**, not either missing check. The boundary is derived from the entries it judges, so any failure is downgraded once something valid follows it. Duplicates and linkage breaks are two ways of noticing one rule.
- **The brief's claim that entries #1-#10 are pre-convention skips was wrong.** They are positively attested by `Entry #492: MIGRATION ATTESTATION`, and `verify()` prints `OK Entry #N: attested by migration entry #492` after re-checking an LF-normalized body digest. That is stronger than a skip: edit an attested body and `verify()` fails.

## Design

### D1: share the whole unresolvable-entry ladder (the fourth gap)

`verify()` disposes of an entry whose hashes do not resolve through four rungs at `ledger_hash.py:527-573`:

1. at or above the markup-required cutoff (123) -> FAIL, missing markup
2. else migration-attested -> re-check the body digest -> OK or FAIL
3. else any hash label present -> FAIL, unreadable claim
4. else -> silent skip

`verify_post_anchor` reimplements only rungs 3 and 4, at `:654-665`. Rungs 1 and 2 are absent. That is the same defect shape as the other three: a subset of a ladder, reimplemented by hand.

Both modes call one shared disposition. Measured consequences on this repository's ledger:

| | before | after |
|---|---|---|
| entries reported by post-anchor | 735 of 757 | 757 of 757 |
| attested entries invisible to the gate | 22 | 0 |
| entries classified `fail` needing boundary tolerance | 10 | 0 |

The 22 omitted entries are all migration-attested. They are upgraded from invisible to positively verified, which is a second correction this phase makes rather than a cost it pays.

### D2: a boundary must be asserted by someone, and every caller must be able to hear it

Iteration 2 said "unpinned is strict" and told a damaged consumer to pin `--boundary`. **That flag exists only in `qor/cli.py:204-205`.** `seal_entry_check.py:149`, `governance_health.py:167` and `ledger_upgrade.py:71` all call `verify_post_anchor(path)` and have no parameter to forward. So iteration 2 would have given a damaged consumer a permanently red seal gate on every push (`ci.yml:55`), a permanently DAMAGED preflight and a refused upgrade, with the remedy its own error message named reachable from none of them.

**This was already solved in this cluster and not consulted.** `docs/plan-qor-phase263-declared-post-anchor-anchor.md` LD-3 and LD-4 specify the resolution order:

1. an explicit `boundary_entry` argument;
2. else a declaration in `.qorlogic/config.json`, read through `qorlogic_config.load_section` (`qor/scripts/qorlogic_config.py:22`), which is total and never raises, so a missing file, unreadable path, invalid JSON or non-object section all read as "declared nothing";
3. else auto-detection, **permitted only when a strict evaluation of the ledger would raise nothing at all**. Not an enumeration of failure kinds: the gate is derived from the error count, so a failure kind added later is covered on the day it is added rather than when someone remembers to widen a clause. A ledger with nothing to disclose needs no declaration, which is what leaves every clean-ledger caller unchanged;
4. else fail closed, naming the failing entries and the declaration needed.

Phase 263 is cited as the predecessor rather than superseded. It measured the GH #55 consumer break independently, by another route, and its LD-2 rejected taint-exclusion as contract-breaking before this phase re-derived the same conclusion. Its own worked example needed a declared boundary of 111 precisely because it left the ten attested entries classified `fail`; D1's ladder makes them attested-OK, so **this repository needs no declaration at all** and 263's LD-1 measurement is superseded on that point only.

**One correction to 263, found by testing its assumption.** LD-3 proposes to add a parameter to `verify_post_anchor` (`repo_root`), defaulting to the ledger's grandparent so every call site picks the declaration up unchanged. That overshoots for any ledger not nested in `docs/`: `tests/test_seal_entry_check.py:71` writes `tmp_path/META_LEDGER.md`, whose grandparent is outside the fixture, while `tests/test_governance_health_post_anchor_tolerance.py:30-32` writes `base/docs/META_LEDGER.md`, whose grandparent is `base`. A single fixed depth cannot serve both.

Both callers already hold the root and simply do not forward it: `seal_entry_check.check()` takes `repo_root` at `:79` and drops it at `:149`; `governance_health._classify_one` has `base` and passes `base / _LEDGER`. So the root is **forwarded by callers that know it**, with the ledger's ancestor chain searched for a `.qorlogic/` directory as a bounded fallback. The emphasis matters: on the path CI actually runs, `_main --auto` calls `check_latest(args.ledger)` at `seal_entry_check.py:227` with no root and `check_latest` forwards that `None` at `:214`, so **the ancestor search is the production mechanism and forwarding is what makes the fixtures expressible**. `qor/cli.py:66-70` computes no root either. `ledger_upgrade` writes its temp beside the real ledger (`:66`), so the chain resolves to the original's root; the declaration is an entry NUMBER and `migrate` does not renumber, so a declaration valid for the original is valid for the temp. An out-of-tree ledger resolves nothing and fails closed, which is the safe direction.

### D3: linkage breaks are errors as `verify()` has them, except below a boundary someone asserted

In `verify()` a break sums straight into the return value at `:461-463` and `:594`; it is not boundary-relative.

**Iteration 2 kept that and contradicted D2.** A failure below a declared boundary is disclosed; a boundary-free break ignores the declaration; a break below the line is both. Proven on the fixture this plan cites as its own precedent: `tests/test_ledger_hash_duplicate_entry.py:155` contains a BREAK, so boundary-free linkage turns its asserted `rc == 0` red.

The contradiction resolves once the boundary means something. A break **below a declared or pinned boundary is disclosed**, like any other failure there: a re-anchored consumer whose pre-anchor history had an entry removed has a break below the line by construction, and if that cannot be disclosed then declaring a boundary is not an escape hatch at all. A break is disclosed only when **both members of the pair** are at or below the boundary, and is an error otherwise. That keeps the pair as the unit, per the paragraph above, and is conservative exactly where it matters: the canonical GH #55 re-anchor produces no break at all, because the re-anchor entry records the disclosed predecessor's recorded hash, so a straddling break means specifically that an entry was removed at the re-anchor point.

**Iteration 3 called the auto-mode case moot and was wrong, for the third appearance of one shape.** Under its wording "no entry classifies as a failure" was a per-entry term, and a fork produces no failing classification: every entry in the #443 fixture is internally self-consistent. Auto was permitted, the boundary became the maximum, and the breaks fell below it. Measured:

```
fork at the tail            auto=True  boundary=#4  break at/above=1  rc=1  DIRTY
fork + one honest append    auto=True  boundary=#5  break at/above=0  rc=0  CLEAN
```

The same honest append defeated iteration 1 through `max(ok_entries)` and iteration 3 through the resolution order. D2 step 3's derived gate is what closes it, and it closes #425 identically, because a duplicate is not a classification either.

A break is a property of an adjacent PAIR in file order. It is reported as such rather than collapsed onto the successor's entry number, because the successor is not the damaged link -- the message says "an entry may have been removed" -- and a number-keyed set would mark both occurrences of a duplicated number when only the second broke.

### D4: six fixtures encode the weakness, and a declaration is what makes them expressible

Iteration 2 proposed pinning `boundary_entry` in three `governance_health` tests. **That is inexpressible**: those tests reach the verifier through `_classify_one` (`tests/test_governance_health_post_anchor_tolerance.py:37-38`) and there is no boundary anywhere on that path. With D2's declaration they become expressible, because a fixture can write `.qorlogic/config.json` under its own `tmp_path`.

- `test_fully_valid_ledger_is_ok:73` -- the fixture gives entries arbitrary `previous_hash` values, `verify()` rejects it with a BREAK, and the test is named for validity. Measured. The fixture is wrong on its own terms and is corrected to chain properly. Fixing a test, not fitting one.
- `:41`, `:85`, `:106` -- each declares a boundary in a config under `tmp_path`. The intent survives; what changes is that the assertion is now made rather than inferred.
- `tests/test_seal_entry_check.py:156` -- GH #88's contract. Entry #100's chain is deliberately broken and the test asserts `ok is True`. `check()` already receives `repo_root` at `:79` and drops it; forwarding it lets this fixture declare, which is the only route, since pinning was never available here.
- `tests/test_ledger_hash_duplicate_entry.py:155` -- pinned at 2 and containing a BREAK. It stays green under D3 as corrected, because a break below a pinned boundary is disclosed. Under iteration 2 it went red, and this plan cited it as its own precedent while breaking it.

## Consumer-visible break, stated rather than discovered

**A re-anchored consumer ledger with genuine unattested pre-anchor damage passes today with no operator action. After this phase it must declare a boundary in `.qorlogic/config.json`, committed.** That removes the auto-tolerance GH #55 was filed for. Pinning `--boundary` is not the remedy: that flag reaches only `qor/cli.py`, and the gates that go red are the three that cannot accept it.

This is the correct trade -- an assertion should be asserted, and the current behaviour is what lets a fork print as a tolerated residual -- but it is a break, and consumers meet it as a newly red gate. It is the reason `change_class` is `feature` rather than `hotfix`: this narrows a documented tolerance in two gates and is more than a patch.

`breaking` was considered and rejected, and the reason is arithmetic rather than judgement about severity. `_compute_new` maps `breaking` to major+1 (`qor/scripts/governance_helpers.py:93-94`), which would declare v1.0.0. Whether this project is 1.0 is a release-positioning decision the operator owns, and it is not a consequence of one gate becoming stricter. In 0.x the minor bump is the conventional signal for a behaviour change consumers must act on, and `feature` produces v0.170.0. If the operator would rather this ship as v1.0.0, the change_class is the only edit required.

Mitigations in scope: the fail-closed refusal names the declaration, the file it goes in, the entry numbers at issue and what a declaration at the recommended value would disclose, by kind. The remedy is in the output rather than in a changelog.

## Reach

- `qor/references/glossary.md:624` and `:633-634` define DISCLOSED_PRE_ANCHOR and the post-anchor boundary as "operator-pinned (or auto-detected)". D2 makes those asymmetric; glossary drift is a seal-aborting condition here.
- `qor/references/doctrine-governance-enforcement.md:336-349` states the two-mode contract this changes.
- `qor/skills/governance/qor-validate/SKILL.md` and five compiled variants carry post-anchor prose asserted by `tests/test_qor_validate_skill_post_anchor_prose.py`; a prose change forces a dist recompile.
- `.github/workflows/ci.yml:55` runs `seal_entry_check --auto`, so this exit code gates every push, not only the seal.
- `qor/cli.py:205` documents `--boundary` as boundary selection only; under D2 pinning also waives fork tolerance and the help text must say so.
- `qor/scripts/ledger_upgrade.py:71` never pins, but its temp sits beside the real ledger (`:66`), so the ancestor chain resolves the original's declaration and a duplicate or break below a declared boundary is disclosed and the upgrade proceeds. An UNDECLARED fork is refused, which is the intended narrowing rather than an unconditional one. Its streams are swallowed at `:69-70` and it prints only "post-anchor verification rejected the upgraded form" at `:88-89`. Rejecting more while explaining nothing is a usability regression; the diagnosis is surfaced.
- `qor/scripts/ledger_attest_legacy.py:38-51` is a fifth consumer of the ladder's semantics: `collect_unverifiable` selects on `_resolve_recorded(body) is None` and its `body_digest` duplicates `_legacy_body_digest` (`ledger_hash.py:312-314`). Sharing rung 2 makes the gate depend on those two copies of the LF-normalisation rule agreeing. They agree today by identical implementation; a refactor must move both.
- The grandfathered set is gated in `verify()` behind `tolerate_known_grandfathered` (`ledger_hash.py:502-506`), which `ci.yml:51` does not set. Passing it unconditionally to post-anchor would suppress breaks that `verify()`'s default reports, reopening a weaker-than-verify gap inside the phase that closes them. `reconciled` is passed unconditionally; `grandfathered` is gated the same way `verify()` gates it.
- Iteration 1's snippet left `tolerated` unbound: `verify_post_anchor` computes neither the reconciled set nor the grandfathered one. Both are computed and passed, since `tolerated` is a continuity RESET and not merely message suppression.

## Tests

| Test | Pins | Red before |
|---|---|---|
| `test_post_anchor_reports_every_entry_in_the_ledger` | rungs 1 and 2 shared; nothing omitted | yes |
| `test_post_anchor_verifies_a_migration_attested_entry` | rung 2 reaches post-anchor | yes |
| `test_post_anchor_fails_an_edited_attested_body` | attestation is stronger than a skip | yes |
| `test_post_anchor_fails_unmarked_entry_above_cutoff` | rung 1 reaches post-anchor | yes |
| `test_post_anchor_fails_a_linkage_fork` | #443 | yes |
| `test_post_anchor_fails_a_linkage_fork_after_later_appends` | #443 with the window closed | yes |
| `test_post_anchor_fails_a_duplicate_after_later_appends` | #425 | yes |
| `test_post_anchor_declares_at_3_and_still_reports_entry_4_ok` | #430's mechanism asserted, not arrived at incidentally | no |
| `test_auto_is_refused_unless_a_strict_pass_would_raise_nothing` | D2 step 3, the derived gate | yes |
| `test_a_break_straddling_the_boundary_is_an_error` | D3's pair rule, in the one shape where it decides | yes |
| `test_a_break_entirely_below_the_boundary_is_disclosed` | the other half of the pair rule | no |
| `test_pinned_boundary_still_tolerates_below_the_line` | the operator's assertion is honoured | no |
| `test_refusal_names_the_declaration_and_the_file` | the remedy is in the output | yes |
| `test_refusal_reports_what_a_declaration_would_disclose_by_kind` | the tool does not recommend burying a fork | yes |
| `test_auto_is_refused_on_a_fork_with_an_honest_append` | the defect that killed three iterations | yes |
| `test_auto_is_refused_on_a_duplicate_below_the_high_water_mark` | #425 through the same clause | yes |
| `test_declaration_resolves_from_config` | resolution order step 2 | yes |
| `test_malformed_declaration_reads_as_declared_nothing` | load_section is total, so it composes fail-closed | yes |
| `test_explicit_argument_beats_a_declaration` | resolution order step 1 | yes |
| `test_ancestor_search_resolves_a_ledger_not_under_docs` | the production path, since --auto forwards None | yes |
| `test_seal_entry_check_forwards_repo_root` | forwarding is real where a caller has one | yes |
| `test_this_repositorys_ledger_needs_no_declaration` | after D1 nothing fails, so auto still resolves it | no |
| `test_post_anchor_and_verify_agree_on_this_repositorys_ledger` | the two modes stop disagreeing | no |

Fixtures build ledgers from real SHA-256 values; sequential hex trips the placeholder detector and fails for the wrong reason.

## Affected files

- `qor/scripts/ledger_hash.py` (shared ladder, resolution order, linkage pass, refusal text)
- `qor/reliability/seal_entry_check.py` (forward `repo_root` at `:149`; derive one in `_main` at `:227`)
- `qor/scripts/governance_health.py` (`_verify_post_anchor` gains the parameter; `_classify_one` already holds `base`)
- `tests/test_seal_entry_check.py` (D4, and `:186` must pass `repo_root=tmp_path`)
- `tests/test_ledger_hash_duplicate_entry.py` (`:127` takes the fail-closed path rather than the duplicate branch)

The refusal's wording is a contract, not a fit to a test: it names every condition it refuses over and the entries involved. `:127`'s docstring says the gate "must not report post-anchor clean" on GH #361's repro, and a refusal that names the fork satisfies that intent more directly than the duplicate branch did. The literal assertions are `"duplicate entry number" in full` (`:151`) and `"FAIL Entry #3" in err` (`:152`) -- the token is `FAIL Entry #3`, on stderr. The mode already emits `FAIL Entry #N` for post-boundary failures (`ledger_hash.py:693-696`), so keeping that form is consistency rather than concession.
- `qor/scripts/ledger_upgrade.py` (surface the diagnosis)
- `qor/cli.py` (`--boundary` help text)
- `qor/references/glossary.md`, `qor/references/doctrine-governance-enforcement.md`
- `qor/skills/governance/qor-validate/SKILL.md` and compiled variants
- `tests/test_post_anchor_verify.py` (the established home; not a new file)
- `tests/test_governance_health_post_anchor_tolerance.py` (D4)

## CI Commands

```
python -m pytest tests/test_post_anchor_verify.py tests/test_governance_health_post_anchor_tolerance.py tests/test_ledger_hash_duplicate_entry.py -q
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m qor.scripts.gate_provenance verify-committed
python -m pytest -q
```

## Limitations

- An entry heading that does not match `ENTRY_RE` (`ledger_hash.py:140`) is invisible to both modes and therefore to any version of D2's gate, which counts errors among the entries it can see. Not introduced here and not fixable here; recorded so the next reader does not rediscover it.
- Rung 1 makes any unmarked entry at or above #123 a hard post-anchor failure. Measured as empty on this ledger; unverifiable for consumer ledgers.
- The two modes still differ. This closes the direction where the gate was weaker and does not claim equivalence. No claim is made that a fifth gap does not exist -- four were found, three of them after the design was first written, and the brief's own framing is that a hand-reimplemented subset is where these come from.
- `_classify_entry` is unreachable for attested entries, so sharing it alone would deliver #430's taint propagation and nothing for the ten. The ladder is what covers both.
