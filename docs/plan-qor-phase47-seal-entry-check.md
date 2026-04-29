# Plan: Phase 47 — Seal Entry Check (SG-AdjacentState-A countermeasure)

**change_class**: feature

Closes the bookkeeping-gap class that allowed Phase 46's original substantiate to skip ledger entries entirely. Documented as the sixth instance of SG-AdjacentState-A in [Entry #152](docs/META_LEDGER.md). Adds a new reliability gate `qor/reliability/seal_entry_check.py` and wires it into `/qor-substantiate` as a new Step 7.7 (post-seal verification), running *after* Step 7 (Final Merkle Seal) writes the SESSION SEAL ledger entry the check verifies.

**Pass 2 amendment**: addresses Pass 1 VETO ([Entry #153](docs/META_LEDGER.md)). The Pass 1 plan placed the new gate in Step 4.6 (Reliability Sweep) which runs before Step 7 (the seal-entry-write); the gate's precondition was structurally false at that step. Pass 2 moves the gate to a new Step 7.7 (after Step 7), eliminates the undefined `$MERKLE_SEAL` shell variable by having the helper read the latest entry's chain hash directly from the ledger (no caller-supplied expectation), and replaces shell-interpolation `python -c "...('$VAR')..."` with argv-form CLI invocation. Phase 1 (helper module + tests) is unchanged in content but loses the `expected_merkle_seal` argument — the helper now verifies the latest entry's chain hash is internally consistent (chain_hash == chain_hash(content_hash, previous_hash)) rather than equal to a caller-supplied value. Result: simpler API, single source of truth (the ledger).

**Pass 3 amendment**: addresses Pass 2 VETO ([Entry #154](docs/META_LEDGER.md)). The Pass 2 bash example for deriving `$PLAN_PATH` from the session file would have produced empty output (session file format is `2026-04-28T0247-92f578`, not a phase number; plan filenames need the phase number). Pass 3 replaces the broken bash with a one-liner that calls the grounded helper `governance_helpers.current_phase_plan_path()` directly. The `python -c` invocation is hardcoded — no shell-variable interpolation into Python literals — so V-3 stays resolved. Phase 1 helper, Phase 1 tests, Phase 2 step-numbering placement (Step 7.7), and Phase 2 defensive countermeasure tests are all unchanged.

## Open Questions

None. Design fully resolved during dialogue:

- **Script location**: `qor/reliability/seal_entry_check.py` — matches sibling scripts (`intent_lock.py`, `skill_admission.py`, `gate_skill_matrix.py`).
- **Function shape**: pure functions returning a typed result; CLI wrapper for skill-step invocation. Same pattern as `skill_admission.py` (pure `discover_skills` + `admit` functions, CLI shell on top).
- **Phase identity**: helper resolves it internally via `governance_helpers.derive_phase_metadata(plan_path)`. Caller passes `--plan <path>` only; no shell-level phase derivation. Eliminates Pass 1 V-3 shell-injection vector.
- **Merkle seal acquisition**: the helper reads the latest entry's chain hash from the ledger and verifies internal consistency (`chain_hash == chain_hash(content_hash, previous_hash)`). No caller-supplied `expected_merkle_seal` argument; the ledger is the single source of truth for what the seal hash IS. Eliminates Pass 1 V-2 undefined-variable defect.
- **Wiring location**: new `/qor-substantiate` **Step 7.7** (post-seal verification), running *after* Step 7 (Final Merkle Seal, [SKILL.md:266](qor/skills/governance/qor-substantiate/SKILL.md)) writes the entry. Eliminates Pass 1 V-1 sequencing infrastructure mismatch. Same `ABORT on non-zero exit` pattern as the Step 4.6 reliability gates.
- **Scope discipline**: this phase ONLY adds the runtime gate. It does NOT retrofit historical ledger gaps, does NOT add a parallel pre-audit check, and does NOT modify the existing reliability scripts.

## Phase 1: Pure-function helper + tests

### Affected Files

- `tests/test_seal_entry_check.py` — new; behavioral tests for the verification function across valid/invalid ledger fixtures.
- `qor/reliability/seal_entry_check.py` — new; pure-function module with optional CLI entry.

### Unit Tests (write first)

All tests build synthetic META_LEDGER fixtures in tmpdir, invoke `seal_entry_check.check()`, and assert the returned `SealEntryResult` against expected values. Per `qor/references/doctrine-test-functionality.md`: each test invokes the unit and asserts on its output, not on artifact presence.

- `tests/test_seal_entry_check.py` — covers:
  - `test_check_passes_when_latest_entry_is_seal_for_current_phase` — fixture: 3 entries (audit/impl/seal) where the seal entry's phase number matches the supplied phase and the chain hash is internally consistent (`chain_hash == chain_hash(content_hash, previous_hash)`). Invokes `check(ledger_path=..., phase_num=47)`. Asserts `result.ok is True` and `result.errors == []`.
  - `test_check_fails_when_latest_entry_is_not_a_seal` — fixture: latest entry is IMPLEMENTATION (no SEAL appended). Invokes `check`. Asserts `result.ok is False` and `result.errors[0]` names the latest entry's actual kind ("IMPLEMENTATION") and the missing-seal condition.
  - `test_check_fails_when_seal_phase_number_mismatches` — fixture: latest entry is `SESSION SEAL -- Phase 46 ...` but caller supplies `phase_num=47`. Asserts `result.ok is False` and `result.errors` names the mismatch (expected 47, found 46).
  - `test_check_fails_when_chain_hash_internally_inconsistent` — fixture: valid SEAL entry shape but the entry's `chain_hash` field does NOT equal `chain_hash(content_hash, previous_hash)`. Invokes `check`. Asserts `result.ok is False` and `result.errors` cites the mismatch with both the recorded and recomputed values, mirroring `ledger_hash.py verify` output discipline.
  - `test_check_fails_when_full_chain_verification_fails` — fixture: latest entry is correct internally, but a prior entry's chain is broken. Invokes `check`. Asserts `result.ok is False` and `result.errors` cites which earlier entry failed (delegates to `ledger_hash.verify()`).
  - `test_check_replays_phase_46_original_gap` — meta-test: fixture replays Phase 46's pre-remediation state (META_LEDGER ends at Entry #146 = Phase 44 seal; Phase 46 seal commit exists but no ledger entries added). Invokes `check(ledger_path=..., phase_num=46)`. Asserts `result.ok is False` because the latest entry is `SESSION SEAL -- Phase 44 ...` (phase 44 ≠ 46) — proving this is the structural countermeasure that would have caught the original Phase 46 gap. Test name documents the historical incident.
  - `test_cli_resolves_phase_from_plan_path_argv` — invokes `python -m qor.reliability.seal_entry_check --ledger <path> --plan <path>` via `subprocess.run` (argv form, NO shell interpolation). Asserts `returncode == 0` against a passing fixture. The CLI internally calls `derive_phase_metadata(plan)` to extract phase_num — Pass 2 directly addresses Pass 1 V-3 (shell injection). The test name documents that the CLI accepts `--plan` and resolves phase internally.
  - `test_cli_exits_zero_on_pass_and_one_on_fail` — invokes the CLI twice against passing and failing fixtures. Asserts (returncode 0, stdout contains "OK") and (returncode 1, stderr contains the error message returned by `check()`). Confirms the skill-step wiring (which depends on exit code) works end-to-end.
  - `test_cli_rejects_path_with_shell_metacharacters_safely` — invokes the CLI with `--plan` set to a path containing characters that would have broken the Pass 1 shell interpolation (single quote, backslash, dollar sign in a tmpdir filename). Asserts the CLI either processes the path correctly or fails with a parse error from Python's argparse — never executes injected code, never silently expands to empty. Confirms argv-form invocation eliminates the OWASP A03 vector flagged in Pass 1 V-3.

Run: `python -m pytest tests/test_seal_entry_check.py -v` (matches CI's `python -m pytest tests/ -v`).

### Implementation

`qor/reliability/seal_entry_check.py`:

```python
"""Seal entry check — verify substantiate appended a SESSION SEAL ledger entry.

Closes SG-AdjacentState-A: a class of bookkeeping gaps where /qor-substantiate
runs to completion (commit, tag, push) without appending the mandatory
SESSION SEAL entry to docs/META_LEDGER.md. Phase 46's first substantiate
sealed at v0.33.0 without writing entries #150-#152; intent-lock and the
existing reliability gates did not catch it.

Usage:
    seal_entry_check.py --ledger <path> --plan <path> [--repo <dir>]

Returns 0 on PASS, 1 on FAIL with error message on stderr.
"""
from dataclasses import dataclass

@dataclass
class SealEntryResult:
    ok: bool
    errors: list[str]

def check(ledger_path: Path, phase_num: int) -> SealEntryResult:
    ...
```

Three internal helpers:

- `_parse_latest_entry(text: str) -> dict | None` — pure regex parse. Returns the latest `### Entry #N: ...` block as a dict with `entry_num`, `kind` ("GATE TRIBUNAL" / "IMPLEMENTATION" / "SESSION SEAL"), `phase_num`, `content_hash`, `previous_hash`, `chain_hash`, or `None` if no entries found.
- `_verify_chain(text: str) -> tuple[bool, list[str]]` — wraps `qor.scripts.ledger_hash.verify()`. Returns `(ok, errors)` where errors are file:line citations from the verifier output.
- `check()` composes the two: parse → assert kind == SESSION SEAL → assert phase_num matches → assert latest entry's `chain_hash == ledger_hash.chain_hash(content_hash, previous_hash)` (internal consistency) → run full chain verification → return `SealEntryResult`. The Merkle seal value is read from the ledger, not supplied by the caller — single source of truth.

CLI wrapper at module bottom: parses argv via `argparse` (NOT shell interpolation), calls `derive_phase_metadata(plan)` internally to get `phase_num`, calls `check`, prints result, exits 0/1.

Constraints satisfied:

- **Pure**: `check()` reads files but does no network/random/time. Deterministic.
- **No coupling to substantiate skill state**: takes ledger path + phase_num as args; doesn't read session state, doesn't depend on `$MERKLE_SEAL` or any other shell variable. Skill-step shell wrapper (in Step 7.7) supplies `--ledger` and `--plan` paths only.
- **No injection surface**: argparse parses argv; the CLI does not expand or eval any string.
- **Single source of truth**: the ledger holds the Merkle seal value; the helper reads it rather than asking the caller to repeat it. Chain verification delegates to existing `ledger_hash.verify()` rather than duplicating regex.
- **Razor**: `check()` projected at ~22 lines, file ~110 lines (well under limits).

## Phase 2: Wire into /qor-substantiate as new Step 7.7

### Affected Files

- `tests/test_substantiate_seal_entry_wiring.py` — new; verifies the skill prompt contains the wiring text via proximity-anchored assertion paired with strip-and-fail negative-path test (per Phase 46 doctrine).
- `qor/skills/governance/qor-substantiate/SKILL.md` — modify; insert new Step 7.7 between Step 7.6 (Stamp CHANGELOG, line 290) and Step 8 (Cleanup Staging, line 307).

### Unit Tests (write first)

- `tests/test_substantiate_seal_entry_wiring.py` — covers:
  - `test_step_7_7_invokes_seal_entry_check` — reads `qor/skills/governance/qor-substantiate/SKILL.md`. Within a bounded span starting at the `### Step 7.7` header, asserts the proximity-anchored regex matches `qor.reliability.seal_entry_check` and the ABORT discipline (`|| ABORT`). Invokes the file-read + regex match (the unit under test is the skill prompt's enforcement language); asserts the match result, not just substring presence.
  - `test_step_7_7_negative_path` — strip-and-fail pair. Mutates the SKILL.md content in-memory to remove the Step 7.7 section; asserts the same regex match returns None. Proves the positive assertion is anchored to the section, satisfying Phase 46's strip-and-fail pairing requirement (SG-035 self-defense).
  - `test_step_7_7_runs_after_step_7_seal_write` — positional assertion: re-reads the file and confirms the byte offset of `### Step 7.7` is greater than `### Step 7:` (Final Merkle Seal). The seal entry must already exist at this step. **Direct countermeasure to Pass 1 V-1**: the test fails if a future edit moves the gate back to Step 4.6 or any pre-Step-7 location.
  - `test_step_7_7_does_not_use_python_c_shell_interpolation` — reads the Step 7.7 code block; asserts the bash does NOT contain the pattern `python -c ".*'\$.*'"` (single-quoted Python string literal containing a shell variable reference). **Direct countermeasure to Pass 1 V-3**: the test fails if a future edit reintroduces the injection vector.
  - `test_step_7_7_uses_argv_form_for_plan_path` — reads the Step 7.7 code block; asserts the wiring uses `--plan "$PLAN_PATH"` (or equivalent argv form, double-quoted to handle paths with spaces). Confirms the helper receives the plan path as an argument, not via interpolation. The test invokes the regex match against the bash and asserts the match returns a result with the expected argv pattern.
  - `test_step_7_7_does_not_reference_undefined_merkle_seal_variable` — asserts the Step 7.7 code block does NOT contain `$MERKLE_SEAL` or `--merkle`. **Direct countermeasure to Pass 1 V-2**: the helper resolves the seal hash from the ledger; the wiring must not pretend to pass a value it cannot have.

Run: `python -m pytest tests/test_substantiate_seal_entry_wiring.py -v`.

### Implementation

Edit `qor/skills/governance/qor-substantiate/SKILL.md` to insert Step 7.7 between existing Step 7.6 (Stamp CHANGELOG) and Step 8 (Cleanup Staging):

```markdown
### Step 7.7: Post-seal verification (Phase 47 wiring)

Closes SG-AdjacentState-A (Phase 46's sixth instance: substantiate sealed at v0.33.0 without writing META_LEDGER entries #150-#152; intent-lock and the Step 4.6 reliability gates did not catch it because they run before the seal entry is written).

Runs after Step 7 (Final Merkle Seal) has appended the SESSION SEAL entry to `docs/META_LEDGER.md`. Verifies the entry exists for this phase and the latest chain hash is internally consistent. ABORT on non-zero exit, leaving the session unsealed.

​```bash
PLAN_PATH=$(python -c "from qor.scripts.governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")

python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --plan "$PLAN_PATH" || ABORT
​```

The `python -c` is hardcoded — no shell variable is interpolated into the Python source — so V-3's injection vector stays closed. `current_phase_plan_path()` ([qor/scripts/governance_helpers.py:57-67](qor/scripts/governance_helpers.py:57)) reads the git branch name (`phase/NN-slug`) via `git symbolic-ref` and globs `docs/plan-qor-phase{NN}*.md`. The helper resolves phase number from the plan file path internally and reads the latest entry's chain hash from the ledger; no caller-supplied Merkle seal expectation. Argv-form invocation throughout.
```

(Plan file note: the bash `​```` fences shown in the inline draft above are placeholders; the actual SKILL.md edit uses standard triple-backtick fences.)

The five-step seal phase becomes: 7 (Final Merkle Seal) → 7.5 (version bump) → 7.6 (Stamp CHANGELOG) → 7.7 (post-seal verification, NEW) → 8 (Cleanup Staging). The new step runs at the end of the seal cycle, after the entry exists, after the version is bumped, after the changelog is stamped — guaranteed to have the seal entry to verify.

Variant artifacts (`qor/dist/variants/{claude,codex,gemini,kilo-code}`) regenerate via `BUILD_REGEN=1 python qor/scripts/dist_compile.py` post-edit; covered by existing `tests/test_compile.py` which the implementer runs before commit.

## CI Commands

To validate this plan locally before pushing:

```
python -m pytest tests/test_seal_entry_check.py tests/test_substantiate_seal_entry_wiring.py -v
python -m pytest tests/ -v
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```

The first command is the focused phase-47 suite; the remaining three match the gates in `.github/workflows/ci.yml`.
