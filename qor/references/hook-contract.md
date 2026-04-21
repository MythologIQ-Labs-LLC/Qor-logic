# `gate_written` hook contract

qor-logic fires a `gate_written` event after every successful call to
`qor.scripts.gate_chain.write_gate_artifact`. Consumers can register
handlers via two channels:

1. **Python entry-points** (group `qor_logic.events.gate_written`) —
   resolved once per process and cached.
2. **Project-local config** at `<root>/.qor/hooks.yaml` — loaded on
   every dispatch.

The hook is a **non-authoritative observer**. The authoritative gate
artifact is written to disk before any hook fires. Exceptions raised
by hooks are swallowed and logged to `<root>/.qor/hooks/hooks.log`;
they never abort the write.

## Event payload

```python
@dataclass(frozen=True)
class GateWrittenEvent:
    phase: str              # "plan" | "audit" | "implement" | ...
    session_id: str
    artifact_path: Path     # absolute path to the written artifact
    payload_sha256: str     # SHA-256 of artifact file bytes
    ts: str                 # ISO-8601 UTC instant of the hook fire
```

## Entry-point registration (consumer `pyproject.toml`)

```toml
[project.entry-points."qor_logic.events.gate_written"]
my-handler = "my_package.hooks:on_gate_written"
```

The referenced callable must accept a single `GateWrittenEvent`
positional argument. Its return value is ignored.

## Config-file format (`.qor/hooks.yaml`)

```yaml
gate_written:
  # Python dotted-path: imported and invoked with the event.
  - module: my_package.hooks:on_gate_written

  # Shell command: argv list (no shell=True). The artifact path is
  # appended as the final argv element.
  - command: [/usr/local/bin/my-hook.sh]
```

YAML is parsed with `yaml.safe_load`; top-level keys other than
`gate_written` are ignored. Missing file → no config hooks.

## Invocation order

1. All entry-point hooks run first, in the order returned by
   `importlib.metadata.entry_points` (typically install order).
2. Config-file hooks run next, top-to-bottom as declared.

Each hook has a 30-second subprocess timeout (shell commands) or is
invoked synchronously (Python callables). There is no concurrency
between hooks — one completes before the next begins.

## Log format

On every fire attempt (success or error), one JSONL line is appended
to `<root>/.qor/hooks/hooks.log`:

```json
{"ts":"2026-04-20T00:00:00Z","hook":"my-handler","event":{...},"status":"ok","duration_ms":3}
```

On error, a `"status":"error"` record includes a stringified
`"exception"` field with the traceback.

## Trust model

**Shell commands and Python dotted paths in `.qor/hooks.yaml` run
arbitrary code from the consumer's repo.** This matches the trust
model of:

- `.github/workflows/` (GitHub Actions)
- `.pre-commit-config.yaml`
- `Makefile` / `noxfile.py`
- npm `package.json` `scripts.preinstall`

If your team treats `.qor/hooks.yaml` as a security-sensitive file
(review on every PR, code-owners, etc.), apply the same treatment
as for those files. qor-logic does not sandbox, sign, or vet hooks.

Entry-point registration is subject to the standard Python packaging
trust model: any installed package can register in the
`qor_logic.events.gate_written` group.

## Performance

With no hooks registered and no `.qor/hooks.yaml` present, the
dispatch path is an `importlib.metadata.entry_points` lookup (cached
after first call) plus a `Path.exists` check — sub-millisecond.

Hook dispatch happens synchronously on the calling thread after the
gate artifact has already been persisted, so slow hooks slow the skill
but never risk artifact corruption.
