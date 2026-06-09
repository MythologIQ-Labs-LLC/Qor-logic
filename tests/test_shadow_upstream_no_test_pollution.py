"""Phase 143: the tracked upstream shadow genome must carry no synthetic test
events, and emit_gate_override must honor a patched upstream append path.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import gate_chain, override_friction, shadow_process

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = REPO / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"


def _events(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _sess1_count(path: Path) -> int:
    return len([e for e in _events(path) if e.get("session_id") == "sess-1"])


def test_upstream_file_has_no_test_session_events():
    n = _sess1_count(UPSTREAM)
    assert n == 0, f"{n} synthetic sess-1 events polluting the tracked upstream file"


def test_emit_gate_override_append_respects_patched_upstream_path(tmp_path, monkeypatch):
    fric = tmp_path / "fric.jsonl"
    fric.write_text(
        "\n".join(
            json.dumps({"event_type": "gate_override", "session_id": "sess-1", "ts": f"2026-04-30T0{i}:00:00Z"})
            for i in range(3)
        )
        + "\n",
        encoding="utf-8",
    )
    up = tmp_path / "upstream.jsonl"
    monkeypatch.setattr(override_friction, "_shadow_log_path", lambda: fric)
    monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", up)

    before = _sess1_count(UPSTREAM)
    just = (
        "Operator: research phase intentionally skipped for this hotfix because the "
        "upstream change is purely cosmetic and the existing baseline already covers the surface."
    )
    gate_chain.emit_gate_override(
        current_phase="plan", prior_phase_name="research",
        reason="user override: hotfix scope", session_id="sess-1", justification=just,
    )
    # The event landed in the patched tmp upstream file...
    assert up.exists()
    assert any("gate_override" in line for line in up.read_text(encoding="utf-8").splitlines())
    # ...and the real tracked file was not touched.
    assert _sess1_count(UPSTREAM) == before
