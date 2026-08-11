#!/usr/bin/env python3
"""Shadow Process Genome append helper + reader.

Validates events against qor/gates/schema/shadow_event.schema.json,
computes deterministic ids, appends atomically.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema

from qor import resources as _resources
from qor import workdir as _workdir

SCHEMA_PATH = Path(str(_resources.schema("shadow_event.schema.json")))
LOCAL_LOG_PATH = _workdir.shadow_log()
UPSTREAM_LOG_PATH = _workdir.shadow_log_upstream()
LOG_PATH = LOCAL_LOG_PATH

_SCHEMA_CACHE: dict | None = None


def load_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def compute_id(event: dict) -> str:
    """SHA256 over ts, skill, session_id, event_type, severity, json(details), source_entry_id."""
    parts = [
        event["ts"],
        event["skill"],
        event["session_id"],
        event["event_type"],
        str(event["severity"]),
        json.dumps(event.get("details", {}), sort_keys=True, separators=(",", ":")),
        event.get("source_entry_id") or "",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def validate(event: dict) -> None:
    jsonschema.validate(event, load_schema())


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_path_for(attribution: Literal["UPSTREAM", "LOCAL"]) -> Path:
    if attribution == "UPSTREAM":
        return UPSTREAM_LOG_PATH
    if attribution == "LOCAL":
        return LOCAL_LOG_PATH
    raise ValueError(f"Invalid attribution: {attribution!r}")


def _apply_override_friction(event: dict, log_path: Path) -> None:
    """Charge friction for a repeated gate override (GH #324).

    The friction check used to live only in ``gate_chain.emit_gate_override``.
    Every observed override was recorded through ``append_event`` instead --
    that is what an operator reaches for when disclosing a gate they have
    already decided to pass -- so the control guarded one of two equivalent
    entry points and never fired.

    Friction is a COST, not a wall. An override that cannot be *recorded* past
    the threshold leaves the operator choosing between undisclosed progress and
    no progress, and the first is strictly worse than the defect being fixed. A
    re-invocation carrying a written justification records normally, matching
    ``emit_gate_override``.
    """
    if event.get("event_type") != "gate_override":
        return
    if event.get("justification"):
        return
    from qor.scripts import override_friction

    session = override_friction.check(
        event.get("session_id", ""), log_path=log_path)
    gate = (event.get("details") or {}).get("gate")
    recurrence = (override_friction.gate_recurrence(gate, log_path=log_path)
                  if gate else None)
    # Count the event being recorded, not just its predecessors. The threshold
    # was chosen so the THIRD occurrence is charged (entry #556: "at 3 it fires
    # one phase before a human noticed"); comparing prior-count alone would
    # charge the fourth and deliver none of that reasoning.
    session_hit = session.count + 1 >= session.threshold
    gate_hit = recurrence is not None and recurrence.count + 1 >= recurrence.threshold
    if not session_hit and not gate_hit:
        return
    detail = (f"gate {gate!r} overridden {recurrence.count + 1} times across sessions"
              if gate_hit
              else f"{session.count + 1} overrides this session")
    raise override_friction.OverrideFrictionRequired(
        f"override friction: {detail}. Re-record with justification=<text> "
        "(>=50 chars) stating why this recurrence is acceptable."
    )


def append_event(
    event: dict,
    *,
    attribution: Literal["UPSTREAM", "LOCAL"] | None = None,
    log_path: Path | None = None,
) -> str:
    """Validate, id, append JSONL line. Returns computed id."""
    if log_path is None:
        if attribution is None:
            raise ValueError("append_event requires attribution=... or log_path=...")
        log_path = log_path_for(attribution)
    validate(event)
    _apply_override_friction(event, log_path)
    event_id = compute_id(event)
    event_with_id = {"id": event_id, **event}
    line = json.dumps(event_with_id, separators=(",", ":")) + "\n"
    _atomic_append(log_path, line)
    return event_id


def _lock_file(fh):
    """Acquire exclusive lock. POSIX: fcntl. Windows: msvcrt."""
    try:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    except ImportError:
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)


def _unlock_file(fh):
    """Release exclusive lock. POSIX: fcntl. Windows: msvcrt."""
    try:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except ImportError:
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)


def _atomic_append(path: Path, line: str) -> None:
    """Append a line atomically with file locking: read existing, write temp, os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.parent / (path.name + ".lock")
    lock_path.touch(exist_ok=True)
    with open(lock_path, "r") as lock_fh:
        _lock_file(lock_fh)
        try:
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            new_content = existing + (line if existing.endswith("\n") or not existing else "\n" + line)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
            ) as tf:
                tf.write(new_content)
                tmp_path = tf.name
            os.replace(tmp_path, path)
        finally:
            _unlock_file(lock_fh)


def read_events(log_path: Path | None = None) -> list[dict]:
    """Parse JSONL lines from log; skip markdown prose."""
    if log_path is None:
        log_path = LOG_PATH
    if not log_path.exists():
        return []
    events: list[dict] = []
    for i, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"WARN: skipping malformed JSONL line {i}", file=sys.stderr)
            continue
    return events


def write_events(events: list[dict], log_path: Path | None = None) -> None:
    """Rewrite log preserving prose header + replacing JSONL section.

    Reads the current file, keeps all non-JSON lines, then appends re-serialized events.
    """
    if log_path is None:
        log_path = LOG_PATH
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        prose = ""
    else:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        prose_lines = [ln for ln in lines if not ln.strip().startswith("{")]
        # Strip trailing blank lines from prose
        while prose_lines and not prose_lines[-1].strip():
            prose_lines.pop()
        prose = "\n".join(prose_lines) + "\n\n"
    body = "\n".join(json.dumps(e, separators=(",", ":")) for e in events) + "\n"
    content = prose + body
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=log_path.parent, delete=False, suffix=".tmp"
    ) as tf:
        tf.write(content)
        tmp_path = tf.name
    os.replace(tmp_path, log_path)


def read_all_events() -> list[dict]:
    return read_events(LOCAL_LOG_PATH) + read_events(UPSTREAM_LOG_PATH)


def id_source_map() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for e in read_events(LOCAL_LOG_PATH):
        out[e["id"]] = LOCAL_LOG_PATH
    for e in read_events(UPSTREAM_LOG_PATH):
        out[e["id"]] = UPSTREAM_LOG_PATH
    return out


def write_events_per_source(
    events: list[dict],
    src_map: dict[str, Path],
) -> None:
    by_file: dict[Path, list[dict]] = {}
    for e in events:
        path = src_map.get(e["id"])
        if path is not None:
            by_file.setdefault(path, []).append(e)
    for path, batch in by_file.items():
        write_events(batch, path)
