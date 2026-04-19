# Plan: Phase 35 — installed-mode import fix

**change_class**: feature
**target_version**: v0.25.0
**doc_tier**: system
**terms_introduced**: none

## Context

Third recurrence of the "state-duplicated-from-source-of-truth" family (SG-Phase32-B README, SG-Phase33-A tag, SG-Phase34-A CLI version), but at a different layer: skill prose embedded a repo-layout assumption (`sys.path.insert(0, 'qor/scripts')`) that works in dev but fails post-`pip install qor-logic`. Every governance skill's Python block broke silently on installed users from v0.18.0 forward.

Parallel breakage: `qor/reliability/{intent-lock,skill-admission,gate-skill-matrix}.py` used hyphen-named files invoked via `python qor/reliability/<name>.py` — invalid Python module names, and again CWD-dependent. Subprocess calls from `/qor-implement` Step 5.5 and `/qor-substantiate` Step 4.6 failed post-install.

Two bare intra-`qor/scripts` imports compounded: `doc_integrity.py` did `import shadow_process`; `doc_integrity_strict.py` did `from doc_integrity import parse_glossary`. Only worked under the `sys.path` hack.

## Phase 1: Import path rewrite

### Unit Tests (TDD — written first)

- `tests/test_installed_import_paths.py` — NEW
  - `test_no_sys_path_hack_in_skills`: structural lint, zero `sys.path.insert.*qor/scripts` remain in `qor/skills/**/*.md`.
  - `test_no_hyphen_named_reliability_invocations`: structural lint, zero `qor/reliability/<hyphen>.py` invocations in skill prose.
  - `test_qor_scripts_modules_importable`: runtime — 10 key governance modules load cleanly via `from qor.scripts import X`.
  - `test_qor_reliability_modules_importable`: runtime — 3 reliability modules load as `qor.reliability.X`, each carrying a `main()` entry point for `python -m` invocation.

### Affected Files

- `tests/test_installed_import_paths.py` (NEW).
- `qor/reliability/intent-lock.py` → `qor/reliability/intent_lock.py` (git mv).
- `qor/reliability/skill-admission.py` → `qor/reliability/skill_admission.py` (git mv).
- `qor/reliability/gate-skill-matrix.py` → `qor/reliability/gate_skill_matrix.py` (git mv).
- `qor/scripts/doc_integrity.py` — `import shadow_process` → `from qor.scripts import shadow_process`.
- `qor/scripts/doc_integrity_strict.py` — `from doc_integrity import parse_glossary` → `from qor.scripts.doc_integrity import parse_glossary`.
- 12 skill `.md` files (all 49 occurrences of the hack pattern) — mechanical rewrite from `import sys; sys.path.insert(0, 'qor/scripts'); import X` / `from X import ...` to `from qor.scripts import X` / `from qor.scripts.X import ...`.
- `qor/skills/governance/qor-substantiate/SKILL.md` Step 4.6 — subprocess invocations: `python qor/reliability/<hyphen>.py ARGS` → `python -m qor.reliability.<snake> ARGS`.
- `qor/skills/sdlc/qor-implement/SKILL.md` Step 5.5 — same rewrite for intent-lock invocation.
- `tests/test_reliability_scripts.py`, `tests/test_security_fixes.py` — update hardcoded file-path constants and regex patterns to match new snake_case names.

### Changes

```python
# Before (broken post-install):
import sys; sys.path.insert(0, 'qor/scripts')
import gate_chain, session

# After (works in both modes):
from qor.scripts import gate_chain, session
```

```bash
# Before:
python qor/reliability/intent-lock.py verify --session "$SESSION_ID"

# After:
python -m qor.reliability.intent_lock verify --session "$SESSION_ID"
```

### Rationale

- `from qor.scripts import X` works from any CWD once the package is importable (either `pip install` OR `PYTHONPATH=. python` at repo root). Removes the brittle CWD assumption that was never doctrinally declared.
- Hyphen-named Python files cannot be imported as modules (`import intent-lock` is a syntax error). Snake_case allows both script-path invocation AND `python -m` invocation.
- `python -m qor.reliability.X` resolves the module via Python's module system, not the shell's CWD. Installed and dev modes converge.

## Phase 2: Doctrine + Shadow Genome backfill

### Unit Tests (TDD)

Covered by the existing `test_installed_import_paths.py` tests above. No separate test module needed (Rule 4 satisfied by the structural + runtime pair).

### Affected Files

- `docs/SHADOW_GENOME.md` — Entry #25 SG-Phase35-A documenting the installed-mode breakage across v0.18.0–v0.24.1.
- `qor/references/doctrine-governance-enforcement.md` — add §9 "Installed-Mode Invariants" stating: (a) all skill Python blocks use fully-qualified `qor.scripts.*` / `qor.reliability.*` imports; (b) reliability scripts are Python modules (snake_case) invoked via `python -m`; (c) structural lint enforces both.
- `docs/SYSTEM_STATE.md` — Phase 35 snapshot marker.
- `docs/lifecycle.md` — note Step 4.6 + Step 5.5 now use `python -m qor.reliability.*` (was path-invocation).

## CI Validation

```bash
python -m pytest tests/test_installed_import_paths.py -q
python -m pytest -q  # full suite stays green
python -c "from qor.scripts import gate_chain, governance_helpers, shadow_process, doc_integrity, doc_integrity_strict; from qor.reliability import intent_lock, skill_admission, gate_skill_matrix; print('OK')"
python -m qor.reliability.gate_skill_matrix  # exits 0
```
