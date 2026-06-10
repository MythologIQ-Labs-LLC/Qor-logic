# Plan: Phase 156 -- re-verify the committed seal binding in CI (GAP-GOV-03)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

None. Closes the GAP-GOV-03 half of GH #210 (audit Sprint A). The seal gates run against the
working-tree META_LEDGER before commit; nothing re-verifies the committed bytes. Research narrowed the
real residual: CI (`ci.yml:40`, `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`) already
re-verifies the committed *chain*, so the chain TOCTOU is caught at push -- but the GOV-01
`content_hash`<->plan binding (`seal_entry_check`) is NOT re-verified on the committed bytes. Fix:
re-run the seal-entry binding against the committed ledger in CI. The substantiate SKILL.md is at the
40 KB skill-size budget (9 bytes headroom), so the wiring lives in CI (the correct post-commit home),
not in the skill.

## Phase 1: seal_entry_check --auto + CI re-verification

### Affected Files

- `qor/reliability/seal_entry_check.py` - add `check_latest(ledger_path, repo_root=None)` (derives the phase from the latest SESSION SEAL entry, then runs `check`) and an `--auto` CLI flag.
- `.github/workflows/ci.yml` - add a step that re-verifies the committed seal binding via `--auto`.
- `tests/test_seal_entry_check_auto.py` (NEW).

### Changes

Add to `seal_entry_check.py`:
```python
def check_latest(ledger_path: Path, repo_root: Path | None = None) -> SealEntryResult:
    """Re-verify the committed latest SESSION SEAL entry without an external
    plan argument: derive the phase from the entry itself, then run check (which
    recomputes content_hash from the entry's cited plan -- the GOV-01 binding)."""
    text = Path(ledger_path).read_text(encoding="utf-8")  # UnicodeDecodeError -> caller path
    latest = _parse_latest_entry(text)
    if latest is None:
        return SealEntryResult(ok=False, errors=["no parseable latest entry"])
    return check(ledger_path, latest["phase_num"], repo_root=repo_root)
```
`_main` gains `--auto` (mutually satisfying with `--plan`): when set, resolve the phase from the latest
entry via `check_latest` instead of from `--plan`. `ci.yml` gains a step after the existing chain verify:
`python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto` -- so a committed seal
whose `content_hash` does not match its committed plan fails CI (the binding TOCTOU residual), completing
the committed-bytes re-verification alongside the chain check.

### Unit Tests

- `tests/test_seal_entry_check_auto.py`:
  - `test_check_latest_passes_on_bound_seal` - a synthetic committed-style ledger whose latest SESSION SEAL entry's `content_hash == sha256(plan)` (plan on disk) returns `ok=True` via `check_latest` (no `--plan` needed).
  - `test_check_latest_fails_on_unbound_seal` - the same entry with a `content_hash` that does NOT match the plan returns `ok=False` naming the content_hash<->plan mismatch.
  - `test_auto_cli_exit_codes` - `_main(["--ledger", <bound>, "--auto"])` exits 0; `_main(["--ledger", <unbound>, "--auto"])` exits 1.
  - `test_ci_step_present` - `.github/workflows/ci.yml` contains the `seal_entry_check ... --auto` re-verification step (guards the wiring against silent removal).

## Definition of Done

### Deliverable: D-committed-seal-reverify

- **D1**: the committed seal's GOV-01 binding is re-verified at push (not only locally pre-commit), completing the committed-bytes re-verification (chain via ci.yml:40 + binding via the new step) and closing the GAP-GOV-03 TOCTOU residual.
- **D2**: `seal_entry_check.check_latest` + `--auto` exist; `ci.yml` runs the `--auto` re-verification step.
- **D3**: ledger SEAL records GAP-GOV-03 closed; this is the last GH #210 item before GOV-05 (the deferred-decision item).
- **D4**: `test_check_latest_fails_on_unbound_seal` (ok=False on mismatch) + `test_auto_cli_exit_codes` (0/1) + `test_ci_step_present`.

## CI Commands

- `python -m pytest tests/test_seal_entry_check_auto.py tests/test_seal_entry_content_hash_binding.py tests/test_seal_entry_sealable.py -q` -- new + existing seal-entry tests (run twice).
- `python -m pytest -q` -- full suite green.
