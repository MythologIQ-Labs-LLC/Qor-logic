# Plan: Declared post-anchor anchor

**change_class**: feature

**doc_tier**: minimal

**iteration**: 1

**originating_remediation**: GH #430

**boundaries**:
- limitations:
  - The declaration is a single entry number. It says where a repository's trustworthy band begins; it does not say why the entries below it fail, which stays in the operator's disclosure prose.
  - A consumer whose ledger carries failures and declares no anchor changes from exit 0 to exit 1. That is the defect being closed, but it is a behaviour change for anyone currently relying on the inferred boundary, including `ledger_upgrade.upgrade`, which will decline to swap rather than swap on an inferred pass.
  - This repository's own declaration must be `111` rather than `12`, because entries #109 and #111 classify as failures. They are deliberate non-chain-advancing narrative entries, so the declaration understates how much of the chain verifies by 81 measured entries. Correcting that requires recognizing the non-chain-advancing form, which is a separate decision.
- non_goals:
  - Changing what counts as a failing entry. The classification loop is untouched.
  - Taint propagation in post-anchor mode. GH #430's first suggestion, excluding tainted entries from anchor eligibility, is measured below as contract-breaking and is not adopted.
- exclusions:
  - GH #443 and GH #425.
  - GH #430's third suggestion, that `governance_health` surface the strict/post-anchor disagreement. It is a diagnostic improvement, not a correctness fix, and it becomes less urgent once a declaring repository's gate is honest.
  - Formalizing the `Non-chain-advancing` entry marker. It appears on three entries (#109, #111, #112), is documented in no doctrine or script, and admitting an undocumented convention into the classifier is a governance decision that deserves its own phase.

## Scoping

One resolution rule, one declaration, one doctrine section. The preceding two attempts in this cluster were stopped before a plan was written because the remedy each issue proposed was never run against the case it targeted. Every rule in this plan was executed against the failing fixture and against this repository's live ledger before it was written down, and the observed exit codes are recorded in the Locked Decisions.

## Open Questions

None. The one that would have been open -- whether this repository can satisfy the new rule -- was measured and is answered in LD-5.

## Phase 1: Resolve the boundary from a declaration

### Affected Files

- `tests/test_post_anchor_declared_anchor.py` NEW - the resolution order, the fail-closed branch, and the guidance message
- `qor/scripts/ledger_hash.py` - boundary resolution in `verify_post_anchor`
- `.qorlogic/config.json` - this repository's declaration
- `qor/references/doctrine-governance-enforcement.md` - section 14 gains the declared-anchor contract
- `qor/references/glossary.md` - the existing `post-anchor boundary` definition at line 633 is corrected, since auto-detection is no longer its unconditional default. No term is introduced: the concept is unchanged and only how its value is resolved differs, which is why this plan declares `doc_tier: minimal`.

Callers of `verify_post_anchor`, enumerated per SG-AffectedFilesContract-A. All keep working unchanged because the new parameter is optional and defaulted:

- `qor/cli.py:70` - passes `boundary_entry` from `--boundary`; explicit argument still wins.
- `qor/reliability/seal_entry_check.py:149` - passes neither; picks up the declaration.
- `qor/scripts/governance_health.py:167` - passes neither; picks up the declaration.
- `qor/scripts/ledger_upgrade.py:71` - passes neither, against a temp file written beside the real ledger, so the declaration resolves.

### Locked Decisions

**LD-1. The boundary is inferred from the data it is supposed to judge, and that is the defect.** `verify_post_anchor` picks the highest entry that classified `ok`:

- `git show d07daac3:qor/scripts/ledger_hash.py | grep -nE 'boundary_entry = max' -> 684:        boundary_entry = max(ok_entries) if ok_entries else 0`

A ledger whose newest entry is self-consistent therefore certifies itself, however much of its history failed. This repository is such a ledger: run against `docs/META_LEDGER.md`, `verify_post_anchor` returns 0 and prints `post-anchor clean (boundary=#740)` while classifying ten entries as failures, at #1, #2, #3, #4, #5, #7, #8, #10, #109 and #111.

**LD-2. GH #430's own first suggestion is not adopted, because it breaks the contract the mode exists for.** Excluding tainted entries from anchor eligibility was simulated against three shapes. `verify()` taints unconditionally from the first failure onward and never resets, which is visible in the classifier: the taint branch fires on `if last_failed:` before the math check and does not clear it.

Simulated exit codes, boundary under the suggestion in parentheses:

| shape | today | suggestion 1 + 2 |
|---|---|---|
| GH #55 consumer, early failures then a clean band | 0 (#8) | 1 (#2) |
| GH #430 reporter, all early entries fail | 0 (#8) | 1 (#0) |
| this repository, live | 0 (#740) | 1 (#740, no untainted anchor) |

It fixes the reporter and breaks both the consumer contract and this repository. Tainted and disclosed-pre-anchor are the same condition under the current model, so a rule that rejects the first necessarily rejects the second.

**LD-3. The declaration replaces the inference only where the inference is unsafe.** Resolution order becomes: an explicit `boundary_entry` argument; then a declared value; then auto-detection, permitted only when no entry classifies as a failure; then a fail-closed error. A ledger with no failures has nothing to disclose and nothing to declare, so auto-detection remains correct for it and no clean-ledger caller changes behaviour.

**LD-4. The declaration is read through the one tolerant config reader.** `.qorlogic/config.json` already carries operator declarations and has a single canonical reader:

- `git show d07daac3:qor/scripts/qorlogic_config.py | grep -nE 'CONFIG_RELPATH = Path' -> 19:CONFIG_RELPATH = Path(".qorlogic") / "config.json"`
- `git show d07daac3:qor/scripts/qorlogic_config.py | grep -nE 'def load_section' -> 22:def load_section(repo_root: Path | None, name: str) -> dict:`

`load_section` is total and never raises, so a missing file, unreadable path, invalid JSON or non-object section all read as "declared nothing". That composes correctly with LD-3: a malformed declaration on a failing ledger falls through to the fail-closed branch rather than to a tolerated pass.

**LD-5. This repository can satisfy the rule, and the value is 111 rather than 12.** The failing entries are #1, #2, #3, #4, #5, #7, #8, #10, #109 and #111, so the lowest declaration that leaves a clean band is 111. Verified by calling the real function rather than a reimplementation of it:

| declared boundary | rc | stderr lines |
|---|---|---|
| 11 | 1 | 3 |
| 108 | 1 | 3 |
| 111 | 0 | 0 |
| 112 | 0 | 0 |

Entries #109 and #111 are `GATE TRIBUNAL` and `IMPLEMENTATION` narrative entries carrying a `Previous Hash` label and an explicit `Non-chain-advancing` note, with no Content or Chain Hash. They classify as failures under the GH #363 labelled-but-incomplete rule. Declaring 111 is therefore accurate about what verifies contiguously, and understates the chain by the 81 entries in the #12 to #108 span that do verify individually (81 measured, not the 97 the number range would suggest). That understatement is disclosed in the boundaries above rather than fixed here.

**LD-6. No existing test changes.** The three tests that call `verify_post_anchor` with no boundary use fixtures with zero failing entries, so they keep auto-detecting: `test_boundary_defaults_to_last_clean_entry` (two correctly chained entries), `test_empty_ledger_returns_clean` (no entries) and `test_session_seal_entry_counts_as_clean_boundary_candidate` (one valid seal entry). The GH #55 pattern test, `test_corefoge_pre_anchor_cluster_tolerated`, pins `boundary_entry=6` explicitly, and an explicit argument still wins. This is the property that distinguishes this phase from GH #425, whose fix must amend a currently-green test.

### Changes

`verify_post_anchor` gains `repo_root: Path | None = None`. When `None` it resolves to the ledger's grandparent directory, so every existing caller resolves the repository root without changing its call. The boundary is then resolved in the order LD-3 states, and the fail-closed branch prints the failing entry numbers and the declaration needed, to stderr, before returning 1.

`.qorlogic/config.json` gains a `ledger` section declaring `post_anchor_boundary` as 111.

Section 14 of the enforcement doctrine gains the declared-anchor contract, and the `post-anchor boundary` glossary entry is amended so its stated default matches the resolution order.

### Unit Tests

- `tests/test_post_anchor_declared_anchor.py::test_declared_boundary_is_used_when_no_argument_is_given` - writes a ledger with a pre-boundary failure and a config declaring the boundary above it, calls `verify_post_anchor` with no `boundary_entry`, and asserts the return is 0 and the printed boundary is the declared number rather than the highest clean entry. Red before the change: the printed boundary is the auto-detected one.
- `tests/test_post_anchor_declared_anchor.py::test_explicit_argument_outranks_the_declaration` - same tree, called with an explicit `boundary_entry` differing from the declaration, and asserts the printed boundary is the argument. Confirms `qor/cli.py:70` keeps its meaning.
- `tests/test_post_anchor_declared_anchor.py::test_failing_ledger_without_a_declaration_returns_one` - a ledger with a failing entry and no config, asserting the return is 1. Red before the change: it returns 0 by anchoring on its own newest entry.
- `tests/test_post_anchor_declared_anchor.py::test_the_refusal_names_the_failing_entries_and_the_remedy` - the same call, asserting the stderr text contains each failing entry number and the config key an operator must set. A refusal that does not say what to do converts one defect into a support question.
- `tests/test_post_anchor_declared_anchor.py::test_clean_ledger_still_auto_detects_without_a_declaration` - a ledger with no failing entry and no config, asserting the return is 0 and the boundary is the highest entry. This is the branch LD-3 relies on to leave clean-ledger callers untouched.
- `tests/test_post_anchor_declared_anchor.py::test_malformed_declaration_does_not_tolerate_a_failing_ledger` - a failing ledger whose config declares a non-integer boundary, asserting the return is 1. Confirms the tolerant reader composes fail-closed rather than fail-open.
- `tests/test_post_anchor_declared_anchor.py::test_this_repository_verifies_under_its_own_declaration` - calls `verify_post_anchor` on the live `docs/META_LEDGER.md` with no argument and asserts the return is 0, so the migration is proven by the gate rather than by the plan asserting it.

## Definition of Done

### Deliverable: declared post-anchor anchor

- **D1**: A ledger that carries failures certifies its trustworthy band by declaring where that band begins, rather than by inferring it from the newest entry that happens to verify.
- **D2**: `verify_post_anchor(ledger_md, boundary_entry=None, repo_root=None)` resolves the boundary as explicit argument, then declaration, then auto-detection when no entry fails, then a fail-closed refusal returning 1.
- **D3**: Section 14 of `doctrine-governance-enforcement.md` states the contract; the `post-anchor boundary` glossary entry matches it; `.qorlogic/config.json` declares 111; the seal entry records that this repository's declaration understates the chain by the #12 to #108 span.
- **D4**: The seven tests above pass, each red beforehand for its own stated reason, and the existing `tests/test_post_anchor_verify.py` and `tests/test_ledger_hash_duplicate_entry.py` suites stay green with no amendment.

## Feature Inventory Touches

None. This phase touches no user-facing command surface enumerated in `FEATURE_INDEX.md`; it changes how an internal verification mode resolves one parameter.

## CI Commands

- `python -m pytest tests/test_post_anchor_declared_anchor.py -v` - the new suite; run twice to confirm determinism
- `python -m pytest tests/test_post_anchor_verify.py tests/test_ledger_hash_duplicate_entry.py tests/test_ledger_hash.py tests/test_seal_entry_check.py tests/test_ledger_upgrade.py tests/test_governance_health.py -v` - every suite over the changed function and its four callers
- `python -m pytest -q` - full suite; no regression
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - chain integrity, run without a truncating pipe
- `ruff check .` - lint
