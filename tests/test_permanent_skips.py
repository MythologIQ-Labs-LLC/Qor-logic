"""Phase 256: operator-declared permanent skips close on emission.

Three gate skips re-emit on every cycle because they name properties of this
repository that no enforcer will ever satisfy -- no SQL migrations, no `Surface`
column in the feature index, no host agent-teams capability. Closing the events
they have already written is a treadmill: the next seal writes new ones with the
same signature.

The declaration is bounded to event types that report an *absence* (tribunal
ground V-1). A defect keeps the attested two-stage path through `mark_addressed`,
which refuses to flip anything without a PASS review artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import shadow_process as sp

_JUSTIFICATION = (
    "This repository ships no SQL migrations, so the Data-API grant and "
    "definer-view scan has no subject and exits 0 by design."
)


def _config(root: Path, skips: dict) -> None:
    cfg = root / ".qorlogic"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "config.json").write_text(
        json.dumps({"permanent_skips": skips}), encoding="utf-8"
    )


def _event(event_type: str, severity: int = 1, **details) -> dict:
    return {
        "ts": "2026-09-03T00:00:00Z",
        "skill": "qor-substantiate",
        "session_id": "2026-09-03T0000-aaaaaa",
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def _append_and_read(tmp_path, monkeypatch, event) -> dict:
    """Append through the real choke point and read the event back."""
    monkeypatch.chdir(tmp_path)
    log = tmp_path / "genome.md"
    sp.append_event(event, log_path=log)
    return sp.read_events(log)[-1]


def test_declared_skip_is_closed_on_emission(tmp_path, monkeypatch):
    """The treadmill stops at the emitter, not one closure pass at a time."""
    _config(tmp_path, {"data_api_acl_lint": _JUSTIFICATION})

    written = _append_and_read(
        tmp_path, monkeypatch,
        _event("gate_skipped_prerequisite_absent", gate="data_api_acl_lint"),
    )

    assert written["addressed"] is True
    assert written["addressed_reason"] == "remediated"
    assert written["closure_enforcer"] == f"cannot-automate: {_JUSTIFICATION}"
    assert written["addressed_ts"]


def test_undeclared_skip_still_accrues(tmp_path, monkeypatch):
    """Without this the change is a blanket amnesty rather than a declaration."""
    _config(tmp_path, {"data_api_acl_lint": _JUSTIFICATION})

    written = _append_and_read(
        tmp_path, monkeypatch,
        _event("gate_skipped_prerequisite_absent", gate="secret_scanner"),
    )

    assert written["addressed"] is False
    assert "closure_enforcer" not in written


def test_capability_discriminator_is_honored(tmp_path, monkeypatch):
    """`agent-teams` and `codex-plugin` arrive with `capability`, not `gate`."""
    justification = (
        "The host exposes no agent-teams capability and the declared fallback "
        "in qor_platform.FALLBACKS satisfies the function it was needed for."
    )
    _config(tmp_path, {"agent-teams": justification})

    written = _append_and_read(
        tmp_path, monkeypatch,
        _event("capability_shortfall", severity=2, capability="agent-teams"),
    )

    assert written["addressed"] is True
    assert justification in written["closure_enforcer"]


def test_declared_key_cannot_close_a_defect_event(tmp_path, monkeypatch):
    """Tribunal ground V-1.

    Emit-time closure reaches `addressed: true` without the review-pass
    attestation `mark_addressed` demands. Bounded to absences, a declaration
    naming a gate cannot silence a report that something went wrong.
    """
    _config(tmp_path, {"intent_lock": _JUSTIFICATION})

    written = _append_and_read(
        tmp_path, monkeypatch,
        _event("degradation", severity=4, gate="intent_lock"),
    )

    assert written["addressed"] is False, (
        "a permanent-skip declaration must not close a defect event"
    )


def test_short_justification_raises(tmp_path, monkeypatch):
    """A typo must not silently restore the treadmill."""
    _config(tmp_path, {"data_api_acl_lint": "no migrations"})
    monkeypatch.chdir(tmp_path)

    with pytest.raises(sp.PermanentSkipDeclarationError):
        sp.append_event(
            _event("gate_skipped_prerequisite_absent", gate="data_api_acl_lint"),
            log_path=tmp_path / "genome.md",
        )


def test_declared_skip_still_reaches_the_log(tmp_path, monkeypatch):
    """Phase 75's disclosed-skip exists so a skipped gate stays visible.

    This is the test that fails if the fix ever becomes suppression: only debt
    accrual changes, never the record.
    """
    _config(tmp_path, {"data_api_acl_lint": _JUSTIFICATION})
    monkeypatch.chdir(tmp_path)
    log = tmp_path / "genome.md"

    sp.append_event(
        _event("gate_skipped_prerequisite_absent", gate="data_api_acl_lint"),
        log_path=log,
    )

    events = sp.read_events(log)
    assert len(events) == 1
    assert events[0]["details"]["gate"] == "data_api_acl_lint"
