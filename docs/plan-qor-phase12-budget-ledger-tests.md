# Plan: Phase 12 — CI Budget Doctrine + Ledger Hash Tests

**Status**: Active (scope-limited; 2 independent tracks)
**Author**: QorLogic Governor
**Date**: 2026-04-15
**Scope**: (A) Author CI budget doctrine + preventive workflow audit test — lands before any GitHub Actions workflow exists. (B) Add `tests/test_ledger_hash.py` to close Phase 11D deferred S-11.

## Open Questions

None. Both tracks are mechanical; no design decisions needed.

## Why combined

Both small. Both preventive/safety-net. Neither touches skills. Single phase keeps amendment-drift surface tiny.

## Track A — CI Budget Doctrine

### A.1 `qor/references/doctrine-ci-budget.md`

Doctrine doc codifying:

- **No scheduled workflows** (`schedule:` triggers) without explicit cost justification + budget review documented in the workflow file's header comment
- **Path filters mandatory**: workflows MUST declare `paths-ignore: ['docs/**', '*.md', '.gitignore']` (or equivalent) so doc-only PRs don't burn CI minutes
- **No matrix expansion** unless test logic genuinely differs per OS/runtime version. Solo Python/Linux runs cover most cases; matrix is opt-in with justification.
- **Aggressive caching mandatory**: `actions/cache` for `~/.cache/pip`, `qor/dist/`, `__pycache__/`, `.pytest_cache/`. Cache key includes `pyproject.toml` hash.
- **Pre-commit hook ownership**: fast checks (drift, doctrine tests, lint) run pre-commit; CI runs only what can't be done locally (gh-CLI integration, multi-platform sanity, full test suite on PR/main only)
- **Workflow concurrency**: every workflow declares `concurrency: { group: ... cancel-in-progress: true }` to kill superseded PR runs

Doctrine includes a "Budget tally" table tracking minutes consumed per workflow per month; future workflows MUST estimate before merging.

### A.2 `tests/test_workflow_budget.py`

Static analysis over `.github/workflows/*.yml`:

- `test_no_workflows_yet_or_compliant` — passes vacuously when `.github/workflows/` is empty/missing; otherwise enforces rules
- `test_no_unjustified_schedule` — workflows with `schedule:` MUST have a comment block explaining cost justification
- `test_paths_ignore_present` — every workflow has `paths-ignore` (or `on:` filter that explicitly excludes doc-only paths)
- `test_no_matrix_without_justification` — matrix expansions MUST have a `# matrix justification: <reason>` comment
- `test_concurrency_declared` — every workflow declares concurrency to cancel superseded runs
- `test_caching_present_for_python_workflows` — workflows that install Python deps MUST use `actions/cache` or `actions/setup-python@v* with cache:`

Parser: `pyyaml` would be ideal but adds dep. Use `re` + simple line scans (workflows are small; regex is fine).

If `pyyaml` is already a transitive dep (via `jsonschema`?), use it. Check: `pip show pyyaml`.

## Track B — `tests/test_ledger_hash.py` (S-11)

Closes Phase 11D deferred S-11. Module is critical infrastructure (every audit/substantiate writes via it) and currently has zero direct test coverage.

### B.1 Tests

- `test_content_hash_deterministic` — same file content → same hash
- `test_content_hash_changes_on_byte_diff` — single-byte diff → different hash
- `test_chain_hash_recomputable` — recompute matches stored chain hash for known Entry #20
- `test_chain_hash_differs_on_content_change` — change content → chain hash changes
- `test_write_manifest_sorted_by_path` — manifest entries always sorted; deterministic
- `test_write_manifest_includes_glob_matches` — include_globs filter works
- `test_write_manifest_atomic` — partial write doesn't leave torn state (cover via mock-write-failure)
- `test_verify_passes_on_clean_chain` — full ledger verify exits 0
- `test_verify_detects_tampered_chain_hash` — flip one chain hash → verify fails
- `test_verify_skips_pre_machine_verifiable_entries` — entries #1-#11 use older markup; verify gracefully skips

## Affected Files

### Track A
- `qor/references/doctrine-ci-budget.md` (new)
- `tests/test_workflow_budget.py` (new)
- (No `.github/workflows/` files added — doctrine and test are preventive)

### Track B
- `tests/test_ledger_hash.py` (new)

No SKILL.md edits, no script changes.

## Constraints

- **No new runtime code** — both tracks are tests + doctrine only
- **No GitHub Actions workflows added** in this phase (doctrine prevents until budget review documented)
- **Honor token-efficiency** — workflow audit test parses files lazily, no full YAML parse if regex covers
- **Defer to next phase**: 11F (Delegation sections + agent refs) and 12A (living artifacts release-doc), 12B (README governance)

## Success Criteria

- [ ] `qor/references/doctrine-ci-budget.md` exists with 6 budget rules + rationale
- [ ] `tests/test_workflow_budget.py` exists with 6 tests; all pass (vacuously when no workflows)
- [ ] `tests/test_ledger_hash.py` exists with 10 tests; all pass against current `qor/scripts/ledger_hash.py`
- [ ] Full suite 179+/179+ passing (163 prior + 6 + 10)
- [ ] Drift clean; ledger chain intact
- [ ] Committed + pushed

## CI Commands

```bash
python -m pytest tests/test_workflow_budget.py tests/test_ledger_hash.py -v
python -m pytest tests/
python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
```
