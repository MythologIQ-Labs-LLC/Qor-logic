# Plan: Phase 173 - Iteration-versioned gate artifacts (GH #237)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**: (none)

**boundaries**:
- limitations: Immutability is enforced at the writer (the versioned file is never re-targeted); filesystem-level tampering remains detectable only via the provenance sidecar, unchanged from Phase 158. Legacy session dirs (no `-iter` files) keep singleton-only semantics; a phase re-run in a PRE-173 session dir starts iteration numbering from 1 without recovering already-lost bytes.
- non_goals: No retroactive migration of existing session dirs; no change to schema semantics, provenance env binding (`QOR_SKILL_ACTIVE`), tier_guard short-chain rules, or hook fail-open behavior; no CLI surface changes.
- exclusions: `validate_all_current_session` keeps iterating singleton names (the latest copy is definitionally current); no glossary terms; consumer-repo remediation is out of scope (GH #237 records it as already hand-remediated).

## Open Questions

(none)

## Origin

Research brief docs/research-brief-gate-artifact-iteration-2026-07-13.md (ledger entry #410, session `2026-07-13T0335-8e819f`); GH #237 (one seal, one immutable file). Defect confirmed by live repro (research F1).

## Locked Decisions

- **LD-1: version at the single write point.**
  `grep -nE 'def write_artifact' qor/scripts/validate_gate_artifact.py -> 123`; `grep -nE 'os.replace' qor/scripts/validate_gate_artifact.py -> 139`. Every gate write funnels through this one function (gate_chain.write_gate_artifact delegates: `grep -nE 'vga.write_artifact' qor/scripts/gate_chain.py -> 289`), so iteration versioning lives here and nowhere else. It writes `<phase>-iter<N>.json` (N = max existing iteration + 1, starting 1; atomic tempfile + os.replace preserved), then refreshes `<phase>.json` as a byte-identical latest copy, and returns the VERSIONED path.
- **LD-2: the singleton stays, as a latest copy.**
  Seal-side consumers all join on `<sid>/<phase>.json`: `grep -nE 'def check' qor/reliability/gate_chain_completeness.py -> 52`; `grep -nE 'def verify_committed' qor/scripts/gate_provenance.py -> 206`; `grep -nE 'def _gate_artifacts|def _provenance|def _audit_history' qor/scripts/evidence_bundle.py -> 80,98,118`; `grep -nE 'def declared_artifacts' qor/scripts/tier_guard.py -> 59`. None of them change: the singleton is always byte-identical to the highest iteration, so their reads stay valid.
- **LD-3: sidecar duality.**
  `grep -nE 'def sidecar_path' qor/scripts/gate_provenance.py -> 95` derives `<stem>.provenance` via `with_suffix`, so `audit-iter2.json -> audit-iter2.provenance` needs no naming change. `gate_chain.write_gate_artifact` calls `write_sidecar` twice: once for the versioned file (immutable evidence binding) and once for the singleton (keeps `verify_committed` + `evidence_bundle._provenance` green). Identical bytes give identical `payload_sha256`.
- **LD-4: resolution prefers the highest iteration, singleton is the fallback.**
  `grep -nE 'def check_prior_artifact' qor/scripts/gate_chain.py -> 59`; `grep -nE 'def read_phase_artifact' qor/scripts/gate_chain.py -> 198`. A new helper `latest_artifact_path(phase, session_dir)` in validate_gate_artifact.py globs `<phase>-iter*.json`, parses N with `^<phase>-iter([0-9]+)\.json$`, and returns the max-N path or the singleton when no iteration exists (legacy sessions). check_prior_artifact, read_phase_artifact, and _check_short_chain_plan resolve through it. Validation semantics unchanged (resolve, then validate_one).
- **LD-5: audit history rows bind the versioned filename.**
  `grep -nE 'def append' qor/scripts/audit_history.py -> 34`; `grep -nE 'additionalProperties' qor/gates/schema/audit.schema.json -> 6 (true)`. `append` gains keyword `artifact_filename: str | None = None`; when set, the row records it. Schema-additive: `additionalProperties: true` means no schema amendment, no SCHEMA_REGISTRY change, no gate_schema_freeze_lint exposure.
- **LD-6: hook and sidecar bind the exact evidence.**
  `grep -nE 'def _fire_gate_written_hook' qor/scripts/gate_chain.py -> 302`. The gate-written event's `artifact_path` and `payload_sha256` are computed from the versioned path returned by the writer, so observers record the immutable file. `write_gate_artifact` returns the versioned path (callers used it for logging only; tests asserting the singleton return are updated in the same phase).
- **LD-7: filename grammar cannot collide.**
  Phase names are lowercase alphabetic (`grep -nE '^PHASES' qor/scripts/validate_gate_artifact.py -> 53`; all entries `[a-z]+`), so `-iter<N>` is unambiguous and `audit_history.jsonl` / `*.provenance` never match the `<phase>-iter([0-9]+)\.json` pattern.

## Phase 1: Iteration-versioned writer + sidecar duality + history binding (TDD first)

### Affected Files

- tests/test_gate_artifact_iteration.py - NEW; behavioral tests for versioned write, immutability of prior iterations, sidecar duality, history filename binding
- tests/test_gate_chain_fires_hook.py - hook event now carries the versioned artifact path (assertion update)
- tests/test_gates.py - two exact-path assertions on the writer's return value (`out == gates / sid / "plan.json"` at test_write_gate_artifact_creates_file_at_correct_path and test_write_gate_artifact_respects_explicit_session_id) updated to the versioned form `plan-iter1.json`; all other writer tests read through the returned path or the singleton and are unaffected (caller sweep evidence: `grep -rn 'assert out ==' tests/test_gates.py`)
- qor/scripts/validate_gate_artifact.py - `iteration_pattern`, `latest_artifact_path`, `next_iteration_path` helpers; `write_artifact` writes versioned file then refreshes singleton; returns versioned path
- qor/scripts/gate_chain.py - `write_gate_artifact` writes both sidecars, passes `artifact_filename` to audit_history, fires hook with versioned path
- qor/scripts/audit_history.py - `append(payload, session_id, artifact_filename=None)` records the field

### Changes

`validate_gate_artifact.py`: module-level `_ITER_RE_TMPL` compiled per call as `re.compile(rf"^{re.escape(phase)}-iter([0-9]+)\.json$")`. `latest_artifact_path(phase, session_dir) -> Path` returns max-N versioned path, else the singleton path (which may not exist; caller checks). `next_iteration_path(phase, session_dir) -> Path` returns N = max + 1 (1 when none). `write_artifact` validates, writes the versioned target atomically, refuses to land on an existing versioned path (advances N and retries once; raises `FileExistsError` on a second collision), then copies the same bytes to the singleton via tempfile + os.replace, returns the versioned path.

`gate_chain.write_gate_artifact`: capture the returned versioned path; `audit_history.append(payload, session_id=sid, artifact_filename=versioned.name)`; `gate_provenance.write_sidecar(phase, sid, versioned)` AND `gate_provenance.write_sidecar(phase, sid, singleton)`; `_fire_gate_written_hook(phase, sid, versioned)`; return the versioned path.

`audit_history.append`: `record["artifact_filename"] = artifact_filename` when provided, before schema validation (validates under `additionalProperties: true`).

### Unit Tests

- tests/test_gate_artifact_iteration.py::test_first_write_creates_iter1_and_identical_singleton - one write produces `audit-iter1.json` and `audit.json` with byte-identical content; returned path is the versioned file
- tests/test_gate_artifact_iteration.py::test_rerun_preserves_sealed_iter1_bytes - GH #237 acceptance: record iter1's SHA-256, re-run the phase with a different payload (VETO -> PASS), assert iter1 exists with the identical hash, iter2 exists, singleton equals iter2
- tests/test_gate_artifact_iteration.py::test_rerun_preserves_iter1_provenance_sidecar - iter1's `.provenance` bytes are unchanged by the re-run; iter2 and the singleton each get a fresh sidecar whose `payload_sha256` verifies via `gate_provenance.verify_sidecar`
- tests/test_gate_artifact_iteration.py::test_audit_history_rows_carry_versioned_filenames - two audit writes yield history rows whose `artifact_filename` values are `audit-iter1.json`, `audit-iter2.json` in order
- tests/test_gate_artifact_iteration.py::test_collision_advances_iteration_never_overwrites - pre-placing `plan-iter1.json` by hand, a write lands on `plan-iter2.json` and the pre-placed bytes are untouched
- tests/test_gate_artifact_iteration.py::test_hook_event_binds_versioned_path - the dispatched gate-written event's `artifact_path` names the versioned file and its `payload_sha256` matches those bytes

## Phase 2: Latest-iteration resolution with legacy fallback (TDD first)

### Affected Files

- tests/test_gate_artifact_iteration.py - resolution + fallback tests (same file, second group)
- qor/scripts/gate_chain.py - `check_prior_artifact`, `read_phase_artifact`, `_check_short_chain_plan` resolve via `latest_artifact_path`

### Changes

`check_prior_artifact`: `artifact = vga.latest_artifact_path(prior, GATES_DIR / sid)` replaces the direct singleton join (existence check and validate_one flow unchanged). `read_phase_artifact` and `_check_short_chain_plan` get the same substitution. `_check_ideation_predecessor` also resolves through the helper (ideation re-runs are legal).

### Unit Tests

- tests/test_gate_artifact_iteration.py::test_check_prior_artifact_resolves_highest_iteration - with `plan-iter1.json` (marker payload A) and `plan-iter2.json` (marker payload B) plus singleton, `check_prior_artifact("audit")` reports the iter2 path
- tests/test_gate_artifact_iteration.py::test_read_phase_artifact_returns_latest_payload - `read_phase_artifact("plan")` returns payload B, not payload A
- tests/test_gate_artifact_iteration.py::test_legacy_singleton_only_session_still_resolves - a session dir containing only a hand-placed valid `plan.json` (no `-iter` files) resolves and validates exactly as before (backward compatibility)
- tests/test_gate_artifact_iteration.py::test_stale_singleton_does_not_shadow_iterations - when the singleton is stale (hand-edited to payload A while iter2 holds payload B), resolution still returns iter2 (versioned files are authoritative)

## Phase 3: Contract documentation

### Affected Files

- qor/gates/chain.md - "Artifact locations" section documents the versioned form, the latest-copy singleton, resolution order, and the no-overwrite rule

### Changes

chain.md gains an "Iteration versioning (Phase 173)" subsection under Artifact locations: runtime layout `.qor/gates/<sid>/<phase>-iter<N>.json` (immutable, one per emission) + `<phase>.json` (latest copy, compatibility); resolution = highest N, singleton fallback; audit_history rows carry `artifact_filename`; sidecars exist for both forms. Prose stays descriptive (no definitional glossary patterns).

## Feature Inventory Touches

(empty -- governance tooling only; no user-touchable feature row in FEATURE_INDEX.md)

## Definition of Done

### Deliverable: immutable iteration-versioned gate artifacts

- **D1**: A later gate run can never overwrite evidence already bound by a seal: every emission lands in its own immutable versioned file; the mutable singleton is only a latest-copy convenience (GH #237 "one seal, one immutable file").
- **D2**: `validate_gate_artifact.write_artifact` returns the versioned path; `latest_artifact_path` / `next_iteration_path` helpers; `gate_chain.write_gate_artifact` binds sidecar + hook + audit-history rows to the versioned file; all under the existing atomic-write and provenance-env invariants.
- **D3**: Ledger entries for plan/audit/implement/seal recorded in META_LEDGER.md; chain.md documents the layout; GH #237 acceptance criteria quoted in the seal entry; no schema or registry change.
- **D4**: `test_rerun_preserves_sealed_iter1_bytes` observes that re-running a gate leaves earlier sealed bytes hash-identical; `test_check_prior_artifact_resolves_highest_iteration` and `test_legacy_singleton_only_session_still_resolves` observe resolution and backward compatibility.

## CI Commands

- `python -m pytest tests/test_gate_artifact_iteration.py -q` - focused suite for the new behavior (run twice for determinism)
- `python -m pytest -q` - full suite; locks singleton-consumer compatibility (completeness, provenance, evidence bundle, hooks)
- `python -m qor.scripts.gate_provenance verify-committed --repo-root .` - committed sidecars still verify with the latest-copy singleton
- `python -m qor.reliability.gate_chain_completeness --repo-root .` - sealed sessions still resolve all required gate artifacts
- `python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md` - ledger chain integrity across the phase's entries
