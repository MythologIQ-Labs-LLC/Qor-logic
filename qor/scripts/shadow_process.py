#!/usr/bin/env python3
"""Shadow Process Genome append helper + reader.

Validates events against qor/gates/schema/shadow_event.schema.json,
computes deterministic ids, appends atomically.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "qor" / "gates" / "schema" / "shadow_event.schema.json"
LOG_PATH = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME.md"

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


def append_event(event: dict, log_path: Path = LOG_PATH) -> str:
    """Validate, id, append JSONL line. Returns computed id."""
    validate(event)
    event_id = compute_id(event)
    event_with_id = {"id": event_id, **event}
    line = json.dumps(event_with_id, separators=(",", ":")) + "\n"
    _atomic_append(log_path, line)
    return event_id


def _atomic_append(path: Path, line: str) -> None:
    """Append a line atomically: read existing, write temp, os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    new_content = existing + (line if existing.endswith("\n") or not existing else "\n" + line)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as tf:
        tf.write(new_content)
        tmp_path = tf.name
    os.replace(tmp_path, path)


def read_events(log_path: Path = LOG_PATH) -> list[dict]:
    """Parse JSONL lines from log; skip markdown prose."""
    if not log_path.exists():
        return []
    events: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def write_events(events: list[dict], log_path: Path = LOG_PATH) -> None:
    """Rewrite log preserving prose header + replacing JSONL section.

    Reads the current file, keeps all non-JSON lines, then appends re-serialized events.
    """
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
