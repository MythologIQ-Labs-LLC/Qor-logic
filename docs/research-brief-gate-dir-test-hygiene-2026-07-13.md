# Research Brief

**Date**: 2026-07-13T04:40:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #274 -- suite tests write to the live `.qor/gates/` tree under fixed fixture session ids
**Scope**: locate every unswept offender, identify the root-cause patch pattern, decide the fate of the tracked pollution dirs

---

## Executive Summary

Three test files write gate artifacts into the LIVE `.qor/gates/` tree because their
redirects miss the module constant the writer actually uses. Two distinct defect
shapes: (a) a doppelganger import (`sys.path.insert(0, "qor/scripts")` + top-level
`import gate_chain` / `import validate_gate_artifact`) whose monkeypatches hit a
second module object the production code never reads; (b) patching only
`gate_chain.GATES_DIR` (the resolver constant) while the write path goes through
`qor.scripts.validate_gate_artifact.GATES_DIR`, plus one wrong env var
(`QORLOGIC_PROJECT_DIR` controls host install dirs per `qor/hosts.py:8-11`, not the
gate tree; `qor.workdir.root()` reads `QOR_ROOT`). The five tracked
fixture dirs the writes accreted into are referenced by NO ledger entry, NO qor/
module, and NO test read -- they are committable pollution and can be untracked.

## Findings

### F1. Offender: tests/test_gate_chain_provenance.py (doppelganger imports)

- `tests/test_gate_chain_provenance.py:16-17`: `sys.path.insert(0, "qor/scripts")`
  + `import gate_chain` -- a module object DISTINCT from `qor.scripts.gate_chain`.
  Inside it, `from qor.scripts import validate_gate_artifact as vga` resolves the
  CANONICAL writer module, so `monkeypatch.setattr(gate_chain, "GATES_DIR", ...)`
  redirects only resolution, never the write.
- Writers hitting the live tree: `:74` (sid `2026-04-30T0000-test03`), `:91`
  (`...test04`), `:108` (`...test06`). test06 additionally does
  `import validate_gate_artifact as _vga` (`:108` block) -- patching the
  doppelganger's `GATES_DIR` is a no-op on the canonical one -- and sets
  `QOR_ROOT=tmp` for keys, so each run rewrites the live tracked
  `plan.provenance` with a fresh tmp-keyed `hmac_tag` (the mutation observed in
  Phase 173).
- Non-writers (raise-only): `:43` (test01), `:58` (test02), `:122` (test05).

### F2. Offender: tests/test_qor_ideate_writes_gate_artifact.py (resolver-only patch)

- `:35` and `:51`: `monkeypatch.setattr(gate_chain, "GATES_DIR", tmp...)` patches
  the canonical `qor.scripts.gate_chain` -- but `write_gate_artifact` delegates to
  `vga.write_artifact` (`qor/scripts/gate_chain.py:293`), which joins
  `vga.GATES_DIR` (`qor/scripts/validate_gate_artifact.py:176`). Both tests write
  live `ideate-e2e/` and `ideate-prov/` (tracked dirs), plus sidecars and, since
  Phase 173, `-iter` accretion.

### F3. Offender: tests/test_skill_active_env.py (dead env var)

- `:29`: `monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))` -- that
  variable controls host INSTALL directories (`qor/hosts.py:8-11`), not the gate
  tree; `qor.workdir.root()` reads `QOR_ROOT` (`qor/workdir.py:29`).
  `:36` writes a live audit artifact for sid `2026-01-01T0000-aaaaaa`: artifact +
  sidecar + one `audit_history.jsonl` row appended per run (the tracked-fixture
  mutation observed twice in Phase 173 -- one row per suite/batch run).

### F4. Non-offenders sharing the sid strings (verified)

- `tests/test_gate_chain_completeness.py:46` -- fully synthetic (`tmp_path` gates
  root + explicit `ledger_path`/`gates_root` args). No live I/O.
- `tests/test_gate_provenance_bypass_pytest_only.py:20,32` -- both calls carry a
  schema-invalid payload (`{"phase": "plan"}`); `write_artifact` raises
  `ValueError` at `_validate_data` before any disk write.
- `tests/test_skill_prose_cites_ai_provenance.py:68` -- `phase="fake"` fails
  schema load before write.
- `tests/test_gate_chain_fires_hook.py` / `test_gate_chain_hook_does_not_break_write.py`
  / `test_gate_chain_phase52_provenance_still_enforced.py` -- use
  `monkeypatch.chdir(tmp_path)` which does NOT move the import-time `GATES_DIR`
  constant, but their sids (`test-session*`, `x` raises pre-write) fall inside the
  conftest session-end sweep (`tests/conftest.py:27-56`) or never write. Latent
  same-class bug, but swept; out of #274's named scope.

### F5. The five tracked pollution dirs are safe to untrack

`git ls-files` confirms `.qor/gates/2026-01-01T0000-aaaaaa/`,
`.qor/gates/2026-04-30T0000-test03|test04|test06/`, `.qor/gates/ideate-e2e/`,
`.qor/gates/ideate-prov/` are tracked. Verified consumers: zero -- no META_LEDGER
entry cites any of these session ids (grep over docs/META_LEDGER.md: 0 hits), no
qor/ module references them (grep: 0 hits), `gate_chain_completeness` and
`gate_provenance.verify_committed` walk ONLY ledger-seal-referenced sessions, and
no test reads their committed contents (all matching tests write or use synthetic
dirs, F4). They are historical accidental commits of this same defect.

### F6. Conftest sweep widening is NOT safe as proposed

`tests/conftest.py:27-56` sweeps `test*` / `cli-*` / `t<N>` dirs at session end. A
pattern wide enough to catch `2026-04-30T0000-test03` or `ideate-e2e` risks
matching tracked historical session dirs (e.g. `2026-05-24T0430-gh118-research`,
`2026-06-09T0000-fable354` -- many non-canonical tracked ids exist). The root fix
(redirect the writers) makes widening unnecessary; recommend declining issue
proposal item 2 with this rationale.

## Blueprint Alignment

`docs/ARCHITECTURE_PLAN.md` is silent on test-fixture hygiene; the operative
contracts are the test-discipline doctrine (no live-state coupling) and
`qor/gates/chain.md` (gate tree is runtime state, not fixture space).

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| doctrine-test-discipline: no live-state hardcoding/coupling | 3 files couple to the live gate tree | DRIFT (the defect under research) |
| conftest sweep removes synthetic-session pollution | Sweep patterns miss all five fixture ids | MATCH (by design; widening unsafe per F6) |
| chain.md: `.qor/gates/` is runtime consumer state | Tracked fixture dirs exist with no consumer | DRIFT (untrack them) |

## Recommendations

1. (P0) Fix the three offender files: canonical imports (drop the sys.path
   doppelganger), patch `qor.scripts.validate_gate_artifact.GATES_DIR` (writer)
   alongside `gate_chain.GATES_DIR` (resolver), replace `QORLOGIC_PROJECT_DIR`
   with `QOR_ROOT` + writer patch.
2. (P0) `git rm -r` the five tracked pollution dirs (F5: zero consumers).
3. (P1) Regression guard: a test that snapshots the `.qor/gates/` inventory, runs
   the three fixed files in a pytest subprocess, and asserts the live tree is
   byte-identical (catches any future resolver-only patch regression).
4. (P2) Decline conftest-sweep widening with the F6 rationale, recorded on GH #274.

## Updated Knowledge

No Shadow Genome entry needed (defect recorded as GH #274; fix in flight this
session). The doppelganger-import shape is worth a line in the brief only; if it
recurs, promote to an SG countermeasure.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
