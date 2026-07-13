#!/usr/bin/env python3
"""Append-only audit history log (Phase 37 B20 Part 1).

Solves the V10 finding from Phase 36's original plan: `gate_chain.write_gate_artifact`
writes `.qor/gates/<sid>/<phase>.json` as a singleton (overwrite on re-emission). The
stall-detection mechanism proposed in the original plan assumed multi-pass audit
accumulation which did not occur.

This module adds an append-only JSONL log at `.qor/gates/<sid>/audit_history.jsonl`
that records every audit gate payload in session order. The singleton contract is
unchanged -- downstream phases still read `.qor/gates/<sid>/audit.json` for chain
gating. The history log is advisory for stall detection.

Each record is schema-validated against `audit.schema.json` before append. Malformed
lines during read raise with a line number.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor import workdir as _workdir
from qor.scripts import validate_gate_artifact as _vga


_HISTORY_FILENAME = "audit_history.jsonl"


def history_path(session_id: str) -> Path:
    """Return the audit history JSONL path for the given session."""
    return _workdir.gate_dir() / session_id / _HISTORY_FILENAME


def append(
    payload: dict, session_id: str, artifact_filename: str | None = None
) -> Path:
    """Validate and append one audit gate payload to the session history log.

    Payload must conform to ``audit.schema.json``. The function enforces
    ``phase == "audit"`` and ``session_id`` matching the argument. Returns the
    history path.

    Phase 173 (GH #237): ``artifact_filename`` records the versioned file this
    emission landed in (e.g. ``audit-iter2.json``), closing the loop between a
    history row and the immutable evidence bytes on disk. Additive under the
    audit schema's ``additionalProperties: true``; absent on pre-173 rows.
    """
    record = dict(payload)
    record.setdefault("phase", "audit")
    record.setdefault("session_id", session_id)
    if artifact_filename is not None:
        record["artifact_filename"] = artifact_filename
    _vga._validate_data("audit", record)

    path = history_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path


def read(session_id: str) -> list[dict]:
    """Read all audit history records in file order.

    Returns ``[]`` when the history file is absent. Raises ``ValueError`` naming
    the offending line number on malformed JSON or schema failure.
    """
    path = history_path(session_id)
    if not path.is_file():
        return []

    records: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_num, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Malformed JSON in {path} at line {line_num}: {exc}"
                ) from exc
            try:
                _vga._validate_data("audit", record)
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    f"Schema violation in {path} at line {line_num}: {exc}"
                ) from exc
            records.append(record)
    return records
