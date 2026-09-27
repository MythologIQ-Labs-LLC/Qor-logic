# Plan: Phase 297 - Distinguish sealed versions from published releases

**change_class**: hotfix

**doc_tier**: minimal

**Issue**: GH #520

**Current base**: `15729311f9f4d55d5dad2db004b972415c39432c`

**Iteration**: 3 (responds to the iteration-2 VETO, ledger #810: V1, advisories A1-A5; the iteration-1 VETO, ledger #809, was resolved by iteration 2)

## Open Questions

None. OQ-1 (the boundary finding in a Shadow Genome event) was decided by the operator on 2026-09-27 and is locked as LD-10.

## Problem

`tests/test_changelog_tag_coverage.py` currently exempts every dated CHANGELOG version above the highest observed Git tag. That rule was sufficient while only one release candidate was in flight, but it allows a stack of sealed-but-unpublished versions to remain implicit and therefore conflates version sealing with publication.

The same test reads every local tag (`git tag -l`), including tags that exist only on another line of history. A parallel governed phase's local seal tag, which every substantiation creates, therefore breaks this branch's coverage even though it says nothing about this branch's CHANGELOG.

Qor-logic needs an explicit distinction between:

- a version stamped and sealed by `/qor-substantiate`;
- a local-only seal tag created during governed work, on this branch or on another;
- the one current release candidate that may legitimately remain untagged;
- a version actually published through the remote tag-driven release path.

The repository also carries historical untagged exceptions whose stronger publication history cannot be reconstructed safely from the retained evidence. Manufacturing remote tags for those versions would misstate history and can re-trigger release automation.

## Locked Decisions

### LD-1: exceptional release state is explicit data, not a test constant

Add `docs/release-state.json` as the machine-readable record for versions whose tag/publication history differs from the ordinary release path. The root shape is closed and versioned:

```json
{
  "schema": "qor.release-state/v1",
  "exceptions": []
}
```

The root object contains exactly `schema` and `exceptions`. `schema` is exactly `qor.release-state/v1`; `exceptions` is a list. Each exception entry contains exactly:

- `version`: strict `MAJOR.MINOR.PATCH`;
- `state`: `sealed_unpublished`, `legacy_untagged`, or `unreachable_tag`;
- `reason`: non-empty explanatory text.

The current base hard-codes the historical exceptions in the test. Evidence, one line per statement:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE '^_GRANDFATHERED_UNTAGGED_SECTIONS'` -> `29:_GRANDFATHERED_UNTAGGED_SECTIONS = frozenset({"0.69.0", "0.70.0", "0.71.0", "0.102.2"})`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE 'def _released_orphans'` -> `56:def _released_orphans(versions: set[str], tags: set[str]) -> set[str]:`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE 'Versions above the highest existing'` -> `59:    Versions above the highest existing tag are pre-release entries (about to ship`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE 'versions - tags - '` -> `70:        for v in versions - tags - _GRANDFATHERED_UNTAGGED_SECTIONS`

The exceptional record is not a release registry and does not duplicate ordinary tagged releases.

### LD-2: `[project].version` is the single implicit untagged candidate

For the inverse direction:

- read `[project].version` from `pyproject.toml`;
- require that exact version to have a dated CHANGELOG section;
- treat only that exact project version as the implicit untagged release candidate;
- the ceiling is the greater of the project version and the highest tag reachable from `HEAD` (LD-7);
- require every other dated CHANGELOG version at or below the ceiling to have a reachable tag or an explicit release-state disposition.

The current base establishes the candidate and its dated section. Evidence, one line per statement:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.0"`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[Unreleased\]'` -> `11:## [Unreleased]`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[0\.175\.0\]'` -> `13:## [0.175.0] - 2026-09-24`

This replaces the broad "everything above the highest tag is pre-release" exemption. An older missing tag may not hide merely because later versions were sealed without publication.

### LD-3: local tag presence does not mint publication truth

A `sealed_unpublished` disposition remains authoritative even when the checkout contains a local-only seal tag for that version, whether or not the tag is reachable from `HEAD`. The tag does not void the disposition, and the disposition does not make the tag a coverage failure. Unit tests must not attempt network access to infer remote publication from local Git state.

If a version is intentionally published later, its exceptional disposition must be removed or changed in the same governed release action. This phase does not push or backfill any remote tag.

### LD-4: uncertain legacy history stays uncertain

Move the existing four hard-coded historical exceptions into `docs/release-state.json` as `legacy_untagged` rather than inventing a stronger release claim:

- `0.69.0`
- `0.70.0`
- `0.71.0`
- `0.102.2`

Record the currently established sealed-but-unpublished versions as `sealed_unpublished`:

- `0.173.0`
- `0.174.0`
- `0.174.1`
- `0.174.2`
- `0.174.3`
- `0.175.0`

Record the three versions whose tag exists but is not reachable from `HEAD` (LD-7) as `unreachable_tag`:

- `0.24.1`
- `0.25.0`
- `0.39.0`

`0.175.0` is the implicit candidate at base. Once `/qor-substantiate` bumps the project version to `0.175.1`, it stops being the candidate, and its `sealed_unpublished` entry is what keeps coverage green. This phase records no disposition for `0.175.1` or any later version, and it does not rewrite any historical CHANGELOG section.

### LD-5: doctrine names the lifecycle boundary

Update `qor/references/doctrine-changelog.md` to state explicitly:

`sealed/versioned != released/published`

The base doctrine already establishes that the seal stamps the CHANGELOG mechanically, as a pure rename, before any publication step. Evidence, one line per statement:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/references/doctrine-changelog.md | grep -nE 'stamped mechanically on seal'` -> `5:> hand during implementation and stamped mechanically on seal.`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/references/doctrine-changelog.md | grep -nE 'stamp is a pure rename'` -> `22:  stamp is a pure rename.`

The updated doctrine must separate that sealed/versioned state from the later remote publication transition. It must also document the narrow exceptional-state record and the reachable-tag rule (LD-7).

The doctrine also names CI as the enforcement point for tag coverage. A local checkout can hold a reachable local-only seal tag, so a version can be covered locally while it is an orphan in CI, which sees only the tags on origin. The CI result is authoritative. The local result is advisory (iteration-2 A1).

### LD-6: release-state rules have one canonical owner module

Create `qor/scripts/release_state.py` as the canonical owner of the closed-schema parser/validator, the reachable-tag reader (LD-7), and the pure coverage computation. The grammar is not embedded in the already-large tag-coverage test.

Validation fails closed on:

- invalid JSON or unreadable file;
- wrong root shape, extra root fields, or unsupported schema id;
- non-list `exceptions`;
- non-object or extra-field entries;
- non-SemVer versions;
- unsupported states;
- empty reasons;
- duplicate versions;
- exception versions absent from CHANGELOG.

This module's enforcement consumer is the repository test gate, `tests/test_changelog_tag_coverage.py`, which runs in CI. No runtime CLI or skill caller is added, because the rule exists to fail the test gate. It is not called a production runtime surface (iteration-1 A3 accepted).

Every exception state is an operator-asserted disposition. The validator does not check that an `unreachable_tag` entry names a version whose tag exists and is unreachable, just as it does not check publication history for the other two states (iteration-2 A2 accepted).

`tests/test_release_state.py` owns validator and reachable-tag regressions. `tests/test_changelog_tag_coverage.py` owns the live candidate/tag coverage behavior and consumes the module. This keeps each modified source or test file inside the Section 4 budget of 250 lines.

### LD-7: tag coverage considers only tags reachable from `HEAD`

Tag observation uses `git tag --merged HEAD --list 'v*'`, filtered to strict `vMAJOR.MINOR.PATCH`. The tag coverage rules use only this reachable set:

- **Forward rule:** every reachable SemVer tag must have a dated CHANGELOG section.
- **Ceiling (LD-2):** the ceiling is computed from reachable tags and the project version.
- **Inverse membership:** an older version counts as tag-covered only by a reachable tag.

A tag that is not reachable from `HEAD` belongs to another line of history, for example a parallel phase's local seal tag. It makes no claim about this branch's CHANGELOG. It cannot fail the forward rule, raise the ceiling, or cover an older version.

A shallow repository cannot decide reachability, because its history is truncated and older tags look unreachable. The reader detects this with `git rev-parse --is-shallow-repository` and raises a named error instead of returning a partial set. The live coverage test turns that error into a `pytest.skip` that states the reason, which matches the existing skip when git is unavailable. CI checks out full history, so CI enforcement is unchanged:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:.github/workflows/ci.yml | grep -m1 -nE 'fetch-depth: 0'` -> `31:          fetch-depth: 0`

The base test reads every local tag instead:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:tests/test_changelog_tag_coverage.py | grep -nE '"git", "tag", "-l"'` -> `36:            ["git", "tag", "-l", "v*"],`

Three historical tags are not reachable from the base. Each was created on a phase branch whose tagged commit is not an ancestor of the base. Evidence, one line per statement:

`git merge-base --is-ancestor v0.24.1 15729311f9f4d55d5dad2db004b972415c39432c; echo $?` -> `1`

`git merge-base --is-ancestor v0.25.0 15729311f9f4d55d5dad2db004b972415c39432c; echo $?` -> `1`

`git merge-base --is-ancestor v0.39.0 15729311f9f4d55d5dad2db004b972415c39432c; echo $?` -> `1`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[0\.24\.1\]'` -> `3083:## [0.24.1] - 2026-04-19`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[0\.25\.0\]'` -> `3072:## [0.25.0] - 2026-04-19`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:CHANGELOG.md | grep -nE '^## \[0\.39\.0\]'` -> `2894:## [0.39.0] - 2026-04-30`

Under the reachable-only rule these three dated versions would be orphans. The plan does not widen inverse membership to unreachable tags, because that would let a tag from another line of history cover a version. Instead each version gets an explicit `unreachable_tag` disposition (LD-4). The state says only that a tag exists off this line of history. It makes no claim about remote publication (LD-3). With the LD-4 entries, the base has no missing section and no orphan under this rule.

This rule is the self-application of GH #520 (iteration-1 V2). A local seal tag on another line of history does not mint release truth for this branch.

### LD-8: release target and in-flight candidate continuity

Phase 297 targets `0.175.1`: a `hotfix` bump from the base project version `0.175.0`.

On 2026-09-27 the operator decided that Phase 297 lands first and takes `0.175.1`. The operator also deleted the never-pushed local tag `v0.175.1`, which the held Phase 298 seal had created on its unmerged branch. In this checkout, `git tag -l 'v0.175*'` prints nothing, and `git ls-remote --tags origin` lists no `v0.175.x` tag. `version_applicability.validate` now returns ok: target `v0.175.1` is greater than the current highest tag, `v0.172.2`. Neither a downgrade nor a tag collision remains (iteration-1 V1).

Phase 298 remains a superseded candidate. Its sealed evidence stays on its own pull request, bound to its revision. It re-seals later, at `0.175.2`, after it rebases onto the new `main`. This plan records no release-state disposition for Phase 298 or its versions. That disposition, together with the rest of its 0.175.x continuity handling (CHANGELOG section, ledger numbering, and a `sealed_unpublished` entry for `0.175.1` if 297 is still unpublished), belongs to Phase 298's own rebase (iteration-1 A6 accepted as out of scope).

The substantiate-time version guard still reads all local tags. Its parallel-phase collisions are resolved by operator ordering, as they were here. Changing that guard is outside this hotfix.

### LD-9: pre-audit implementation checkpoint has no gate standing

This branch carries implementation commits made before any audit gate. The last of them is `6d1a146102e8019aef99c1290c18d4536ff51f02`. Those commits are drafts, not evidence (iteration-1 A5). This decision resolves iteration-2 V1 by naming the exact restore set. They changed exactly six paths relative to base. One is this plan, and the other five are the draft implementation. The count is six, and each named path occurs once in the list. Evidence, one line per statement:

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | wc -l` -> `6`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'docs/plan-qor-phase297-sealed-unpublished-release-state.md'` -> `1`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'docs/release-state.json'` -> `1`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'qor/references/doctrine-changelog.md'` -> `1`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'qor/scripts/release_state.py'` -> `1`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'tests/test_changelog_tag_coverage.py'` -> `1`

`git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 6d1a146102e8019aef99c1290c18d4536ff51f02 | grep -cxF 'tests/test_release_state.py'` -> `1`

Three of the five do not exist at base, and two do:

`git ls-tree --name-only 15729311f9f4d55d5dad2db004b972415c39432c qor/scripts/release_state.py docs/release-state.json tests/test_release_state.py | wc -l` -> `0`

`git ls-tree --name-only 15729311f9f4d55d5dad2db004b972415c39432c qor/references/doctrine-changelog.md tests/test_changelog_tag_coverage.py | wc -l` -> `2`

`/qor-implement` must not treat the draft commits as authorized. Its first change to the working tree, made after its protocol preflight steps and before any test is written or any RED observation, resets exactly this restore set and no other path:

- delete `qor/scripts/release_state.py`, `docs/release-state.json`, and `tests/test_release_state.py`, which do not exist at base: `git rm -q qor/scripts/release_state.py docs/release-state.json tests/test_release_state.py`;
- restore `qor/references/doctrine-changelog.md` and `tests/test_changelog_tag_coverage.py` to base content: `git checkout 15729311f9f4d55d5dad2db004b972415c39432c -- qor/references/doctrine-changelog.md tests/test_changelog_tag_coverage.py`.

After the reset, `git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c -- qor/scripts/release_state.py docs/release-state.json tests/test_release_state.py qor/references/doctrine-changelog.md tests/test_changelog_tag_coverage.py` prints nothing.

The restore set is closed. Nothing outside it is restored, reset, or rewritten:

- the plan itself is not restored, because it is the authorizing document;
- append-only governance records are never restored or rewritten: `docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `docs/PROCESS_SHADOW_GENOME.md`, `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`, everything under `.qor/gates/`, and every intent lock under `.qor/intent-lock/`;
- `CHANGELOG.md` is not restored. It already equals base, and its historical sections are never rewritten. Phase 2 adds only the one Unreleased note.

`docs/META_LEDGER.md` and `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` change in this phase only through LD-10: one appended AMENDMENT entry and the one-line edit of the LD-10 event. Every ledger entry and Shadow Genome event recorded by plan and audit sessions before implementation, including the LD-10 target event, stays in place.

### LD-10: disclosed remediation of one Shadow Genome event (operator decision OQ-1)

`publication_boundary_lint` reports one structural finding on this branch. `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` line 75 is the `gate_override` event from plan session `2026-09-25T2350-e05ce1`. Its `details.reason` carries an absolute local worktree path. The seal ladder runs this lint fail-closed at `/qor-substantiate` Step 4.6.14, so Phase 297 cannot seal while that line stands.

On 2026-09-27 the operator chose the disclosed direct edit for this one event only. There is no history rewrite and no force-push. `/qor-implement` performs the remediation. It is not performed during planning.

The event id function and the append serialization at base. Evidence, one line per statement:

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/shadow_process.py | grep -nE '^def compute_id'` -> `40:def compute_id(event: dict) -> str:`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/shadow_process.py | grep -nE 'line = json.dumps'` -> `129:    line = json.dumps(event_with_id, separators=(",", ":")) + "\n"`

`git show 15729311f9f4d55d5dad2db004b972415c39432c:qor/scripts/ledger_emit.py | grep -nE '^def append'` -> `70:def append(ledger_path: Path, entry: LedgerEntry,`

Mechanics:

1. Parse line 75 with `json.loads`. Confirm that its `id` is `70f04c8458699f7e7c82c864f19d02ad7d77820cffba8c2517a38e76df454073` and equals `shadow_process.compute_id(event)`. If either check fails, stop.
2. In `details.reason`, replace only the absolute worktree-root path that immediately precedes `/.qor/gates/2026-09-25T2350-e05ce1/research.json` with the neutral token `<repo-root>`. That path starts at its leading `/` and ends just before `/.qor/gates/`. The reason's leading text, `user override: research.json not found at `, stays unchanged, and so does the `/.qor/gates/...` suffix. The resulting reason is `user override: research.json not found at <repo-root>/.qor/gates/2026-09-25T2350-e05ce1/research.json`. Change no other field.
3. Set `id` to `shadow_process.compute_id(event)` on the edited event. The expected value is `6c2548c1e5116925fc5da35e5899c8905d6a679f7631ddcc2d0c1d7c99ccb437`. It was computed during planning from the same inputs, and the implementation must recompute it and confirm the match.
4. Serialize with `json.dumps(event, separators=(",", ":"))`, keeping key order with `id` first, and write it back as line 75. `git diff` must show exactly one changed line in that file.
5. Append one META_LEDGER entry through `ledger_emit.append(Path("docs/META_LEDGER.md"), LedgerEntry(...))`. It takes the next free entry number. The title is `AMENDMENT -- publication-boundary edit disclosure for shadow event of session 2026-09-25T2350-e05ce1`. The fields are `Timestamp`, `Phase: IMPLEMENT`, and `Author: Specialist`. The entry has no `**Artifact**` line, because nothing binds the file's bytes. It has no `**Amends**` line, because no ledger entry records the event. Its content hash is the default self-bound body hash. The body states:
   - the file `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` and line 75;
   - the event's session `2026-09-25T2350-e05ce1` and type `gate_override`;
   - the old id `70f04c8458699f7e7c82c864f19d02ad7d77820cffba8c2517a38e76df454073` and the new id `6c2548c1e5116925fc5da35e5899c8905d6a679f7631ddcc2d0c1d7c99ccb437`;
   - the edited field, `details.reason`, where an absolute local path was replaced by `<repo-root>`;
   - the reason: the path violated the publication boundary, and `publication_boundary_lint` fails closed at seal;
   - the authority: operator decision OQ-1, dated 2026-09-27;
   - that no other byte of the file changed, that no history was rewritten, and that the removed text is not quoted.

No ledger entry, gate artifact, or other governance record binds the old id, so nothing else changes. Outside the log itself, only this plan and the iteration-2 audit report mention it, and both name it as the subject of this edit. Neither quotes the removed path.

The log is append-only, so the target stays at line 75 while later sessions append events. Step 1's id check is the guard: if line 75 does not carry the expected id, the remediation stops.

Proof:

- `tests/test_shadow_log_integrity.py` (NEW, written first and observed RED on the unremediated line). For each tracked log, `docs/PROCESS_SHADOW_GENOME.md` and `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`, it reads the events with `shadow_process.read_events`. Every event passes `shadow_process.validate`, which is `shadow_event.schema.json`. Every event's `id` equals `shadow_process.compute_id(event)`. The ids are unique. `publication_boundary_lint.scan_text(rel, text, [])` returns no finding. These are invariants over every event, and the test asserts no specific id or hash.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` exits 0.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` verifies the chain with the AMENDMENT included.

## Feature Inventory Touches

Empty. This is release-governance/test maintenance and introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Release-state contract and candidate coverage

### Affected Files

Test files are listed first. Each entry says whether it is in the LD-9 restore set.

- `tests/test_release_state.py` - NEW validator, reachable-tag, and coverage-computation regressions. In the LD-9 restore set: the draft is deleted, then the file is written test-first.
- `tests/test_changelog_tag_coverage.py` - live candidate, reachable-tag, and explicit-disposition coverage. In the LD-9 restore set: reset to base, then edited.
- `tests/test_shadow_log_integrity.py` - NEW schema, id, uniqueness, and boundary invariants over the tracked Shadow Genome logs (LD-10). Absent at base and on this branch, so it is not in the restore set.
- `qor/scripts/release_state.py` - NEW closed-schema validator, reachable-tag reader, and coverage computation. In the LD-9 restore set: the draft is deleted, then the file is written after RED.
- `docs/release-state.json` - NEW explicit exceptional release dispositions. In the LD-9 restore set: the draft is deleted, then the file is written after RED.
- `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md` - append-only, never restored. Line 75 only: neutral token and recomputed id (LD-10).
- `docs/META_LEDGER.md` - append-only, never restored. One appended AMENDMENT disclosing the LD-10 edit.

### Changes

1. Reset exactly the LD-9 restore set with the two LD-9 commands. The set is `qor/scripts/release_state.py`, `docs/release-state.json`, and `tests/test_release_state.py`, which are deleted, and `qor/references/doctrine-changelog.md` and `tests/test_changelog_tag_coverage.py`, which are restored to base. No other path is touched. This step comes before every other step of this list, including the RED observation in step 2.
2. Write `tests/test_release_state.py` and the new `tests/test_changelog_tag_coverage.py` in their final form, as listed under Unit Tests. In `tests/test_changelog_tag_coverage.py`:
   - remove `_GRANDFATHERED_UNTAGGED_SECTIONS`, `_git_tags`, and `_released_orphans`;
   - remove the four base unit tests that encode the removed "above the highest tag is exempt" rule and the hard-coded exception set. They are `test_changelog_section_above_highest_tag_is_exempt`, `test_changelog_section_at_or_below_highest_tag_still_enforced`, `test_grandfathered_untagged_sections_are_precise`, and `test_released_orphans_no_tags_returns_empty`. Their surviving behaviors (an older untagged version is an orphan, and a disposition exempts only the named version) are re-asserted against `coverage_violations` in `tests/test_release_state.py` (iteration-2 A3).

   Observe both files RED, failing because `qor.scripts.release_state` does not exist yet.
3. Add `qor/scripts/release_state.py` with three parts: `load_release_state(path, changelog_versions)`, which raises `ReleaseStateError` on every LD-6 shape; `merged_semver_tags(repo_root)`, which raises `ShallowHistoryError` on a shallow repository; and the pure `coverage_violations(versions, tags, project_version, exceptions)`, which returns missing sections and orphans.
4. Add `docs/release-state.json` with the LD-4 entries.
5. Write `tests/test_shadow_log_integrity.py` and observe it RED on line 75 (the boundary check only). Then perform the LD-10 remediation and the AMENDMENT append, and observe it GREEN.
6. Observe the focused tests GREEN twice in a row.

### Unit Tests

- `tests/test_release_state.py`:
  - accepted `sealed_unpublished`, `legacy_untagged`, and `unreachable_tag` entries load, and each named version is returned with its state;
  - these records raise `ReleaseStateError`: wrong root shape, extra root fields, unsupported schema id, non-list `exceptions`, duplicate, malformed version, unsupported state, orphaned version, empty reason, extra entry field, invalid JSON, and an unreadable path;
  - `coverage_violations` reports an older untagged version under the ceiling as an orphan;
  - `coverage_violations` does not report the project version as an orphan;
  - `coverage_violations` reports a project version that has no dated section;
  - a reachable tag above the project version raises the ceiling;
  - an explicit disposition exempts only the named version;
  - a `sealed_unpublished` version that also has a tag still produces no violation (LD-3);
  - every fixture repository is built with `git init` in `tmp_path` and uses no network. It is isolated from the host's git configuration: `monkeypatch.setenv` sets `GIT_CONFIG_GLOBAL` to an empty file in `tmp_path` and `GIT_CONFIG_NOSYSTEM` to `1`, so settings such as `commit.gpgsign` or a default branch name cannot leak in. It pins author and committer identity through `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` (iteration-2 A4);
  - fixture repository: a `v*` tag on an unmerged side branch is absent from `merged_semver_tags`. With a CHANGELOG lacking that version, `coverage_violations` reports no missing section, and the tag raises no ceiling;
  - fixture repository: a tag reachable from `HEAD` whose version has no CHANGELOG section is returned by `merged_semver_tags`, and `coverage_violations` reports it as a missing section;
  - fixture repository: a dated CHANGELOG version below the project version, whose only tag sits on an unmerged side branch, is reported as an orphan. It stops being reported once an `unreachable_tag` disposition names it;
  - fixture repository: a `--depth 1` clone of a two-commit fixture makes `merged_semver_tags` raise `ShallowHistoryError`. The clone source is `Path.as_uri()` of the fixture, a `file://` URL, so the clone is shallow on every OS in the CI matrix.
- `tests/test_shadow_log_integrity.py`:
  - every event in each tracked Shadow Genome log validates against `shadow_event.schema.json`;
  - every event's `id` equals `shadow_process.compute_id` of that event, and no id repeats;
  - `publication_boundary_lint.scan_text` reports no finding for either log.
- `tests/test_changelog_tag_coverage.py`:
  - the live repository's reachable tags each have a dated section;
  - the live repository has no orphans under the project-version candidate and `docs/release-state.json`;
  - both live tests read tags through one module-level helper, `_reachable_tags()`. It calls `release_state.merged_semver_tags(REPO)`. It turns `ShallowHistoryError` into `pytest.skip` with a reason that names shallow history, and it turns an unavailable git (`FileNotFoundError` or `subprocess.CalledProcessError`) into the existing git-unavailable skip;
  - skip mechanism (iteration-2 A5): with `monkeypatch.setattr(release_state, "merged_semver_tags", ...)` replacing the reader with one that raises `ShallowHistoryError`, calling `_reachable_tags()` raises `pytest.skip.Exception`, and its message names shallow history. With a reader that raises `FileNotFoundError`, it raises `pytest.skip.Exception` with the git-unavailable reason. These tests run on every checkout, shallow or not.

## Phase 2: Doctrine and user-facing release-state disclosure

### Affected Files

- `qor/references/doctrine-changelog.md` - define sealed/versioned versus released/published state, the candidate/exception coverage rule, the reachable-tag rule, and CI as the enforcement point (LD-5). In the LD-9 restore set: reset to base in Phase 1 step 1, then edited here.
- `CHANGELOG.md` - add one user-facing Unreleased note before substantiation. Not in the restore set: it already equals base, and no historical section changes.

### Changes

Document the new state boundary without claiming that a local tag proves publication. The Unreleased note describes the correction as release-state/tag-coverage hardening, not as a published release.

### Unit Tests

- existing changelog format/stamp/substantiate integration tests remain green;
- tag-coverage tests exercise the documented candidate, reachable-tag, and explicit-exception behavior.

## Definition of Done

### Deliverable: explicit sealed-versus-published release-state model

- **D1**: sealed/versioned state and released/published state are no longer conflated. Only the current project version is an implicit untagged candidate, and exceptional history is explicit. Only tags reachable from `HEAD` take part in coverage.
- **D2**: `qor/scripts/release_state.py`, `docs/release-state.json`, and the tag-coverage integration implement the closed state vocabulary, the reachable-tag reader, and the candidate/tag ceiling. Each modified code or test file stays within the Section 4 budget.
- **D3**: doctrine states `sealed/versioned != released/published` and the reachable-tag rule. No historical remote tag is fabricated, and no package is published. The LD-10 remediation changes only line 75 of `docs/PROCESS_SHADOW_GENOME_UPSTREAM.md`, and one META_LEDGER AMENDMENT discloses it with the old and new event ids. Promotion happens only after truthful audit and substantiation evidence exists for the current revision.
- **D4**: the focused release-state/tag-coverage suite and `tests/test_shadow_log_integrity.py` are observed RED before implementation and GREEN after it. On the implemented revision, the changelog/substantiation regression set, the full repository suite, and `publication_boundary_lint` all pass.

## CI Commands

- `python -m pytest tests/test_changelog_tag_coverage.py tests/test_release_state.py -q` - verifies candidate coverage, reachable-tag scoping, and exceptional-state validation.
- `python -m pytest tests/test_shadow_log_integrity.py -q` - verifies every Shadow Genome event validates, carries its computed id, and is boundary-clean.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain including the LD-10 AMENDMENT.
- `python -m pytest tests/test_changelog_format.py tests/test_changelog_stamp.py tests/test_substantiate_changelog_integration.py -q` - verifies CHANGELOG/substantiation compatibility.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `ruff check qor/ tests/` - verifies the repository's configured Python lint contract.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the LD-10 remediation leaves no boundary finding.

## Non-goals

- pushing any remote Git tag;
- publishing any package;
- modifying historical CHANGELOG sections;
- changing release workflow behavior;
- changing the substantiate-time version guard's tag source;
- recording any release-state disposition for Phase 298's versions;
- editing any Shadow Genome event other than the LD-10 event;
- inferring remote publication through network access in unit tests;
- reconstructing uncertain historical publication state from incomplete evidence;
- changing semantic-version calculation;
- broad lifecycle redesign;
- unrelated repository cleanup.
