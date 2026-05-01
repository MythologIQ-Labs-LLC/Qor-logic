"""Phase 54: override-friction escalator behavior tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import override_friction
from qor.scripts.override_friction import (
    DEFAULT_THRESHOLD,
    MIN_JUSTIFICATION_LEN,
    OverrideFrictionRequired,
    check,
    record_with_justification,
)


def _write_log(tmp_path: Path, events: list[dict]) -> Path:
    log = tmp_path / "shadow.jsonl"
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return log


def _override(session_id: str, n: int = 1) -> list[dict]:
    return [
        {"event_type": "gate_override", "session_id": session_id, "ts": f"2026-04-30T{i:02d}:00:00Z"}
        for i in range(n)
    ]


def test_check_returns_false_below_threshold(tmp_path):
    log = _write_log(tmp_path, _override("sess-1", 2))
    result = check("sess-1", log_path=log)
    assert result.threshold_reached is False
    assert result.count == 2
    assert result.threshold == DEFAULT_THRESHOLD


def test_check_returns_true_at_threshold(tmp_path):
    log = _write_log(tmp_path, _override("sess-1", 3))
    result = check("sess-1", log_path=log)
    assert result.threshold_reached is True
    assert result.count == 3


def test_check_isolates_by_session_id(tmp_path):
    events = _override("sess-1", 5) + _override("sess-2", 1)
    log = _write_log(tmp_path, events)
    assert check("sess-2", log_path=log).count == 1
    assert check("sess-1", log_path=log).count == 5


def test_check_ignores_non_override_events(tmp_path):
    events = [
        {"event_type": "regression", "session_id": "sess-1", "ts": "2026-04-30T00:00:00Z"},
        {"event_type": "gate_override", "session_id": "sess-1", "ts": "2026-04-30T01:00:00Z"},
    ]
    log = _write_log(tmp_path, events)
    assert check("sess-1", log_path=log).count == 1


def test_check_handles_missing_log(tmp_path):
    missing = tmp_path / "no-such-log.jsonl"
    result = check("sess-1", log_path=missing)
    assert result.count == 0
    assert result.threshold_reached is False


def test_check_skips_malformed_lines(tmp_path):
    log = tmp_path / "shadow.jsonl"
    log.write_text(
        '{"event_type": "gate_override", "session_id": "sess-1"}\n'
        'not valid json\n'
        '{"event_type": "gate_override", "session_id": "sess-1"}\n',
        encoding="utf-8",
    )
    assert check("sess-1", log_path=log).count == 2


def test_record_with_justification_validates_length():
    event = {"event_type": "gate_override", "session_id": "sess-1"}
    short = "x" * (MIN_JUSTIFICATION_LEN - 1)
    with pytest.raises(ValueError, match=f"at least {MIN_JUSTIFICATION_LEN}"):
        record_with_justification(event, short)


def test_record_with_justification_attaches_field():
    event = {"event_type": "gate_override", "session_id": "sess-1"}
    just = "x" * MIN_JUSTIFICATION_LEN
    out = record_with_justification(event, just)
    assert out["justification"] == just
    assert out["event_type"] == "gate_override"


def test_record_with_justification_rejects_non_string():
    event = {"event_type": "gate_override"}
    with pytest.raises(ValueError, match="must be a string"):
        record_with_justification(event, 12345)


def test_emit_gate_override_raises_on_third_without_justification(tmp_path, monkeypatch):
    """Behavior invariant: third call without justification raises."""
    log = _write_log(tmp_path, _override("sess-1", 3))
    monkeypatch.setattr(override_friction, "_shadow_log_path", lambda: log)

    from qor.scripts import gate_chain
    with pytest.raises(OverrideFrictionRequired, match="threshold reached"):
        gate_chain.emit_gate_override(
            current_phase="plan",
            prior_phase_name="research",
            reason="user override: no research artifact",
            session_id="sess-1",
        )


def test_emit_gate_override_succeeds_with_justification(tmp_path, monkeypatch):
    log = _write_log(tmp_path, _override("sess-1", 3))
    monkeypatch.setattr(override_friction, "_shadow_log_path", lambda: log)

    from qor.scripts import gate_chain
    just = "Operator: research phase intentionally skipped for this hotfix because the upstream change is purely cosmetic and the existing baseline already covers the surface."
    # Should not raise.
    gate_chain.emit_gate_override(
        current_phase="plan",
        prior_phase_name="research",
        reason="user override: hotfix scope",
        session_id="sess-1",
        justification=just,
    )
