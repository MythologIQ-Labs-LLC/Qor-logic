# Plan: Phase 57 — `gate_written` observer channel (PR #12 reintegration)

**change_class**: feature

**doc_tier**: standard

**terms_introduced**:
- term: gate_written hook
  home: qor/references/doctrine-hook-contract.md
- term: hook contract
  home: qor/references/doctrine-hook-contract.md

**boundaries**:
- limitations:
  - Hooks are non-authoritative observers; the gate artifact is persisted to disk before any hook fires. Hook errors never abort the write.
  - Per-callable timeout applies only to subprocess hooks (30s default); Python callables run synchronously and may hang the calling skill (operator must SIGINT — Phase 57 fix vs. the original PR #12 design ensures SIGINT propagates).
  - Dispatch order is deterministic: entry-points first (in `importlib.metadata.entry_points` order), then `.qor/hooks.yaml` entries top-to-bottom. No concurrency.
  - Trust model is the consumer's repo: shell commands and Python dotted paths in `.qor/hooks.yaml` execute arbitrary code. Documented explicitly; mirrors `.github/workflows/`, `.pre-commit-config.yaml`, `npm preinstall` pattern.
- non_goals:
  - Cryptographic signing or sandboxing of hooks. Out of scope; consumers apply repo-level review controls.
  - Async/concurrent hook invocation. Synchronous-by-design for determinism and ordering.
  - Replacing the FailSafe-Pro filesystem-watcher push channel — Phase 57 ships an *additional* push-channel; consumers may use either.
  - Bidirectional event flow. Hooks observe; they do not affect the gate write.
- exclusions:
  - Modifying the gate-artifact schema or write-path semantics. Phase 57 only adds a post-write hook fire.
  - Phase 52 provenance-binding contract changes. Hooks fire AFTER provenance check passes and the authoritative write succeeds.
  - Retroactive hook fires for pre-Phase-57 historical gate writes.

## Sprint context

PR #12 was opened 2026-04-20 against `main` predating the five-phase compliance sprint (Phase 52 provenance binding, Phase 53 prompt-injection, Phase 54 AI provenance, Phase 55 admission/SBOM/lints, Phase 56 secret-scanning). The PR's design is sound but has two binding issues per `.agent/staging/AUDIT_REPORT.md` (Phase 57 audit, VETO):

1. `except BaseException` in hook-invoke and fire-hook helpers swallows SIGINT (OWASP A04 insecure design).
2. Stale branch — code authored before five intervening sealed phases.

Phase 57 reintegrates the PR's API surface (the `GateWrittenEvent` contract, entry-point group, config-file format, swallow-log error semantics) on top of current main with the VETO grounds resolved. PR #12 closes with a link to this plan after Phase 57 seals.

## Open Questions

1. **Default fire-on-phase set**: should the hook fire on every successful `write_gate_artifact` call (every phase: research/plan/audit/implement/substantiate/deliver/remediate/etc.), or only on a subset (e.g. only seal-adjacent phases)? Default: **fire on every phase** (matches PR #12; downstream consumers filter by `event.phase` themselves).
2. **Hook-log location**: `<root>/.qor/hooks/hooks.log` (PR #12 default) or `<root>/.qor/gates/<sid>/hooks.log` (sidecar to the session)? Default: **`<root>/.qor/hooks/hooks.log`** — repo-scoped, append-only, easier for FailSafe-Pro to tail.
3. **Subprocess hook argv**: PR #12 appends `str(event.artifact_path)` as the final argv element. Should `event.payload_sha256` and `event.phase` also be passed? Default: **artifact_path only** — hooks parse the file at the path and extract whatever they need; minimizes argv-size attack surface and matches PR #12.

Defaults will be encoded unless overridden during audit.

## Phase 1: `gate_hooks` module + dispatcher + frozen event payload

### Affected Files

- `tests/test_gate_hooks_dispatch.py` — NEW: locks `dispatch_gate_written` API, entry-point cache, ordering invariant.
- `tests/test_gate_hooks_swallow.py` — NEW: locks swallow-log semantics + `except Exception` (NOT `except BaseException`) — Phase 57 fix vs. PR #12.
- `tests/test_gate_hooks_sigint_propagates.py` — NEW: regression test for the Phase 57 VETO ground; asserts `KeyboardInterrupt` raised inside a hook callable propagates to the caller (i.e. dispatch does NOT catch it).
- `tests/test_gate_hooks_config_file.py` — NEW: locks `.qor/hooks.yaml` parse + dotted-path + subprocess-argv resolution.
- `tests/test_gate_hooks_no_hooks_file.py` — NEW: missing config file → empty hook list, no error.
- `tests/test_gate_hooks_event_payload_shape.py` — NEW: locks `GateWrittenEvent` frozen-dataclass field set + types.
- `qor/scripts/gate_hooks.py` — NEW (~165 LOC; reduced from PR #12's 176 by removing redundant exception trace formatting). Public API:
  - `GateWrittenEvent` frozen dataclass: `(phase: str, session_id: str, artifact_path: Path, payload_sha256: str, ts: str)`.
  - `ENTRY_POINT_GROUP = "qor_logic.events.gate_written"` constant.
  - `HOOK_TIMEOUT_SECONDS = 30` constant.
  - `dispatch_gate_written(event: GateWrittenEvent) -> None` — fires entry-points then config-file hooks; swallows `Exception` per hook (NOT `BaseException`); appends JSONL to `<root>/.qor/hooks/hooks.log`.
  - `reload_entry_points() -> None` — invalidates module-level cache; tests-only.
  - `_HookTarget` frozen dataclass: internal hook representation with `name`, `kind` (`callable`|`command`), `callable`, `argv`.
  - `_enumerate_entry_points()`, `_load_config_file_hooks(root)`, `_resolve_config_entry(idx, entry)`, `_invoke_hook_safely(target, event, log_path)`, `_run_command_hook(target, event)`, `_append_log(...)` — internal helpers.

### Changes

The Phase 57 module's primary docstring cites Phase 57 and the framework surface it serves (downstream observer push-channel for governance-ledger bridges; OWASP LLM07 Insecure Plugin Design adjacent; closes the polling-vs-push gap that prompted PR #12). The "B24 / FailSafe-Pro origin" attribution moves to `CHANGELOG.md` per Phase 53/54/55/56 docstring discipline.

`_invoke_hook_safely` uses `except Exception` (not `except BaseException`). `KeyboardInterrupt` and `SystemExit` propagate. The `# noqa: BLE001` comment is removed because `Exception` does not trip the BLE001 rule.

The hook-target cache (`_entry_point_cache`) is module-level; `reload_entry_points()` is the single invalidation point. Entry-points are resolved once per process and reused.

`_load_config_file_hooks` reads `<root>/.qor/hooks.yaml` via `yaml.safe_load` (existing PyYAML dep — zero new deps). Top-level keys other than `gate_written` are ignored. Missing file → empty list.

`_resolve_config_entry` accepts two entry shapes: `{module: "pkg.mod:attr"}` (dotted-path imported via `importlib.import_module` + `getattr`) or `{command: ["argv", "list"]}` (subprocess argv list, no shell=True). Anything else is silently dropped.

`_run_command_hook` invokes `subprocess.run(argv + [str(event.artifact_path)], check=False, capture_output=True, timeout=30)`. Per Open Question 3 default: only artifact_path appended.

`_append_log` writes one JSONL record per hook fire to `<root>/.qor/hooks/hooks.log` with `{ts, hook, event, status, duration_ms, exception?}`. Phase 57 uses `shadow_process.now_iso()` for the timestamp (consistent with all other Phase 53+ modules).

### Unit Tests

- `tests/test_gate_hooks_dispatch.py`:
  - `test_dispatch_with_no_hooks_is_noop` — fixture: empty entry-points, no hooks.yaml; assert `dispatch_gate_written(event)` returns None and writes no log file.
  - `test_dispatch_invokes_entry_point_callable_once` — fixture: monkeypatch `importlib.metadata.entry_points` to return one mock callable; assert callable invoked exactly once with the event.
  - `test_dispatch_caches_entry_points` — invoke `dispatch_gate_written` twice with different events; assert `entry_points` lookup ran once.
  - `test_dispatch_runs_entry_points_before_config_hooks` — fixture: one entry-point callable + one hooks.yaml dotted-path; assert ordering by inspecting log timestamps.
  - `test_reload_entry_points_invalidates_cache` — invoke dispatch (cache populated), monkeypatch entry_points to new set, call `reload_entry_points()`, dispatch again; assert new set used.
- `tests/test_gate_hooks_swallow.py`:
  - `test_callable_hook_raising_exception_is_swallowed_and_logged` — fixture: callable raises `ValueError`; assert dispatch returns None, log contains `status: error` + traceback.
  - `test_subprocess_hook_with_nonzero_exit_is_logged_with_status_ok` — subprocess hooks BLOCK is the consumer's responsibility; non-zero exit codes are logged but not classified as error (matches PR #12 + Phase 57 design — the artifact is the source of truth, hooks observe).
  - `test_swallow_uses_except_exception_not_baseexception` — static check: `qor/scripts/gate_hooks.py` source contains `except Exception` and does NOT contain `except BaseException` in `_invoke_hook_safely`. Anchored to function source, not file substring (Phase 50 co-occurrence model).
- `tests/test_gate_hooks_sigint_propagates.py`:
  - `test_keyboard_interrupt_in_callable_hook_propagates` — fixture: callable raises `KeyboardInterrupt`; assert `dispatch_gate_written` re-raises (does NOT swallow). Phase 57 VETO-remediation regression test.
  - `test_system_exit_in_callable_hook_propagates` — fixture: callable raises `SystemExit`; assert re-raised.
- `tests/test_gate_hooks_config_file.py`:
  - `test_loads_dotted_path_hook_from_yaml` — fixture: `.qor/hooks.yaml` with `gate_written: [{module: "test_fixtures.hook:on_event"}]`; assert hook resolved + invoked.
  - `test_loads_command_hook_from_yaml_with_list_argv` — fixture: `command: ["echo", "hello"]`; assert `subprocess.run` called with `["echo", "hello", str(artifact_path)]`.
  - `test_rejects_command_with_string_argv` — fixture: `command: "echo hello"` (string, not list); assert silently dropped (no shell=True attack surface).
  - `test_rejects_unknown_entry_shape` — fixture: `gate_written: [{not_a_known_key: "x"}]`; assert dropped silently.
  - `test_subprocess_hook_argv_only_appends_artifact_path` — verify Open Question 3 default: payload_sha256 and phase are NOT appended.
  - `test_yaml_parse_error_returns_empty_list` — fixture: malformed YAML; assert empty list, no exception.
- `tests/test_gate_hooks_no_hooks_file.py`:
  - `test_missing_hooks_yaml_returns_empty_list` — fixture: no `.qor/hooks.yaml`; assert `_load_config_file_hooks(root)` returns `[]`.
- `tests/test_gate_hooks_event_payload_shape.py`:
  - `test_gate_written_event_is_frozen_dataclass` — assert `dataclasses.is_dataclass(GateWrittenEvent)`; assert frozen via attempted attribute mutation raising.
  - `test_gate_written_event_field_set` — assert field set is exactly `{phase, session_id, artifact_path, payload_sha256, ts}`.
  - `test_gate_written_event_field_types` — assert `phase: str`, `session_id: str`, `artifact_path: Path`, `payload_sha256: str`, `ts: str`.
  - `test_payload_sha256_is_hex64` — assert dispatch's computed `payload_sha256` matches `hashlib.sha256(file_bytes).hexdigest()` form (regex `^[0-9a-f]{64}$`).

## Phase 2: `gate_chain.write_gate_artifact` post-write hook fire + Phase 50 co-occurrence invariant

### Affected Files

- `tests/test_gate_chain_fires_hook.py` — NEW: end-to-end test that `write_gate_artifact` fires `dispatch_gate_written` after the authoritative write succeeds.
- `tests/test_gate_chain_hook_does_not_break_write.py` — NEW: regression — when `dispatch_gate_written` raises `Exception`, the gate artifact is still on disk (write happens BEFORE hook fire).
- `tests/test_gate_chain_phase52_provenance_still_enforced.py` — NEW: regression — Phase 52 provenance binding (`QOR_SKILL_ACTIVE` env check) still fires BEFORE the hook chain. A write rejected for missing provenance does NOT fire any hook.
- `tests/test_gate_chain_co_occurrence_hook_dispatch.py` — NEW: Phase 50 co-occurrence behavior invariant. Conditional rule: every successful path through `write_gate_artifact` MUST call `gate_hooks.dispatch_gate_written`. Anchored to actual function source, not substring.
- `qor/scripts/gate_chain.py` — UPDATE: insert `_fire_gate_written_hook(phase, sid, path)` call after `audit_history.append(...)` block. Helper imports `gate_hooks` lazily; computes `payload_sha256` from file bytes; constructs `GateWrittenEvent`; calls `dispatch_gate_written`. Wraps in `try/except Exception` (NOT `BaseException`).

### Changes

The fire-hook helper lives in `gate_chain.py` (not in `gate_hooks.py`) because it bridges the authoritative write path to the observer dispatcher; the bridging concern belongs to `gate_chain`. `gate_hooks` itself remains a leaf module (depends on `qor.workdir` + `qor.scripts.shadow_process`; does not depend on `gate_chain`).

Phase 52 provenance binding (lines 171-183 of current `gate_chain.py`) runs FIRST, before the artifact write. If `QOR_SKILL_ACTIVE` is missing or mismatched, `ProvenanceError` is raised and the function returns before any hook fires. This is the tested invariant in `test_gate_chain_phase52_provenance_still_enforced`.

`_fire_gate_written_hook` reads the artifact bytes back from disk to compute `payload_sha256` (rather than re-serializing the in-memory payload). This guarantees the hash matches what's actually on disk — protects against in-memory/on-disk divergence if a future schema-write helper transforms the payload.

The hook fire is wrapped in `try/except Exception` so that no hook failure can break the authoritative write path. `KeyboardInterrupt` and `SystemExit` still propagate (Phase 57 VETO ground 1 fix).

### Unit Tests

- `tests/test_gate_chain_fires_hook.py`:
  - `test_write_gate_artifact_fires_dispatch_with_correct_event_shape` — monkeypatch `gate_hooks.dispatch_gate_written` to capture invocation; write a gate artifact; assert dispatch called with `GateWrittenEvent` whose `phase`, `session_id`, `artifact_path`, `payload_sha256`, `ts` match the written artifact.
  - `test_payload_sha256_matches_artifact_file_bytes` — write artifact, capture event, assert `event.payload_sha256 == hashlib.sha256(artifact_path.read_bytes()).hexdigest()`.
- `tests/test_gate_chain_hook_does_not_break_write.py`:
  - `test_dispatch_raising_exception_does_not_prevent_artifact_write` — monkeypatch `dispatch_gate_written` to raise `RuntimeError`; assert `write_gate_artifact` returns the path AND the file exists on disk.
  - `test_dispatch_raising_keyboard_interrupt_propagates_after_write` — monkeypatch dispatch to raise `KeyboardInterrupt`; assert `write_gate_artifact` raises `KeyboardInterrupt` BUT the file is on disk (write completed before fire).
- `tests/test_gate_chain_phase52_provenance_still_enforced.py`:
  - `test_provenance_error_blocks_write_and_blocks_hook` — `QOR_SKILL_ACTIVE` unset; monkeypatch `dispatch_gate_written` to record invocation; assert `ProvenanceError` raised AND dispatch never called AND no artifact on disk.
- `tests/test_gate_chain_co_occurrence_hook_dispatch.py`:
  - `test_write_gate_artifact_function_body_calls_fire_hook` — Phase 50 model. Conditional rule: function `write_gate_artifact` in `qor/scripts/gate_chain.py` MUST contain a call to `_fire_gate_written_hook` AFTER the `vga.write_artifact(...)` call but BEFORE the function returns. Anchored to AST inspection, not substring grep — verifies call ordering at the AST level.

## Phase 3: doctrine + glossary + audit-pass alignment

### Affected Files

- `tests/test_doctrine_hook_contract_anchored.py` — NEW: heading-tree round-trip integrity for the new `qor/references/doctrine-hook-contract.md`.
- `tests/test_phase57_self_application.py` — NEW: 4 self-application tests verifying Phase 57 plan + ledger + module behavior end-to-end.
- `qor/references/doctrine-hook-contract.md` — NEW: lifts and rewrites PR #12's `hook-contract.md` content under qor-logic doctrine conventions. Sections: `## Applicability`, `## Event payload`, `## Entry-point registration`, `## Config-file format`, `## Invocation order`, `## Log format`, `## Trust model`, `## Performance`, `## Phase 57 changes vs. PR #12 origin`. Adds a Phase 57-specific section explaining the `except Exception` (not `BaseException`) discipline and the SIGINT-propagation contract.
- `qor/references/glossary.md` — APPEND 2 new terms: `gate_written hook` (post-write observer event), `hook contract` (the doctrine specifying the event payload + dispatch semantics + trust model).
- `qor/references/doctrine-shadow-genome-countermeasures.md` — APPEND new SG entry `SG-BareExceptionSwallowsSignals-A` codifying the BaseException-swallowing risk class + Phase 57 countermeasure (use `except Exception`; reserve `BaseException` only when explicitly handling `KeyboardInterrupt`/`SystemExit` for cleanup-then-reraise patterns).
- `CHANGELOG.md` — APPEND `[0.43.0] - 2026-05-XX` entry summarizing Phase 57 (gate_written observer channel; closes PR #12; FailSafe-Pro consumer attribution noted here, NOT in module docstring per Phase 53+ discipline).

### Changes

The new doctrine section codifies what Phase 57 wiring delivers and explicitly contrasts the Phase 57 hardening vs. the original PR #12 design (BaseException → Exception; module docstring discipline; phase-number citation).

`SG-BareExceptionSwallowsSignals-A` joins the SG catalog at the end of the existing list, following the `SG-Phase24-A`/`SG-PreAuditLintGap-A`/`SG-SecretLeakAtSeal-A` named pattern.

Glossary entries follow the YAML-fence convention with `term`, `definition`, `home`, `referenced_by`, `introduced_in_plan: phase57-gate-written-observer-channel`.

### Unit Tests

- `tests/test_doctrine_hook_contract_anchored.py`:
  - `test_doctrine_hook_contract_declares_phase_57_section_with_non_empty_body` — heading-tree integrity: `## Phase 57 changes vs. PR #12 origin` section present with non-empty body (>=20 chars after whitespace collapse). Body must mention `except Exception`, `except BaseException`, and `KeyboardInterrupt` literally.
  - `test_doctrine_event_payload_section_lists_all_GateWrittenEvent_fields` — round-trip: imports `qor.scripts.gate_hooks.GateWrittenEvent`; reads doctrine; asserts each field name appears in the doctrine body.
- `tests/test_phase57_self_application.py`:
  - `test_phase57_implement_gate_carries_ai_provenance` — reads `.qor/gates/<this_session>/implement.json`; asserts `ai_provenance` field present with `human_oversight: absent`.
  - `test_secret_scanner_clean_against_phase57_plan_and_doctrine` — invokes `secret_scanner.scan(path, mask_blocks=True)` against this plan + the new doctrine; asserts empty findings.
  - `test_pre_audit_lints_clean_against_phase57_plan` — invokes `plan_test_lint` and `plan_grep_lint` against this plan; asserts empty.
  - `test_glossary_round_trips_against_phase57_terms` — reads glossary; asserts both new terms have entries with `home: qor/references/doctrine-hook-contract.md` and `introduced_in_plan: phase57-gate-written-observer-channel`.

## CI Commands

- `python -m pytest tests/test_gate_hooks_*.py tests/test_gate_hooks_event_payload_shape.py tests/test_gate_hooks_sigint_propagates.py -v` — Phase 1 lock.
- `python -m pytest tests/test_gate_chain_fires_hook.py tests/test_gate_chain_hook_does_not_break_write.py tests/test_gate_chain_phase52_provenance_still_enforced.py tests/test_gate_chain_co_occurrence_hook_dispatch.py -v` — Phase 2 lock.
- `python -m pytest tests/test_doctrine_hook_contract_anchored.py tests/test_phase57_self_application.py -v` — Phase 3 lock.
- `python -m pytest -x` — full suite; expect 1141 + ~22 new = ~1163 passing twice (deterministic).
- `python -m qor.scripts.prompt_injection_canaries --mask-code-blocks --files docs/plan-qor-phase57-gate-written-observer-channel.md qor/references/doctrine-hook-contract.md` — Phase 53 self-application.
- `python -m qor.scripts.plan_test_lint --plan docs/plan-qor-phase57-gate-written-observer-channel.md` — Phase 55 self-application.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase57-gate-written-observer-channel.md --repo-root .` — Phase 55 self-application.
- `python -m qor.scripts.secret_scanner --files docs/plan-qor-phase57-gate-written-observer-channel.md qor/references/doctrine-hook-contract.md qor/scripts/gate_hooks.py qor/scripts/gate_chain.py` — Phase 56 self-application.
- `python -m qor.reliability.skill_admission qor-substantiate` — admit (substantiate skill body unchanged).
- `python -m qor.reliability.gate_skill_matrix` — handoff integrity unchanged.
- `python -m qor.scripts.check_variant_drift` — dist parity.
- `python -m qor.scripts.badge_currency --repo-root . --ledger docs/META_LEDGER.md` — badges current.
- After Phase 57 seal: `gh pr close 12 --comment "Superseded by Phase 57 — see commit <sha> on main + docs/plan-qor-phase57-gate-written-observer-channel.md"`.
