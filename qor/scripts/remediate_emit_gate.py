#!/usr/bin/env python3
"""remediate: emit .qor/gates/<session_id>/remediate.json for downstream audit.

Step 5 of the /qor-remediate skill protocol. Persists the proposal for later
review by /qor-audit when a subsequent implementation cycle checks whether
remediation recommendations were followed.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_SESSION_ID_RE = re.compile(r'^[\w\-T:]+$')


def validate_session_id(session_id: str) -> None:
    """Validate session_id matches ^[\\w\\-T:]+$. Raises ValueError on invalid."""
    if not session_id or not _SESSION_ID_RE.match(session_id):
        raise ValueError(f"Invalid session_id: {session_id!r}")


from qor import workdir as _workdir
from qor.scripts.validate_gate_artifact import next_iteration_path


def _atomic_write(target: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=target.parent, delete=False, suffix=".tmp"
    ) as tf:
        tf.write(text)
        tmp_path = tf.name
    os.replace(tmp_path, target)


def emit(
    proposal: dict,
    session_id: str,
    base_dir: Path | None = None,
) -> Path:
    """Write the proposal to .qor/gates/<session_id>/remediate.json.

    Returns the singleton path written. Adds a `ts` field to the payload.

    GH #446: a second remediation proposal in the same session no longer
    destroys the first. Every call also writes an immutable versioned
    copy (`remediate-iter<N>.json`, never re-targeting an existing
    iteration) before refreshing the singleton, mirroring the pattern
    `gate_chain.write_gate_artifact`/`validate_gate_artifact.write_artifact`
    already use for the other gate phases. The singleton path and return
    value are unchanged so existing consumers (`remediate_mark_addressed`'s
    `remediate_gate_path` argument) keep working against a fixed name.
    """
    validate_session_id(session_id)
    root = base_dir if base_dir is not None else _workdir.root()
    out_dir = root / ".qor" / "gates" / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "remediate.json"

    payload = dict(proposal)
    payload["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    versioned_path = next_iteration_path("remediate", out_dir)
    _atomic_write(versioned_path, text)
    _atomic_write(out_path, text)
    return out_path
