# Phase 278: the validator that guards nothing gets called, at all four sites

**change_class**: hotfix
**Issues**: GH #459
**Research**: docs/research-brief-event-id-validation-2026-09-08.md
**Iteration**: 4 (iterations 1-3 VETOed)
**Session**: 2026-09-08T1956-274e42

## Scope note

`validate_event_id` exists, has its own regex, is tested, and is called from nowhere. Four sites build the set of event ids to act on and none validates; a malformed id matches no event, the selection is empty, and the process exits 0 on a breached governance threshold.

The function, the regex and the tests already exist. What is missing is the call, a normalizer in front of it, and an exception conversion.

## What iteration 1 got wrong

1. **"Two entry points" was structurally false.** There are **four** `target_ids` constructions: `:230` (`--mark-resolved`), `:239` (`--flip-only`), `:250`, `:254`. The plan guarded one and would have shipped reading as "the CLI path is now guarded" while two thirds of `--events` usage stayed open. D1's own rationale -- "leaves `--events` as an unguarded way to reach the same silent-success" -- indicted the two sites it had not found.
2. **"Measured cost: zero" measured the wrong population.** All 151 live ids match the regex, but on the `--events` paths validation runs on **split elements**. `"<id>,"` yields an empty element and `" <id> , <id> "` yields two failing ones, so naive validation would have converted working invocations into aborts. The claim that the change was free appeared in the sentence that made it not free.
3. **The failure mode contradicted the shape the plan invoked.** `load_marker` raises `SystemExit` exclusively with a `_REGEN` remediation hint, and all six Phase 273 tests assert `pytest.raises(SystemExit)`. `validate_event_id` raises `ValueError`. D1 said "beside the type check Phase 273 added ... the module's established shape" and never specified the conversion, so a literal implementation gives an unhandled traceback one line below a clean named message -- and no test row named an exception type, so the specification did not force the right choice.

All three are the same error in different places: asserting a structural property without measuring it.

## D1: all four sites, and the one exclusion is named

Every `target_ids` construction validates. Guarding a subset is what iteration 1 did.

| site | line | flag | in scope |
|---|---|---|---|
| `--mark-resolved` | 230 | `--events` | yes |
| `--flip-only` | 239 | `--events` | yes -- id validation only |
| issue creation | 250 | `--events` | yes |
| marker | 254 | marker file | yes |

**Validation lives in `main`'s argparse branches, not inside `flip_events_only` or `mark_resolved`.** Those are a direct-call public API: `tests/test_collect.py:291,311` invoke `flip_events_only` and `tests/test_shadow.py:281,298` invoke `mark_resolved`, both without going through `main`, and `flip_events_only`'s docstring records the cross-repo collector as a consumer. **Both** functions named in this boundary have direct callers. A guard inside them would add a failure mode to a caller this plan has not analyzed.

**One shared helper serves all three `--events` sites**, returning a validated `set[str]`. It raises a single dedicated exception and does **not** choose the error mechanism -- each argparse branch converts that to its own `print` + `return 2`, so the helper cannot impose a mechanism on a caller whose convention it does not know.

**`--flip-only` gets id validation here; its unlink defect does not.** At `:243-244` it deletes the breach marker unconditionally, discarding the `flipped` count it just printed. Validation narrows the exposure -- a malformed id now aborts before reaching the unlink -- but does **not** fix it: a well-formed id matching no event still flips nothing and still deletes the marker. Filed as GH #472. This plan must not be read as having guarded `--flip-only`; it guards the ids that reach it.

## D2: normalize, then require, then validate

Three distinct rules, in order. Conflating the first two is what reintroduces this phase's own defect through its fix.

```
split on ","  ->  strip each  ->  drop empties  ->  require non-empty  ->  validate each survivor
```

| `--events` value | normalized | outcome |
|---|---|---|
| `"<id>"` | `{<id>}` | accepted |
| `"<id>,"` | `{<id>}` | accepted -- **current behaviour preserved** |
| `"<id>,,<id>"` | `{<id>, <id>}` | accepted |
| `" <id> , <id> "` | `{<id>, <id>}` | accepted |
| `","` | `{}` | **error: `--events` given but named no ids** |
| `"evt-1"` | `{evt-1}` | error: malformed id |

Normalization is a parse concern: a trailing comma is an artifact of the separator, not an id the operator named, and every CSV consumer drops it. Validation is a value concern. The **require non-empty** rule sits between them, because an operator who passes `--events ","` asked to act on ids and named none -- without that rule the normalizer produces an empty target set, which matches nothing and exits 0, which is precisely the silent success this phase exists to close.

## D3: the exception shape matches the site

- **Marker path**: validation happens inside `load_marker`, and raises **`SystemExit`** carrying the `_REGEN`-style remediation hint, matching every existing guard there. A `ValueError` escaping `load_marker` would be an unhandled traceback one line below a clean named message.
- **`--events` paths**: `print("ERROR: ...", file=sys.stderr)` then **`return 2`**. The convention is measured at **two** of the three sites: `:227-229` and `:236-238` already do exactly this for a *missing* `--events`, and `tests/test_shadow.py:308` pins `rc == 2`. The third site has no such sibling -- `:249` is a bare `if args.events:` -- so `return 2` there is chosen for consistency across the three `--events` paths rather than read off a neighbour. An earlier draft said "three lines above each site", generalizing a property of two sites to three. A `raise` here would sit three lines below a `return 2` for the same class of argument fault.

  Iteration 2 specified a raise, which is iteration 1's own finding in mirror position: the marker convention was measured and honoured, the `--events` convention was assumed.

**The two sites fail differently on purpose, and that is the conventional split rather than an inconsistency.** Measured: `raise SystemExit("msg")` prints to stderr and exits **1**; the `--events` sites return **2**. That is the standard Unix division -- 2 for a command-line usage error, which is argparse's own convention, and 1 for a runtime or data fault. The marker is data, not argv. Measuring each site's local convention independently arrived at that split by construction; the plan states it explicitly because a reader seeing identical faults exit differently will otherwise ask.

`validate_event_id` itself keeps raising `ValueError` -- it is a value-level predicate and its two existing tests assert that. The conversion happens at the call site, which is where the module's convention lives.

**Every rejection row below names its expected outcome** -- `SystemExit` for the marker path, `rc == 2` for the three `--events` paths. Iteration 1 named none; iteration 2 named them for the marker rows and omitted them from the four rows it added while expanding scope, repairing the finding where it was raised and reproducing it where the plan grew.

## D4: the validator is made total

`_EVENT_ID_RE.match(12345)` raises `TypeError`, not the `ValueError` its docstring promises. A caller obeying the documented contract does not catch the integer case -- and an integer is what a hand-edited or machine-generated marker yields. Wiring an untotal validator would convert a silent exit-0 into an unhandled traceback: a different failure, not a fixed one.

A type check precedes the regex and raises `ValueError` as documented. **This changes an existing public function's behaviour.** Verified safe repo-wide: zero production call sites, no match in `qor/dist/` or `skills/`, and the only references are the definition, two tests in `test_security_fixes.py:149-162` (one accept-case, unaffected by a type guard; one reject-case asserting `ValueError` for hex-alphabet and length), plus docs prose and an untracked `build/lib/` copy that no parity gate reaches.

## D5: what this does NOT do

- **Does not fix GH #472** -- the unconditional unlink. Same module, different trigger, and validation would mask how reachable it is.
- **Does not address #463**, whether wired guards run at all. Adding a call does not answer it and must not be read as evidence that it did.
- **Does not validate the marker's other fields** or the flags' siblings. The fields guarded are the ones these four lines dereference.
- **Does not change what a valid id matching no event does.** That is a legitimate empty result and keeps exiting 0.
- **Does not reconcile an inherited `--events ""` inconsistency.** An empty string is falsy, so at `:250` it skips the branch and falls through to `load_marker()`, running off the marker instead of the flag and exiting 0 -- while `:227` and `:236` return 2 for the same input. Pre-existing, measured, and left alone rather than silently inherited: folding it in would change which source of ids a bare `--events ""` acts on, which is a behaviour question this phase has not researched.

## Tests

Written first. Each runs twice for determinism. The red-before column is per row and is not uniform: four rows are green-before by construction, being characterization tests of behaviour that is already correct and must stay so.

An earlier draft's preamble asserted "red before the change" and "exception types are named" over the whole table. Both cells had been corrected individually and the sentence generalizing over them had not -- the same restatement drift this plan records elsewhere. The column and D3 carry those properties now; the preamble no longer restates them.

| Test | Pins | Red before |
|---|---|---|
| `test_marker_with_non_hash_event_ids_exits_with_systemexit` | `["evt-1"]`; **`SystemExit`**, matching the module's shape | yes |
| `test_marker_with_an_integer_event_id_exits_with_systemexit` | `[12345]`; the `TypeError` case, converted | yes |
| `test_marker_with_a_truncated_hash_exits_with_systemexit` | `["a" * 32]` | yes |
| `test_marker_with_an_uppercase_hash_exits_with_systemexit` | `["A" * 64]`; the regex is lowercase-only | yes |
| `test_marker_rejection_message_names_the_regen_command` | the `_REGEN` hint, as every sibling guard does | yes |
| `test_marker_with_generated_valid_ids_is_accepted` | the accept path, over **generated** ids | no |
| `test_mark_resolved_with_a_malformed_id_is_rejected` | **D1**; site `:230`; **`rc == 2`** | yes |
| `test_flip_only_with_a_malformed_id_is_rejected` | **D1**; site `:239`; **`rc == 2`** AND **`marker.exists()` still true** -- pins that the guard sits BEFORE the unlink at `:243-244`, not that the unlink is fixed | yes |
| `test_issue_path_with_a_malformed_id_is_rejected` | **D1**; site `:250`; **`rc == 2`** | yes |
| `test_events_with_a_trailing_comma_is_still_accepted` | **D2**; the regression iteration 1 would have shipped | **no** -- passes today; a characterization test, which is why it is worth writing |
| `test_events_with_surrounding_whitespace_is_accepted` | D2 stripping | yes |
| `test_events_naming_no_ids_is_an_error` | **D2**; `","` must not become a silent empty set; **`rc == 2`** | yes |
| `test_validate_event_id_raises_ValueError_on_an_int` | **D4**; the docstring's contract | yes |
| `test_validate_event_id_still_raises_on_hex_and_length` | the existing contract survives | no |
| `test_a_valid_id_matching_no_event_still_exits_zero` | D5; an empty result is not an error | no |

**No test asserts a live count.** Iteration 1's row read "the 151 real ids must keep working", which would read `docs/PROCESS_SHADOW_GENOME.md` -- a git-tracked file appended to by routine governance operation, modified in the working tree right now. Such a test goes red on the next shadow event, which is the test-discipline doctrine's `no live-state hardcoding` clause. The 151 stays in the brief as a measurement; the test asserts a property over generated ids.

## Affected files

- `qor/scripts/create_shadow_issue.py` (`validate_event_id`, `load_marker`, and the three `--events` branches)
- `tests/test_shadow.py` (additions) -- holds Phase 273's `load_marker` guards, 15 references; verified to exist
- `tests/test_security_fixes.py` (additions) -- holds the `validate_event_id` contract tests at 149-162; verified to exist
- `CHANGELOG.md`

There is **no** `tests/test_create_shadow_issue.py`. Both real files were located before this plan was audited.

## Reach

- A malformed marker or `--events` value now exits non-zero naming the fault, where it previously exited 0 reporting "nothing to do".
- `--events` gains normalization; the trailing-comma and whitespace invocations that work today keep working, and `","` becomes an error rather than an empty set.
- `validate_event_id` gains a type guard; its documented `ValueError` contract becomes true.
- **One in-repo consumer of the CLI exit contract**, enumerated rather than assumed absent: `qor/scripts/collect_shadow_genomes.py:191-200` subprocesses `create_shadow_issue --flip-only <url> --events <ids>`, branches on `result.returncode != 0`, and otherwise parses a count out of stdout. Making `--flip-only` return 2 for malformed ids changes what it observes. Verified safe: the non-zero branch WARNs and records `0` for that repo rather than raising, and the ids it sends are real `e["id"]` values, so there is no live regression -- but the contract change reaches it and Reach must say so.
- **No skill or template changes, so the dist tree is untouched -- but it is not unrelated.** Generated skill prose instructs `create_shadow_issue.py --mark-resolved --events <ids>` in every host variant (e.g. `qor/dist/variants/claude/skills/qor-process-review-cycle/SKILL.md:86`, and the same line in the cline, codex, cursor, gemini and kilo-code variants). That prose is an invocation, not an exit-code consumer, so nothing there needs changing -- and `rc == 2` on a malformed id is precisely the improvement reaching an agent following it. Stated rather than left implied.
- `hotfix` per `doctrine-governance-enforcement.md:25`: no new capability, no new CLI surface, no signature change -- a wrong output made right.

## CI Commands

```
python -m pytest tests/test_shadow.py tests/test_security_fixes.py -q
python -m pytest tests/ -q -k "shadow_issue or event_id"
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.governance_health --profile skill-entry
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- Validates ids, not events. A well-formed id naming no event still yields an empty selection and exit 0, correctly.
- **`--flip-only` still deletes the breach marker when a well-formed id flips nothing** (GH #472). This phase narrows the trigger and does not remove it.
- The marker's other fields keep Phase 273's guards and gain none.
- Makes one uncalled guard reachable; establishes nothing about the others (#461, #463).
- `--events` remains a way to act on ids no marker recorded. That is its purpose; validating format does not constrain provenance.
