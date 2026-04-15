# Plan: Phase 12 v2 — Budget Doctrine + Ledger Tests (Remediation)

**Status**: Active (post-VETO remediation; user-ratified Q-A=(a), Q-B=(a), Q-C=(b), prior Q1=(a), Q2=(a), Q3=(i))
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Supersedes**: `docs/plan-qor-phase12-budget-ledger-tests.md` (v1, VETO — Ledger #22)

## Open Questions

None. All design choices ratified pre-draft.

## Audit remediation (V-1..V-11 from Entry #22, quoted verbatim per /qor-plan grounding protocol)

| ID | Audit instruction | Plan §addressing |
|---|---|---|
| V-1 | "Acknowledge in plan header: 'Plan rewritten post-dialogue with user Q1=(a), Q2=(a), Q3=(i) decisions ratified.'" | Header above |
| V-2 | "Replace conditional pyyaml prose with definitive: 'Track A uses regex parsing (no pyyaml dep). YAML-aware refactor deferred to Phase 13 if rules outgrow regex.'" | §Track A.1 |
| V-3 | "Rename `test_write_manifest_atomic_write` → `test_write_manifest_uses_os_replace`" | §Track B.1 |
| V-4 | "Split combined-assertion test name into two distinct tests." | §Track A.2 |
| V-5 | "Narrow caching rule scope OR enumerate heuristic blind spots in the doctrine doc." | §Track A.1 (narrow scope chosen) |
| V-6 | "Replace Entry-#20 coupling with synthetic-known-value pattern (compute expected via the algorithm, don't hardcode a live entry)." | §Track B.2 |
| V-7 | "Add `test_write_gate_artifact_*` to Track B" | §Track B.3 |
| V-8 | "Add classification to plan: 'Track B = regression coverage backfill (not TDD; module pre-existed Phase 11D).'" | §Classification below |
| V-9 | "Reconcile test count" | §Track B totals (15 ledger + 4 gate = 19) |
| V-10 | "Add `test_verify_handles_malformed_entry_header` to Track B." | §Track B.1 |
| V-11 | "Add `tests/test_skill_doctrine.py` to CI commands list." | §CI Commands |

## Classification

**Track A** (CI budget) = preventive infrastructure (test passes vacuously today; enforces when first workflow lands).
**Track B** (ledger_hash + gate_chain coverage) = regression coverage backfill — modules pre-exist Phase 11D, not TDD. Honest classification per V-8.

## Track A — CI Budget Doctrine

### A.1 `qor/references/doctrine-ci-budget.md`

Doctrine doc with 6 rules:

1. **No scheduled workflows** without explicit cost justification + budget review documented in workflow file's header comment
2. **Path filters mandatory**: `paths-ignore: ['docs/**', '*.md', '.gitignore']` or equivalent
3. **No matrix expansion** unless test logic genuinely differs per OS/runtime version (matrix MUST carry `# matrix justification: <reason>` comment)
4. **Aggressive caching mandatory**: workflows installing Python deps MUST use `actions/setup-python@v* with cache:` OR `actions/cache` with key including pyproject.toml hash. **Narrowed per V-5**: rule applies only to workflows that explicitly use `setup-python` action; workflows using uv/poetry/pdm/Docker images are exempt (operator chooses caching mechanism appropriate to their tooling)
5. **Pre-commit hook ownership**: fast checks (drift, doctrine, lint) run pre-commit; CI runs only what can't be done locally (gh-CLI, multi-platform, full test suite on PR/main)
6. **Workflow concurrency**: every workflow declares `concurrency: { group: ..., cancel-in-progress: true }`

YAML parsing decision (per V-2 / Q3=(i)): **regex only**. No pyyaml dep. YAML-aware refactor deferred to Phase 13 if rules outgrow regex.

### A.2 `tests/test_workflow_budget.py`

Tests (per V-4: split combined assertions):

- `test_workflow_dir_optional` — passes when `.github/workflows/` is missing or empty
- `test_workflow_rules_enforced_when_present` — placeholder until first workflow lands; for now asserts that if any `.yml` file exists under `.github/workflows/`, all subsequent rule tests run
- `test_no_unjustified_schedule` — workflows with `schedule:` MUST have a comment block in the file containing the literal "cost justification:"
- `test_paths_ignore_present` — every workflow MUST contain `paths-ignore:` OR `paths:` key
- `test_no_matrix_without_justification` — workflows with `matrix:` MUST contain `matrix justification:` comment
- `test_concurrency_declared` — every workflow MUST declare `concurrency:` key
- `test_setup_python_uses_cache` — workflows that use `actions/setup-python@` MUST also declare `cache:` parameter (narrowed per V-5)

7 tests total. All pass vacuously when no workflows exist.

## Track B — Regression Coverage

### B.1 `tests/test_ledger_hash.py` revisions

Apply audit fixes to the existing 15-test file:

- V-3: rename `test_write_manifest_atomic_write` → `test_write_manifest_uses_os_replace`. Update docstring to "verifies write goes through os.replace (atomicity is an os-level guarantee delegated to the stdlib)".
- V-6: replace `test_chain_hash_recomputable_for_entry_20` with `test_chain_hash_recomputable_synthetic` — derive expected via the algorithm using a fixed synthetic content+prev pair (not coupled to any live entry).
- V-10: add `test_verify_handles_malformed_entry_header` — fake ledger with non-monotonic entry numbers + entries missing required hash markers + entries with malformed numeric IDs. Verify() must skip them gracefully without crashing.

Final test count: 15 (V-9 reconciled — keep all per Q-C=(b)).

### B.2 New tests for `gate_chain.write_gate_artifact` (V-7)

Add to `tests/test_gates.py`:

- `test_write_gate_artifact_creates_file_at_correct_path` — invoke for plan phase; verify `.qor/gates/<sid>/plan.json` exists
- `test_write_gate_artifact_validates_payload_against_schema` — invalid payload (missing required fields) → raises ValueError
- `test_write_gate_artifact_uses_session_get_or_create` — when session_id=None, helper invokes session.get_or_create
- `test_write_gate_artifact_returns_path` — return value is the written Path

4 tests. All pass against existing `gate_chain.write_gate_artifact()` implementation.

## Affected Files

### Track A (2 new)
- `qor/references/doctrine-ci-budget.md`
- `tests/test_workflow_budget.py`

### Track B (1 modified, 1 modified)
- `tests/test_ledger_hash.py` (rename V-3, replace V-6, add V-10)
- `tests/test_gates.py` (add 4 V-7 tests)

No SKILL.md edits, no script changes, no new runtime deps.

## Constraints

- **No new runtime code**
- **No GitHub Actions workflows added** in this phase (doctrine prevents until budget review)
- **Honor token-efficiency** — workflow audit test parses files lazily, regex only
- **Existing test_ledger_hash.py is regression coverage backfill** (V-8)
- **Defer to next phase**: 11F (Delegation sections + agent refs), 12A (living artifacts release-doc), 12B (README governance)

## Success Criteria

- [ ] `qor/references/doctrine-ci-budget.md` exists with 6 rules + V-5-narrowed caching scope + regex-only commitment
- [ ] `tests/test_workflow_budget.py` exists with 7 tests; all pass vacuously
- [ ] `tests/test_ledger_hash.py` updated (V-3 rename, V-6 synthetic, V-10 parser robustness)
- [ ] `tests/test_gates.py` augmented with 4 `write_gate_artifact` tests (V-7)
- [ ] Full suite 184/184 passing (163 prior + 7 workflow + 1 V-10 + 4 V-7 + 9 unchanged ledger tests already running)
- [ ] Drift clean; ledger chain intact (#22 still verified)
- [ ] Plan v1 + v2 retained in docs/ for chain continuity
- [ ] Committed + pushed

## CI Commands (V-11 reconciled)

```bash
python -m pytest tests/test_skill_doctrine.py tests/test_workflow_budget.py tests/test_ledger_hash.py tests/test_gates.py -v
python -m pytest tests/
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```
