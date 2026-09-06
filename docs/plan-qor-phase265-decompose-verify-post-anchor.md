# Plan: Decompose verify_post_anchor

**change_class**: hotfix

**doc_tier**: minimal

**iteration**: 5

**originating_remediation**: GH #430

**boundaries**:
- limitations:
  - This changes no behaviour. Every exit code, every printed line and every stream stays byte-identical in the implementation commit. No open issue in the cluster is closed by this phase.
  - The corpus pins observable behaviour, not intent. Where current behaviour is wrong -- several defects in this function are already recorded -- the corpus pins the wrong behaviour on purpose, so a later phase changing it must do so deliberately and visibly.
  - Nothing shipped here re-measures the corpus against the function as it later changes. That decay is real, is not solved by this phase, and has a worked instance in this same file at GH #445.
  - The file gets longer, so the razor's file clause moves further from compliance. That clause was already violated before this phase and is not addressed by it.
  - The re-derivation commands in this plan assume a POSIX shell. This repository's primary environment is PowerShell, where `grep` and `sed` are absent; a reader there needs Git Bash or WSL.
- non_goals:
  - Fixing anything. GH #443, GH #425, GH #430 and the missing attestation paths remain open and untouched.
  - Extracting the entry-parsing loop, which appears at `ledger_hash.py` lines 241, 509, 642 and 735.
  - Unifying `_post_anchor_classify` with `_classify_entry`. That is a behaviour change and belongs to the parity phase this one makes cheaper.
- exclusions:
  - GH #444 and GH #445.
  - Any change to `governance_health`, `seal_entry_check`, `ledger_upgrade`, `qor/cli.py` or `pyproject.toml`.

## Scoping

Iterations 1 through 4 were VETOed at META_LEDGER entries #743, #744, #745 and #746. The design has not been the ground of any verdict since #744. Iteration 4 introduced the rule that a number appears only when the plan states the command that re-derives it; the tribunal found that rule real and load-bearing, and found it had exposed a hole the figures had been sitting on top of. This iteration repairs that hole and applies the rule to the places iteration 4 missed, including the rule's own command, which had never been run before being written down.

Every command quoted below was executed against the working tree before this plan was written.

## Open Questions

None.

## Phase 1: Separate the concerns behind a golden master

### Affected Files

- `tests/post_anchor_corpus.py` NEW - the fixture builder, shipped as a module so the corpus is an artifact rather than a description. Exports `build(root) -> dict[str, Path]`.
- `tests/test_post_anchor_characterization.py` NEW - inlined literal goldens over every fixture the corpus module builds.
- `tests/test_post_anchor_decomposition.py` NEW - razor and helper assertions.
- `qor/scripts/ledger_hash.py` - `verify_post_anchor` decomposed into five helpers

Modules that reach the function, by `grep -rln 'verify_post_anchor' --include=*.py qor/`: `qor/cli.py`, `qor/reliability/seal_entry_check.py`, `qor/scripts/governance_health.py`, `qor/scripts/ledger_upgrade.py`, and `qor/scripts/ledger_hash.py` itself, which is the definition site. The four consuming modules call it at `cli.py:70`, `seal_entry_check.py:149`, `governance_health.py:167` (through a local wrapper invoked at `:149`) and `ledger_upgrade.py:71`. Each uses the return code only; `governance_health` and `ledger_upgrade` actively discard the streams through `redirect_stdout`/`redirect_stderr`. The public signature is unchanged, so none requires amendment. No test monkeypatches the function's internals.

### Locked Decisions

**LD-1. The function exceeds the razor's function and nesting clauses, and its shape caused four refuted designs.** Boundaries, pinned to the sealed ref so the citation keeps resolving after this phase lands:

- `git show d07daac3:qor/scripts/ledger_hash.py | sed -n '615p;725p'` -> `def verify_post_anchor(` and `    return 1 if errors else 0`

The limits it is measured against are 40 lines per function, 250 per file and nesting depth 3, per `qor/references/doctrine-audit-report-language.md:16`. The concerns are contiguous and separable at existing boundaries:

- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'classifications: list\[tuple\[int, str\]\]' -> 649:    classifications: list[tuple[int, str]] = []  # [(entry_num, "ok"|"fail")]`
- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'boundary_entry = max\(ok_entries\)' -> 684:        boundary_entry = max(ok_entries) if ok_entries else 0`
- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'for n in _duplicate_entry_numbers\(entries\)' -> 704:    for n in _duplicate_entry_numbers(entries):`
- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'print\(f"post-anchor clean' -> 719:        print(f"post-anchor clean (boundary=#{boundary_entry})")`

**LD-2. There is no post-anchor resolver to build, because `_resolve_recorded` already is one.** The inline resolution block and the shipped helper return the same triple on every path; the only thing the inline block adds is the GH #363 labelled-but-unreadable check, and `verify` already places that check in its caller:

- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'elif _dialect.any_hash_label_present\(body\)' -> 554:            elif _dialect.any_hash_label_present(body):`

So the post-anchor path reuses the shipped helper and puts the label check where `verify` puts it. This deletes a helper and a sentinel protocol, and shrinks the classification duplication.

**The coupling this creates runs in both directions and touches a third consumer.** `_resolve_recorded` is called at `ledger_hash.py:385` inside `_sequence_breaks` and at `:525` inside `verify`. After this phase it is also on the post-anchor path, so a change made for any one of the three moves the other two, and one of them is the release gate. The direction that matters most is not the one that sounds worst: GH #443's linkage fix plausibly needs continuity information from the resolver, so the widening that D1 says this phase makes cheaper is also the widening that would now propagate furthest. `tests/test_ledger_hash_verify_helpers.py` already pins `_resolve_recorded` directly, which is the existing guard on that surface.

**LD-3. Five helpers, named, with signatures.**

- `_post_anchor_classify(entries: list[tuple[int, str]]) -> list[tuple[int, str]]`
- `_post_anchor_boundary(classifications: list[tuple[int, str]], boundary_entry: int | None) -> int`
- `_post_anchor_report_entries(classifications: list[tuple[int, str]], boundary_entry: int) -> int`
- `_post_anchor_report_duplicates(entries: list[tuple[int, str]], boundary_entry: int) -> int`
- `_post_anchor_summary(errors: int, boundary_entry: int) -> int`

`_post_anchor_report_duplicates` takes `entries` rather than `classifications`, because a duplicate entry number is invisible to classification by construction, which is what GH #361 records. The `_post_anchor_` prefix avoids confusion with the existing `_classify_entry` at `ledger_hash.py:337`, which does a different job for `verify`; iteration 4 claimed the unprefixed name would collide by one character, which was simply wrong.

**LD-4. Razor facts are asserted by a test, and the counting rule the test uses is stated here.** A unit's length is its inclusive AST span, `end_lineno - lineno + 1`, which includes the `def` line, the docstring and the final `return`; its nesting depth is the maximum nesting of `For`, `While`, `If`, `With` and `Try` nodes within it. Under that rule the current function measures 111 and depth 4, re-derivable with:

- `python -c "import ast,pathlib;n=[x for x in ast.walk(ast.parse(pathlib.Path('qor/scripts/ledger_hash.py').read_text())) if getattr(x,'name','')=='verify_post_anchor'][0];print(n.end_lineno-n.lineno+1)"` -> `111`

The convention is stated because no existing checker in this repository defines one, so the test would otherwise invent it silently. `test_each_unit_is_within_the_razor_limits` applies it to the composition and each helper.

**LD-5. The move is not verbatim, and the differences are named rather than counted.** Helpers that end in a value gain a `return`. `_post_anchor_boundary` receives what is currently a rebound parameter, so the composition writes its result back. `errors` is one accumulator today, split across two reporting helpers and re-joined by the caller. The GH #363 label check moves out of the resolution block into the classification loop.

`boundary_entry` deserves separate mention: it is the one argument where identity and truthiness diverge, and `--boundary` is declared `type=int, default=None` at `qor/cli.py:204` and forwarded verbatim at `:69-70`, so `0` is reachable and must not reroute to auto-detection.

**LD-6. The shipped corpus is the safety argument, and it is a file.** `tests/post_anchor_corpus.py` builds one ledger per distinguishable path: a clean chain, an empty ledger, a GH #55 pre-anchor cluster with a clean later band, a ledger whose every early entry fails, a GH #443 linkage fork, a duplicate entry number at the boundary, a duplicate below it, entries carrying no hash label, Session Seal markup, a placeholder-pattern hash, a GH #363 labelled non-hex value, a trailing labelled failure, one firing both error accumulators together, **and one whose chain hash verifies only under `legacy_chain_hash`**.

That last fixture is the repair for the defect that vetoed iteration 4. `ledger_hash.py:676` accepts an entry when `expected == recorded or expected_legacy == recorded`, and those are different digests -- `chain_hash` is SHA256(content + "|" + prev), `legacy_chain_hash` is SHA256(content + prev), per `:41-48`. The branch is not historical trivia in this repository:

- `python -c "from pathlib import Path; from qor.scripts import ledger_hash as lh; parts=lh.ENTRY_RE.split(Path('docs/META_LEDGER.md').read_text(encoding='utf-8')); E=[(int(parts[i]),parts[i+1] if i+1<len(parts) else '') for i in range(1,len(parts),2)]; print(sum(1 for _,b in E if (r:=lh._resolve_recorded(b)) and lh.chain_hash(r[0],r[1])!=r[2] and lh.legacy_chain_hash(r[0],r[1])==r[2]))"` -> `119`

Without that fixture a decomposition dropping `expected_legacy` passes every other fixture and every golden while breaking the live chain.

The goldens can be inlined literals because the output alphabet interpolates only integers, re-derivable with a command that shows the templates rather than the `print(` lines they start on:

- `sed -n '686,725p' qor/scripts/ledger_hash.py | grep -oE '"[^"]*Entry #\{[a-z_]+\}[^"]*"|"post-anchor [^"]*"'` -> seven templates whose only interpolations are `{num}`, `{n}`, `{boundary_entry}` and `{errors}`

Iteration 4 offered a `grep -nE 'print\('` for this and it did not work, because four of the seven format strings sit on the line after their `print(`. That command was written without being run, in the iteration whose thesis was that commands must back claims.

A drafted decomposition was compared against the current implementation over this corpus before this plan was written, across every fixture plus a pinned boundary of 2, a pinned boundary of 0 and the live ledger. **Every invocation matched.** That outcome is stated because it is material and is not a figure; it remains a smoke check rather than evidence, because the drafted text ships in no file and one input was the live ledger, which moves at every seal.

**LD-7. The ordering convention, and everything it does not establish.** The corpus module and `tests/test_post_anchor_characterization.py` land in the first commit; `tests/test_post_anchor_decomposition.py` and the decomposition land in the second. The characterization file imports only `verify_post_anchor`, which already exists, so it collects and passes at the pre-change SHA.

What this establishes: the refactor commit's diff shows the goldens unchanged, so they were not tuned to match refactored behaviour.

What it does not establish, stated in full because iteration 4 disclosed the smaller gap and stayed silent on the larger one. First, that the goldens were captured before the refactor: a sequence built goldens-first and one built decompose-first-then-back-commit produce identical diffs, and a reviewer wanting the stronger fact must check out the first commit and run the corpus, which is a manual step. Second, and more seriously, **the decomposition suite's red-before-green property is established by no artifact at all.** That file lands in the second commit, so it exists at no commit in a failing state, and checking out the first commit does not help because the file is not there. Its tests are red against the pre-change code, and the only record of that is this sentence and the implementer's account. Third, there is no CI record at either commit unless a pull request is already open: `.github/workflows/ci.yml` fires `push` only for `branches: [main]`, and `pull_request` runs against the merge ref rather than the branch head.

**LD-8. No coverage guard ships and no coverage figure is quoted.** `coverage` is in no dependency group and CI installs only `.[dev]`, so such a guard could not run; and a coverage number in prose is the artifact this method exists to stop producing. GH #445 records what becomes of such numbers in this very file.

**LD-9. Corrections to earlier iterations, each of which was confidently wrong when written.** Iteration 1 called the pinned-boundary path the only route to the reporting loop's error branch; the placeholder and non-hex fixtures reach it under auto-detection, because with no ok entries the boundary resolves to 0 and entry 1 exceeds it. Iteration 1 also attributed the placeholder/non-hex output collision solely to the discarded field name at `ledger_hash.py:671`; the non-hex path at `:657-664` never computes a field name, so the collision has two independent causes. Iterations 2 and 3 each claimed a fixture was the sole guard against a specific mutation and each was refuted by a wider enumeration than its author performed, so no such claim is made here. The tribunal record for all four iterations is at META_LEDGER entries #743 through #746; no count of their findings is restated here, because those counts are the one class of figure this plan cannot re-derive with a command.

### Changes

`verify_post_anchor`'s body becomes the composition of the five helpers of LD-3, carrying the code from the ranges in LD-1 with the differences LD-5 names and nothing else. No emitted string is edited, no branch condition is inverted, and the public signature is unchanged.

The golden master is inlined literals in the characterization test. It is never generated at test time, and never a snapshot file that autocreates on first run, because an autocreating snapshot self-approves whatever the refactored code emits on a fresh clone and reports green.

### Unit Tests

In `tests/test_post_anchor_characterization.py`, green before and after the decomposition:

- `test_every_corpus_fixture_reproduces_its_recorded_output` - for every fixture `tests/post_anchor_corpus.py` builds, asserts return code, stdout and stderr equal inlined literals. Fails on any reordering, dropped line or changed exit code, and fails if a fixture is added without a golden.
- `test_legacy_chain_hash_entry_still_verifies` - asserts the legacy-form fixture classifies ok and the run reports clean. Fails if the `expected_legacy` acceptance branch is dropped, which no other fixture detects.
- `test_pinned_boundary_two_reproduces_its_recorded_output` - the same golden assertion with `boundary_entry=2`, a contract `qor/cli.py` exercises.
- `test_pinned_boundary_zero_is_not_auto_detection` - on a fixture whose auto-detected boundary is non-zero and which returns 0 there, asserts `boundary_entry=0` returns 1 and prints `boundary=#0`. Fails if the resolution test becomes truthiness rather than an identity check against `None`.
- `test_the_two_known_output_collisions_are_still_collisions` - asserts the empty and unlabelled fixtures produce identical output, and likewise placeholder and non-hex. A signpost rather than a net: the goldens already pin all four, so this exists to make a future fix delete an assertion naming what it changes.
- `test_both_error_accumulators_are_joined` - asserts the both-loops fixture reports two post-boundary failures with one entry failure and one duplicate failure on stderr. Also a signpost, for the same reason and stated in the same terms.

In `tests/test_post_anchor_decomposition.py`, red against the pre-change code:

- `test_each_unit_is_within_the_razor_limits` - applies LD-4's counting rule by AST to the composition and each helper, asserting at most 40 lines and depth at most 3. Red beforehand on both clauses.
- `test_classify_returns_expected_statuses` - calls `_post_anchor_classify` over bodies covering the canonical triple, the legacy form, Session Seal, placeholder, labelled-unreadable and unlabelled cases, asserting the returned status list.
- `test_boundary_prefers_the_explicit_value_including_zero` - asserts `_post_anchor_boundary` returns a pinned 0 rather than auto-detecting, and returns the highest ok entry when passed `None`.
- `test_report_entries_returns_the_post_boundary_error_count` - asserts the returned count and the emitted lines for a classification list spanning ok, disclosed and failing entries.
- `test_report_duplicates_returns_the_error_count` - asserts the returned count and emitted lines for duplicates above and below the boundary.
- `test_summary_returns_the_exit_code_and_emits_one_line` - asserts both branches of `_post_anchor_summary`.
- `test_classification_delegates_to_the_shared_resolver` - replaces `ledger_hash._resolve_recorded` with a spy forwarding to the original, runs `_post_anchor_classify`, and asserts the spy was called at least once and that its recorded arguments are the entry bodies. Fails if resolution is re-inlined, which an assertion on classification output alone cannot detect. The assertion is on arguments and at-least-once rather than an exact per-entry count, so a delegating implementation that short-circuits before resolving is not reddened for a legitimate choice.

Each helper is exercised by its own named test rather than by one test asserting that the suite exercises them, so a failure localises to a helper and an unexercised sixth helper cannot leave the suite green.

## Definition of Done

### Deliverable: decomposed verify_post_anchor

- **D1**: The concerns that collided in four refuted designs are separable units, so the next attempt at GH #443, GH #425 or GH #430 edits one named helper. Because the post-anchor path reuses `_resolve_recorded`, the parity phase reconciles two classifiers rather than two resolvers, at the cost LD-2 records.
- **D2**: `verify_post_anchor` composes five module-private helpers and its public signature is unchanged. Razor compliance for the function and nesting clauses is asserted by `test_each_unit_is_within_the_razor_limits` under LD-4's stated counting rule. The file clause is not satisfied and was not before.
- **D3**: No governance artifact changes in the implementation commit, no dependency is added, and no issue is closed. The seal entry names the shipped corpus and characterization suite as the evidence for behaviour preservation.
- **D4**: Every test listed above passes. The characterization tests pass identically before and after; the decomposition tests are red against the pre-change code, with the evidentiary limits of that claim stated in LD-7 rather than implied.

## Feature Inventory Touches

None. No user-facing surface changes; this phase is defined by producing no observable difference.

## CI Commands

- `python -m pytest tests/test_post_anchor_characterization.py tests/test_post_anchor_decomposition.py -v` - the new suites; run twice to confirm determinism
- `python -m pytest tests/test_post_anchor_verify.py tests/test_ledger_hash_duplicate_entry.py tests/test_ledger_hash.py tests/test_ledger_hash_validation.py tests/test_ledger_hash_verify_helpers.py tests/test_verify_ledger_cli.py tests/test_seal_entry_check.py tests/test_ledger_upgrade.py tests/test_governance_health.py tests/test_governance_health_post_anchor_tolerance.py tests/test_governance_health_json.py tests/test_cli_governance_health.py tests/test_qor_status_governance_health.py tests/test_variant_drift_governance_health.py tests/test_ledger_dialect.py tests/test_qor_validate_skill_post_anchor_prose.py -v` - every suite over the changed module, its four consuming callers and the one skill-prose consumer
- `python -m pytest -q` - full suite; no regression
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity, run without a truncating pipe
- `ruff check .` - lint
