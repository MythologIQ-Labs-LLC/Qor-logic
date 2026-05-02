# `gate_written` hook contract (Phase 57)

Phase 57 wires a non-authoritative observer push-channel that fires after every successful `qor.scripts.gate_chain.write_gate_artifact` call. The channel exists so downstream governance-ledger bridges (e.g. FailSafe-Pro) and adjacent tooling can react to gate writes without polling the filesystem. Closes the polling-vs-push gap that prompted PR #12 and addresses OWASP LLM07 (Insecure Plugin Design) at the contract layer.

## Applicability

Hooks fire after **every** successful `write_gate_artifact` call (every phase: research, plan, audit, implement, substantiate, deliver, remediate, etc.). Consumers filter by `event.phase` themselves. Pre-Phase-57 historical writes are NOT replayed; forward-only enforcement starting at the Phase 57 seal.

## Event payload

```python
@dataclass(frozen=True)
class GateWrittenEvent:
    phase: str              # "plan" | "audit" | "implement" | ...
    session_id: str
    artifact_path: Path     # absolute path to the written artifact
    payload_sha256: str     # SHA-256 of artifact file bytes (read back from disk)
    ts: str                 # ISO-8601 UTC instant of the hook fire
```

`payload_sha256` is computed from the on-disk bytes (not the in-memory payload) so the hash matches what's actually persisted. Future schema-write helpers that transform the payload during write cannot create in-memory/on-disk drift.

## Entry-point registration (consumer `pyproject.toml`)

```toml
[project.entry-points."qor_logic.events.gate_written"]
my-handler = "my_package.hooks:on_gate_written"
```

The referenced callable must accept a single `GateWrittenEvent` positional argument. Its return value is ignored. Entry-points are resolved once per process via `importlib.metadata.entry_points` and cached. Test-only `gate_hooks.reload_entry_points()` invalidates the cache; production never calls it.

## Config-file format (`.qor/hooks.yaml`)

```yaml
gate_written:
  # Python dotted-path: imported and invoked with the event.
  - module: my_package.hooks:on_event

  # Shell command: argv list (no shell=True). Artifact path appended as final arg.
  - command: [/usr/local/bin/my-hook.sh]
```

YAML parsed with `yaml.safe_load`. Top-level keys other than `gate_written` are ignored. Missing file → no config hooks. Malformed YAML → empty list (no error). String-form `command` entries are silently dropped (A03 Injection guard: argv must be a list).

## Invocation order

1. All entry-point hooks run first, in the order returned by `importlib.metadata.entry_points` (typically install order).
2. Config-file hooks run next, top-to-bottom as declared.

Each hook has a 30-second subprocess timeout (shell commands) or runs synchronously (Python callables). There is no concurrency between hooks — one completes before the next begins.

## Log format

On every fire attempt (success or error), one JSONL line is appended to `<root>/.qor/hooks/hooks.log`:

```json
{"ts":"2026-04-20T00:00:00Z","hook":"my-handler","event":{...},"status":"ok","duration_ms":3}
```

On error, a `"status":"error"` record includes a stringified `"exception"` field with the traceback. Subprocess hooks with non-zero exit code are logged as `status: ok` (BLOCK semantics are the consumer's responsibility; the artifact on disk is the authoritative source).

## Trust model

Shell commands and Python dotted paths in `.qor/hooks.yaml` execute arbitrary code from the consumer's repo. This matches the trust model of:

- `.github/workflows/` (GitHub Actions)
- `.pre-commit-config.yaml`
- `Makefile` / `noxfile.py`
- npm `package.json` `scripts.preinstall`

If your team treats `.qor/hooks.yaml` as security-sensitive, apply the same review and code-owner controls as for those files. qor-logic does not sandbox, sign, or vet hooks. Entry-point registration is subject to standard Python packaging trust: any installed package can register in the `qor_logic.events.gate_written` group.

## Performance

With no hooks registered and no `.qor/hooks.yaml` present, the dispatch path is an `importlib.metadata.entry_points` lookup (cached after first call) plus a `Path.exists` check — sub-millisecond.

Hook dispatch happens synchronously on the calling thread after the gate artifact has already been persisted to disk. Slow hooks slow the skill, but artifact corruption is impossible.

## Phase 57 changes vs. PR #12 origin

The original PR #12 (opened 2026-04-20, B24 from FailSafe-Pro) used `except BaseException` (with `# noqa: BLE001`) in `_invoke_hook_safely` and the `_fire_gate_written_hook` bridge. This swallowed `KeyboardInterrupt` and `SystemExit`, meaning operators could not interrupt a runaway hook with Ctrl-C. With the 30-second per-hook subprocess timeout AND swallow-on-callable-hook, a misbehaving Python entry-point hook could spin indefinitely with SIGKILL the only escape.

Phase 57 fixes this by using `except Exception` (not `BaseException`) in both the dispatcher's per-hook invoke (`gate_hooks._invoke_hook_safely`) and the gate-chain bridge (`gate_chain._fire_gate_written_hook`). `KeyboardInterrupt` and `SystemExit` propagate through the dispatch and out to the calling skill. Operator retains Ctrl-C control over runaway hooks.

This pattern is codified in `qor/references/doctrine-shadow-genome-countermeasures.md` as `SG-BareExceptionSwallowsSignals-A`. New regression tests:
- `tests/test_gate_hooks_swallow.py::test_swallow_uses_except_exception_not_baseexception` — AST-anchored static check that `_invoke_hook_safely` catches `Exception` and never `BaseException`.
- `tests/test_gate_hooks_sigint_propagates.py` — `KeyboardInterrupt` and `SystemExit` raised inside a hook callable propagate to the dispatch caller.
- `tests/test_gate_chain_hook_does_not_break_write.py::test_dispatch_raising_keyboard_interrupt_propagates_after_write` — KeyboardInterrupt from the dispatch propagates to the `write_gate_artifact` caller, but only AFTER the artifact is on disk.

## References

- `qor/scripts/gate_hooks.py` — dispatcher implementation (Phase 57).
- `qor/scripts/gate_chain.py` `_fire_gate_written_hook` — bridge from authoritative write path.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-BareExceptionSwallowsSignals-A`.
- PR #12 `feat/b24-gate-written-hooks` — original FailSafe-Pro contribution; superseded by Phase 57.
- Entry #186 (PR #12 audit VETO) and Entry #187 (Phase 57 plan audit PASS) in `docs/META_LEDGER.md`.
