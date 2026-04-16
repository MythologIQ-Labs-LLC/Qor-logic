## Phase 17 — Reliability Scripts (B49/B50/B51)

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/17-reliability-scripts`
**Target version**: `0.7.0 → 0.8.0`

## Open Questions

None. Legacy implementations exist at `qor/scripts/legacy/intent-lock.py` (43 lines, grounded via `wc -l qor/scripts/legacy/intent-lock.py` 2026-04-16), `qor/scripts/legacy/admit-skill.py` (60 lines, grounded 2026-04-16), and `qor/scripts/legacy/gate-skill-matrix.py` (92 lines, grounded 2026-04-16). These inform spec but are superseded — current repo has no `processed/` directory; skills live under `qor/skills/**` (grounded via `find qor/skills -name SKILL.md | wc -l` → 28 skill files, 2026-04-16). The legacy `INTENT_LOCK.json`-style semantics (manual declaration) are replaced with fingerprint-capture semantics (plan + audit + HEAD hash). Legacy admission is path-based; new admission is name-based against a registry built from live skill discovery.

No `.qor/` runtime directory exists yet (grounded via `ls .qor/` 2026-04-16 → absent). Scripts must create their session subdirs on first use.

## Constraints

- Python stdlib + existing `jsonschema` only. No new dependencies.
- Each new script file: <250 lines (Section 4 Razor). Each function: <40 lines.
- TDD-first: write failing test, then implement.
- Deterministic test runs required (no network, no wall-clock coupling, no random seeds).
- `qor/skills/sdlc/qor-remediate/SKILL.md` is out of scope (Phase 18 parallel).
- User-global `~/.claude/skills/` is out of scope.
- **SG-036 active**: every file-size/location claim below carries inline `wc -l` or equivalent provenance with date 2026-04-16.
- **SG-038 active**: prose, code blocks, and Success Criteria below cite the same 3 scripts, same 2 skills edited, and same 11 new tests (see SG-038 Lockstep Manifest below).

## SG-038 Lockstep Manifest (canonical counts)

All other sections of this plan must quote these exact numbers:

- **New scripts**: 3 (`tools/reliability/intent-lock.py`, `tools/reliability/skill-admission.py`, `tools/reliability/gate-skill-matrix.py`)
- **Skills edited**: 2 (`qor/skills/sdlc/qor-implement/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`)
- **New test functions**: 11 (see per-track test counts: Track 1 = 4, Track 2 = 3, Track 3 = 3, Track 4 = 1)
- **New test file**: 1 (`tests/test_reliability_scripts.py`)
- **Baseline tests**: 234 passing + 6 skipped (grounded via `python -m pytest tests/ -q` 2026-04-16)
- **Target tests**: 245 passing + 6 skipped (234 + 11)

## Tracks

### Track 1 — `tools/reliability/intent-lock.py`

**Affected Files**

- `tools/reliability/intent-lock.py` (new, projected ~100 lines)
- `tests/test_reliability_scripts.py` (new test file; intent-lock covers 4 tests)

**Behavior**

Two subcommands: `capture` and `verify`.

`capture --session <sid> --plan <path> --audit <path>`:
1. Read plan file, compute SHA-256 of bytes.
2. Read audit report, compute SHA-256 of bytes. If audit content does not contain "PASS" verdict line, exit 1 with reason "audit not PASS".
3. Read current HEAD commit via `git rev-parse HEAD` (subprocess, no network).
4. Write JSON fingerprint to `.qor/intent-lock/<sid>.json`: `{session, plan_path, plan_hash, audit_path, audit_hash, head_commit, captured_ts}`. `captured_ts` is the UTC ISO timestamp of capture.
5. Exit 0, print `LOCKED: <sid>`.

`verify --session <sid>`:
1. Load `.qor/intent-lock/<sid>.json`. If missing, exit 1 with "NO LOCK".
2. Re-hash the plan file at the stored path; if it differs from stored `plan_hash`, exit 1 with "DRIFT: plan".
3. Re-hash the audit at the stored path; if it differs, exit 1 with "DRIFT: audit".
4. Read current HEAD; if it differs from stored `head_commit`, exit 1 with "DRIFT: head".
5. Exit 0, print `VERIFIED: <sid>`.

Determinism: timestamps are captured but never compared; verify is pure content-hash equality. No network. Git subprocess runs with a fixed working directory argument.

**Tests (4 new)**

1. `test_intent_lock_capture_writes_fingerprint` — capture against a tmp plan, tmp audit (containing "PASS"), tmp git dir; assert output JSON has all required keys.
2. `test_intent_lock_verify_passes_when_unchanged` — capture then verify immediately; exit 0.
3. `test_intent_lock_verify_detects_plan_drift` — capture, mutate plan, verify; exit 1 with "DRIFT: plan".
4. `test_intent_lock_capture_rejects_non_pass_audit` — capture against audit lacking "PASS"; exit 1 with "audit not PASS".

### Track 2 — `tools/reliability/skill-admission.py`

**Affected Files**

- `tools/reliability/skill-admission.py` (new, projected ~80 lines)
- `tests/test_reliability_scripts.py` (skill-admission covers 3 tests)

**Behavior**

`skill-admission.py <skill-name>`:
1. Discover skills: walk `qor/skills/**/SKILL.md`, derive skill name from directory basename (e.g. `qor-implement`).
2. If `<skill-name>` not in discovered set, exit 1, print `NOT-ADMITTED: <name> reason=unregistered`.
3. Load the skill file. Verify YAML frontmatter exists (lines starting and ending with `---`) and contains required keys: `name`, `description`, `phase`.
4. If any required frontmatter key missing, exit 1, print `NOT-ADMITTED: <name> reason=missing-frontmatter:<key>`.
5. If `name` value in frontmatter does not match `<skill-name>`, exit 1, print `NOT-ADMITTED: <name> reason=name-mismatch`.
6. Exit 0, print `ADMITTED: <name>`.

No YAML library (stdlib only) — parse frontmatter by finding the two `---` delimiters and splitting `key: value` lines (simple line-based parse sufficient; avoids PyYAML dependency).

**Tests (3 new)**

1. `test_skill_admission_admits_registered_skill` — passes against a real registered skill like `qor-implement`; exit 0.
2. `test_skill_admission_rejects_unregistered` — passes a bogus name; exit 1 with `reason=unregistered`.
3. `test_skill_admission_rejects_missing_frontmatter_key` — fixture skill dir with SKILL.md missing `phase` key; exit 1 with `reason=missing-frontmatter:phase`.

### Track 3 — `tools/reliability/gate-skill-matrix.py`

**Affected Files**

- `tools/reliability/gate-skill-matrix.py` (new, projected ~100 lines)
- `tests/test_reliability_scripts.py` (gate-skill-matrix covers 3 tests)

**Behavior**

Standalone script (no arguments required):
1. Walk `qor/skills/**/SKILL.md`; build `skills` map `{name -> path}` from directory basenames.
2. For each skill file, extract `/qor-<name>` references via regex `r"/qor-([a-z][\w-]*)"`.
3. Drop self-references (skill pointing at its own trigger).
4. Classify each reference as either resolved (target in `skills`) or broken.
5. Print matrix, then summary line: `Skills: N | Handoffs: M | Broken: K`.
6. Exit 0 if `K == 0`, else exit 1.

Reference: legacy version at `qor/scripts/legacy/gate-skill-matrix.py` (92 lines) used `processed/` flat layout; new implementation walks nested `qor/skills/<category>/<name>/SKILL.md` layout.

**Tests (3 new)**

1. `test_gate_skill_matrix_runs_clean_on_current_repo` — invoke against real `qor/skills/` tree; assert exit 0 and summary shows "Broken: 0".
2. `test_gate_skill_matrix_detects_broken_handoff` — fixture skill tree with a skill referencing `/qor-nonexistent`; exit 1 and output contains `qor-nonexistent`.
3. `test_gate_skill_matrix_ignores_self_references` — fixture skill whose only reference is to its own trigger; exit 0.

### Track 4 — Unwire the deferred no-ops (skill edits)

**Affected Files**

- `qor/skills/sdlc/qor-implement/SKILL.md` (currently 309 lines — grounded via `wc -l qor/skills/sdlc/qor-implement/SKILL.md` 2026-04-16)
- `qor/skills/governance/qor-substantiate/SKILL.md` (currently 314 lines — grounded via `wc -l qor/skills/governance/qor-substantiate/SKILL.md` 2026-04-16)

**Changes**

In `qor-implement/SKILL.md`, insert a new **Step 5.5: Intent Lock Capture** between existing Step 5 (TDD-Light) and Step 6 (Precision Build). Block content:

```bash
python tools/reliability/intent-lock.py capture \
  --session "$(cat .qor/session/current 2>/dev/null || echo default)" \
  --plan <current-plan> \
  --audit .agent/staging/AUDIT_REPORT.md
```

On non-zero exit, ABORT implementation with message citing the intent-lock reason.

In `qor-substantiate/SKILL.md`, insert a new **Step 4.6: Reliability Sweep** between existing Step 4.5 (Skill File Integrity Check) and Step 5 (Section 4 Razor Final Check). Block content runs three scripts sequentially, each an interdiction gate:

```bash
python tools/reliability/intent-lock.py verify --session "$(cat .qor/session/current 2>/dev/null || echo default)" || ABORT
python tools/reliability/skill-admission.py qor-substantiate || ABORT
python tools/reliability/gate-skill-matrix.py || ABORT
```

Projected size after edits: qor-implement ~325 lines (+16); qor-substantiate ~335 lines (+21). Both well over the 250-line skill Razor target — but both were already over (309 and 314 before edit); Section 4 Razor applies to **new scripts** this phase, and the growth of already-oversized skill files is policy-accepted (documented in `qor/references/patterns-skill-lifecycle.md` practice of splitting into `references/` when approaching 400). Neither file crosses 400 after this edit, so no split required.

**Tests (1 new — Track 4 skill-edit verification)**

1. `test_reliability_unwired_in_skills` — read both SKILL.md files; assert each contains the invocation command `tools/reliability/intent-lock.py` (both skills) and `tools/reliability/skill-admission.py` + `tools/reliability/gate-skill-matrix.py` (substantiate only). Proximity-anchored to the respective step headers ("Step 5.5" in implement, "Step 4.6" in substantiate) per SG-035.

## Affected Files Summary

New:
- `tools/reliability/intent-lock.py`
- `tools/reliability/skill-admission.py`
- `tools/reliability/gate-skill-matrix.py`
- `tests/test_reliability_scripts.py`

Modified:
- `qor/skills/sdlc/qor-implement/SKILL.md` (+Step 5.5)
- `qor/skills/governance/qor-substantiate/SKILL.md` (+Step 4.6)
- `docs/META_LEDGER.md` (Entry #48 GATE, Entry #49 IMPLEMENTATION, Entry #50 SEAL)
- `pyproject.toml` (version bump 0.7.0 → 0.8.0)
- `qor/dist/variants/**` (regenerated by compile.py)

Total: 3 new scripts, 2 edited skills, 1 new test file (11 new test functions), ledger + version + variants.

## Success Criteria

- [ ] 3 new scripts exist under `tools/reliability/` (intent-lock, skill-admission, gate-skill-matrix).
- [ ] Each new script file is under 250 lines (Section 4 Razor).
- [ ] Each function in new scripts is under 40 lines.
- [ ] 1 new test file `tests/test_reliability_scripts.py` with exactly 11 new test functions (Track 1 = 4, Track 2 = 3, Track 3 = 3, Track 4 = 1).
- [ ] Full suite: 245 passing + 6 skipped (baseline 234 + 11 new).
- [ ] 2 skills edited (Step 5.5 in qor-implement, Step 4.6 in qor-substantiate); both contain live invocation of the new scripts.
- [ ] `BUILD_REGEN=1 python qor/scripts/compile.py` regenerates variants cleanly.
- [ ] Deterministic pytest 2x back-to-back (no flakes).
- [ ] META_LEDGER extended with Entries #48 (GATE), #49 (IMPLEMENTATION), #50 (SEAL) — chain verified.
- [ ] pyproject version = 0.8.0; tag `v0.8.0` created at seal.
- [ ] No edits to `qor/skills/sdlc/qor-remediate/` (Phase 18 boundary).

## CI Commands

```bash
# Baseline check (pre-work)
python -m pytest tests/ -q

# Implementation checks
python -m pytest tests/test_reliability_scripts.py -v
python -m pytest tests/ -q  # full suite, run twice for determinism
python -m pytest tests/ -q

# Script smoke tests
python tools/reliability/gate-skill-matrix.py
python tools/reliability/skill-admission.py qor-implement

# Variant regen
BUILD_REGEN=1 python qor/scripts/compile.py

# Ledger verification
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```
