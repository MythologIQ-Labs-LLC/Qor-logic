"""Phase 57: gate_written observer channel. Closes PR #12 reintegration.

Non-authoritative observer hooks fired after each successful
``gate_chain.write_gate_artifact``. Two dispatch sources, both pure-Python:

1. **Entry-points** under group ``qor_logic.events.gate_written`` — installed
   packages register a callable via standard packaging metadata.
2. **Config-file** at ``<root>/.qor/hooks.yaml`` — project-local hooks declared
   as Python dotted paths or shell-command argv lists (list-form only).

Error semantics: catch ``Exception``, swallow + JSONL-log to
``<root>/.qor/hooks/hooks.log``. ``KeyboardInterrupt`` and ``SystemExit``
propagate so operators retain Ctrl-C control over runaway hooks (Phase 57
VETO-remediation per Entry #186 audit; previously
``except BaseException`` swallowed signals, see SG-BareExceptionSwallowsSignals-A).

The hook channel is a non-authoritative observer of governance writes. The
authoritative gate artifact is on disk before any hook fires; hook errors
never abort the write. Trust model is the consumer's repo (mirrors
``.github/workflows/`` / ``.pre-commit-config.yaml`` / npm preinstall);
qor-logic does not sandbox, sign, or vet hooks. See
``qor/references/doctrine-hook-contract.md``.
"""
from __future__ import annotations

import importlib
import importlib.metadata
import json
import subprocess
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from qor import workdir as _workdir
from qor.scripts import shadow_process

ENTRY_POINT_GROUP = "qor_logic.events.gate_written"
HOOK_TIMEOUT_SECONDS = 30

_entry_point_cache: list["_HookTarget"] | None = None


@dataclass(frozen=True)
class GateWrittenEvent:
    """Event payload fired after a successful gate-artifact write."""
    phase: str
    session_id: str
    artifact_path: Path
    payload_sha256: str
    ts: str


@dataclass(frozen=True)
class _HookTarget:
    name: str
    kind: str  # "callable" | "command"
    callable: object | None
    argv: list[str] | None


def reload_entry_points() -> None:
    """Invalidate the entry-point cache. Tests only — production never calls."""
    global _entry_point_cache
    _entry_point_cache = None


def dispatch_gate_written(event: GateWrittenEvent) -> None:
    """Fire all registered hooks for `gate_written`. Swallow Exception per hook.

    KeyboardInterrupt / SystemExit propagate (Phase 57 fix vs. PR #12).
    """
    targets = _enumerate_entry_points() + _load_config_file_hooks(_workdir.root())
    if not targets:
        return
    log_path = _workdir.root() / ".qor" / "hooks" / "hooks.log"
    for target in targets:
        _invoke_hook_safely(target, event, log_path)


def _enumerate_entry_points() -> list[_HookTarget]:
    global _entry_point_cache
    if _entry_point_cache is not None:
        return _entry_point_cache
    eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
    targets = [
        _HookTarget(name=ep.name, kind="callable", callable=ep.load(), argv=None)
        for ep in eps
    ]
    _entry_point_cache = targets
    return targets


def _load_config_file_hooks(root: Path) -> list[_HookTarget]:
    hooks_yaml = root / ".qor" / "hooks.yaml"
    if not hooks_yaml.exists():
        return []
    try:
        data = yaml.safe_load(hooks_yaml.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    entries = data.get("gate_written") or []
    return [t for t in (_resolve_config_entry(idx, e) for idx, e in enumerate(entries)) if t]


def _resolve_config_entry(idx: int, entry: dict) -> _HookTarget | None:
    if not isinstance(entry, dict):
        return None
    if "module" in entry:
        dotted = entry["module"]
        try:
            target = _import_dotted(dotted)
        except (ImportError, AttributeError, ValueError):
            return None
        return _HookTarget(
            name=f"config[{idx}]:{dotted}", kind="callable",
            callable=target, argv=None,
        )
    if "command" in entry:
        cmd = entry["command"]
        if not isinstance(cmd, list) or not all(isinstance(a, str) for a in cmd):
            return None
        return _HookTarget(
            name=f"config[{idx}]:{cmd[0]}", kind="command",
            callable=None, argv=list(cmd),
        )
    return None


def _import_dotted(dotted: str):
    module_name, _, attr = dotted.partition(":")
    if not attr:
        raise ValueError(f"dotted path must use 'module:attr' form: {dotted!r}")
    module = importlib.import_module(module_name)
    return getattr(module, attr)


def _invoke_hook_safely(
    target: _HookTarget, event: GateWrittenEvent, log_path: Path,
) -> None:
    """Invoke one hook; swallow Exception; let SIGINT/SystemExit propagate.

    Phase 57 fix: ``except Exception`` (NOT ``except BaseException``) — see
    SG-BareExceptionSwallowsSignals-A. KeyboardInterrupt and SystemExit
    propagate so operators retain Ctrl-C control.
    """
    start = time.monotonic()
    status, exception = "ok", None
    try:
        if target.kind == "callable":
            target.callable(event)  # type: ignore[misc]
        else:
            _run_command_hook(target, event)
    except Exception:
        status = "error"
        exception = traceback.format_exc()
    duration_ms = int((time.monotonic() - start) * 1000)
    _append_log(log_path, target.name, event, status, duration_ms, exception)


def _run_command_hook(target: _HookTarget, event: GateWrittenEvent) -> None:
    argv = list(target.argv or []) + [str(event.artifact_path)]
    subprocess.run(
        argv, check=False, capture_output=True,
        timeout=HOOK_TIMEOUT_SECONDS,
    )


def _append_log(
    log_path: Path, hook_name: str, event: GateWrittenEvent,
    status: str, duration_ms: int, exception: str | None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event_dict = asdict(event)
    event_dict["artifact_path"] = str(event.artifact_path)
    record = {
        "ts": shadow_process.now_iso(),
        "hook": hook_name,
        "event": event_dict,
        "status": status,
        "duration_ms": duration_ms,
    }
    if exception is not None:
        record["exception"] = exception
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
