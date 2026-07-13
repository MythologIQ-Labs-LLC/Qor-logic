# Plan: Phase 182 - Health gate silences tolerated pre-anchor diagnostics (GH #268)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-health-preanchor-output-2026-07-13.md (ledger entry #446, session `2026-07-13T0817-5d9c1c`); GH #268. Presentation fix; the verdict logic is untouched.

## Locked Decisions

- **LD-1: suppress stderr beside stdout at both verification call sites.**
  `grep -nE 'redirect_stdout' qor/scripts/governance_health.py -> 134,142`; the bleed source is `ledger_hash.verify`/`verify_post_anchor` printing to stderr (`grep -nE 'file=sys.stderr' qor/scripts/ledger_hash.py -> 417,429,520,529`). `contextlib.redirect_stderr(io.StringIO())` joins each context. The verifiers themselves are UNCHANGED (their direct CLI use keeps full diagnostics).
- **LD-2: the tolerance becomes a positive note in the OK reason.**
  `_ledger_damage` (`grep -nE 'def _ledger_damage' qor/scripts/governance_health.py -> 127`) returns the damage reason today; it gains a module-visible tolerated flag by returning a `(damage, note)` pair threaded through `_damage_reason` (sole caller: `_classify_one`); when strict verify failed but post-anchor passed, the OK finding's reason reads "passes health checks (disclosed pre-anchor residuals tolerated; post-anchor band clean)". Non-ledger artifacts return `(reason, None)`. External `_classify_one` callers pass positionally and are unaffected (return type unchanged).
- **LD-3: structured output is out of scope.**
  The JSON-classification acceptance defers to the GH #271 typed-model roadmap (recorded on GH #268 at disposition).

## Phase 1: Suppression + positive note (TDD first)

### Affected Files

- tests/test_governance_health_post_anchor_tolerance.py - capture-both-streams + reason-note tests appended (fixture reused)
- qor/scripts/governance_health.py - redirect_stderr at both sites; `(damage, note)` threading; OK-reason note

### Changes

`_ledger_damage -> tuple[str | None, str | None]`: both redirected calls gain `contextlib.redirect_stderr(io.StringIO())`; the tolerated branch (strict rc != 0, post-anchor rc == 0) returns `(None, "disclosed pre-anchor residuals tolerated; post-anchor band clean")`. `_damage_reason` returns the pair (`(None, None)` default; empty-file and non-ledger paths unchanged semantics). `_classify_one`: damage -> DAMAGED as today; OK path uses `note` to build the reason ("passes health checks (<note>)" when present, else the current literal).

### Unit Tests

- tests/test_governance_health_post_anchor_tolerance.py::test_tolerated_residuals_emit_no_fail_or_tainted_lines - on the re-anchored fixture, `_classify_one` runs under capsys: NEITHER stream contains "FAIL Entry" or "TAINTED" and the finding is OK (GH #268 acceptance; red today via the stderr bleed)
- tests/test_governance_health_post_anchor_tolerance.py::test_ok_reason_names_the_disclosed_tolerance - the OK finding's reason contains "disclosed pre-anchor residuals tolerated"
- tests/test_governance_health_post_anchor_tolerance.py::test_post_anchor_failure_still_damaged (existing) - regression lock, unchanged

## Feature Inventory Touches

(empty -- governance tooling)

## Definition of Done

### Deliverable: diagnostics match the verdict

- **D1**: An operator (or status_json / the nightly summary) running the health gate on a legally re-anchored ledger sees an OK finding whose reason NAMES the tolerance -- and zero contradictory FAIL/TAINTED lines (GH #268; structured output deferred to GH #271 with rationale recorded).
- **D2**: `redirect_stderr` at both call sites; `(damage, note)` threading per LD-2; verifier CLIs untouched.
- **D3**: Ledger entries for plan/audit/implement/seal; GH #268 disposition records the deferral.
- **D4**: `test_tolerated_residuals_emit_no_fail_or_tainted_lines` observes the acceptance (red today); the existing DAMAGED regression test stays green.

## CI Commands

- `python -m pytest tests/test_governance_health_post_anchor_tolerance.py tests/test_governance_health.py tests/test_cli_governance_health.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
