# Plan: Phase 174 - Gate-dir test hygiene (GH #274)

**change_class**: hotfix

**doc_tier**: minimal

## Open Questions

(none)

## Origin

Research brief docs/research-brief-gate-dir-test-hygiene-2026-07-13.md (ledger entry #414, session `2026-07-13T0427-d0d371`); GH #274 (Phase 173 follow-up). Test-only repo-hygiene fix: no runtime code changes.

## Locked Decisions

- **LD-1: the doppelganger import is the root cause in test_gate_chain_provenance.py.**
  `grep -nE 'sys.path.insert' tests/test_gate_chain_provenance.py -> 16` (+ `import gate_chain` at 17, `import validate_gate_artifact as _vga` inside the test06 body). Monkeypatches on those module objects never reach `qor.scripts.gate_chain` / `qor.scripts.validate_gate_artifact`, which production code imports absolutely. Fix: drop the sys.path insert; import both canonically; patch BOTH constants.
- **LD-2: the writer joins `validate_gate_artifact.GATES_DIR`, not `gate_chain.GATES_DIR`.**
  `grep -nE 'session_dir = GATES_DIR' qor/scripts/validate_gate_artifact.py -> 101,176` (176 is `write_artifact`); `grep -nE 'vga.write_artifact' qor/scripts/gate_chain.py -> 293`. Any test that writes must patch `vga.GATES_DIR`; tests that also resolve must patch `gate_chain.GATES_DIR`. This is the established pattern in tests/test_gates.py and tests/test_gate_artifact_iteration.py.
- **LD-3: gate-tree redirection env var is QOR_ROOT.**
  `grep -nE 'QOR_ROOT' qor/workdir.py -> 29`. `QORLOGIC_PROJECT_DIR` (tests/test_skill_active_env.py:29) controls host INSTALL dirs (`grep -nE 'QORLOGIC_PROJECT_DIR' qor/hosts.py -> 8,11`), not `.qor/gates`. QOR_ROOT also redirects the provenance key dir and audit_history (both resolve `workdir.root()` at call time).
- **LD-4: the five tracked pollution dirs have zero consumers.**
  `grep -c '2026-01-01T0000-aaaaaa\|2026-04-30T0000-test0\|ideate-e2e\|ideate-prov' docs/META_LEDGER.md -> 0 (pre-#414 entries)`; same grep over `qor/` -> 0. `gate_chain_completeness.check` and `gate_provenance.verify_committed` walk only ledger-seal-referenced sessions (`qor/reliability/gate_chain_completeness.py:52`; `qor/scripts/gate_provenance.py:206`). Tests matching the sid strings write or use synthetic dirs (research F4); none read committed bytes. `git rm -r` is safe.
- **LD-5: the guard test must mirror the conftest sweep filter.**
  `grep -nE 'is_pollution' tests/conftest.py -> 49,54`: the session-end sweep deletes `test*` / `cli-*` / `t<N>` dirs. The guard's inner pytest process runs its own session-end sweep, which may legitimately delete such dirs created earlier by the OUTER suite. The guard therefore snapshots the live gate tree EXCLUDING sweep-pattern dirs, keeping it deterministic under any test ordering.

## Phase 1: Guard test + offender fixes (TDD first)

### Affected Files

- tests/test_gate_dir_hygiene.py - NEW; subprocess inventory guard proving the three fixed files leave the live gate tree byte-identical
- tests/test_gate_chain_provenance.py - canonical imports (`from qor.scripts import gate_chain`, `from qor.scripts import validate_gate_artifact as vga`); every writing test patches `vga.GATES_DIR` (+ `gate_chain.GATES_DIR` where resolution is exercised); test06 patches the canonical vga
- tests/test_qor_ideate_writes_gate_artifact.py - both tests additionally patch `vga.GATES_DIR` to the same tmp gates root
- tests/test_skill_active_env.py - `test_skill_param_avoids_shell_prefix_provenance_error` replaces `QORLOGIC_PROJECT_DIR` with `QOR_ROOT=tmp_path` and patches `vga.GATES_DIR` (audit write also touches audit_history + provenance keys, both QOR_ROOT-anchored)

### Changes

`tests/test_gate_dir_hygiene.py`: `_snapshot(gates_root) -> dict[str, str]` maps every file under `.qor/gates/` (repo-relative via `Path(__file__).resolve().parent.parent`) to its SHA-256, EXCLUDING files under first-level dirs matching the conftest sweep patterns (LD-5: `test*`, `cli-*`, `t<N>`). The test snapshots, runs `[sys.executable, "-m", "pytest", "-q", <the three fixed files>]` as a subprocess with `cwd=repo_root` and `timeout=180`, asserts exit code 0, re-snapshots, and asserts equality (no file added, removed, or modified in the live tree).

`tests/test_gate_chain_provenance.py`: delete lines 16-17 (sys.path insert + doppelganger import); `from qor.scripts import gate_chain` and `from qor.scripts import validate_gate_artifact as vga` at top; every `monkeypatch.setattr(gate_chain, "GATES_DIR", ...)` in a WRITING test gains a sibling `monkeypatch.setattr(vga, "GATES_DIR", ...)` AND `monkeypatch.setenv("QOR_ROOT", str(tmp_path))` (sidecar writes mint per-session keys via `workdir.root()`; without the env redirect the gitignored live `.qor/session/keys/` accretes key files); the test06 body's local `import validate_gate_artifact as _vga` block is replaced by the module-level canonical `vga`.

`tests/test_qor_ideate_writes_gate_artifact.py`: import vga; add `monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")` and `monkeypatch.setenv("QOR_ROOT", str(tmp_path))` beside the existing gate_chain patch in both tests.

`tests/test_skill_active_env.py`: import vga; in the writing test set `monkeypatch.setenv("QOR_ROOT", str(tmp_path))` and `monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")`; drop the `QORLOGIC_PROJECT_DIR` line.

### Unit Tests

- tests/test_gate_dir_hygiene.py::test_gate_writing_tests_leave_live_tree_untouched - RED against the current offenders (the subprocess run mutates the live tree), GREEN after the three fixes; asserts inner exit code 0 AND byte-identical filtered snapshots, so it fails if any fixed test regresses to a resolver-only patch OR starts failing outright
- tests/test_gate_chain_provenance.py (existing tests, redirected) - same behavioral assertions as today (ProvenanceError paths, sidecar verify) now proven against tmp-tree writes; `verify_sidecar` still passes payload+hmac on the canonical module (behavior, not placement, is what each test asserts)
- tests/test_qor_ideate_writes_gate_artifact.py (existing, redirected) - written ideation artifact validates against the schema from the tmp path returned by the writer
- tests/test_skill_active_env.py (existing, redirected) - ProvenanceError without `skill=`, successful write with `skill="audit"`, env restored -- unchanged assertions against tmp

## Phase 2: Untrack the pollution fixtures

### Affected Files

- .qor/gates/2026-01-01T0000-aaaaaa/ - git rm -r (zero consumers per LD-4)
- .qor/gates/2026-04-30T0000-test03/ - git rm -r
- .qor/gates/2026-04-30T0000-test04/ - git rm -r
- .qor/gates/2026-04-30T0000-test06/ - git rm -r
- .qor/gates/ideate-e2e/ - git rm -r
- .qor/gates/ideate-prov/ - git rm -r

### Changes

Remove the six tracked pollution paths (five fixture identities; test03/test04/test06 are three of them) from index and working tree. Post-removal proof commands (run in Phase 2, recorded in the seal entry): `qor-logic reliability gate_chain_completeness --repo-root . --phase-min 52` and `python -m qor.scripts.gate_provenance verify-committed --repo-root .` both stay green (neither walks unreferenced sessions), and the full suite stays green (no test reads the removed bytes).

### Unit Tests

- tests/test_gate_dir_hygiene.py::test_gate_writing_tests_leave_live_tree_untouched - re-run after removal proves the fixed tests do not recreate the removed dirs (the snapshot filter does not exclude these identities, so any recreation fails equality)

## Feature Inventory Touches

(empty -- test hygiene only; no user-touchable feature)

## Definition of Done

### Deliverable: clean-tree test suite

- **D1**: A full-suite run on a clean tree leaves the live `.qor/gates/` tree byte-identical outside conftest-swept synthetic dirs (GH #274 acceptance), and the five historical pollution identities are no longer tracked.
- **D2**: Three test files patch the writer constant (`validate_gate_artifact.GATES_DIR`) and use canonical imports; no `sys.path.insert` doppelganger remains in tests/test_gate_chain_provenance.py; guard test at tests/test_gate_dir_hygiene.py with the LD-5 sweep-pattern filter.
- **D3**: Ledger entries for plan/audit/implement/seal in META_LEDGER.md; GH #274 closes with the F6 decline rationale (conftest widening rejected) recorded on the issue.
- **D4**: `test_gate_writing_tests_leave_live_tree_untouched` observes byte-identical live-tree snapshots around a subprocess run of the three fixed files (red against the pre-fix offenders, green after).

## CI Commands

- `python -m pytest tests/test_gate_dir_hygiene.py tests/test_gate_chain_provenance.py tests/test_qor_ideate_writes_gate_artifact.py tests/test_skill_active_env.py -q` - focused suite (run twice for determinism)
- `python -m pytest -q` - full suite; proves no test read the untracked fixture bytes
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
