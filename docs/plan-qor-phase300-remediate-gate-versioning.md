# Plan: Phase 300 - A second remediation proposal no longer destroys the first

**change_class**: hotfix

**doc_tier**: standard

**terms**: `[]` (this plan introduces no new term; the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: `remediate.json` still holds only the newest proposal, so a review that cites `remediate.json` finds the newest proposal at that path; a superseded proposal is readable, byte for byte, in its own `remediate-iter<N>.json` (LD-5); `emit` writes no provenance sidecar for either file, as at the base (LD-5); two concurrent `emit` calls in one session are not serialized (LD-5)
- non_goals: routing `emit` through `gate_chain.write_gate_artifact`; changing `emit`'s return value, the remediate schema, `/qor-remediate` or `/qor-audit` skill text, `remediate_attestation` or `remediate_mark_addressed`; recovering a proposal overwritten before this fix; release publication
- exclusions: gate files already on disk or in history, which this plan neither rewrites nor migrates (LD-5)

**iteration**: 1 (on branch `phase/300-remediate-gate-versioning`)

**Issue**: GH #446 ("remediate_emit_gate overwrites a previously audited proposal; the remediation path is the only gate writer without versioning")

**Current base**: `25002459b02c21e1067454fded55f47f2de967f1` (`main` after Phase 299 merged; project version `0.175.3`, sealed at META_LEDGER #825)

**Target version**: `0.175.4` (hotfix bump from `0.175.3`)

**Provenance**: the code and tests below are carried, with the deviations declared in LD-7, from the candidate branch `phase/292-remediate-gate-versioning`, head `878c38b3c7bbe5801501ab39f5d6f670205894d2` (PR #494). Relative to its merge base with the current base, `15729311f9f4d55d5dad2db004b972415c39432c`, the candidate changes exactly three files: `git diff --stat 15729311f9f4d55d5dad2db004b972415c39432c 878c38b3c7bbe5801501ab39f5d6f670205894d2` lists `docs/plan-qor-phase292-remediate-gate-versioning.md`, `qor/scripts/remediate_emit_gate.py` and `tests/test_remediate.py` and ends `3 files changed, 244 insertions(+), 8 deletions(-)`. It therefore adds no gate artifact, intent lock, ledger entry, seal, CHANGELOG entry or version change. Its phase number is not canonical on `main`: Phase 292 is already sealed there by a different plan (META_LEDGER Entry #801, `v0.174.3`, LD-11). `git merge-base --is-ancestor 878c38b3c7bbe5801501ab39f5d6f670205894d2 25002459b02c21e1067454fded55f47f2de967f1` exits 1. The candidate is reference and ancestry only; it is not audit, implementation or seal authority. The PR #494 owner direction is to carry only the GH #446 fix and test intent onto current `main` without widening scope; this plan does that and adds only the release-state continuity and CHANGELOG note that every sealed hotfix in this train carries (Phase 3). Every claim below is re-derived at the current base; the candidate plan's own citations are not relied on (one of them, the `tests/test_remediate.py` line it gives for the `s-req-rp` fixture, does not reproduce at the current base, LD-3).

**Base currency of the ported files**: `git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 25002459b02c21e1067454fded55f47f2de967f1 -- qor/scripts/remediate_emit_gate.py tests/test_remediate.py qor/scripts/validate_gate_artifact.py qor/scripts/gate_chain.py qor/scripts/remediate_attestation.py qor/scripts/remediate_mark_addressed.py qor/scripts/gate_provenance.py qor/skills/sdlc/qor-remediate/SKILL.md` prints nothing, so the two files the candidate edits and every module or skill this plan relies on are byte-identical at the candidate's merge base and at the current base. `qor/gates/chain.md` differs between the two revisions only in line 20 (the Phase 299 session-marker sentence), which this plan does not rely on.

**Citation currency**: every `git show` evidence statement below cites `25002459b02c21e1067454fded55f47f2de967f1` and was re-executed against it while authoring (one observed line per statement, 0 mismatches). Each statement's pattern is written exactly as it is run: the patterns use `.` in place of regex metacharacters, so no statement depends on a backslash escape. The other command outputs quoted (`git diff`, `git grep`, `git ls-tree`, `git merge-base`, scratch runs) were observed on 2026-09-28. Scratch runs used a clone of the base outside the repository, with the Phase 1 test edits, the Phase 2 code and the Phase 3 edits applied exactly as specified below.

## Open Questions

None.

## Problem

`remediate_emit_gate.emit` writes each remediation proposal to one fixed file, `.qor/gates/<sid>/remediate.json`, through a temporary file and `os.replace`. A second proposal in the same session replaces the first. Revising a proposal after a VETO is the expected remediation cycle (Entry #748 calls it "propose, VETO, revise"), so the replaced proposal can be one a reviewer already audited. A gate artifact written through `gate_chain.write_gate_artifact` lands in its own `<phase>-iter<N>.json` beside the latest copy (LD-1); `emit` does not.

The defect has one recorded instance on `main`. META_LEDGER Entry #748 (a GATE TRIBUNAL VETO of a remediation proposal) carries an "Artifact-integrity disclosure, added after the fact" (line 21758 at the base; the line carries inline code spans and is quoted in part): the audited proposal "no longer exists at the cited path", because `emit` "writes to a fixed `remediate.json`", the superseding proposal "overwrote the audited one, which had never been committed and is unrecoverable", and the content hash that entry records "is now unverifiable against any file".

Reproduction at the base (scratch clone, Phase 1 test edits applied, base `remediate_emit_gate.py`): `python -B -m pytest tests/test_remediate.py -q` gives `4 failed, 32 passed`. The four failures are the four Phase 1 tests: the base writes no `remediate-iter*.json` file, so after two emissions only the second proposal exists anywhere in the session directory.

## Locked Decisions

### LD-1: the defect is a fixed write target with no iteration

At the base, `emit` computes one fixed path, replaces it, and returns it:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/remediate_emit_gate.py | grep -nE 'out_path = out_dir / "remediate.json"'` -> `42:    out_path = out_dir / "remediate.json"`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/remediate_emit_gate.py | grep -nE 'os.replace.tmp_path, out_path.'` -> `53:    os.replace(tmp_path, out_path)`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/remediate_emit_gate.py | grep -nE 'return out_path'` -> `54:    return out_path`

The recorded instance is Entry #748:

`git show 25002459b02c21e1067454fded55f47f2de967f1:docs/META_LEDGER.md | grep -nE '^### Entry #748'` -> `21724:### Entry #748: GATE TRIBUNAL -- remediation proposal review, Phase 265 cluster (VETO)`

Line 21758 of the same file, inside Entry #748, is the disclosure quoted in `## Problem`.

The other gate phases write through `validate_gate_artifact.write_artifact`, which writes a new versioned file, then the singleton, and returns the versioned path:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE '^    versioned = next_iteration_path'` -> `199:    versioned = next_iteration_path(phase, session_dir)`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE '_atomic_write.session_dir / f'` -> `206:    _atomic_write(session_dir / f"{phase}.json", text)`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE '^    return versioned$'` -> `207:    return versioned`

`gate_chain.write_gate_artifact` delegates to it:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/gate_chain.py | grep -nE 'path = vga.write_artifact.phase, payload, session_id=sid.'` -> `297:    path = vga.write_artifact(phase, payload, session_id=sid)`

Decision: `emit` also writes each proposal to its own versioned file before it refreshes `remediate.json`.

### LD-2: reuse `next_iteration_path`; the numbering is shared with `write_gate_artifact`

The next free versioned path is already computed by one phase-parameterized function:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE 'def next_iteration_path'` -> `169:def next_iteration_path(phase: str, session_dir: Path) -> Path:`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE 'iter._max_iteration'` -> `171:    return session_dir / f"{phase}-iter{_max_iteration(phase, session_dir) + 1}.json"`

It numbers after the highest existing iteration, not after the count of files:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE 'def _max_iteration'` -> `145:def _max_iteration(phase: str, session_dir: Path) -> int:`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE 'best = max.best, int.match.group.1'` -> `153:                best = max(best, int(match.group(1)))`

Gaps are real. A tracked session on `main` holds remediate iterations 1 to 4 and 6, each with a `.provenance` sidecar, which `emit` never writes: `git ls-tree --name-only 25002459b02c21e1067454fded55f47f2de967f1 .qor/gates/2026-08-12T0214-799d77/` lists `remediate-iter1.json`, `remediate-iter2.json`, `remediate-iter3.json`, `remediate-iter4.json`, `remediate-iter6.json`, `remediate.json`, and a `.provenance` file beside each of them, twelve remediate entries in all. A counter based on the number of files would give 6 there and overwrite `remediate-iter6.json`; `next_iteration_path` gives 7. Because `emit` uses the same function with the phase name `"remediate"`, an `emit` call and a `write_gate_artifact(phase="remediate", ...)` call in one session draw from one sequence and never pick the same free number one after the other.

Decision: `emit` calls `next_iteration_path("remediate", out_dir)`; no second counter is written. The import adds no cycle: from the `qor` package, `validate_gate_artifact` imports only `session`, `resources` and `workdir`, and nothing under `qor/` imports `remediate_emit_gate` (`git grep -n 'remediate_emit_gate' 25002459b02c21e1067454fded55f47f2de967f1 -- '*.py'` prints only four lines, all in `tests/test_remediate.py` and `tests/test_security_fixes.py`):

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE '^from qor.scripts import session'` -> `18:from qor.scripts import session`

The skill imports the module flat (`import remediate_emit_gate as reg`); the new `from qor.scripts.validate_gate_artifact import next_iteration_path` needs the `qor` package importable, which the base module already requires (`from qor import workdir as _workdir`, line 26 at the base). `jsonschema`, which `validate_gate_artifact` imports, is a declared runtime dependency (`pyproject.toml` line 25 at the base).

### LD-3: `remediate.json` keeps its path and `emit` keeps its return value

Consumers name the fixed singleton. The skill declares it as its gate output, calls `emit`, and passes the singleton to the review-pass flip:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/skills/sdlc/qor-remediate/SKILL.md | grep -nE 'gate_writes: '` -> `13:gate_writes: .qor/gates/<session_id>/remediate.json`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/skills/sdlc/qor-remediate/SKILL.md | grep -nE 'path = reg.emit.proposal, session_id=sid.'` -> `119:path = reg.emit(proposal, session_id=sid)`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/skills/sdlc/qor-remediate/SKILL.md | grep -nE 'remediate_gate_path=".qor/gates/<sid>/remediate.json",'` -> `134:    remediate_gate_path=".qor/gates/<sid>/remediate.json",`

The review-pass attestation compares paths, so the path the audit declared must still name a file the operator can pass:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/remediate_attestation.py | grep -nE 'if Path.declared_gate..resolve.. != Path.remediate_gate_path..resolve..:'` -> `178:    if Path(declared_gate).resolve() != Path(remediate_gate_path).resolve():`

The existing tests pin the returned path and pass the singleton path to `mark_addressed`:

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_remediate.py | grep -nE 'expected = tmp_path / ".qor" / "gates" / "gate-session-1" / "remediate.json"'` -> `297:    expected = tmp_path / ".qor" / "gates" / "gate-session-1" / "remediate.json"`

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_remediate.py | grep -nE 'remediate_gate = tmp_path / ".qor" / "gates" / "s-req-rp" / "remediate.json"'` -> `362:    remediate_gate = tmp_path / ".qor" / "gates" / "s-req-rp" / "remediate.json"`

The current-session validator reads the singleton by name:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/validate_gate_artifact.py | grep -nE 'artifact = session_dir / f'` -> `130:        artifact = session_dir / f"{phase}.json"`

Decision: `emit` writes the proposal text once to the versioned path and then the same text to `remediate.json`, and returns `remediate.json` as before. `write_artifact` returns the versioned path because its callers bind provenance to it; `emit` has no such caller, and changing its return value would change what the skill hands to the review step. The singleton therefore stays the newest proposal, byte-identical to the newest iteration that `emit` wrote.

### LD-4: the other readers of gate files are unaffected

- Generic resolution picks the highest iteration, with the singleton as fallback. For `remediate`, the highest iteration and the singleton hold the same bytes after either writer runs, because both write the iteration and then the singleton:

  `git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/gate_chain.py | grep -nE 'path = vga.latest_artifact_path.phase, vga.GATES_DIR / sid.'` -> `208:    path = vga.latest_artifact_path(phase, vga.GATES_DIR / sid)`

- The active-phase reporter reads the `phase` field of the newest `*.json` file in the session directory; `emit` writes the iteration file and the singleton from one text, so whichever is newer gives the same answer as the singleton alone did at the base:

  `git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/active_phase.py | grep -nE 'newest = max.candidates'` -> `27:    newest = max(candidates, key=lambda p: p.stat().st_mtime)`

- The status snapshot does not read `remediate` at all:

  `git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/snapshot_export.py | grep -nE '^_PHASES = '` -> `45:_PHASES = ("research", "plan", "audit", "implement", "substantiate")`

- Provenance verification skips a gate file that has no sidecar, and `emit` writes none, so a new `remediate-iter<N>.json` from `emit` adds no finding:

  `git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/gate_provenance.py | grep -nE 'if not sidecar_path.art..is_file..:'` -> `251:        if not sidecar_path(art).is_file():`

- Session liveness (Phase 299) matches exact file names, none of which is a remediate file, so a session directory holding only `remediate.json` and `remediate-iter1.json` still rotates a stale marker:

  `git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/session.py | grep -nE '_GATE_PHASE_ARTIFACTS = '` -> `63:_GATE_PHASE_ARTIFACTS = ("ideation.json", "research.json", "plan.json", "audit.json", "implement.json")`

  Observed in the scratch clone with the Phase 2 code: after one `emit` into a session whose marker is 25 h old, the directory holds `remediate-iter1.json` and `remediate.json`, and `session.current(marker=...)` returns `None`. `tests/test_session_marker_staleness.py` passes unchanged (Phase 2).

### LD-5: residuals and limits of the fix

- GH #446 suggests that a superseded proposal stay readable "at the path its tribunal cited". This plan meets that when the review cites the iteration file. A review that cites `remediate.json`, the path the skill documents and `emit` returns (LD-3), finds the newest proposal there after a later emission; the superseded proposal's exact bytes are in its own `remediate-iter<N>.json`, where any hash computed over the file bytes can be checked again. Pointing reviews at the iteration path would change `emit`'s return value, the `/qor-remediate` Step 5 and Step 6 text, its six compiled copies and the `mark_addressed` call contract; that is wider than the GH #446 fix and is left out (Non-goals).
- `emit` writes no provenance sidecar, before or after this fix. In a session where `write_gate_artifact(phase="remediate", ...)` also wrote `remediate.provenance`, a later `emit` refreshes `remediate.json` without refreshing that sidecar. The base has the same behavior, since it overwrites `remediate.json` too; this plan does not change it.
- `next_iteration_path` followed by the write is not atomic. Two `emit` calls running at the same moment in one session could pick the same number, and the later write would replace the earlier. The base loses one of the two proposals in the same case; the check-then-write in `write_artifact` has the same window.
- A proposal overwritten before this fix is not recovered, including the Entry #748 proposal. No gate file on disk or in history is rewritten or migrated.

### LD-6: documentation surfaces stay true without edits

The normative statements about the remediation gate file at the base are exactly these (`git grep -n -e 'remediate[.]json' -e 'remediate-iter' 25002459b02c21e1067454fded55f47f2de967f1 -- qor/skills qor/gates qor/references qor/scripts docs/lifecycle.md docs/operations.md docs/architecture.md README.md` prints ten lines): `qor/gates/chain.md` line 41, `qor/gates/schema/audit.schema.json` line 23, `qor/references/doctrine-governance-enforcement.md` lines 218 and 230, `qor/scripts/remediate_emit_gate.py` lines 2, 34 and 42, and `qor/skills/sdlc/qor-remediate/SKILL.md` lines 13, 122 and 134. Each still holds after Phase 2: `emit` still writes `remediate.json` (chain.md line 41's output column, the module docstring lines 2 and 34, skill lines 13 and 122), the review signal still names a remediate gate path (doctrine lines 218 and 230, schema line 23), and skill line 134 still passes a path that exists. Line 42 is the code line Phase 2 keeps.

The general rule at `qor/gates/chain.md` line 16 ("Runtime:" names `<phase>-iter<N>.json`, immutable, one per emission, plus `<phase>.json` as the latest copy; the line carries inline code spans and is paraphrased) was false for `remediate` at the base and becomes true with this fix; `docs/lifecycle.md` line 15 states the same rule. `qor/gates/chain.md` line 24 scopes its iteration-versioning paragraph, including the sidecar sentence on line 27, to "Every emission through `write_gate_artifact`" (quoted in part), which `emit` is not. No documentation file, skill or compiled variant changes, so `check_variant_drift.py` is unaffected.

### LD-7: fidelity to the candidate, with every deviation declared

`qor/scripts/remediate_emit_gate.py` after Phase 2 equals the candidate head `878c38b3c7bbe5801501ab39f5d6f670205894d2` byte for byte. `tests/test_remediate.py` after Phase 1 equals the candidate except for exactly these deviations:

1. `test_emit_gate_second_proposal_does_not_destroy_first` reads the bytes of `remediate.json` after the first emission (the bytes a reviewer of that proposal would have hashed) and, after the second emission, asserts that one of the `remediate-iter*.json` files holds exactly those bytes. To do this it defines `session_dir` before the two `emit` calls and globs `versioned = sorted(session_dir.glob("remediate-iter*.json"))` once. The candidate asserted only that the proposal text is recoverable, and its three tests stay green when `emit` writes the singleton with different bytes (M6 below; observed `35 passed` with the candidate's test file under M6).
2. `test_emit_gate_singleton_still_written_as_latest_copy` asserts that `remediate.json` and `remediate-iter2.json` hold identical bytes. The candidate's docstring claims byte identity but its body checks only `proposal_text`. With this assertion the test is RED at the base (no `remediate-iter2.json`), where the candidate's version was GREEN.
3. `test_emit_gate_numbers_after_highest_existing_iteration` is added. Without it no test fails when the next number is derived from the count of iteration files (M3 below; observed `35 passed` with the candidate's test file under M3), which is the failure mode the LD-2 gap would expose.

The candidate plan text is not carried; this plan replaces it. The candidate's code is not otherwise changed: `emit`, `_atomic_write` and the new import are the candidate's.

The tests use only `tmp_path`, write fixed content, never sleep, use no network, and assert no live repository state. The `ts` field is set from the clock, but every byte comparison is between files written by the same `emit` call from one text, so the clock cannot make them differ. The 36-item file was observed green twice in a row with the Phase 2 code (`36 passed`, twice).

The implementer writes the Phase 1 tests first and the Phase 2 code second. No file is checked out, copied or cherry-picked from the candidate branch as a substitute for that sequence; the Phase 2 fidelity check compares the result with the candidate afterwards.

### LD-8: version target is 0.175.4

`git show 25002459b02c21e1067454fded55f47f2de967f1:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.3"`

`git show 25002459b02c21e1067454fded55f47f2de967f1:CHANGELOG.md | grep -nE '^## .0.175.3. - '` -> `13:## [0.175.3] - 2026-09-28`

`git show 25002459b02c21e1067454fded55f47f2de967f1:docs/META_LEDGER.md | grep -nE '^### Entry #825'` -> `24359:### Entry #825: SESSION SEAL -- Phase 299 stale session marker keeps its gate chain (v0.175.3)`

`change_class: hotfix` bumps `0.175.3` to `0.175.4` at `/qor-substantiate`.

### LD-9: CHANGELOG Unreleased note

`/qor-implement` writes the user-facing note under `## [Unreleased]`; the seal stamps it and refuses an empty section:

`git show 25002459b02c21e1067454fded55f47f2de967f1:CHANGELOG.md | grep -nE '^## .Unreleased.'` -> `11:## [Unreleased]`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

Line 14 continues line 13, which opens the `/qor-implement` rule for `## [Unreleased]`; lines 14 to 16 exclude internal refactors, ledger entry numbers and hash values from the CHANGELOG. Line 32 continues line 31, the rule that an empty `Unreleased` section raises `ValueError` at the stamp. Line 9 allows `Fixed` as a subsection label. (Lines 9, 13, 16 and 31 carry inline code spans and are paraphrased.)

The note is one `### Fixed` bullet with exactly this text:

```markdown
- **Phase 300 (hotfix; a second remediation proposal no longer destroys the first, GH #446)**: `/qor-remediate` Step 5 wrote every proposal to the same `.qor/gates/<sid>/remediate.json`, so a second proposal in a session overwrote the first, including one that had already been reviewed. Each proposal is now also written to its own `.qor/gates/<sid>/remediate-iter<N>.json`, where N is one more than the highest existing iteration in that session, so an existing iteration file is never overwritten, and a superseded proposal stays readable, byte for byte, in its own iteration file. `remediate.json` keeps its path and is refreshed with the same bytes as the newest iteration, and the Step 5 call still returns that path, so readers of `remediate.json` keep working and see the newest proposal there. A proposal overwritten before this fix is not recovered. `docs/release-state.json` records `0.175.3` as `sealed_unpublished`.
```

It is ASCII only and states only what Phase 2 implements. Its only `#` number is the issue reference `GH #446`; it carries no ledger entry number and no hash value; it names no private helper; `/qor-remediate` Step 5 and `.qor/gates/<sid>/` paths are the operator-facing surface. Clause to proof:

- each proposal also goes to its own iteration file, numbered after the highest existing iteration, and no existing iteration is overwritten: LD-2, `test_emit_gate_versioned_paths_never_reused`, `test_emit_gate_numbers_after_highest_existing_iteration`;
- a superseded proposal stays readable byte for byte: `test_emit_gate_second_proposal_does_not_destroy_first`;
- `remediate.json` keeps its path, holds the newest iteration's bytes, and is still returned: LD-3, `test_emit_gate_singleton_still_written_as_latest_copy`, `test_emit_gate_writes_json_at_expected_path`;
- readers of `remediate.json` keep working: LD-3, LD-4, the unchanged `mark_addressed` tests in `tests/test_remediate.py`;
- earlier losses are not recovered: LD-5;
- the release-state record: LD-10.

Its last sentence has the form of the sealed Phase 299 bullet, whose line 18 in `CHANGELOG.md` at the base ends "`docs/release-state.json` records `0.175.2` as `sealed_unpublished`." (quoted in part, because the line carries inline code spans).

### LD-10: release-state continuity for 0.175.3

Once the seal bumps the project version to `0.175.4`, `0.175.3` stops being the implicit candidate, and the coverage rule treats it as an orphan unless a reachable tag or a disposition covers it:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set.exceptions. - .project_version.'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/release_state.py | grep -nE 'if _semver.v. <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.3` has no release tag on the remote. At the base, `grep -n` for the sentence "No remote tag is created; the seal tag stays local." over `docs/META_LEDGER.md` prints lines 24134, 24228 and 24381; line 24381 is the `**Version**:` line of Entry #825 (the other two are Entries #814 and #818). While authoring, `git ls-remote --tags origin` listed no `v0.173` or later tag; the highest remote tag was `v0.172.2` (observation, 2026-09-28; not a test expectation).

The record at the base ends with `0.175.2` and has no `0.175.3` entry:

`git show 25002459b02c21e1067454fded55f47f2de967f1:docs/release-state.json | grep -nE '"version": "0.175.(2|3)"'` -> `75:      "version": "0.175.2",`

This phase appends exactly one entry after the `0.175.2` entry, mirroring how Phase 299 recorded `0.175.2`:

- `version`: `0.175.3`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #825); no release tag was pushed to the remote, so the version is sealed but not published.`

The immediate precedent:

`git show 25002459b02c21e1067454fded55f47f2de967f1:docs/release-state.json | grep -nE 'META_LEDGER #818'` -> `77:      "reason": "Sealed by /qor-substantiate (META_LEDGER #818); no release tag was pushed to the remote, so the version is sealed but not published."`

The changelog rule that excludes ledger entry numbers (LD-9) governs `CHANGELOG.md`, not this record; `qor/references/doctrine-changelog.md` lines 78 and 79 give the record's closed shape (each entry exactly `version`, `state`, `reason`), and lines 91 to 93 make every state an operator-asserted disposition whose validator checks the shape and the dated CHANGELOG section (cited in prose; the lines carry inline code spans). `0.175.3` has a dated section (LD-8), which the validator requires:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.3` is reachable from the base in a local checkout (`git merge-base --is-ancestor v0.175.3 25002459b02c21e1067454fded55f47f2de967f1` exits 0). It is not on the remote, so CI does not see it, and it does not void the disposition:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.3` locally, the plain local tag-coverage run cannot tell whether the entry is present. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 3): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. The suite consumes the live record:

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state.RELEASE_STATE, versions.'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The rule the entry relies on is already unit-tested:

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show 25002459b02c21e1067454fded55f47f2de967f1:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 3), not written by hand at seal time. No entry is recorded for `0.175.4`: after the seal it is the implicit candidate. No ledger entry, seal, gate artifact or dated CHANGELOG section is edited.

### LD-11: canonical governance shape

This file is the canonical `docs/plan-qor-phase300-*.md` plan on branch `phase/300-remediate-gate-versioning`:

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/governance_helpers.py | grep -nE '_BRANCH_PHASE_RE ='` -> `23:_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")`

`git show 25002459b02c21e1067454fded55f47f2de967f1:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase.nn'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

Phase 292 on `main` is a different, sealed phase:

`git show 25002459b02c21e1067454fded55f47f2de967f1:docs/META_LEDGER.md | grep -nE '^### Entry #801'` -> `23849:### Entry #801: SESSION SEAL -- Phase 292 escalation origin signature promotion (v0.174.3)`

so the candidate's `phase/292-` branch cannot carry this work canonically, and it is renumbered 300. The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored.

## Feature Inventory Touches

Empty. This plan changes a governance gate writer and its tests; it introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_remediate.py` - three candidate tests with deviations 1 and 2, and one added test (LD-7), in the `remediate_emit_gate` block after `test_emit_gate_writes_json_at_expected_path`.

### Changes

Insert the four tests below between `test_emit_gate_writes_json_at_expected_path` and `test_emit_gate_payload_roundtrips`. Each calls `reg.emit(..., base_dir=tmp_path)` with its own session id and reads files under `tmp_path / ".qor" / "gates" / <sid>`. The file then collects 36 items.

### Unit Tests

- `tests/test_remediate.py::test_emit_gate_second_proposal_does_not_destroy_first` - emits proposal A, reads the bytes of `remediate.json`, emits proposal B in the same session; asserts both proposal texts appear among the `remediate-iter*.json` files and that one of those files holds exactly the bytes read after A. RED at the base (only B exists); discriminates M1, M2, M4 and M6.
- `tests/test_remediate.py::test_emit_gate_versioned_paths_never_reused` - three emissions in one session; asserts the iteration files are exactly `remediate-iter1.json`, `remediate-iter2.json`, `remediate-iter3.json`. RED at the base; discriminates M1 and M2.
- `tests/test_remediate.py::test_emit_gate_singleton_still_written_as_latest_copy` - two emissions; asserts `emit` returns `.../remediate.json`, that file holds the second proposal, and its bytes equal `remediate-iter2.json`. RED at the base (no iteration file); discriminates M1, M2, M4, M5 and M6.
- `tests/test_remediate.py::test_emit_gate_numbers_after_highest_existing_iteration` (added; LD-7 deviation 3) - the session directory already holds `remediate-iter1.json` and `remediate-iter3.json` with fixed bytes; one emission; asserts both files keep their bytes, the iteration files are exactly iterations 1, 3 and 4, and `remediate-iter4.json` holds the new proposal. RED at the base; discriminates M1, M2 and M3.

TDD: the four tests are observed RED before Phase 2 (`4 failed, 32 passed` at the base). The existing `test_emit_gate_writes_json_at_expected_path` and `test_emit_gate_payload_roundtrips` stay GREEN before and after (regression coverage: the return value and payload shape the fix must keep). Discrimination is proven after Phase 2 by local, uncommitted mutations of `qor/scripts/remediate_emit_gate.py`, each run with `python -B -m pytest tests/test_remediate.py -q` and then reverted:

- M1: delete `_atomic_write(versioned_path, text)` -> the four Phase 1 tests FAIL.
- M2: replace `next_iteration_path("remediate", out_dir)` with `out_dir / "remediate-iter1.json"` -> the four Phase 1 tests FAIL.
- M3: replace `next_iteration_path("remediate", out_dir)` with `out_dir / f"remediate-iter{len(list(out_dir.glob('remediate-iter*.json'))) + 1}.json"` -> `test_emit_gate_numbers_after_highest_existing_iteration` FAILS.
- M4: delete `_atomic_write(out_path, text)` -> `test_emit_gate_writes_json_at_expected_path`, `test_emit_gate_second_proposal_does_not_destroy_first`, `test_emit_gate_singleton_still_written_as_latest_copy` and `test_emit_gate_payload_roundtrips` FAIL.
- M5: return `versioned_path` instead of `out_path` -> `test_emit_gate_writes_json_at_expected_path` and `test_emit_gate_singleton_still_written_as_latest_copy` FAIL.
- M6: write the singleton with `json.dumps(payload, indent=2, sort_keys=True) + "\n"` instead of `text` -> `test_emit_gate_second_proposal_does_not_destroy_first` and `test_emit_gate_singleton_still_written_as_latest_copy` FAIL.

Observed in the scratch clone with the Phase 2 code and the 36-item file: M1 `4 failed, 32 passed`; M2 `4 failed, 32 passed`; M3 `1 failed, 35 passed`; M4 `4 failed, 32 passed`; M5 `2 failed, 34 passed`; M6 `2 failed, 34 passed`. Each failing set is exactly the one named above. With the candidate's test file instead, M3 and M6 each give `35 passed` (LD-7 deviations 1 and 3). After each mutation the implementer restores the Phase 2 content, re-runs the Phase 2 fidelity check to confirm no mutation remains, and runs the file twice GREEN.

## Phase 2: Versioned emission

### Affected Files

- `qor/scripts/remediate_emit_gate.py` - import `next_iteration_path`; add `_atomic_write`; `emit` writes the versioned file, then the singleton; docstring of `emit`.

### Changes

- Below `from qor import workdir as _workdir`, add `from qor.scripts.validate_gate_artifact import next_iteration_path`.
- Add `_atomic_write(target: Path, text: str) -> None`: `tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False, suffix=".tmp")`, write `text`, then `os.replace(tmp_path, target)`.
- In `emit`, after `payload["ts"]` is set: `text = json.dumps(payload, indent=2, sort_keys=False) + "\n"`; `versioned_path = next_iteration_path("remediate", out_dir)`; `_atomic_write(versioned_path, text)`; `_atomic_write(out_path, text)`; `return out_path`. The base's inline temporary-file block is removed. `validate_session_id`, the directory creation and `out_path` are unchanged.
- The `emit` docstring is the candidate's: it keeps its first line, says it returns the singleton path, and adds a GH #446 paragraph on the versioned copy, the shared pattern with `write_gate_artifact`, and the unchanged singleton path and return value.

The bytes written are the base's bytes: `json.dump(payload, tf, indent=2, sort_keys=False)` followed by `"\n"` at the base equals `json.dumps(payload, indent=2, sort_keys=False) + "\n"`.

### Unit Tests

- Re-run `tests/test_remediate.py` after the edit: all 36 items GREEN, twice in a row.
- Run mutations M1-M6 (Phase 1) and observe each named failure; revert.
- The consumers named in LD-3 and LD-4 stay GREEN unchanged: `python -m pytest tests/test_security_fixes.py tests/test_sg_closure_enforcement.py tests/test_remediate_enforcer_edges.py tests/test_remediate_per_event_enforcers.py tests/test_session_marker_staleness.py tests/test_gates.py -q` (observed in the scratch clone with Phase 2 applied: `100 passed`).
- Full suite: `python -m pytest tests/ -q` stays GREEN (observed in the scratch clone with Phases 1 to 3 applied: `3615 passed, 3 skipped, 4 deselected`); `python -m ruff check qor/ tests/` prints `All checks passed!`, and `python -m qor.scripts.publication_boundary_lint --repo-root .` reports `0 finding(s)`.
- Fidelity check (LD-7), after `git fetch origin phase/292-remediate-gate-versioning`: `git diff 878c38b3c7bbe5801501ab39f5d6f670205894d2 -- qor/scripts/remediate_emit_gate.py` prints nothing, and `git diff 878c38b3c7bbe5801501ab39f5d6f670205894d2 -- ./tests/test_remediate.py` shows only deviations 1 to 3. The implementer records the observed diff summary in the implementation report.

## Phase 3: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.3` `sealed_unpublished` entry (LD-10).
- `CHANGELOG.md` - the Phase 300 bullet under `## [Unreleased]` (LD-9). No dated section is edited.

### Changes

Append the LD-10 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-9 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.4]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-10).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` and `python -m pytest tests/test_changelog_format.py -q` stay GREEN (observed in the scratch clone with both Phase 3 edits applied: `34 passed` for the three files together).
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.4`, remote tags only). At the base, before the entry exists, it prints `{'0.175.3'} {'0.175.3'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.3'}`: no orphan with the entry, exactly `{'0.175.3'}` with the entry removed in memory. That shows the entry is what keeps coverage green (observed in the scratch clone).
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.4` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.3` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in a scratch clone of the base outside the repository with `origin` set to the real remote and `TMPDIR` inside the scratch area; the simulated commits never entered this repository):
  - base commit (`version = "0.175.3"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.4 (project version 0.175.3)`;
  - a commit that bumps `version` to `0.175.4` without the `[0.175.4]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.4 (project version 0.175.4)`;
  - simulated seal commit (`version = "0.175.4"`, `## [0.175.4] - ` section, local `v0.175.4` tag), no `0.175.3` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.3`;
  - the same seal commit with the LD-10 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: a second remediation proposal no longer destroys the first

- **D1**: every `emit` call writes the proposal to a new `.qor/gates/<sid>/remediate-iter<N>.json`, N being one more than the highest existing remediate iteration in that directory, then refreshes `.qor/gates/<sid>/remediate.json` with the same bytes, and returns the `remediate.json` path. No existing iteration file is overwritten by a sequential `emit`. The LD-5 residuals are declared.
- **D2**: `qor/scripts/remediate_emit_gate.py` imports `next_iteration_path` from `qor.scripts.validate_gate_artifact`, defines `_atomic_write(target: Path, text: str) -> None`, and keeps `emit(proposal: dict, session_id: str, base_dir: Path | None = None) -> Path` and `validate_session_id` unchanged in signature. The Phase 2 fidelity check shows no diff to the candidate for the module and only LD-7 deviations 1 to 3 for the test file.
- **D3**: no documentation, skill, schema or compiled variant changes (LD-6). Phase 300 follows canonical branch and plan resolution and receives current-revision audit and substantiation evidence before promotion; no evidence from the candidate branch is reused as authority. The `## [Unreleased]` bullet carries exactly the LD-9 text at implement time.
- **D4**: the four Phase 1 tests are RED before Phase 2 and GREEN after (`4 failed, 32 passed` at the base; `36 passed` twice after). Each mutation M1-M6 turns exactly its named tests RED. The LD-3 and LD-4 consumer tests stay GREEN.

### Deliverable: release-state continuity for 0.175.3

- **D1**: after the Phase 300 seal bumps the project version to `0.175.4`, `0.175.3` (sealed on `main` at META_LEDGER #825, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.3` / `sealed_unpublished` with the LD-10 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.3` to `0.175.4` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.3'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.4` with a dated `[0.175.4]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_remediate.py -q` - verifies versioned emission, byte recovery of a superseded proposal, numbering after the highest iteration, and the unchanged singleton path and return value (36 test items).
- `python -m pytest tests/test_security_fixes.py tests/test_sg_closure_enforcement.py tests/test_remediate_enforcer_edges.py tests/test_remediate_per_event_enforcers.py tests/test_session_marker_staleness.py tests/test_gates.py -q` - verifies the consumers of the remediate gate file and the session-liveness rule are unchanged.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-9 bullet keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.4'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.4', ex).orphans, rs.coverage_violations(versions, tags, '0.175.4', {k: v for k, v in ex.items() if k != '0.175.3'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.3'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.4' and '## [0.175.4] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.4 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.4`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed module and test file.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the publication-boundary surface remains clean.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.
- `python -m qor.scripts.dependency_admission_lint` - PR Dependency Review admission steps; no dependency or lockfile changes in this plan.
- `python qor/scripts/check_variant_drift.py` - no skill or compiled variant changes in this plan (LD-6).

## Non-goals

- routing `emit` through `gate_chain.write_gate_artifact` or the remediate schema, or reconciling the proposal fields with that schema;
- changing `emit`'s return value, or pointing `/qor-remediate` Step 5 or Step 6, `/qor-audit` `reviews-remediate:` or `mark_addressed` at the iteration path (LD-5);
- provenance sidecars for `emit`-written files, and refreshing a `remediate.provenance` written by another writer (LD-5);
- serializing concurrent `emit` calls (LD-5);
- recovering or migrating any proposal or gate file written before this fix, including the Entry #748 proposal;
- documentation, skill, schema or compiled-variant edits (LD-6);
- release-state dispositions for any version other than `0.175.3`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- reusing any evidence from the candidate branch as audit, implementation or seal authority;
- hand-issuing governance evidence;
- unrelated repository cleanup.
