## Phase 17 v2 — Reliability Scripts (B49/B50/B51) — remediation of Entry #48 VETO

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/17-reliability-scripts`
**Target version**: `0.7.0 → 0.8.0`
**Supersedes**: `docs/plan-qor-phase17-reliability-scripts.md` (VETO'd — Entry #48)

## Delta from v1 (inline-grounded)

v2 closes three Entry #48 findings.

### V-1 closure: correct skill count (SG-016/SG-036)

Audit: "28 skill files" was wrong. Actual: 27. Grounded via `find qor/skills -name SKILL.md | wc -l` 2026-04-16 → `27`. v2 Open Questions cites **27**.

### V-2 closure: delete fabricated policy citation (SG-017/SG-021)

Audit: plan cited a "splits at 400" policy in `patterns-skill-lifecycle.md`. No such policy exists (grounded via `grep -n "400|split|references/" qor/references/patterns-skill-lifecycle.md` 2026-04-16 → 0 matches). v2 Track 4 states plainly: both skill files are already over the 250-line Section 4 Razor target (309, 314); adding ~16-21 lines does not materially change that; further splitting is out of scope for this phase and deferred to a future refactor phase if triggered. No fabricated citation.

### V-4 closure: resolve `<current-plan>` with explicit resolver (SG-021)

Audit: `--plan <current-plan>` placeholder was ambiguous. v2 Track 4 Step 5.5 block resolves the plan path explicitly via `governance_helpers.current_phase_plan_path()` (used in substantiate Step 7.5).

## Open Questions

None. Legacy implementations exist at `qor/scripts/legacy/intent-lock.py` (43 lines, grounded via `wc -l qor/scripts/legacy/intent-lock.py` 2026-04-16), `qor/scripts/legacy/admit-skill.py` (60 lines, grounded 2026-04-16), and `qor/scripts/legacy/gate-skill-matrix.py` (92 lines, grounded 2026-04-16). Current skill layout: **27 SKILL.md files** under `qor/skills/**` (grounded via `find qor/skills -name SKILL.md | wc -l` 2026-04-16 → 27). No `processed/` directory exists; no `.qor/` runtime directory exists yet (grounded via `ls .qor/` 2026-04-16 → absent). Scripts must create their session subdirs on first use. Legacy `INTENT_LOCK.json` manual-declaration semantics are replaced with fingerprint-capture semantics (plan + audit + HEAD hash).

## Constraints

- Python stdlib + existing `jsonschema` only. No new dependencies.
- Each new script file: <250 lines (Section 4 Razor). Each function: <40 lines.
- TDD-first: write failing test, then implement.
- Deterministic test runs required (no network, no wall-clock coupling, no random seeds).
- `qor/skills/sdlc/qor-remediate/SKILL.md` is out of scope (Phase 18 parallel).
- User-global `~/.claude/skills/` is out of scope.
- **SG-036 active**: every file-size/location claim below carries inline `wc -l` or equivalent provenance with date 2026-04-16.
- **SG-038 active**: prose, code blocks, and Success Criteria cite the same 3 scripts, same 2 skills edited, and same 11 new tests (see SG-038 Lockstep Manifest).

## SG-038 Lockstep Manifest (canonical counts)

All other sections of this plan must quote these exact numbers:

- **New scripts**: 3 (`tools/reliability/intent-lock.py`, `tools/reliability/skill-admission.py`, `tools/reliability/gate-skill-matrix.py`)
- **Skills edited**: 2 (`qor/skills/sdlc/qor-implement/SKILL.md`, `qor/skills/governance/qor-substantiate/SKILL.md`)
- **New test functions**: 11 (Track 1 = 4, Track 2 = 3, Track 3 = 3, Track 4 = 1)
- **New test file**: 1 (`tests/test_reliability_scripts.py`)
- **Baseline tests**: 234 passing + 6 skipped (grounded via `python -m pytest tests/ -q` 2026-04-16)
- **Target tests**: 245 passing + 6 skipped (234 + 11)

## Tracks

### Track 1 — `tools/reliability/intent-lock.py`

**Affected Files**

- `tools/reliability/intent-lock.py` (new, projected ~100 lines)
- `tests/test_reliability_scripts.py` (new file; intent-lock section covers 4 tests)

**Behavior**

Two subcommands: `capture` and `verify`.

`capture --session <sid> --plan <path> --audit <path>`:
1. Read plan file; compute SHA-256 of bytes.
2. Read audit report; compute SHA-256 of bytes. If audit content does not contain a "PASS" verdict line, exit 1 with reason "audit not PASS".
3. Read current HEAD commit via `git rev-parse HEAD` (subprocess, `cwd=repo_root`, no network).
4. Write JSON fingerprint to `.qor/intent-lock/<sid>.json`: `{session, plan_path, plan_hash, audit_path, audit_hash, head_commit, captured_ts}`. `captured_ts` is UTC ISO timestamp.
5. Exit 0; print `LOCKED: <sid>`.

`verify --session <sid>`:
1. Load `.qor/intent-lock/<sid>.json`. If missing, exit 1 with "NO LOCK".
2. Re-hash the plan file at the stored path; if differs from stored `plan_hash`, exit 1 with "DRIFT: plan".
3. Re-hash the audit at the stored path; if differs, exit 1 with "DRIFT: audit".
4. Read current HEAD; if differs from stored `head_commit`, exit 1 with "DRIFT: head".
5. Exit 0; print `VERIFIED: <sid>`.

Determinism: timestamps captured but never compared. Verify is pure content-hash equality. No network. Git subprocess uses fixed cwd argument.

**Tests (4 new)**

1. `test_intent_lock_capture_writes_fingerprint` — capture against tmp plan, tmp audit (containing "PASS"), tmp git dir; assert output JSON has all required keys.
2. `test_intent_lock_verify_passes_when_unchanged` — capture then verify immediately; exit 0.
3. `test_intent_lock_verify_detects_plan_drift` — capture, mutate plan, verify; exit 1 with "DRIFT: plan".
4. `test_intent_lock_capture_rejects_non_pass_audit` — capture against audit lacking "PASS"; exit 1 with "audit not PASS".

### Track 2 — `tools/reliability/skill-admission.py`

**Affected Files**

- `tools/reliability/skill-admission.py` (new, projected ~80 lines)
- `tests/test_reliability_scripts.py` (skill-admission section covers 3 tests)

**Behavior**

`skill-admission.py <skill-name>`:
1. Discover skills: walk `qor/skills/**/SKILL.md`, derive skill name from directory basename (e.g. `qor-implement`). Currently 27 registered (grounded 2026-04-16).
2. If `<skill-name>` not in discovered set, exit 1; print `NOT-ADMITTED: <name> reason=unregistered`.
3. Load skill file; verify YAML frontmatter exists (lines starting and ending with `---`) and contains required keys: `name`, `description`, `phase`.
4. If any required frontmatter key missing, exit 1; print `NOT-ADMITTED: <name> reason=missing-frontmatter:<key>`.
5. If frontmatter `name` value does not match `<skill-name>`, exit 1; print `NOT-ADMITTED: <name> reason=name-mismatch`.
6. Exit 0; print `ADMITTED: <name>`.

Stdlib-only frontmatter parser: locate two `---` delimiters, split remaining lines on first `:`. Simple line-based parse sufficient; no PyYAML dependency.

**Tests (3 new)**

1. `test_skill_admission_admits_registered_skill` — invoke against `qor-implement`; exit 0.
2. `test_skill_admission_rejects_unregistered` — bogus name; exit 1 with `reason=unregistered`.
3. `test_skill_admission_rejects_missing_frontmatter_key` — fixture skill dir with SKILL.md missing `phase` key; exit 1 with `reason=missing-frontmatter:phase`.

### Track 3 — `tools/reliability/gate-skill-matrix.py`

**Affected Files**

- `tools/reliability/gate-skill-matrix.py` (new, projected ~100 lines)
- `tests/test_reliability_scripts.py` (gate-skill-matrix section covers 3 tests)

**Behavior**

Standalone script (no required args):
1. Walk `qor/skills/**/SKILL.md`; build `skills` map `{name -> path}` from directory basenames.
2. For each skill file, extract `/qor-<name>` references via regex `r"/qor-([a-z][\w-]*)"`.
3. Drop self-references.
4. Classify each reference as resolved (target in `skills`) or broken.
5. Print matrix, then summary: `Skills: N | Handoffs: M | Broken: K`.
6. Exit 0 if K == 0, else exit 1.

Reference: legacy `qor/scripts/legacy/gate-skill-matrix.py` (92 lines, grounded 2026-04-16) used `processed/` flat layout; new implementation walks nested `qor/skills/<category>/<name>/SKILL.md` layout.

**Tests (3 new)**

1. `test_gate_skill_matrix_runs_clean_on_current_repo` — invoke against real `qor/skills/` tree; assert exit 0 and summary shows `Broken: 0`.
2. `test_gate_skill_matrix_detects_broken_handoff` — fixture skill tree with a skill referencing `/qor-nonexistent`; exit 1, output contains `qor-nonexistent`.
3. `test_gate_skill_matrix_ignores_self_references` — fixture skill whose only reference is its own trigger; exit 0.

### Track 4 — Unwire the deferred no-ops (skill edits)

**Affected Files**

- `qor/skills/sdlc/qor-implement/SKILL.md` (currently 309 lines — grounded via `wc -l qor/skills/sdlc/qor-implement/SKILL.md` 2026-04-16)
- `qor/skills/governance/qor-substantiate/SKILL.md` (currently 314 lines — grounded via `wc -l qor/skills/governance/qor-substantiate/SKILL.md` 2026-04-16)

**Changes**

In `qor-implement/SKILL.md`, insert a new **Step 5.5: Intent Lock Capture** between existing Step 5 (TDD-Light) and Step 6 (Precision Build). The plan path is resolved via the existing helper `governance_helpers.current_phase_plan_path()` (used in substantiate Step 7.5 — V-4 closure). Block:

```bash
PLAN_PATH=$(python -c "import sys; sys.path.insert(0,'qor/scripts'); from governance_helpers import current_phase_plan_path; print(current_phase_plan_path())")
SESSION_ID=$(cat .qor/session/current 2>/dev/null || echo default)
python tools/reliability/intent-lock.py capture \
  --session "$SESSION_ID" \
  --plan "$PLAN_PATH" \
  --audit .agent/staging/AUDIT_REPORT.md
```

On non-zero exit, ABORT implementation citing the intent-lock reason.

In `qor-substantiate/SKILL.md`, insert a new **Step 4.6: Reliability Sweep** between existing Step 4.5 (Skill File Integrity Check) and Step 5 (Section 4 Razor Final Check). Block:

```bash
SESSION_ID=$(cat .qor/session/current 2>/dev/null || echo default)
python tools/reliability/intent-lock.py verify --session "$SESSION_ID" || ABORT
python tools/reliability/skill-admission.py qor-substantiate || ABORT
python tools/reliability/gate-skill-matrix.py || ABORT
```

**Size impact** (V-2 closure — no fabricated citation): qor-implement projects to ~325 lines (+~16) and qor-substantiate to ~335 lines (+~21). Both skill files are already above the 250-line Section 4 Razor target (309 and 314 before this edit); adding ~16-21 lines does not materially change that. Further splitting of these skill files is out of scope for this phase and deferred to a future refactor phase if and when triggered.

**Tests (1 new)**

1. `test_reliability_unwired_in_skills` — read both SKILL.md files; assert implement contains both the literal step header "Step 5.5" and the literal path `tools/reliability/intent-lock.py`; substantiate contains "Step 4.6" plus all three paths (`tools/reliability/intent-lock.py`, `tools/reliability/skill-admission.py`, `tools/reliability/gate-skill-matrix.py`). Proximity-anchored per SG-035: each assertion uses `re.search` with the step header within 500 chars of the path.

## Affected Files Summary

New:
- `tools/reliability/intent-lock.py`
- `tools/reliability/skill-admission.py`
- `tools/reliability/gate-skill-matrix.py`
- `tests/test_reliability_scripts.py`

Modified:
- `qor/skills/sdlc/qor-implement/SKILL.md` (+Step 5.5)
- `qor/skills/governance/qor-substantiate/SKILL.md` (+Step 4.6)
- `docs/META_LEDGER.md` (Entry #49 v2 PASS, Entry #50 IMPLEMENTATION, Entry #51 SEAL)
- `pyproject.toml` (version bump 0.7.0 → 0.8.0)
- `qor/dist/variants/**` (regenerated by compile.py)

Totals (SG-038 echo): 3 new scripts, 2 edited skills, 1 new test file (11 new test functions), ledger + version + variants.

## Success Criteria

- [ ] 3 new scripts exist under `tools/reliability/` (intent-lock, skill-admission, gate-skill-matrix).
- [ ] Each new script file <250 lines (Section 4 Razor).
- [ ] Each function in new scripts <40 lines.
- [ ] 1 new test file `tests/test_reliability_scripts.py` with exactly 11 new test functions (Track 1 = 4, Track 2 = 3, Track 3 = 3, Track 4 = 1).
- [ ] Full suite: 245 passing + 6 skipped (baseline 234 + 11 new).
- [ ] 2 skills edited (Step 5.5 in qor-implement uses `current_phase_plan_path()` resolver; Step 4.6 in qor-substantiate runs all three scripts).
- [ ] `BUILD_REGEN=1 python qor/scripts/compile.py` regenerates variants cleanly.
- [ ] Deterministic pytest 2x back-to-back (no flakes).
- [ ] META_LEDGER extended with Entries #49 (v2 PASS), #50 (IMPLEMENTATION), #51 (SEAL) — chain verified.
- [ ] pyproject version = 0.8.0; tag `v0.8.0` created at seal.
- [ ] No edits to `qor/skills/sdlc/qor-remediate/` (Phase 18 boundary).

## CI Commands

```bash
# Baseline
python -m pytest tests/ -q

# Implementation checks
python -m pytest tests/test_reliability_scripts.py -v
python -m pytest tests/ -q  # full suite, run twice for determinism
python -m pytest tests/ -q

# Script smoke
python tools/reliability/gate-skill-matrix.py
python tools/reliability/skill-admission.py qor-implement

# Variant regen
BUILD_REGEN=1 python qor/scripts/compile.py

# Ledger verify
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```
