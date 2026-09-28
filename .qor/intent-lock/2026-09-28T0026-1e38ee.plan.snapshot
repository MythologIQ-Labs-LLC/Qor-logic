# Plan: Phase 299 - Keep a stale but live session marker bound to its gate chain

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: the marker still goes stale 24h after it was last written, and reads do not refresh it (LD-1); a stale marker is kept only while its own session directory holds `ideation.json`, `research.json`, `plan.json`, `audit.json` or `implement.json` and no `substantiate.json`; an abandoned session in that state therefore stays current past the TTL until an operator ends or rotates it, and a new phase started in it shares its session directory and session-scoped counters (accepted residual, LD-5); liveness is judged against the gate directory of the process's project root at call time (LD-5)
- non_goals: session identity redesign, TTL policy change, gate-chain resolver changes, release publication
- exclusions: markers whose content does not match `SESSION_ID_PATTERN` (traversal, absolute path, empty or wrong format), stale or fresh; they rotate to a fresh id as before, and a test pins it (LD-2)

**iteration**: 5 (on branch `phase/299-session-marker-staleness`; responds to the VETOs at META_LEDGER #819, #820, #821 and #822, see `## Iteration history`)

**Issue**: GH #483 ("A cycle spanning a day boundary loses its session marker, and the recovery path orphans the gate chain")

**Current base**: `8ee9d98aad71f059b69231aa370fdbae6bfe52d4` (`main` after Phase 298 merged; project version `0.175.2`, sealed at META_LEDGER #818)

**Target version**: `0.175.3` (hotfix bump from `0.175.2`)

**Provenance**: the code and tests below are carried, with the deviations declared in LD-7, from the candidate branch `fix/483-session-marker-current`, head `5f8be1e2b325825a022172bc3d2b23697eaa1d30`. That branch is non-canonical (not a `phase/<NN>-` branch; its plan `docs/plan-session-marker-staleness-current.md` is not a `plan-qor-phase<NN>*.md` file), so Qor's resolver cannot audit it. Relative to its merge base `15729311f9f4d55d5dad2db004b972415c39432c` the branch changes exactly four files and nothing else: `git diff --stat 15729311f9f4d55d5dad2db004b972415c39432c 5f8be1e2b325825a022172bc3d2b23697eaa1d30` lists `docs/lifecycle.md`, `docs/plan-session-marker-staleness-current.md`, `qor/scripts/session.py` and `tests/test_session_marker_staleness.py` and ends `4 files changed, 250 insertions(+), 7 deletions(-)`. It therefore carries no gate artifact, intent lock, ledger entry, seal or version change for this work. It is reference and ancestry only; it is not audit, implementation or seal authority. `git merge-base --is-ancestor 5f8be1e2b325825a022172bc3d2b23697eaa1d30 8ee9d98aad71f059b69231aa370fdbae6bfe52d4` exits 1. The candidate plan describes earlier review of the same semantics; this plan does not rely on that description, and every claim below is re-derived at the current base.

**Base currency of the ported files**: `git diff --name-only 15729311f9f4d55d5dad2db004b972415c39432c 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor/scripts/session.py docs/lifecycle.md qor/gates/chain.md qor/references/doctrine-governance-enforcement.md qor/skills/meta/qor-help/SKILL.md` prints nothing, so both files the candidate edits, `qor/gates/chain.md`, the doctrine file and the `qor-help` skill are byte-identical at the candidate's merge base and at the current base. The candidate does not edit the `qor-help` skill (`git diff --stat 15729311f9f4d55d5dad2db004b972415c39432c 5f8be1e2b325825a022172bc3d2b23697eaa1d30 -- qor/skills/meta/qor-help/SKILL.md` prints nothing). `tests/test_session_marker_staleness.py` is absent at the current base.

**Citation currency**: every `git show` evidence statement below cites `8ee9d98aad71f059b69231aa370fdbae6bfe52d4` and was re-executed against it while authoring iteration 5 (one observed line per statement). The other command outputs quoted (`git diff`, `git grep`, `git merge-base`, scratch runs) were observed at authoring time on 2026-09-28; the scratch runs for iteration 5 used a fresh clone of the base outside the repository, with the Phase 1 test file, the Phase 2 edits and the Phase 3 edits applied as specified below.

## Open Questions

None.

## Iteration history

Iteration 5 responds to VETO #822 (iteration 4). Its ground and advisories, and where each is closed:

- #822 V1 (specification-drift): the LD-9 bullet ended "(sealed at META_LEDGER #818; no remote tag)", but `qor/references/doctrine-changelog.md` lines 13 to 16, the `/qor-implement` rule LD-9 cites, say that ledger entry numbers and hash values do not appear in the CHANGELOG. The parenthetical is removed; the bullet now ends "`docs/release-state.json` records `0.175.2` as `sealed_unpublished`.", the form the sealed Phase 298 bullet uses. The ledger number stays only in the `docs/release-state.json` reason (LD-10), which the changelog rule does not govern and where every `sealed_unpublished` precedent carries one (LD-10).
- #822 A1: LD-6's wider grep is restated as an exact command that excludes `docs/archive`, and its full output (eleven lines: six about the session marker, five unrelated and named) was re-executed at the base.
- #822 A2: `qor/skills/meta/qor-help/SKILL.md` line 135 listed "stale beyond TTL" as a reason `current()` returns `None`, which is false for a stale live marker after this fix. The evidence favors the complete fix: the change is one parenthetical in one line; the six compiled copies under `qor/dist/variants/` are produced mechanically by `python -m qor.scripts.dist_compile`; `python qor/scripts/check_variant_drift.py` and the claude, codex, kilo-code and cursor variant sync checks in `tests/test_install_sync_with_source.py` fail when the copies are not recompiled (observed); skill admission reads only frontmatter; the skill stays far under the size budget. The parenthetical is corrected (Phase 2, LD-6, LD-7 deviation 11).
- #822 A3 (ordering): this iteration writes the plan gate artifact after the final plan text, with no plan edit after it. A4 (workspace fragility) is pre-existing.
- Doctrine conformance sweep. Each verbatim text was checked, line by line, against the rules that govern its surface. The CHANGELOG bullet against `doctrine-changelog.md` (lines 3 to 5 and 13 to 18: user-facing effect, `Fixed` label, no ledger entry number, no hash value, no internal refactor): its only `#` number is the issue reference `GH #483`, which dated sections carry (the Phase 298 bullet names `GH #511`); it names `current()` and `get_or_create()` because they are the `session` functions that skills call (`/qor-plan` Step 0, `/qor-help --stuck`), not internals. `docs/release-state.json` against the release-state rules in the same doctrine (lines 78 to 93: closed shape, `version`, `state`, `reason`; free-text reason). `docs/lifecycle.md:68`, `qor/gates/chain.md:20`, doctrine line 109 and the `qor-help` line against `doctrine-documentation-integrity.md` and the glossary: no new term is introduced, so `terms` stays empty, and `check_term_drift` plus `check_cross_doc_conflicts` give the same findings at the base and with all edits applied (none). Every surface against `doctrine-publication-boundary.md`: `publication_boundary_lint` reports 0 findings with all edits applied, and no text names another repository. Every inserted text is ASCII; the `qor-help` line keeps its existing non-ASCII characters outside the replaced parenthetical (LD-6). No mismatch remained after V1.
- Behavioral scope sweep, re-executed in a fresh scratch clone of the base outside the repository with all edits applied: the two-age by ten-directory matrix with valid content, malformed content at both ages, and the installed-CLI `session new`, `session_tool rotate` and `session end` forms gave exactly the results stated in LD-3 and LD-5, which match every clause of the CHANGELOG bullet, `docs/lifecycle.md:68`, `qor/gates/chain.md:20`, the docstrings and the new `qor-help` parenthetical. The 29-item file gave `10 failed, 19 passed` at the base and `29 passed` twice with the fix; M1 to M15 gave the counts in Phase 1; the full suite gave `3611 passed, 3 skipped`; `check_variant_drift.py` printed `OK: 406 files, no drift`; the CI-view simulation printed `set() {'0.175.2'}`. All `git show` citations were re-executed at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`.

Iteration 4 responded to VETO #821 (iteration 3). Its ground and advisories, and where each is closed:

- #821 V1 (specification-drift): the LD-9 CHANGELOG sentence "A marker with malformed content, or one naming an absent, empty or sealed directory or a directory with no pre-seal phase artifact, still rotates to a new id" gave the directory clauses no age qualifier, so it claimed that a fresh valid marker naming such a directory rotates. It does not: a fresh marker with valid content keeps its id whatever its directory holds (LD-3). The sentence is replaced by three scoped clauses: a stale marker whose directory is absent, empty or sealed, or holds no pre-seal phase artifact, rotates; a marker of any age with malformed content rotates; a fresh marker with valid content keeps its id, as before (LD-9). The `docs/lifecycle.md` line 68 text had the same shape in a weaker form ("In every other case", after a sentence about stale markers, listing malformed content beside the directory cases); its last sentence now scopes the directory cases to a stale marker and malformed content to a marker of any age (Phase 2).
- #821 A1: "unsealed phase work" in the `session.py` docstring line 8 is replaced by "a pre-seal phase artifact and no substantiate.json". The candidate's docstrings of `_has_unsealed_gate_artifacts` ("holds phase work and no seal yet") and `_recoverable_stale_id` ("still naming unsealed live work") had the same imprecision, since a directory holding only `remediate.json` holds phase work and rotates; both are replaced by exact text (LD-7 deviation 10). The LD-2 heading uses the same term.
- #821 A2: the LD-9 bullet now names the installed CLI form, `qor-logic scripts session end` and `qor-logic scripts session_tool rotate`, which the repository documents as `qor-logic scripts <module>` and which exists at the base (LD-5). Both were executed in the scratch clone.
- Consistency sweep: every sentence in this plan and in the verbatim replacement texts (the CHANGELOG bullet, `docs/lifecycle.md:68`, `qor/gates/chain.md:20`, the `session.py` docstrings and doctrine line 109) that states marker or rotation behavior was checked for its scope (marker age, content validity, directory state) against the code, by executing all twenty valid-content combinations of two ages and ten directory states plus malformed content at both ages in the scratch clone (LD-3), and against the test that pins it. Beyond the surfaces above, it found one more imprecision of the A1 kind: "an abandoned unsealed session" stays current (boundaries, LD-5 heading, CHANGELOG residual), although an unsealed session whose directory holds no pre-seal phase artifact rotates. Each now names a session whose directory holds a pre-seal phase artifact and no seal. No other mismatch was found.

Iteration 3 responded to VETO #820 (iteration 2). Its grounds and where each is closed:

- #820 V1 (coverage-gap): the rule "a stale marker whose directory holds no pre-seal phase artifact rotates" now has discriminating tests for non-empty directories. `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` is parametrized over a directory holding only `remediate.json`, only `validate.json`, only `audit_history.jsonl`, or only an unrelated `notes.json`. `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` asserts set equality in both directions: the tuple equals the `gate_chain`-derived pre-seal set, and the set of names that keep a stale marker live, probed one name at a time, equals that set too. The auditor's M10 (append `"remediate.json"` to the tuple) now fails 2 items, and M11 (treat any `*.json` as live) fails 3. Over the 150 session-related test files they give `2 failed, 1282 passed, 4 deselected` and `3 failed, 1281 passed, 4 deselected` (Phase 1; LD-2).
- #820 V2 (specification-drift): the age rule is stated exactly on every surface. The marker goes stale 24h after it was last written. A read does not refresh it: `current()` never writes it, and `get_or_create()` returns a fresh marker without writing it. `get_or_create()` re-writes, and so refreshes, the marker when it keeps a stale live id. Each clause was executed in the scratch clone (LD-1), and each has a test that fails when it is false (LD-3). The corrected text covers `docs/lifecycle.md:68`, `qor/gates/chain.md:20`, the `session.py` docstring, the CHANGELOG bullet (exact text in LD-9) and this plan's LDs and DoD. The adversarial re-read also found `qor/references/doctrine-governance-enforcement.md` line 109, which offers `python -m qor.scripts.session new` as a manual rotation. That command is `get_or_create()`, so it does not rotate a fresh marker at the base, and after this fix it also keeps a live stale id. The line is corrected to `python -m qor.scripts.session_tool rotate` (LD-6).
- Adversarial re-read: each normative sentence about marker behavior in LD-2, LD-3 and LD-6 now names the test that fails when it is false. A fresh marker with malformed content was covered only by base code, so the malformed-content test now covers fresh markers too, and M15 pins the `get_or_create` fresh-branch format check. `current()` writing nothing on a stale live marker is pinned by M14, and a fresh-marker read not refreshing it by M13.

Iteration 2 closed VETO #819 (iteration 1): V1, the format guard on the stale-recovery path has a discriminating test (M6, M7); V2, exact replacement text for the normative surfaces; V3, `ideation.json` joins the liveness set, with a parametrized test that derives the phases from `gate_chain`. Advisories A1 to A4 of #819 are handled in LD-5 (A1, A2), LD-4 (A3) and as pre-existing workspace state (A4). #820 advisories: A1 (workspace fragility) is pre-existing; A2 (six callers) matches LD-4; A3 (collection-time `ValueError` if `substantiate` were renamed) is accepted as fail-loud.

## Problem

`session.py` decides marker validity with one boolean. A marker whose file is missing and a marker whose content is valid but which was last written 24 hours or more ago both read as "not fresh". So when a governed cycle (plan, audit, implement, substantiate) runs past 24 hours without a marker write, `session.current()` returns `None` and `session.get_or_create()` issues a new id. The new id's gate directory is empty, so the next phase's prior-artifact check cannot find the earlier artifacts under the old id. The chain splits across two session directories and the operator is pushed into a gate override.

Reproduction at the base (scratch copy of `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, outside the repository, Phase 1 test file added): `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`, `test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current`, the five cases of `test_stale_marker_liveness_covers_every_pre_seal_chain_phase`, `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` and `test_current_on_a_stale_live_marker_does_not_refresh_it` FAIL; the other nineteen test items pass (`10 failed, 19 passed`).

End-to-end at the base, with the real `gate_chain` and `QOR_ROOT` set to a scratch directory: a session holding only `ideation.json` whose marker is 26 h old gives `current()` `None`, `get_or_create()` a new id, and `check_prior_artifact("plan")` reports `prior-phase artifact missing` under the new id. With the Phase 2 code the same setup gives the original id from both calls, and `check_prior_artifact("plan")` finds `ideation.json` in the original session directory.

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

Age is measured from the marker's mtime, that is, from its last write:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'mtime = datetime.fromtimestamp\(path.stat\(\).st_mtime'` -> `61:    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)`

At the base the marker is written only by `get_or_create` when it issues a new id (line 74 above) and by `rotate`; `current` and a `get_or_create` call that finds a fresh marker only read it:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '_atomic_write\(MARKER_PATH, new_id'` -> `104:    _atomic_write(MARKER_PATH, new_id + "\n")`

After Phase 2 the only added write is the stale-live re-write in `get_or_create` (LD-3). So the marker goes stale 24h after it was last written, even while the session is in use. Gate writes that omit `session_id` call `get_or_create`, which only reads a fresh marker: at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `qor/scripts/gate_chain.py` lines 206 and 288 both read `sid = session_id or session.get_or_create()` (two identical lines, so they are cited here in prose rather than as a one-line evidence statement). Observed in the scratch clone with the Phase 2 `session.py` and `QOR_ROOT` set to a scratch directory:

- a marker written 23 h earlier is still 23.0 h old after three rounds of `get_or_create()`, `current()` and `gate_chain.check_prior_artifact("plan")`;
- `_marker_state` returns `"stale"` at exactly 24 h after the mtime and `"fresh"` one second earlier;
- at 25 h, with no gate directory, `current()` returns `None`;
- at 25 h, with `plan.json` in the gate directory, `current()` returns the id and leaves the mtime unchanged, and `get_or_create()` returns the same id and leaves the marker 0.0 h old (`"fresh"`).

Decision: `_marker_fresh` is replaced by `_marker_state(path, now) -> str` returning `"absent"`, `"stale"` or `"fresh"`. `_marker_fresh` is private and has no caller outside `session.py`: `git grep -n '_marker_fresh' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4` prints exactly three lines, all in `qor/scripts/session.py` (lines 58, 69 and 82 above).

### LD-2: a stale marker is kept only while its own session holds a pre-seal phase artifact and no seal

The rotation decision for a stale marker depends on the liveness of the session it names, not on age alone. A stale marker is live when its content matches `SESSION_ID_PATTERN` and `.qor/gates/<sid>/` is a directory that holds at least one of `ideation.json`, `research.json`, `plan.json`, `audit.json`, `implement.json` and does not hold `substantiate.json`. Otherwise (content malformed; directory absent, empty, holding none of those five files, or sealed) it rotates exactly as at the base.

The seal writes `substantiate.json` and then rotates, so a sealed session's directory is the one that holds `substantiate.json`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'phase="substantiate", payload=payload'` -> `499:    phase="substantiate", payload=payload, session_id=sid, ai_provenance=manifest,`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/skills/governance/qor-substantiate/SKILL.md | grep -nE 'new_sid = session.rotate\(\)'` -> `638:new_sid = session.rotate()  # prior artifacts preserved at .qor/gates/<old-sid>/`

The gate directory comes from `workdir.gate_dir()`, which `session.py` already imports:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/workdir.py | grep -nE 'def gate_dir'` -> `35:def gate_dir() -> Path:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/workdir.py | grep -nE 'return root\(\) / ".qor" / "gates"'` -> `37:    return root() / ".qor" / "gates"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^from qor import workdir as _workdir'` -> `21:from qor import workdir as _workdir`

The liveness set is the set of pre-seal phases that `gate_chain` resolves as chain predecessors: every `CHAIN` phase before `substantiate`, plus the optional `ideation` phase, which `gate_chain` accepts as the prior of both `research` and `plan`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^CHAIN = '` -> `28:CHAIN = ["research", "plan", "audit", "implement", "substantiate", "validate"]`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^IDEATION_PHASE = '` -> `29:IDEATION_PHASE = "ideation"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'return _check_ideation_predecessor\(session_id\) or GateResult\('` -> `68:            return _check_ideation_predecessor(session_id) or GateResult(`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'ideation_result = _check_ideation_predecessor\(session_id\)'` -> `86:            ideation_result = _check_ideation_predecessor(session_id)`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'artifact = vga.latest_artifact_path\("ideation", GATES_DIR / sid\)'` -> `140:    artifact = vga.latest_artifact_path("ideation", GATES_DIR / sid)`

`/qor-ideate` writes that artifact through the normal writer:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/skills/sdlc/qor-ideate/SKILL.md | grep -nE 'phase="ideation", payload=payload'` -> `128:    phase="ideation", payload=payload, session_id=sid, ai_provenance=manifest,`

Checking the unversioned `<phase>.json` name is enough, because every write refreshes it beside the versioned `<phase>-iter<N>.json` file:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/validate_gate_artifact.py | grep -nE '_atomic_write\(session_dir / f"\{phase\}.json", text\)'` -> `206:    _atomic_write(session_dir / f"{phase}.json", text)`

`validate` follows `substantiate`, so its directory is already sealed. `remediate` is out-of-band and is not a chain predecessor (`qor/gates/chain.md` line 12 marks it "Not part of the strict forward chain"), so a directory holding only a remediation artifact is not live. More generally, a stale marker whose directory holds none of the five pre-seal artifacts rotates, whatever else the directory holds. `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` pins this for a directory holding only `remediate.json`, only `validate.json`, only `audit_history.jsonl` (the audit history log that `write_gate_artifact` appends beside `audit.json`), or only an unrelated `notes.json`. Mutations M3, M10, M11 and M12 each fail it (Phase 1).

Derivation decision: `session.py` cannot import `gate_chain` at module load, because `gate_chain` imports `session`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^from qor.scripts import session$'` -> `15:from qor.scripts import session`

A call-time import from `session` into `gate_chain` would couple the low-level marker module to `gate_chain`'s import-time state (`GATES_DIR`, `shadow_process`, `validate_gate_artifact`), so it is not the minimal or safe option. The set is therefore a local tuple, `_GATE_PHASE_ARTIFACTS = ("ideation.json", "research.json", "plan.json", "audit.json", "implement.json")`, and the derivation is enforced by tests in both directions. The expected set is `{f"{p}.json" for p in [gate_chain.IDEATION_PHASE, *gate_chain.CHAIN[: gate_chain.CHAIN.index("substantiate")]]}`, computed from `gate_chain`. `test_stale_marker_liveness_covers_every_pre_seal_chain_phase` is parametrized over those phases, so it fails when a phase is missing from the liveness check. `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` asserts that the sorted tuple equals the sorted expected set. It then probes each name in the union of the two sets, one fresh root per name, and asserts that the names which keep a stale marker live are exactly the expected set. It fails when the tuple drops a member (M8, M9) or gains one (M10), and when `gate_chain` gains a pre-seal phase. Observed: with `"review"` inserted into `gate_chain.CHAIN` before `substantiate` in the scratch clone, the file gives `2 failed, 28 passed` (`[review]` and the equality test). Membership widening that leaves the tuple unchanged (M11, M12) is caught by `test_stale_marker_with_only_non_pre_seal_artifacts_rotates`.

The marker content is used as a path segment only after it matches `SESSION_ID_PATTERN`, which admits no `/`, `\` or `.` and no empty string:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^SESSION_ID_PATTERN = '` -> `26:SESSION_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$")`

This guard is the only path-safety check on the recovery path, because `gate_chain` builds `GATES_DIR / sid` without `validate_session_id`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE 'artifact = vga.latest_artifact_path\(prior, GATES_DIR / sid\)'` -> `81:    artifact = vga.latest_artifact_path(prior, GATES_DIR / sid)`

Within `session.py`, the guard runs in every place that reads marker content: `_recoverable_stale_id` (used by `get_or_create` on a stale marker), the fresh branch of `get_or_create` (base code, unchanged), and `current`. `test_marker_with_malformed_content_rotates_to_fresh_id` pins all three. It is parametrized over four contents, `../../evil`, an absolute path under `tmp_path`, the empty string, and `2026-04-17T2335-F284B9` (upper-case hex), and over two marker ages, 25 h (`stale`) and 1 h (`fresh`), so it has 8 items. In each case the test creates `.qor/gates/` and places `plan.json` in the directory the content would resolve to, so the directory looks live and only the guard can reject the content. It asserts `current()` is `None`, `get_or_create()` returns an id that differs from the content and matches `SESSION_ID_PATTERN`, and the marker holds that id. Observed in the scratch clone: with the guards, all 8 pass. Under M6 (the check removed from `_recoverable_stale_id`) the 4 `stale` items fail. Under M15 (the check removed from the fresh branch of `get_or_create`) the 4 `fresh` items fail. Under M7 (the check removed from `current`) all 8 fail. The test creates `.qor/gates/` because otherwise the `traversal` case passes under M6: `..` cannot be resolved through a missing directory.

### LD-3: recovery keeps one gate chain

`get_or_create` on a live stale marker returns the same id and rewrites the marker with that id, which refreshes its mtime (pinned by `test_get_or_create_refreshes_marker_mtime_on_reuse`, M1). It never issues a second id for a session whose directory holds any artifact that `gate_chain` can resolve as a prior phase, from `ideation.json` through `implement.json` and without `substantiate.json` (LD-2). `current` on a live stale marker returns the id and writes nothing (pinned by `test_current_on_a_stale_live_marker_does_not_refresh_it`, M14). On a fresh marker with valid content, `current` and `get_or_create` both return the id without writing it, as at the base, whatever its directory holds: neither consults the gate directory for a fresh marker (pinned by `test_fresh_marker_is_unaffected` and `test_reads_of_a_fresh_marker_do_not_refresh_it`, M13; both use a marker with no gate directory, which is the state after every seal's `session.rotate()`). Observed in the scratch clone with the Phase 2 `session.py`, for a 1 h marker with valid content and each of ten directory states (absent, empty, only `remediate.json`, only `validate.json`, only `audit_history.jsonl`, only `notes.json`, only `ideation.json`, only `plan.json`, only `implement.json`, and `plan.json` with `substantiate.json`): `current()` returned the id, `get_or_create()` kept it, and neither wrote the marker. For a 25 h marker with valid content, the same ten states gave the id from `current()` and a kept id from `get_or_create()` only for the three states holding a pre-seal phase artifact and no `substantiate.json`; `current()` wrote nothing in any state, and `get_or_create()` wrote the marker in every state (the kept id in those three, a new id in the other seven). A marker holding `../../evil`, the empty string or `2026-04-17T2335-F284B9` gave `current()` `None` and a new valid id from `get_or_create()` at both 1 h and 25 h. `current` on an absent marker, on a marker with malformed content of any age, or on a stale non-live marker returns `None`; `get_or_create` on those writes and returns a new id, as at the base (pinned by `test_absent_marker_is_unaffected`, `test_marker_with_malformed_content_rotates_to_fresh_id`, `test_stale_valid_marker_with_no_gate_dir_still_rotates`, `test_stale_valid_marker_with_empty_gate_dir_still_rotates`, `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` and `test_stale_valid_marker_with_sealed_gate_dir_still_rotates`).

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

`test_marker_regenerates_after_24h` stays green because its fresh random id names no gate directory, so the stale marker is not live. Observed in a scratch clone of the base (outside the repository) with the Phase 1 test file and all Phase 2 and Phase 3 edits applied (iteration 5 re-run, including the `qor-help` edit and the recompiled copies): `grep -l -E 'session|lifecycle\.md' tests/*.py` selects 150 test files, the Phase 1 file among them, and they gave `1284 passed, 4 deselected`, twice. The Phase 1 file contributes 29 of those test items. The seven test files that mention `chain.md` or `lifecycle.md`, plus `tests/test_gates.py` and `tests/test_e2e.py`, gave `95 passed`. The six test files that name `doctrine-governance-enforcement` but match neither pattern (`tests/test_codeowners_doctrine.py`, `tests/test_contributing_quickstart.py`, `tests/test_doctrine_context_discipline.py`, `tests/test_install_drift_wiring.py`, `tests/test_pr_citation_lint.py`, `tests/test_skill_doctrine.py`) gave `43 passed`. The full suite gave `3611 passed, 3 skipped, 4 deselected`, and `python qor/scripts/check_variant_drift.py` printed `OK: 406 files, no drift` (the doctrine file is not compiled into `qor/dist`; the six `qor-help` copies are recompiled in Phase 2).

### LD-5: residual - an abandoned session with a pre-seal phase artifact and no seal is not rotated by age

Under LD-2 a session whose directory holds a pre-seal phase artifact and no seal stays current past the TTL indefinitely. This is the accepted cost of never splitting a live chain, and it is an explicit accepted residual, not a mitigated one. Its consequence: if an operator abandons an unsealed cycle and later starts a new phase (for example `/qor-plan` Step 0, which calls `session.get_or_create()`) without ending or rotating the session, the new phase is recorded in the old session directory. Session-scoped state then spans both phases, including the audit history and the session-total VETO counter:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/cycle_count_escalator.py | grep -nE 'def check_session_total'` -> `108:def check_session_total(session_id: str) -> EscalationRecommendation | None:`

This is not new behavior: at the base, an abandoned cycle already carries into the next phase whenever the marker is younger than 24 h. The fix removes the 24 h cut-off, which could only end that carry-over by splitting live chains too. No automatic mitigation is in scope, because telling "abandoned" from "long-running" needs a lifecycle signal that does not exist (non-goal). The CHANGELOG bullet (LD-9) states the residual and the operator action. The operator exits the session explicitly, by ending the session (the marker becomes absent) or by rotating it:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'def end_session'` -> `88:def end_session(marker: Path | None = None) -> None:`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session_tool.py | grep -nE 'sp_rotate = sub.add_parser\("rotate"'` -> `20:    sp_rotate = sub.add_parser("rotate", help="rotate to a fresh session id")`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session_tool.py | grep -nE 'new_id = session.rotate\(\)'` -> `32:    new_id = session.rotate()`

`python -m qor.scripts.session new` alone is not an exit: it is `get_or_create()`, so it keeps a live stale id. Observed in the scratch clone with the Phase 2 `session.py`, on a 25 h marker whose gate directory holds `plan.json`: `python -m qor.scripts.session new` printed the same id; `python -m qor.scripts.session_tool rotate` printed `rotated session: <old> -> <new>` and the marker held the new id; `python -m qor.scripts.session end` followed by `python -m qor.scripts.session new` printed a different id. So the documented reset in `docs/operations.md` (lines 131 and 132: `session.py end`, then `session.py new`) stays accurate and is not edited.

The user-facing note (LD-9) names these commands in the installed CLI form, because `python qor/scripts/session.py` exists only in a source checkout. The CLI entry point runs `qor.scripts.<module>` for `qor-logic scripts <module>`, passing the remaining arguments through, and the `session` module accepts `end`:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:pyproject.toml | grep -nE '^qor-logic = '` -> `59:qor-logic = "qor.cli:main"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/cli.py | grep -nE 'for family in \("reliability", "scripts"\):'` -> `266:    for family in ("reliability", "scripts"):`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/cli.py | grep -nE 'target = f"qor\.\{family\}\.\{args\.module\}"'` -> `285:    target = f"qor.{family}.{args.module}"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'sub.add_parser\("end"'` -> `113:    sub.add_parser("end", help="End session (remove marker)")`

The repository documents this form for its modules: at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `docs/operations.md` gives its module commands as `qor-logic scripts <module> ...` on lines 96, 144 to 146, 232, 238, 267 and 273 (only the session reset on lines 131 and 132 uses the source path), and the Environment sections of five skills, among them `qor/skills/sdlc/qor-plan/SKILL.md` and `qor/skills/sdlc/qor-implement/SKILL.md`, name `qor-logic scripts <module>` as the form that resolves from any shell. (These lines carry inline code spans or placeholders, so they are cited in prose.) Observed in the scratch clone with the Phase 2 `session.py`, through `python -m qor.cli` (the `qor-logic` entry point), on a 25 h marker whose gate directory holds `plan.json`: `qor-logic scripts session new` printed the same id; `qor-logic scripts session_tool rotate` printed `rotated session: <old> -> <new>` and the marker held the new id; `qor-logic scripts session end` exited 0 and removed the marker, and a following `qor-logic scripts session new` printed a new valid id. Each exited 0.

No TTL, rotation command or resolver change is made (non-goals).

Declared limitation (resolution time): `MARKER_PATH` is fixed when `session` is imported, and so is `gate_chain.GATES_DIR`. `_has_unsealed_gate_artifacts` resolves `_workdir.gate_dir()` at call time:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE '^MARKER_PATH = '` -> `23:MARKER_PATH = _workdir.root() / ".qor" / "session" / "current"`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/gate_chain.py | grep -nE '^GATES_DIR = '` -> `21:GATES_DIR = _workdir.gate_dir()`

A process that changes its working directory or `QOR_ROOT` after import can therefore judge liveness against a different gates directory than the one `gate_chain` reads. Likewise, `current(marker=X)` judges liveness against the process's project root, not against X's root. Governed skill runs keep one project root for the process, so the three coincide. This plan changes neither, and the Phase 1 tests rely on call-time resolution (they monkeypatch `_workdir.root`).

### LD-6: every normative statement of the marker rule must match the new rule

Five normative surfaces state or depend on the base rule, which becomes false. The lifecycle doc:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:docs/lifecycle.md | grep -nE 'marker is considered stale'` -> `68:- After 24h of inactivity, the marker is considered stale and a new ID is issued on next read.`

The gate-chain contract: at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `grep -n 'regenerated if older than 24h'` over `qor/gates/chain.md` prints only its line 20, which reads, in full: "Generated by `qor/scripts/session.py get_or_create`. Cached in `.qor/current_session` file, regenerated if older than 24h." (The line carries inline code spans, so it is quoted here in prose rather than as a truth-checked evidence statement.)

The `session.py` module docstring, whose line 7 also names the marker path that `MARKER_PATH` stopped using (it is `.qor/session/current`, LD-5):

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'holds the current id as a single line'` -> `7:- .qor/current_session holds the current id as a single line`

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/scripts/session.py | grep -nE 'Regenerated when missing OR mtime older than 24h'` -> `8:- Regenerated when missing OR mtime older than 24h`

The governance-enforcement doctrine, which offers `get_or_create` (`session new`) as a manual rotation. That was already false for a fresh marker at the base, and after this fix it is also false for a live stale marker (LD-5):

At `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `grep -n 'Manual session rotation'` over `qor/references/doctrine-governance-enforcement.md` prints only its line 109, which reads, in full: "Manual session rotation (e.g., via `python -m qor.scripts.session new`) is". (The line carries an inline code span, so it is quoted here in prose rather than as a truth-checked evidence statement.)

The `/qor-help --stuck` protocol, which lists the cases where `current()` returns `None`. At `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `grep -n 'stale beyond TTL'` over `qor/skills/meta/qor-help/SKILL.md` prints only its line 135, which contains, in full, the parenthetical "(no marker, stale beyond TTL, or invalid format)". After this fix a stale marker whose session is live makes `current()` return its id, so "stale beyond TTL" is no longer a sufficient cause. (The line carries inline code spans and non-ASCII characters, so it is quoted in part here in prose rather than as a truth-checked evidence statement.) The skill is compiled into six copies: `git grep -c 'stale beyond TTL' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor/dist` prints one match in each of `qor/dist/variants/claude/skills/qor-help/SKILL.md`, `qor/dist/variants/cline/workflows/command-qor-help.md`, `qor/dist/variants/codex/skills/qor-help/SKILL.md`, `qor/dist/variants/cursor/skills/qor-help/SKILL.md`, `qor/dist/variants/gemini/commands/qor-help.toml` and `qor/dist/variants/kilo-code/skills/qor-help/SKILL.md`, and nothing else.

Exactly these six source lines change, and no other existing statement of the marker rule changes (the LD-9 CHANGELOG bullet is new text): `docs/lifecycle.md:68`, `qor/gates/chain.md` line 20, `qor/scripts/session.py:7`, `qor/scripts/session.py:8`, `qor/references/doctrine-governance-enforcement.md` line 109 and `qor/skills/meta/qor-help/SKILL.md` line 135 (only its parenthetical). The six compiled `qor-help` copies change only by recompilation. The exact replacement text for each is in Phase 2. The `chain.md` line and docstring line 7 carry the same stale marker path, so the path is corrected in both, since each line is rewritten anyway.

Every replacement that states the age rule states it the same way, and each clause was executed in the scratch clone (LD-1, LD-5): the marker goes stale 24h after it was last written; a read (`current()`, or `get_or_create()` on a fresh marker) does not refresh it; `get_or_create()` re-writes, and so refreshes, the marker when it keeps a stale live id. None of them says "inactivity", because a session in active use still goes stale 24h after its last marker write. Two neighbouring statements were checked and stay accurate unchanged: `docs/lifecycle.md` line 67 ("Session IDs are created or refreshed by `qor/scripts/session.py::get_or_create()`"; after this fix `get_or_create` creates new ids and refreshes a kept stale id) and the `docs/operations.md` reset (LD-5). Completeness: `git grep -nE 'considered stale|regenerated if older than 24h|Regenerated when missing|stale beyond TTL' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor docs/lifecycle.md ':!qor/dist' ':!qor/vendor'` prints exactly four lines: lifecycle line 68, `chain.md` line 20, `session.py` line 8 and `qor-help` line 135. `qor/gates/chain.md` is not compiled into `qor/dist` (`git grep -c 'regenerated if older than 24h' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor/dist` prints nothing), and neither is the doctrine line (`git grep -c 'Manual session rotation' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor/dist` prints nothing). The wider sweep `git grep -nE '24 ?h|24-hour|TTL|inactiv|stale' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor 'docs/*.md' README.md CLAUDE.md CONTRIBUTING.md ':!qor/dist' ':!qor/vendor' ':!docs/archive' ':!docs/plan-*' ':!docs/META_LEDGER.md' | grep -E 'marker|mtime|current\(\)|get_or_create|SESSION_TTL|current_session'` prints exactly eleven lines. Six concern the session marker: lifecycle line 68, `chain.md` line 20, `session.py` lines 8, 24 and 62 (24 and 62 are code), and `qor-help` line 135. Five do not: `docs/research-brief-adr-status-drift-and-extended-status-2026-09-04.md` line 111 (an ADR tracking-tier freshness column), `qor/fixtures/consumer-contract/MANIFEST.json` line 11 and `qor/fixtures/consumer-contract/meta_ledger/stale.md` line 4 (a ledger fixture state named "stale"), `qor/scripts/check_shadow_threshold.py` line 10 (the shadow-threshold marker) and `qor/scripts/governance_index.py` line 114 (the governance-index marker). The `'docs/*.md'` pathspec matches recursively, so `':!docs/archive'` is stated explicitly; with this filter the pipeline prints the same eleven lines without it. (Iteration 4's looser filter on "session", "marker", "staleness" or "inactivity" also matched about a dozen lines of archived third-party material under `docs/archive/2026-04-15/ingest/`, none of which states the Qor marker rule; that was #822 A1.) A separate sweep for manual-rotation guidance, `git grep -nE 'session(\.py)? new|session_tool|rotat' 8ee9d98aad71f059b69231aa370fdbae6bfe52d4 -- qor docs/lifecycle.md docs/operations.md docs/architecture.md docs/policies.md README.md CONTRIBUTING.md ':!qor/dist' ':!qor/vendor' ':!*.py'`, prints 27 lines and finds only doctrine line 109 inaccurate. The other session lines describe `session.rotate()` at the seal (`docs/lifecycle.md` lines 61 and 70, `docs/operations.md` line 49, doctrine lines 92, 93, 103 and 112, the glossary, the `/qor-substantiate` skill and its release-timing reference) or the `end`-then-`new` reset (`docs/operations.md` lines 128 to 135, LD-5), which stay accurate; the rest concern other rotations (secrets, certificates, the hooks log, audit cadence, load balancing) or name session rotation only as a possible cause or a doctrine topic (`docs/operations.md` line 194, `README.md` line 415). Earlier statements of the 24 h rule in dated plans (`docs/plan-qor-phase3-gates.md`, `docs/plan-qor-migration-final.md`) and in dated CHANGELOG sections are historical records and are not edited.

### LD-7: fidelity to the candidate, with every deviation declared

The implemented `qor/scripts/session.py`, `tests/test_session_marker_staleness.py`, `docs/lifecycle.md`, `qor/gates/chain.md`, `qor/references/doctrine-governance-enforcement.md` and `qor/skills/meta/qor-help/SKILL.md` equal the candidate head `5f8be1e2b325825a022172bc3d2b23697eaa1d30` except for exactly these deviations:

1. `docs/lifecycle.md` line 68: replaced by the Phase 2 text instead of the candidate's. The candidate's text says a new id is issued "only if" the directory "is absent, or already sealed", which misstates the empty-directory and no-phase-artifact cases (VETO #819 V2), omits `ideation.json`, keeps the "inactivity" wording (VETO #820 V2), and names Phase 288.
2. `qor/gates/chain.md` line 20: replaced by the Phase 2 text; the candidate leaves it stating the base rule.
3. `qor/scripts/session.py` docstring lines 7 and 8 (LD-6): the candidate leaves both unchanged; this plan corrects them.
4. `qor/scripts/session.py` `_GATE_PHASE_ARTIFACTS` gains `"ideation.json"` as its first member (#819 V3), and its comment names the source set (`gate_chain.IDEATION_PHASE` plus the `gate_chain.CHAIN` phases before `substantiate`) and the pinning tests.
5. `tests/test_session_marker_staleness.py` module docstring: `Phase 288 Phase 1:` reads `Phase 299 Phase 1:`. The module adds `import pytest` and `from qor.scripts import gate_chain`.
6. `tests/test_session_marker_staleness.py` gains `test_stale_valid_marker_with_empty_gate_dir_still_rotates`. Without it no test fails when the phase-artifact membership check is replaced by `True` (mutation M3; observed `7 passed` for the candidate's seven tests under M3).
7. `tests/test_session_marker_staleness.py` gains `test_marker_with_malformed_content_rotates_to_fresh_id` (four contents times two ages, 8 items; #819 V1 and the iteration-3 re-read), `test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current` (#819 V3) and `test_stale_marker_liveness_covers_every_pre_seal_chain_phase` (five parametrized cases; #819 V3).
8. `tests/test_session_marker_staleness.py` gains the helper `_live(root, name, monkeypatch)` and `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` and `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` (four parametrized cases) (#820 V1), plus `test_reads_of_a_fresh_marker_do_not_refresh_it` and `test_current_on_a_stale_live_marker_does_not_refresh_it` (#820 V2). The file then has 15 test functions and 29 collected test items.
9. `qor/references/doctrine-governance-enforcement.md` line 109: replaced by the Phase 2 text (LD-6); the candidate leaves it unchanged.
10. `qor/scripts/session.py` docstrings of `_has_unsealed_gate_artifacts` and `_recoverable_stale_id`: replaced by the Phase 2 text (#821 A1). The candidate's "holds phase work and no seal yet" and "still naming unsealed live work" are imprecise, because a directory holding only `remediate.json` holds phase work and rotates (LD-2).
11. `qor/skills/meta/qor-help/SKILL.md` line 135: its parenthetical is replaced by the Phase 2 text (#822 A2; LD-6); the candidate leaves it unchanged. The six compiled copies under `qor/dist/variants/` follow by recompilation and are outside the fidelity diff, because they are generated.

The candidate's `session.py` logic is otherwise unchanged: the code of `_marker_state`, `_has_unsealed_gate_artifacts`, `_recoverable_stale_id`, `get_or_create` and `current` is the candidate's. With the candidate's `session.py` (no `ideation.json`), the 29-item file gives `3 failed, 26 passed`: the ideation-only test, the `[ideation]` case and the set-equality test fail. That is the #819 V3 gap, now pinned.

The liveness tests use the real clock with margins of at least one hour against the 24-hour TTL (ages 25 h and 1 h; the refresh test compares a just-written mtime with the current time). The two no-refresh tests compare the marker's mtime after the reads with the mtime they set before them, which is exact because no write occurs. The tests do not sleep, use no network, and assert no live repository state; every path is under `tmp_path`. With the Phase 2 `session.py`, the 29-item file was observed green twice in a row (`29 passed`, twice).

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

The same rule excludes ledger entry numbers and hash values from the CHANGELOG:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

Line 14 continues line 13, which opens the `/qor-implement` rule for populating `## [Unreleased]`, and the sentence on lines 14 to 16 reads in full: "Internal refactors, ledger entry numbers, and hash values do NOT appear in the CHANGELOG -- they live in `docs/META_LEDGER.md`." Line 32 continues line 31, the fail-fast rule that an empty `Unreleased` section raises `ValueError` at the stamp. Lines 13, 16 and 31 carry inline code spans and are paraphrased or quoted in prose here rather than as full-line evidence. The doctrine's summary (lines 3 to 5) adds that bullets describe user-facing changes, not implementation details, and line 9 allows `Fixed` as a subsection label.

The note is one `### Fixed` bullet with exactly this text:

```markdown
- **Phase 299 (hotfix; stale session marker keeps its gate chain, GH #483)**: the session marker still goes stale 24h after it was last written, and reads (`current()`, or `get_or_create()` on a fresh marker) do not refresh it. A stale marker now keeps its id while its session is live: the id matches the session-id format, and `.qor/gates/<sid>/` holds `ideation.json`, `research.json`, `plan.json`, `audit.json` or `implement.json` and no `substantiate.json`. Then `current()` returns the id, and `get_or_create()` keeps it and re-writes the marker, which refreshes it, so a cycle that runs past 24h no longer splits its gate chain across two session directories. A stale marker whose directory is absent, empty or sealed, or holds no pre-seal phase artifact, still rotates to a new id, and so does a marker of any age with malformed content. A fresh marker with valid content keeps its id, as before. Accepted residual: an abandoned session whose directory holds a pre-seal phase artifact and no `substantiate.json` now stays current past 24h; after abandoning an unsealed cycle, end the session (`qor-logic scripts session end`) or rotate it (`qor-logic scripts session_tool rotate`) before starting a new phase. `docs/release-state.json` records `0.175.2` as `sealed_unpublished`.
```

It is ASCII only and describes only what is implemented. Conformance with the changelog rule, clause by clause: it carries no ledger entry number and no hash value (its only `#` number is the issue reference `GH #483`; the sealed Phase 298 bullet in the `0.175.2` section likewise names `GH #511`); it names no internal refactor (the private helpers `_marker_state`, `_has_unsealed_gate_artifacts`, `_recoverable_stale_id` and `_GATE_PHASE_ARTIFACTS` do not appear); the functions it names, `current()` and `get_or_create()`, are the `qor.scripts.session` entry points that skills call (`/qor-plan` Step 0 calls `session.get_or_create()`; `/qor-help --stuck` calls `session.current()`), and the commands it names are the operator's installed CLI; it sits under `### Fixed`. Its last sentence has the form of the sealed Phase 298 bullet, whose line 18 in `CHANGELOG.md` at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4` ends "`docs/release-state.json` records `0.175.1` as `sealed_unpublished`." followed by a doctrine pointer (quoted in part in prose, because the line carries inline code spans). The seal provenance of `0.175.2` (META_LEDGER #818) is recorded in `docs/release-state.json` (LD-10), not in the CHANGELOG. Each clause, with its scope and what pins it:

- stale 24h after the last write, and reads (`current()`, or `get_or_create()` on a fresh marker) do not refresh it: LD-1, `test_reads_of_a_fresh_marker_do_not_refresh_it`, `test_current_on_a_stale_live_marker_does_not_refresh_it`;
- a stale marker with valid content whose directory holds a pre-seal phase artifact and no `substantiate.json` keeps its id, `current()` returns it, and `get_or_create()` keeps it and re-writes the marker: LD-2, LD-3, `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`, `test_get_or_create_refreshes_marker_mtime_on_reuse`, the ideation-only, per-phase and set-equality tests;
- a stale marker whose directory is absent, empty or sealed, or holds no pre-seal phase artifact, rotates: `test_stale_valid_marker_with_no_gate_dir_still_rotates`, `test_stale_valid_marker_with_empty_gate_dir_still_rotates`, `test_stale_valid_marker_with_sealed_gate_dir_still_rotates`, `test_stale_marker_with_only_non_pre_seal_artifacts_rotates`;
- a marker of any age with malformed content rotates: `test_marker_with_malformed_content_rotates_to_fresh_id` (25 h and 1 h);
- a fresh marker with valid content keeps its id: LD-3, `test_fresh_marker_is_unaffected`, `test_reads_of_a_fresh_marker_do_not_refresh_it`;
- the residual and the two operator commands: LD-5 (both commands executed in the installed CLI form);
- the release-state record: LD-10 (entry appended in Phase 3).

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

The reason names the seal's ledger entry, as every `sealed_unpublished` precedent does (lines 42, 47, 52, 57, 62, 67 and 72 name `META_LEDGER #792` to `#814`); the immediate precedent:

`git show 8ee9d98aad71f059b69231aa370fdbae6bfe52d4:docs/release-state.json | grep -nE 'META_LEDGER #814'` -> `72:      "reason": "Sealed by /qor-substantiate (META_LEDGER #814); no release tag was pushed to the remote, so the version is sealed but not published."`

The changelog rule that excludes ledger entry numbers (LD-9) governs `CHANGELOG.md`, not this record. The record's own rule fixes its closed shape and leaves `reason` as operator-asserted free text: at `8ee9d98aad71f059b69231aa370fdbae6bfe52d4`, `grep -n 'each entry exactly'` over `qor/references/doctrine-changelog.md` prints only its line 79, which (continuing line 78) gives the closed shape, `schema` and `exceptions`, each entry exactly `version`, `state` and `reason`; lines 91 to 93 say every state is an operator-asserted disposition whose validator checks the shape and the dated CHANGELOG section. (The lines carry inline code spans, so they are cited in prose.)

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

The candidate's test module (LD-7) with the docstring deviation, plus eight test functions and one helper (LD-7 deviations 6 to 8). The module imports `session` from `qor/scripts` via `sys.path` (as the candidate does) and `gate_chain` as `from qor.scripts import gate_chain`, which it only reads for the phase list. Each test isolates state by pointing `session.MARKER_PATH` at `tmp_path / ".qor" / "session" / "current"` and monkeypatching `session._workdir.root` to return `tmp_path`; the set-equality test instead gives each probed name its own root under `tmp_path`, monkeypatches `session._workdir.root` to that root, and passes the marker path to `session.current(marker=...)`. Helper `_write_marker(marker, sid, *, age)` writes the content and sets the mtime `age` into the past with `os.utime`. The fixed id is `2026-04-17T2335-f284b9`; "stale" is age 25 h and "fresh" is age 1 h.

### Unit Tests

- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_unsealed_gate_dir_is_still_current` - stale marker, gate dir holding `plan.json`: `session.current()` returns the id. RED at the base (returns `None`).
- `tests/test_session_marker_staleness.py::test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir` - same setup: `session.get_or_create()` returns the same id. RED at the base (new id).
- `tests/test_session_marker_staleness.py::test_get_or_create_refreshes_marker_mtime_on_reuse` - same setup: after `get_or_create()`, the marker mtime is within `SESSION_TTL` of now. GREEN at the base (the base rotation also writes a fresh marker); it discriminates mutation M1.
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_sealed_gate_dir_still_rotates` - stale marker, gate dir holding `plan.json` and `substantiate.json`: `current()` is `None`, `get_or_create()` returns a different id, and the marker holds that id. GREEN at the base; discriminates M2, M4 and M5.
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_no_gate_dir_still_rotates` - stale marker, no gate dir: `current()` is `None` and `get_or_create()` returns a different id. GREEN at the base; discriminates M4 and M5.
- `tests/test_session_marker_staleness.py::test_absent_marker_is_unaffected` - no marker: `current()` is `None`, and `get_or_create()` writes the id it returns. GREEN at the base and after (regression coverage backfill: preserves the base absent-marker behavior).
- `tests/test_session_marker_staleness.py::test_fresh_marker_is_unaffected` - fresh marker: `current()` and `get_or_create()` both return the id. GREEN at the base and after (regression coverage backfill: preserves the base fresh-marker behavior).
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_empty_gate_dir_still_rotates` (added; LD-7 deviation 6) - stale marker, gate dir exists but is empty: `current()` is `None`, `get_or_create()` returns a different id, and the marker holds that id. GREEN at the base; discriminates M3, M4 and M5.
- `tests/test_session_marker_staleness.py::test_marker_with_malformed_content_rotates_to_fresh_id` (added; #819 V1, iteration-3 re-read), parametrized `kind` in `traversal`, `absolute`, `empty`, `wrong-format`, with content `../../evil`, `str(tmp_path / "abs")`, `""` and `2026-04-17T2335-F284B9`, and `age_h` in `25` (id `stale`) and `1` (id `fresh`). Setup: a marker of that age holding that content; `tmp_path / ".qor" / "gates"` created; `plan.json` placed in the directory that `gates / content` resolves to (`tmp_path / "evil"`, `tmp_path / "abs"`, the gates directory itself, `gates / "2026-04-17T2335-F284B9"`). Assertions: `current()` is `None`, `get_or_create()` returns an id that differs from the content and matches `session.SESSION_ID_PATTERN`, and the marker holds that id. GREEN at the base (the base never reuses malformed content); discriminates M6 (the four `stale` items), M15 (the four `fresh` items) and M7 (all eight).
- `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current` (added; #819 V3) - stale marker, gate dir holding only `ideation.json`: `current()` returns the id, `get_or_create()` returns the same id, and the marker holds it. RED at the base (returns `None`); discriminates M8.
- `tests/test_session_marker_staleness.py::test_stale_marker_liveness_covers_every_pre_seal_chain_phase` (added; #819 V3), parametrized `phase` over `[gate_chain.IDEATION_PHASE, *gate_chain.CHAIN[: gate_chain.CHAIN.index("substantiate")]]`, which evaluates to `ideation`, `research`, `plan`, `audit`, `implement` at the base - stale marker, gate dir holding only `<phase>.json`: `current()` returns the id. RED at the base for all five cases; discriminates M8 (`[ideation]`) and M9 (`[audit]`), and fails if `gate_chain` gains a pre-seal phase the tuple lacks.
- `tests/test_session_marker_staleness.py::test_stale_marker_liveness_set_equals_pre_seal_chain_phases` (added; #820 V1) - the expected set holds `f"{p}.json"` for each phase `p` in the list above. Asserts `sorted(session._GATE_PHASE_ARTIFACTS) == sorted(expected)`. Then, for each name in `sorted(expected | set(session._GATE_PHASE_ARTIFACTS))`, the helper `_live` builds a separate root under `tmp_path` holding a 25 h marker and a gate dir with only that name, points `session._workdir.root` at it, and records whether `session.current(marker=...)` returns the id; the test asserts the recorded live set equals `expected`. RED at the base (`session` has no `_GATE_PHASE_ARTIFACTS`); discriminates M8, M9 and M10, and fails if `gate_chain` gains a pre-seal phase.
- `tests/test_session_marker_staleness.py::test_stale_marker_with_only_non_pre_seal_artifacts_rotates` (added; #820 V1), parametrized `name` in `remediate.json`, `validate.json`, `audit_history.jsonl`, `notes.json` - stale marker, gate dir holding only that file: `current()` is `None`, `get_or_create()` returns a different id, and the marker holds that id. GREEN at the base; discriminates M3, M4 and M5 (all four), M10 (`[remediate.json]`), M11 (`[remediate.json]`, `[validate.json]`, `[notes.json]`) and M12 (all four).
- `tests/test_session_marker_staleness.py::test_reads_of_a_fresh_marker_do_not_refresh_it` (added; #820 V2) - marker written 1 h ago holding the id: `current()` and `get_or_create()` both return the id, and the marker's mtime afterwards equals the mtime set before the calls. GREEN at the base (regression coverage backfill: pins the base read-only behavior that the age rule depends on); discriminates M13.
- `tests/test_session_marker_staleness.py::test_current_on_a_stale_live_marker_does_not_refresh_it` (added; #820 V2) - 25 h marker, gate dir holding `plan.json`: `current()` returns the id, and the marker's mtime afterwards equals the mtime set before the call. RED at the base (returns `None`); discriminates M14.

TDD: `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`, `test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current`, the five `test_stale_marker_liveness_covers_every_pre_seal_chain_phase` cases, `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` and `test_current_on_a_stale_live_marker_does_not_refresh_it` are observed RED before Phase 2 (`10 failed, 19 passed` at the base). The other nineteen items are GREEN before Phase 2 by design, since they pin behavior the fix must keep. Their discrimination is proven after Phase 2 by local, uncommitted mutations of `qor/scripts/session.py`, each run with `python -B -m pytest tests/test_session_marker_staleness.py -q` and then reverted:

- M1: in `get_or_create`, drop the `_atomic_write(marker, recovered + "\n")` call on the stale-live branch -> `test_get_or_create_refreshes_marker_mtime_on_reuse` FAILS.
- M2: in `_has_unsealed_gate_artifacts`, drop the `substantiate.json` check -> `test_stale_valid_marker_with_sealed_gate_dir_still_rotates` FAILS.
- M3: in `_has_unsealed_gate_artifacts`, replace the final `any(...)` with `True` -> `test_stale_valid_marker_with_empty_gate_dir_still_rotates` and all four `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` cases FAIL.
- M4: in `_recoverable_stale_id`, return `content` without the liveness check -> the sealed, no-gate-dir and empty-gate-dir tests and all four `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` cases FAIL.
- M5: in `current`, return `content` for a stale marker without the liveness check -> the same seven items FAIL.
- M6: in `_recoverable_stale_id`, delete the `if not SESSION_ID_PATTERN.match(content): return None` check -> the four `stale` items of `test_marker_with_malformed_content_rotates_to_fresh_id` FAIL (`get_or_create()` returns the malformed content).
- M7: in `current`, delete the `if not SESSION_ID_PATTERN.match(content): return None` check -> all eight `test_marker_with_malformed_content_rotates_to_fresh_id` items FAIL (`current()` returns the malformed content).
- M8: drop `"ideation.json"` from `_GATE_PHASE_ARTIFACTS` -> `test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current`, `test_stale_marker_liveness_covers_every_pre_seal_chain_phase[ideation]` and `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` FAIL.
- M9: drop `"audit.json"` from `_GATE_PHASE_ARTIFACTS` -> `test_stale_marker_liveness_covers_every_pre_seal_chain_phase[audit]` and `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` FAIL.
- M10: append `"remediate.json"` to `_GATE_PHASE_ARTIFACTS` -> `test_stale_marker_liveness_set_equals_pre_seal_chain_phases` and `test_stale_marker_with_only_non_pre_seal_artifacts_rotates[remediate.json]` FAIL.
- M11: in `_has_unsealed_gate_artifacts`, replace the final `any(...)` with `any(p.suffix == ".json" for p in sess_dir.iterdir())` -> `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` `[remediate.json]`, `[validate.json]` and `[notes.json]` FAIL.
- M12: in `_has_unsealed_gate_artifacts`, replace the final `any(...)` with `any(sess_dir.iterdir())` -> all four `test_stale_marker_with_only_non_pre_seal_artifacts_rotates` cases FAIL.
- M13: in `get_or_create`, write the marker (`_atomic_write(marker, content + "\n")`) before returning a fresh marker's content -> `test_reads_of_a_fresh_marker_do_not_refresh_it` FAILS.
- M14: in `current`, write the marker before returning a stale live id -> `test_current_on_a_stale_live_marker_does_not_refresh_it` FAILS.
- M15: in the fresh branch of `get_or_create`, delete the `if SESSION_ID_PATTERN.match(content):` check and return the content unconditionally -> the four `fresh` items of `test_marker_with_malformed_content_rotates_to_fresh_id` FAIL.

Each mutation outcome above was observed while authoring iteration 4 and re-observed with the same counts while authoring iteration 5, in a scratch clone of the base outside the repository, applied to the Phase 2 `session.py` with the 29-item test file. Observed counts: M1 `1 failed, 28 passed`; M2 `1 failed, 28 passed`; M3 `5 failed, 24 passed` (the empty-gate-dir test and the four non-pre-seal cases); M4 `7 failed, 22 passed`; M5 `7 failed, 22 passed`; M6 `4 failed, 25 passed`; M7 `8 failed, 21 passed`; M8 `3 failed, 26 passed`; M9 `2 failed, 27 passed`; M10 `2 failed, 27 passed`; M11 `3 failed, 26 passed`; M12 `4 failed, 25 passed`; M13 `1 failed, 28 passed`; M14 `1 failed, 28 passed`; M15 `4 failed, 25 passed`. Each failing set is exactly the one named above. Over the 150 session-related test files, M10 gives `2 failed, 1282 passed, 4 deselected` and M11 gives `3 failed, 1281 passed, 4 deselected`, so neither leaves the session-related suite green. After each mutation the implementer restores the Phase 2 content, re-runs the Phase 2 fidelity diff to confirm no mutation remains, and runs the file twice GREEN.

## Phase 2: Session marker semantics and lifecycle wording

### Affected Files

- `qor/scripts/session.py` - three-state marker, liveness check, stale-live reuse and refresh; docstring lines 7 and 8; docstrings of `_has_unsealed_gate_artifacts` and `_recoverable_stale_id`.
- `docs/lifecycle.md` - line 68 states the rule exactly (LD-6).
- `qor/gates/chain.md` - line 20 states the rule exactly (LD-6).
- `qor/references/doctrine-governance-enforcement.md` - line 109 names a command that rotates (LD-6).
- `qor/skills/meta/qor-help/SKILL.md` - line 135 lists the exact cases where `current()` returns `None` (LD-6).
- `qor/dist/variants/claude/skills/qor-help/SKILL.md`, `qor/dist/variants/cline/workflows/command-qor-help.md`, `qor/dist/variants/codex/skills/qor-help/SKILL.md`, `qor/dist/variants/cursor/skills/qor-help/SKILL.md`, `qor/dist/variants/gemini/commands/qor-help.toml`, `qor/dist/variants/kilo-code/skills/qor-help/SKILL.md` - regenerated by `python -m qor.scripts.dist_compile`, not edited by hand.
- `qor/dist/manifest.json` and the six `qor/dist/variants/<host>/manifest.json` files - rewritten by the same compile run (not edited by hand; excluded from `check_variant_drift.py`).

### Changes

`qor/scripts/session.py`:

- Add module constants `_GATE_PHASE_ARTIFACTS = ("ideation.json", "research.json", "plan.json", "audit.json", "implement.json")` and `_SEAL_ARTIFACT = "substantiate.json"`, with a comment that the tuple is `gate_chain.IDEATION_PHASE` plus every `gate_chain.CHAIN` phase before `substantiate`, that it is local because `gate_chain` imports this module, and that `tests/test_session_marker_staleness.py` pins the two sets as equal (LD-2).
- Replace `_marker_fresh` with `_marker_state(path: Path, now: datetime) -> str`: `"absent"` when the file is missing, else `"fresh"` when `now - mtime < SESSION_TTL`, else `"stale"`.
- Add `_has_unsealed_gate_artifacts(session_id: str) -> bool`: `sess_dir = _workdir.gate_dir() / session_id`; `False` if `sess_dir` is not a directory or holds `_SEAL_ARTIFACT`; else `any((sess_dir / name).exists() for name in _GATE_PHASE_ARTIFACTS)`.
- Add `_recoverable_stale_id(marker: Path) -> str | None`: read and strip the marker; `None` unless it matches `SESSION_ID_PATTERN`; then the content if `_has_unsealed_gate_artifacts(content)`, else `None`.
- `get_or_create`: compute `state`. On `"fresh"`, return the content if it matches `SESSION_ID_PATTERN` (as at the base). On `"stale"`, if `_recoverable_stale_id(marker)` returns an id, rewrite the marker with `_atomic_write(marker, recovered + "\n")` and return it. Otherwise fall through to the base new-id path unchanged.
- `current`: `None` on `"absent"`; `None` if the content does not match `SESSION_ID_PATTERN`; the content on `"fresh"`; on `"stale"`, the content if `_has_unsealed_gate_artifacts(content)`, else `None`. No write.
- Docstring line 7 becomes exactly: `- .qor/session/current holds the current id as a single line`.
- Docstring line 8 becomes exactly: `- Regenerated when missing, malformed, or stale (last written 24h or more ago; reads do not refresh it), except a stale id whose gate dir holds a pre-seal phase artifact and no substantiate.json, which get_or_create keeps and re-writes (GH #483)`.
- The `_has_unsealed_gate_artifacts` docstring becomes exactly (LD-7 deviation 10):

  ```python
      """True if this session's gate dir holds a pre-seal phase artifact and no seal.

      Pre-seal phase artifacts are the _GATE_PHASE_ARTIFACTS names; the seal is
      _SEAL_ARTIFACT. GH #483: a stale marker naming such a session is kept.
      """
  ```

- The `_recoverable_stale_id` docstring becomes exactly (LD-7 deviation 10): `"""The marker's id if it is valid and its gate dir holds a pre-seal phase artifact and no seal."""`.

`docs/lifecycle.md` line 68 becomes exactly:

```markdown
- The marker goes stale 24h after it was last written: its age is measured from its mtime, and reading it through `current()`, or through `get_or_create()` while it is fresh, does not refresh it. A stale marker keeps its id only while that session is live: the id matches the session-id format, and `.qor/gates/<sid>/` holds at least one pre-seal phase artifact (`ideation.json`, `research.json`, `plan.json`, `audit.json` or `implement.json`) and no `substantiate.json`. Then `current()` returns the id without writing the marker, and `get_or_create()` returns the id and re-writes the marker, which refreshes it, so a long-running cycle does not lose its gate chain to the clock. For a stale marker in any other case (the directory is absent or empty, it holds no pre-seal phase artifact, or it is sealed), and for a marker of any age whose content is malformed, `current()` returns no id and the next `get_or_create()` writes a new ID, as before (GH #483; Phase 299).
```

`qor/gates/chain.md` line 20 becomes exactly:

```markdown
Generated by `qor/scripts/session.py get_or_create`. Cached in `.qor/session/current`. The marker goes stale 24h after it was last written; reads (`current`, or `get_or_create` on a fresh marker) do not refresh it. A stale marker is regenerated unless its session is live: the id matches the session-id format, and `.qor/gates/<sid>/` holds `ideation.json`, `research.json`, `plan.json`, `audit.json` or `implement.json` and no `substantiate.json`. `get_or_create` keeps a live stale id and re-writes its marker, which refreshes it (GH #483).
```

`qor/references/doctrine-governance-enforcement.md` line 109 becomes exactly (line 110 is unchanged):

```markdown
Manual session rotation (e.g., via `python -m qor.scripts.session_tool rotate`) is
```

Each replacement of `docs/lifecycle.md` line 68, `qor/gates/chain.md` line 20, doctrine line 109 and docstring lines 7 and 8 is one line; every replacement, the two function docstrings included, is ASCII only, and every clause matches `_marker_state`, `_has_unsealed_gate_artifacts`, `_recoverable_stale_id`, `get_or_create`, `current` and `session_tool rotate` as specified above. Clause to test (Phase 1): stale 24h after the last write (the 25 h and 1 h cases throughout); reads do not refresh (`test_reads_of_a_fresh_marker_do_not_refresh_it`, `test_current_on_a_stale_live_marker_does_not_refresh_it`); a live stale id is kept (`test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, `test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`, the ideation-only and per-phase tests); `get_or_create` re-writes and refreshes it (`test_get_or_create_refreshes_marker_mtime_on_reuse`); the live set is exactly the five pre-seal artifacts (`test_stale_marker_liveness_set_equals_pre_seal_chain_phases`); a stale marker naming an absent, empty, no-pre-seal-artifact or sealed directory rotates (`test_stale_valid_marker_with_no_gate_dir_still_rotates`, `test_stale_valid_marker_with_empty_gate_dir_still_rotates`, `test_stale_marker_with_only_non_pre_seal_artifacts_rotates`, `test_stale_valid_marker_with_sealed_gate_dir_still_rotates`); malformed content rotates at any age (`test_marker_with_malformed_content_rotates_to_fresh_id`); a fresh marker with valid content keeps its id (`test_fresh_marker_is_unaffected`, `test_reads_of_a_fresh_marker_do_not_refresh_it`). The `session_tool rotate` behavior is existing code that this plan does not change; it was executed in the scratch clone (LD-5). Applied in the scratch clone, the seven test files that mention `chain.md` or `lifecycle.md`, plus `tests/test_gates.py` and `tests/test_e2e.py`, gave `95 passed`.

`qor/skills/meta/qor-help/SKILL.md` line 135: only the parenthetical changes. The text `(no marker, stale beyond TTL, or invalid format)` becomes exactly:

```markdown
(no marker, invalid format, or a stale marker, last written 24h or more ago, whose gate dir is absent, empty or sealed, or holds no pre-seal phase artifact)
```

The rest of the line, including its existing non-ASCII characters (two em-dashes and a section sign), is unchanged: they are outside the corrected clause, the file already carries non-ASCII characters on eight other lines, and rewriting them would widen a one-clause correction. The replacement text is ASCII only. Each case matches `current()` as specified above: an absent marker (`test_absent_marker_is_unaffected`); malformed content at any age (`test_marker_with_malformed_content_rotates_to_fresh_id`); a stale marker, `_marker_state` returning `"stale"` at 24h after the last write, whose directory is absent, empty, sealed or holds no pre-seal phase artifact (`test_stale_valid_marker_with_no_gate_dir_still_rotates`, `test_stale_valid_marker_with_empty_gate_dir_still_rotates`, `test_stale_valid_marker_with_sealed_gate_dir_still_rotates`, `test_stale_marker_with_only_non_pre_seal_artifacts_rotates`). In every other case `current()` returns the id (a fresh marker with valid content, and a stale live marker: `test_fresh_marker_is_unaffected`, `test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, the ideation-only and per-phase tests), and step 2 of the protocol then globs that session's own directory, which is the intended routing for a long-running cycle.

After editing the skill, run `python -m qor.scripts.dist_compile` (the repository's compile step, `docs/operations.md` line 124). Observed in the scratch clone: at the base alone the compile run rewrites only the seven `manifest.json` files (their `generated_ts` and file hashes were already stale at the base); with the skill edit it additionally rewrites exactly the six compiled `qor-help` copies listed under Affected Files, each by the same one-clause change (the gemini TOML copy included), and the manifests then differ from the base-only run only in `generated_ts` and the `qor-help` hash line. No other file changes. No new test is added for the skill line: a test that asserts the prose is present would be a presence-only test (`qor/references/doctrine-test-functionality.md`); the behavior the line states is pinned by the Phase 1 tests named above, and the compiled copies are pinned by `check_variant_drift.py` and `tests/test_install_sync_with_source.py`, which fail when the compile step is skipped (observed: `DRIFT DETECTED: 6 difference(s)`, one per compiled `qor-help` copy, and `4 failed` in `test_claude_variant_skill_sync`, `test_codex_variant_skill_sync`, `test_kilo_code_variant_skill_sync` and `test_cursor_variant_skill_sync`). `python -m qor.reliability.skill_admission qor-help` prints `ADMITTED: qor-help` (admission reads only the frontmatter, which is unchanged), and `skill_size_budget_lint` reports the same three pre-existing WARN findings as at the base (`qor-help` grows from 12330 to 12438 bytes, far under the 25 KB WARN threshold).

`end_session`, `rotate`, `generate_id`, `validate_session_id` and `main` do not change.

### Unit Tests

- Re-run `tests/test_session_marker_staleness.py` after the edit: all 29 items GREEN, twice in a row.
- Run mutations M1-M15 (Phase 1) and observe each named failure; revert.
- Run `tests/test_gates.py` and `tests/test_e2e.py` unchanged: GREEN (LD-4).
- After `python -m qor.scripts.dist_compile`: `python qor/scripts/check_variant_drift.py` prints `OK: 406 files, no drift`, and `tests/test_install_sync_with_source.py`, `tests/test_skill_prose_filesystem_validation.py`, `tests/test_qor_help_conversational.py` and `tests/test_skill_doctrine.py` stay GREEN.
- Fidelity check (LD-7), after `git fetch origin fix/483-session-marker-current`: `git diff 5f8be1e2b325825a022172bc3d2b23697eaa1d30 -- qor/scripts/session.py docs/lifecycle.md qor/gates/chain.md qor/references/doctrine-governance-enforcement.md qor/skills/meta/qor-help/SKILL.md tests/test_session_marker_staleness.py` shows only deviations 1-11. The implementer records the observed diff summary in the implementation report.

## Phase 3: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.2` `sealed_unpublished` entry (LD-10).
- `CHANGELOG.md` - the Phase 299 bullet under `## [Unreleased]` (LD-9). No dated section is edited.

### Changes

Append the LD-10 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-9 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.3]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-10).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` stays GREEN, which proves the record validates with the new entry, and `python -m pytest tests/test_changelog_format.py -q` stays GREEN with the LD-9 bullet under `### Fixed` (observed in the scratch clone with both Phase 3 edits applied).
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.3`, remote tags only). At the base, before the entry exists, it prints `{'0.175.2'} {'0.175.2'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.2'}`: no orphan with the entry, exactly `{'0.175.2'}` with the entry removed in memory. That shows the entry is what keeps coverage green.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.3` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.2` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in a scratch clone of the base outside the repository with `origin` set to the real remote; the simulated commits never entered this repository):
  - base commit (`version = "0.175.2"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.3 (project version 0.175.2)`;
  - a commit that bumps `version` to `0.175.3` without the `[0.175.3]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.3 (project version 0.175.3)`;
  - simulated seal commit (`version = "0.175.3"`, `## [0.175.3] - ` section, local `v0.175.3` tag), no `0.175.2` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.2`;
  - the same seal commit with the LD-10 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: stale-but-live session marker keeps its gate chain

- **D1**: the marker still goes stale 24h after it was last written, and reads (`current()`, or `get_or_create()` on a fresh marker) do not refresh it. A stale marker whose valid id names a gate directory holding `ideation.json`, `research.json`, `plan.json`, `audit.json` or `implement.json` and no `substantiate.json` is treated as the current session: `current()` returns it without writing, and `get_or_create()` reuses it and re-writes the marker, which refreshes it. Absent markers, and stale markers naming a missing, empty or sealed gate directory or one that holds none of those five files, keep the base behavior. Fresh markers with valid content keep their id whatever their gate directory holds, as at the base. Markers with malformed content (traversal, absolute path, empty, wrong format), stale or fresh, are never used as a path segment for reuse and rotate to a fresh id. The LD-5 residual and limitation are declared.
- **D2**: `qor/scripts/session.py` defines `_GATE_PHASE_ARTIFACTS = ("ideation.json", "research.json", "plan.json", "audit.json", "implement.json")`, `_marker_state(path: Path, now: datetime) -> str`, `_has_unsealed_gate_artifacts(session_id: str) -> bool` and `_recoverable_stale_id(marker: Path) -> str | None`, and no longer defines `_marker_fresh`. `_recoverable_stale_id` and `current` both check `SESSION_ID_PATTERN` before any gate-directory lookup. `get_or_create` and `current` keep their signatures (LD-4). The Phase 2 fidelity diff against `5f8be1e2b325825a022172bc3d2b23697eaa1d30` shows only LD-7 deviations 1-11.
- **D3**: `docs/lifecycle.md` line 68, `qor/gates/chain.md` line 20, `qor/scripts/session.py` docstring lines 7 and 8, the `_has_unsealed_gate_artifacts` and `_recoverable_stale_id` docstrings, `qor/references/doctrine-governance-enforcement.md` line 109 and the parenthetical on `qor/skills/meta/qor-help/SKILL.md` line 135 carry exactly the Phase 2 text, the six compiled `qor-help` copies are regenerated by `python -m qor.scripts.dist_compile` and `python qor/scripts/check_variant_drift.py` reports no drift, and no other existing statement of the marker rule changes (LD-6). Phase 299 follows canonical branch and plan resolution and receives current-revision audit and substantiation evidence before promotion; no evidence from the candidate branch is reused as authority. The `## [Unreleased]` bullet carries exactly the LD-9 text at implement time, including the LD-5 residual and its operator action.
- **D4**: `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_unsealed_gate_dir_is_still_current`, `tests/test_session_marker_staleness.py::test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir`, `tests/test_session_marker_staleness.py::test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current`, the five `tests/test_session_marker_staleness.py::test_stale_marker_liveness_covers_every_pre_seal_chain_phase` cases, `tests/test_session_marker_staleness.py::test_stale_marker_liveness_set_equals_pre_seal_chain_phases` and `tests/test_session_marker_staleness.py::test_current_on_a_stale_live_marker_does_not_refresh_it` are RED before Phase 2 and GREEN after (`10 failed, 19 passed` at the base). All 29 items are GREEN twice in a row after Phase 2. `tests/test_session_marker_staleness.py::test_marker_with_malformed_content_rotates_to_fresh_id` is GREEN in all eight items; its four `stale` items turn RED under M6, its four `fresh` items under M15, and all eight under M7. Each mutation M1-M15 turns exactly its named tests RED, and `tests/test_gates.py` and `tests/test_e2e.py` stay GREEN.

### Deliverable: release-state continuity for 0.175.2

- **D1**: after the Phase 299 seal bumps the project version to `0.175.3`, `0.175.2` (sealed on `main` at META_LEDGER #818, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.2` / `sealed_unpublished` with the LD-10 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.2` to `0.175.3` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.2'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.3` with a dated `[0.175.3]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_session_marker_staleness.py -q` - verifies the stale versus absent marker semantics, the malformed-content guard, the pre-seal liveness set and the no-refresh-on-read rule (29 test items).
- `python -m pytest tests/test_gates.py tests/test_e2e.py -q` - verifies existing session and gate-chain behavior is unchanged.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-9 bullet keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.3'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.3', ex).orphans, rs.coverage_violations(versions, tags, '0.175.3', {k: v for k, v in ex.items() if k != '0.175.2'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.2'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.3' and '## [0.175.3] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.3 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.3`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/check_variant_drift.py` - verifies installed/generated variant consistency, including the six recompiled `qor-help` copies.
- `python -m pytest tests/test_install_sync_with_source.py tests/test_skill_prose_filesystem_validation.py tests/test_qor_help_conversational.py -q` - verifies the compiled skill copies match source and the `/qor-help --stuck` protocol still cites the session validator.
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
- changes to `gate_chain`, `validate_gate_artifact`, `session_tool` or any other caller of `session` (`gate_chain` is only read by the new test);
- automatic detection of abandoned sessions, or import-time versus call-time root reconciliation (LD-5);
- edits to dated plans or dated CHANGELOG sections that record the old 24 h rule (LD-6);
- release-state dispositions for any version other than `0.175.2`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- reusing any evidence from the candidate branch as audit, implementation or seal authority;
- hand-issuing governance evidence;
- unrelated repository cleanup.
