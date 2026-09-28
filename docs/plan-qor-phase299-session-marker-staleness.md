# Plan: Phase 299 - Keep a stale but live session marker bound to its gate chain

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: a stale marker is kept only while its own session directory holds `research.json`, `plan.json`, `audit.json` or `implement.json` and no `substantiate.json`; an abandoned unsealed session therefore stays current until an operator ends or rotates it (LD-5)
- non_goals: session identity redesign, TTL policy change, gate-chain resolver changes, release publication
- exclusions: sessions whose marker content does not match `SESSION_ID_PATTERN` (they rotate as before)

**iteration**: 1 (on branch `phase/299-session-marker-staleness`)

**Issue**: GH #483 ("A cycle spanning a day boundary loses its session marker, and the recovery path orphans the gate chain")

**Current base**: `8ee9d98aad71f059b69231aa370fdbae6bfe52d4` (`main` after Phase 298 merged; project version `0.175.2`, sealed at META_LEDGER #818)

**Target version**: `0.175.3` (hotfix bump from `0.175.2`)

**Provenance**: the code, tests and lifecycle wording below are carried from the candidate branch `fix/483-session-marker-current`, head `5f8be1e2b325825a022172bc3d2b23697eaa1d30`. That branch is non-canonical (not a `phase/<NN>-` branch; its plan `docs/plan-session-marker-staleness-current.md` is not a `plan-qor-phase<NN>*.md` file), so Qor's resolver cannot audit it. Relative to its merge base `15729311f9f4d55d5dad2db004b972415c39432c` the branch changes exactly four files and nothing else: `git diff --stat 15729311f9f4d55d5dad2db004b972415c39432c 5f8be1e2b325825a022172bc3d2b23697eaa1d30` lists `docs/lifecycle.md`, `docs/plan-session-marker-staleness-current.md`, `qor/scripts/session.py` and `tests/test_session_marker_staleness.py` and ends `4 files changed, 250 insertions(+), 7 deletions(-)`. It therefore carries no gate artifact, intent lock, ledger entry, seal or version change for this work. It is reference and ancestry only; it is not audit, implementation or seal authority. `git merge-base --is-ancestor 5f8be1e2b325825a022172bc3d2b23697eaa1d30 8ee9d98aad71f059b69231aa370fdbae6bfe52d4` exits 1. The candidate plan describes earlier review of the same semantics; this plan does not rely on that description, and every claim below is re-derived at the current base.

**Base currency of the ported files**: `git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor/scripts/session.py docs/lifecycle.md` prints nothing, so both files the candidate edits are byte-identical at the candidate's merge base and at the current base. `tests/test_session_marker_staleness.py` is absent at the current base.

**Citation currency**: every `git show` evidence statement below cites `8ee9d98aad71f059b69231aa370fdbae6bfe52d4` and was re-executed against it while authoring this plan (one observed line per statement). The other command outputs quoted (`git diff`, `git grep`, `git merge-base`, scratch runs) were observed at authoring time on 2026-09-28.

## Open Questions

None.

## Problem

`session.py` decides marker validity with one boolean. A marker whose file is missing and a marker whose content is valid but whose mtime is older than 24 hours both read as "not fresh". So when a governed cycle (plan, audit, implement, substantiate) runs past 24 hours without a marker write, `session.current()` returns `None` and `session.get_or_create()` issues a new id. The new id's gate directory is empty, so the next phase's prior-artifact check cannot find the earlier artifacts under the old id. The chain splits across two session directories and the operator is pushed into a gate override.

Reproduction at the base (scratch copy of `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, outside the repository, Phase 1 test file added): `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current` and `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir` FAIL; the other six tests pass (`2 failed, 6 passed`).

## Locked Decisions

### LD-1: stale and absent are different marker states

At the base, freshness is one boolean that folds "missing" into "not fresh":

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'def _marker_fresh'` -> `58:def _marker_fresh(path: Path, now: datetime) -> bool:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'if not path.exists\(\):'` -> `59:    if not path.exists():`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'return \(now - mtime\) < SESSION_TTL'` -> `62:    return (now - mtime) < SESSION_TTL`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^SESSION_TTL = '` -> `24:SESSION_TTL = timedelta(hours=24)`

`get_or_create` reuses the marker only when it is fresh, and otherwise writes a new id:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'if _marker_fresh\(marker, now\):'` -> `69:    if _marker_fresh(marker, now):`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '_atomic_write\(marker, new_id'` -> `74:    _atomic_write(marker, new_id + "\n")`

`current` returns `None` for any marker that is not fresh:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'if not _marker_fresh\(marker, now\):'` -> `82:    if not _marker_fresh(marker, now):`

Decision: `_marker_fresh` is replaced by `_marker_state(path, now) -> str` returning `"absent"`, `"stale"` or `"fresh"`. `_marker_fresh` is private and has no caller outside `session.py`: `git grep -n '_marker_fresh' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4` prints exactly three lines, all in `qor/scripts/session.py` (lines 58, 69 and 82 above).

### LD-2: a stale marker is kept only while its own session holds unsealed phase work

The rotation decision for a stale marker depends on the liveness of the session it names, not on age alone. A stale marker is live when its content matches `SESSION_ID_PATTERN` and `.qor/gates/<sid>/` is a directory that holds at least one of `research.json`, `plan.json`, `audit.json`, `implement.json` and does not hold `substantiate.json`. Otherwise it rotates exactly as at the base.

The seal writes `substantiate.json` and then rotates, so a sealed session's directory is the one that holds `substantiate.json`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'phase="substantiate", payload=payload'` -> `499:    phase="substantiate", payload=payload, session_id=sid, ai_provenance=manifest,`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'new_sid = session.rotate\(\)'` -> `638:new_sid = session.rotate()  # prior artifacts preserved at .qor/gates/<old-sid>/`

The gate directory comes from `workdir.gate_dir()`, which `session.py` already imports:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/workdir.py | grep -nE 'def gate_dir'` -> `35:def gate_dir() -> Path:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/workdir.py | grep -nE 'return root\(\) / ".qor" / "gates"'` -> `37:    return root() / ".qor" / "gates"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^from qor import workdir as _workdir'` -> `21:from qor import workdir as _workdir`

The phase artifact names are declared locally in `session.py` as a tuple. They are not imported from `gate_chain.CHAIN`, because `gate_chain` imports `session`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^from qor.scripts import session$'` -> `15:from qor.scripts import session`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^CHAIN = '` -> `28:CHAIN = ["research", "plan", "audit", "implement", "substantiate", "validate"]`

The marker content is used as a path segment only after it matches `SESSION_ID_PATTERN`, which admits no `/`, `\` or `.`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^SESSION_ID_PATTERN = '` -> `26:SESSION_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$")`

### LD-3: recovery keeps one gate chain

`get_or_create` on a live stale marker returns the same id and rewrites the marker with that id, which refreshes its mtime. It never issues a second id for an in-flight phase. `current` on a live stale marker returns the id and writes nothing. `current` on an absent, invalid, or stale non-live marker returns `None`; `get_or_create` on those issues a new id, as at the base.

The orphaning this prevents is in the prior-artifact check, which resolves the session from `current()` and looks only in that session's directory:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'errors=\["no active session'` -> `77:            errors=["no active session; run qor/scripts/session.py new"],`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'artifact = vga.latest_artifact_path\(prior, GATES_DIR / sid\)'` -> `81:    artifact = vga.latest_artifact_path(prior, GATES_DIR / sid)`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'prior-phase artifact missing'` -> `98:            errors=[f"prior-phase artifact missing: {artifact}"],`

### LD-4: public signatures do not change; callers are exempt

`get_or_create` and `current` keep their signatures:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'def get_or_create'` -> `65:def get_or_create(marker: Path | None = None, now: datetime | None = None) -> str:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^def current'` -> `78:def current(marker: Path | None = None, now: datetime | None = None) -> str | None:`

Callers (`qor/scripts/gate_chain.py`, `qor/scripts/validate_gate_artifact.py`, `qor/scripts/active_phase.py`, `qor/scripts/qa_evidence.py`, `qor/scripts/qor_audit_runtime.py`, `qor/scripts/session_tool.py`) need no edit and are exempt: the only change they see is the intended one, a live stale session id instead of `None` or a new id. The existing session tests stay green unchanged, including:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_gates.py | grep -nE 'def test_marker_regenerates_after_24h'` -> `45:def test_marker_regenerates_after_24h(tmp_path, monkeypatch):`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_gates.py | grep -nE 'def test_current_returns_none_when_absent'` -> `57:def test_current_returns_none_when_absent(tmp_path, monkeypatch):`

`test_marker_regenerates_after_24h` stays green because its fresh random id names no gate directory, so the stale marker is not live. Observed in a scratch clone of the base (outside the repository) with the candidate's `qor/scripts/session.py` and `docs/lifecycle.md` and the Phase 1 test file applied: the 149 test files that mention `session` or `lifecycle.md`, the Phase 1 file among them, gave `1263 passed, 4 deselected`. The Phase 2 code differs from the candidate's only in docstring line 8 (LD-7), which no test reads.

### LD-5: residual - an abandoned unsealed session is not rotated by age

Under LD-2 a session with phase work and no seal stays current past the TTL indefinitely. This is the accepted cost of never splitting a live chain. The operator exits it explicitly, by ending the session (the marker becomes absent) or by rotating it:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'def end_session'` -> `88:def end_session(marker: Path | None = None) -> None:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session_tool.py | grep -nE 'sp_rotate = sub.add_parser\("rotate"'` -> `20:    sp_rotate = sub.add_parser("rotate", help="rotate to a fresh session id")`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session_tool.py | grep -nE 'new_id = session.rotate\(\)'` -> `32:    new_id = session.rotate()`

No TTL, rotation command or resolver change is made (non-goals).

### LD-6: lifecycle and module docstring must match the new rule

The lifecycle doc states the base rule, which becomes false:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:docs/lifecycle.md | grep -nE 'marker is considered stale'` -> `68:- After 24h of inactivity, the marker is considered stale and a new ID is issued on next read.`

So does the `session.py` module docstring:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'Regenerated when missing OR mtime older than 24h'` -> `8:- Regenerated when missing OR mtime older than 24h`

Only these two lines change. The docstring's marker-path wording on line 7 is a pre-existing, unrelated inaccuracy and stays out of scope.

### LD-7: fidelity to the candidate, with every deviation declared

The implemented `qor/scripts/session.py`, `tests/test_session_marker_staleness.py` and `docs/lifecycle.md` equal the candidate head `5f8be1e2b325825a022172bc3d2b23697eaa1d30` except for exactly these four deviations:

1. `docs/lifecycle.md` line 68: the candidate's parenthetical `(GH #483; Phase 288)` reads `(GH #483; Phase 299)`. Phase 288 is not this phase.
2. `tests/test_session_marker_staleness.py` module docstring: `Phase 288 Phase 1:` reads `Phase 299 Phase 1:`.
3. `qor/scripts/session.py` line 8 (LD-6): the candidate leaves it unchanged; this plan corrects it.
4. `tests/test_session_marker_staleness.py` gains an eighth test, `test_stale_valid_marker_with_empty_gate_dir_still_rotates`. Without it no test fails when the phase-artifact membership check is replaced by `True` (mutation M3, Phase 1; observed `7 passed` for the candidate's seven tests under M3, `1 failed, 7 passed` with the eighth).

The candidate's seven tests use the real clock with margins of at least one hour against the 24-hour TTL (ages 25 h and 1 h; the refresh test compares a just-written mtime with the current time). They do not sleep, use no network, and assert no live repository state. With the candidate's `session.py`, the eight-test file was observed green twice in a row (`8 passed`, twice).

The implementer writes the tests first (Phase 1) and the code second (Phase 2). No file is checked out, copied or cherry-picked from the candidate branch as a substitute for that sequence. The Phase 2 fidelity check compares the result with the candidate afterwards.

### LD-8: version target is 0.175.3

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.2"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:CHANGELOG.md | grep -nE '^## \[0\.175\.2\]'` -> `13:## [0.175.2] - 2026-09-28`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:docs/META_LEDGER.md | grep -nE '^### Entry #818'` -> `24206:### Entry #818: SESSION SEAL -- Phase 298 dependency review SBOM path coverage (v0.175.2)`

`change_class: hotfix` bumps `0.175.2` to `0.175.3` at `/qor-substantiate`.

### LD-9: CHANGELOG Unreleased note

`/qor-implement` writes the user-facing note under `## [Unreleased]`; the seal stamps it and refuses an empty section:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:CHANGELOG.md | grep -nE '^## \[Unreleased\]'` -> `11:## [Unreleased]`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

Line 14 continues line 13, which opens the `/qor-implement` rule for populating `## [Unreleased]`; line 32 continues line 31, the fail-fast rule that an empty `Unreleased` section raises `ValueError` at the stamp. Lines 13 and 31 carry inline code spans and are paraphrased here rather than quoted as full-line evidence.

The note is one `### Fixed` bullet beginning `**Phase 299 (hotfix; stale session marker keeps its gate chain, GH #483)**:`. It states the LD-2/LD-3 rule, the LD-5 residual, and that `docs/release-state.json` records `0.175.2` as `sealed_unpublished`. It describes only what is implemented.

### LD-10: release-state continuity for 0.175.2

Once the seal bumps the project version to `0.175.3`, `0.175.2` stops being the single implicit candidate. The coverage rule then treats it as an orphan unless a reachable tag or a disposition covers it:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set\(exceptions\) - \{project_version\}'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/release_state.py | grep -nE 'if _semver\(v\) <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.2` has no release tag on the remote. At `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, line 24228 of `docs/META_LEDGER.md` is the Entry #818 `**Version**:` line, and it contains the sentence "No remote tag is created; the seal tag stays local." (`grep -n` for that sentence at that revision prints lines 24134 and 24228; 24134 is Phase 297's Entry #814. The line carries inline code spans and is quoted in part.) While authoring, `git ls-remote --tags origin` listed no `v0.173+` tag; the highest remote tag was `v0.172.2` (observation, 2026-09-28; not a test expectation).

The record at the base ends with `0.175.1` and has no `0.175.2` entry:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:docs/release-state.json | grep -nE '"version": "0\.175\.(1|2)"'` -> `70:      "version": "0.175.1",`

This phase appends exactly one entry to `docs/release-state.json`, after the `0.175.1` entry, mirroring how Phase 298 recorded `0.175.1`:

- `version`: `0.175.2`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #818); no release tag was pushed to the remote, so the version is sealed but not published.`

The record validator requires a dated CHANGELOG section for every entry; `0.175.2` has one (LD-8):

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.2` is reachable from the base in a local checkout (`git merge-base --is-ancestor v0.175.2 8ee9d98aad71f059b69231aa370fdbae6bfe52d4` exits 0). It is not on the remote, so CI does not see it, and it does not void the disposition:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.2` locally, the plain local tag-coverage run cannot tell whether the entry is present. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 3): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. The suite consumes the live record:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state\(RELEASE_STATE, versions\)'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The rule the entry relies on is already unit-tested:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 3), not written by hand at seal time. No entry is recorded for `0.175.3`: after the seal it is the implicit candidate. No ledger entry, seal, gate artifact or historical CHANGELOG section is edited.

### LD-11: canonical governance shape

This file is the canonical `docs/plan-qor-phase299-*.md` plan on branch `phase/299-session-marker-staleness`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/governance_helpers.py | grep -nE '_BRANCH_PHASE_RE ='` -> `23:_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase\{nn\}'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored.

## Feature Inventory Touches

Empty. This is a governance session-continuity correction; it introduces no `src/` or user-touchable product feature surface.

`feature_inventory_touches`: `[]`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_session_marker_staleness.py` (NEW) - stale versus absent marker behavior of `session.current` and `session.get_or_create`.

### Changes

The candidate's test module (LD-7) with the docstring deviation, plus one test. The module imports `session` from `qor/scripts` via `sys.path`, and each test isolates state by pointing `session.MARKER_PATH` at `tmp_path / ".qor" / "session" / "current"` and monkeypatching `session._workdir.root` to return `tmp_path`. Helper `_write_marker(marker, sid, *, age)` writes the id and sets the mtime `age` into the past with `os.utime`. The fixed id is `2026-04-17T2335-f284b9`; "stale" is age 25 h and "fresh" is age 1 h.

### Unit Tests

- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_unsealed_gate_dir_is_still_current` - stale marker, gate dir holding `plan.json`: `session.current()` returns the id. RED at the base (returns `None`).
- `tests/test_session_marker_staleness.py::test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir` - same setup: `session.get_or_create()` returns the same id. RED at the base (new id).
- `tests/test_session_marker_staleness.py::test_get_or_create_refreshes_marker_mtime_on_reuse` - same setup: after `get_or_create()`, the marker mtime is within `SESSION_TTL` of now. GREEN at the base (the base rotation also writes a fresh marker); it discriminates mutation M1.
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_sealed_gate_dir_still_rotates` - stale marker, gate dir holding `plan.json` and `substantiate.json`: `current()` is `None`, `get_or_create()` returns a different id, and the marker holds that id. GREEN at the base; discriminates M2, M4 and M5.
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_no_gate_dir_still_rotates` - stale marker, no gate dir: `current()` is `None` and `get_or_create()` returns a different id. GREEN at the base; discriminates M4 and M5.
- `tests/test_session_marker_staleness.py::test_absent_marker_is_unaffected` - no marker: `current()` is `None`, and `get_or_create()` writes the id it returns. GREEN at the base and after (regression coverage backfill: preserves the base absent-marker behavior).
- `tests/test_session_marker_staleness.py::test_fresh_marker_is_unaffected` - fresh marker: `current()` and `get_or_create()` both return the id. GREEN at the base and after (regression coverage backfill: preserves the base fresh-marker behavior).
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_empty_gate_dir_still_rotates` (added; LD-7 deviation 4) - stale marker, gate dir exists but is empty: `current()` is `None`, `get_or_create()` returns a different id, and the marker holds that id. GREEN at the base; discriminates M3, M4 and M5.

TDD: the first two tests are observed RED before Phase 2 (`2 failed, 6 passed` at the base). The other six are GREEN before Phase 2 by design, since they pin behavior the fix must keep. Their discrimination is proven after Phase 2 by local, uncommitted mutations of `qor/scripts/session.py`, each run with `python -B -m pytest tests/test_session_marker_staleness.py -q` and then reverted:

- M1: in `get_or_create`, drop the `_atomic_write(marker, recovered + "\n")` call on the stale-live branch -> `test_get_or_create_refreshes_marker_mtime_on_reuse` FAILS.
- M2: in `_has_unsealed_gate_artifacts`, drop the `substantiate.json` check -> `test_stale_valid_marker_with_sealed_gate_dir_still_rotates` FAILS.
- M3: in `_has_unsealed_gate_artifacts`, replace the final `any(...)` with `True` -> `test_stale_valid_marker_with_empty_gate_dir_still_rotates` FAILS.
- M4: in `_recoverable_stale_id`, return `content` without the liveness check -> the sealed, no-gate-dir and empty-gate-dir tests FAIL.
- M5: in `current`, return `content` for a stale marker without the liveness check -> the sealed, no-gate-dir and empty-gate-dir tests FAIL.

Each mutation outcome above was observed while authoring, in a scratch copy outside the repository, applied to the candidate's `session.py` (logic identical to Phase 2; LD-7). After each mutation the implementer restores the Phase 2 content, re-runs the Phase 2 fidelity diff to confirm no mutation remains, and runs the file twice GREEN.

## Phase 2: Session marker semantics and lifecycle wording

### Affected Files

- `qor/scripts/session.py` - three-state marker, liveness check, stale-live reuse and refresh; docstring line 8.
- `docs/lifecycle.md` - line 68 states the stale-live exception.

### Changes

`qor/scripts/session.py`:

- Add module constants `_GATE_PHASE_ARTIFACTS = ("research.json", "plan.json", "audit.json", "implement.json")` and `_SEAL_ARTIFACT = "substantiate.json"`, with a comment that they are local because `gate_chain` imports this module (LD-2).
- Replace `_marker_fresh` with `_marker_state(path: Path, now: datetime) -> str`: `"absent"` when the file is missing, else `"fresh"` when `now - mtime < SESSION_TTL`, else `"stale"`.
- Add `_has_unsealed_gate_artifacts(session_id: str) -> bool`: `sess_dir = _workdir.gate_dir() / session_id`; `False` if `sess_dir` is not a directory or holds `_SEAL_ARTIFACT`; else `any((sess_dir / name).exists() for name in _GATE_PHASE_ARTIFACTS)`.
- Add `_recoverable_stale_id(marker: Path) -> str | None`: read and strip the marker; `None` unless it matches `SESSION_ID_PATTERN`; then the content if `_has_unsealed_gate_artifacts(content)`, else `None`.
- `get_or_create`: compute `state`. On `"fresh"`, return the content if it matches `SESSION_ID_PATTERN` (as at the base). On `"stale"`, if `_recoverable_stale_id(marker)` returns an id, rewrite the marker with `_atomic_write(marker, recovered + "\n")` and return it. Otherwise fall through to the base new-id path unchanged.
- `current`: `None` on `"absent"`; `None` if the content does not match `SESSION_ID_PATTERN`; the content on `"fresh"`; on `"stale"`, the content if `_has_unsealed_gate_artifacts(content)`, else `None`. No write.
- Docstring line 8 becomes: `- Regenerated when missing, or when older than 24h unless its own gate dir holds unsealed phase work (GH #483)`.

`docs/lifecycle.md` line 68 becomes exactly:

```markdown
- After 24h of inactivity, the marker is considered stale. A new ID is issued on next read only if the stale marker's own session has no live, unsealed gate directory (its `.qor/gates/<sid>/` is absent, or already sealed via `substantiate.json`); otherwise the existing id is reused and the marker's mtime is refreshed, so a long-running phase does not lose its gate artifacts to the clock (GH #483; Phase 299).
```

`end_session`, `rotate`, `generate_id`, `validate_session_id` and `main` do not change.

### Unit Tests

- Re-run `tests/test_session_marker_staleness.py` after the edit: all eight GREEN, twice in a row.
- Run mutations M1-M5 (Phase 1) and observe each named failure; revert.
- Run `tests/test_gates.py` and `tests/test_e2e.py` unchanged: GREEN (LD-4).
- Fidelity check (LD-7), after `git fetch origin fix/483-session-marker-current`: `git diff 5f8be1e2b325825a022172bc3d2b23697eaa1d30 -- qor/scripts/session.py docs/lifecycle.md tests/test_session_marker_staleness.py` shows only deviations 1-4. The implementer records the observed diff summary in the implementation report.

## Phase 3: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.2` `sealed_unpublished` entry (LD-10).
- `CHANGELOG.md` - the Phase 299 bullet under `## [Unreleased]` (LD-9). No dated section is edited.

### Changes

Append the LD-10 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-9 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.3]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-10).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` stays GREEN, which proves the record validates with the new entry.
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.3`, remote tags only). At the base, before the entry exists, it prints `{'0.175.2'} {'0.175.2'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.2'}`: no orphan with the entry, exactly `{'0.175.2'}` with the entry removed in memory. That shows the entry is what keeps coverage green.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.3` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.2` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in a scratch clone of the base outside the repository with `origin` set to the real remote; the simulated commits never entered this repository):
  - base commit (`version = "0.175.2"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.3 (project version 0.175.2)`;
  - a commit that bumps `version` to `0.175.3` without the `[0.175.3]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.3 (project version 0.175.3)`;
  - simulated seal commit (`version = "0.175.3"`, `## [0.175.3] - ` section, local `v0.175.3` tag), no `0.175.2` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.2`;
  - the same seal commit with the LD-10 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: stale-but-live session marker keeps its gate chain

- **D1**: a marker older than `SESSION_TTL` whose valid id names a gate directory holding research/plan/audit/implement work and no `substantiate.json` is treated as the current session: `current()` returns it and `get_or_create()` reuses it and refreshes the marker mtime. Absent markers, invalid content, and stale markers naming a sealed, empty or missing gate directory keep the base behavior. The LD-5 residual is declared.
- **D2**: `qor/scripts/session.py` defines `_marker_state(path: Path, now: datetime) -> str`, `_has_unsealed_gate_artifacts(session_id: str) -> bool` and `_recoverable_stale_id(marker: Path) -> str | None`, and no longer defines `_marker_fresh`. `get_or_create` and `current` keep their signatures (LD-4). The Phase 2 fidelity diff against `5f8be1e2b325825a022172bc3d2b23697eaa1d30` shows only LD-7 deviations 1-4.
- **D3**: `docs/lifecycle.md` line 68 and the `session.py` docstring describe the stale-live exception (LD-6). Phase 299 follows canonical branch and plan resolution and receives current-revision audit and substantiation evidence before promotion; no evidence from the candidate branch is reused as authority. The `## [Unreleased]` bullet exists at implement time (LD-9).
- **D4**: `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_unsealed_gate_dir_is_still_current` and `tests/test_session_marker_staleness.py::test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir` are RED before Phase 2 and GREEN after. Every test in the file is GREEN twice in a row after Phase 2, each mutation M1-M5 turns its named tests RED, and `tests/test_gates.py` and `tests/test_e2e.py` stay GREEN.

### Deliverable: release-state continuity for 0.175.2

- **D1**: after the Phase 299 seal bumps the project version to `0.175.3`, `0.175.2` (sealed on `main` at META_LEDGER #818, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.2` / `sealed_unpublished` with the LD-10 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.2` to `0.175.3` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.2'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.3` with a dated `[0.175.3]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_session_marker_staleness.py -q` - verifies the stale versus absent marker semantics (eight tests).
- `python -m pytest tests/test_gates.py tests/test_e2e.py -q` - verifies existing session and gate-chain behavior is unchanged.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.3'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.3', ex).orphans, rs.coverage_violations(versions, tags, '0.175.3', {k: v for k, v in ex.items() if k != '0.175.2'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.2'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.3' and '## [0.175.3] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.3 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.3`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/check_variant_drift.py` - verifies installed/generated variant consistency.
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

## Non-goals

- redesign of session identity, the id format, or `SESSION_TTL`;
- automatic rotation of abandoned unsealed sessions (LD-5 residual);
- changes to `gate_chain`, `validate_gate_artifact`, `session_tool` or any other caller of `session`;
- the pre-existing marker-path wording on `session.py` docstring line 7;
- release-state dispositions for any version other than `0.175.2`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- reusing any evidence from the candidate branch as audit, implementation or seal authority;
- hand-issuing governance evidence;
- unrelated repository cleanup.
