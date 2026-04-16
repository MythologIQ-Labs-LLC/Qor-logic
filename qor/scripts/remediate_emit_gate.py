#!/usr/bin/env python3
"""remediate: emit .qor/gates/<session_id>/remediate.json for downstream audit.

Step 5 of the /qor-remediate skill protocol. Persists the proposal for later
review by /qor-audit when a subsequent implementation cycle checks whether
remediation recommendations were followed.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


from qor import workdir as _workdir


def emit(
    proposal: dict,
    session_id: str,
    base_dir: Path | None = None,
) -> Path:
    """Write the proposal to .qor/gates/<session_id>/remediate.json.

    Returns the path written. Adds a `ts` field to the payload.
    """
    root = base_dir if base_dir is not None else _workdir.root()
    out_dir = root / ".qor" / "gates" / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "remediate.json"

    payload = dict(proposal)
    payload["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=out_dir, delete=False, suffix=".tmp"
    ) as tf:
        json.dump(payload, tf, indent=2, sort_keys=False)
        tf.write("\n")
        tmp_path = tf.name
    os.replace(tmp_path, out_path)
    return out_path
