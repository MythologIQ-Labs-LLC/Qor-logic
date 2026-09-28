"""Phase 301 (GH #474): the shadow issue title and header say "threshold
breach" only when a loaded breach marker's threshold is reached by the plain
severity sum the header prints; the --events threshold has one owner."""
from __future__ import annotations

import json
import sys

import pytest

from qor.scripts import check_shadow_threshold as cst
from qor.scripts import create_shadow_issue as csi
from qor.scripts import shadow_process

BREACH_TITLE_PREFIX = "[qor-shadow] Process threshold breach \u2014 "
BREACH_HEADING = "## Process Shadow Genome \u2014 threshold breach"
NEUTRAL_HEADING = "## Process Shadow Genome - unaddressed events"
EVENTS_NOTE = "not checked: the events were named with --events"


def _event(severity: int, gate: str) -> dict:
    ev = {
        "ts": "2026-04-15T12:00:00Z",
        "skill": "qor-audit",
        "session_id": "2026-04-15T12:00-abc123",
        "event_type": "gate_override",
        "severity": severity,
        "details": {"gate": gate},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    ev["id"] = shadow_process.compute_id(ev)
    return ev


def _events(severities) -> list[dict]:
    return [_event(sev, f"gate_{i}") for i, sev in enumerate(severities)]


def _write_log(tmp_path, events: list[dict]):
    log = tmp_path / "shadow.md"
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return log


def _write_marker(tmp_path, monkeypatch, ids, threshold=10):
    marker = tmp_path / "remediate-pending"
    marker.write_text(json.dumps({
        "breach_ts": "2026-04-15T12:30:00Z",
        "threshold": threshold,
        "event_ids": list(ids),
    }), encoding="utf-8")
    monkeypatch.setattr(csi, "MARKER_PATH", marker)
    return marker


def _no_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(csi, "MARKER_PATH", tmp_path / "absent-marker")


def _dry_run(monkeypatch, capsys, argv):
    monkeypatch.setattr(sys, "argv", ["create_shadow_issue.py", "--dry-run", *argv])
    assert csi.main() == 0
    out = capsys.readouterr().out
    title = out.split("Title: ", 1)[1].split("\n", 1)[0]
    body = out.split("\n\n", 1)[1].split("\n")
    return title, body


@pytest.mark.parametrize("severities", [(1,), (5, 5)])
def test_events_selection_never_claims_a_breach(tmp_path, monkeypatch, capsys, severities):
    _no_marker(tmp_path, monkeypatch)
    events = _events(severities)
    log = _write_log(tmp_path, events)
    ids = ",".join(e["id"] for e in events)
    title, body = _dry_run(monkeypatch, capsys, ["--events", ids, "--log", str(log)])
    total = sum(severities)
    assert title == f"[qor-shadow] Process shadow events - {len(events)} events, sev {total}"
    assert body[0] == NEUTRAL_HEADING
    assert body[2] == f"Severity sum: **{total}** (threshold {cst.THRESHOLD}; {EVENTS_NOTE})"
    assert not any(line.startswith("Detected:") for line in body)
    assert "breach" not in title.lower()
    assert "breach" not in "\n".join(body).lower()


def test_marker_subset_below_threshold_is_not_framed_as_breach(tmp_path, monkeypatch, capsys):
    events = _events((5, 5))
    log = _write_log(tmp_path, events)
    _write_marker(tmp_path, monkeypatch, [e["id"] for e in events])
    assert csi.mark_resolved(log, {events[0]["id"]}) == 1
    title, body = _dry_run(monkeypatch, capsys, ["--log", str(log)])
    assert title == "[qor-shadow] Process shadow events - 1 events, sev 5"
    assert body[0] == NEUTRAL_HEADING
    assert body[2] == "Severity sum: **5** (threshold 10; not reached by these events)"
    assert body[3] == "Event count: 1"
    assert body[4] == "Marker written: 2026-04-15T12:30:00Z"
    assert "breach" not in title.lower()
    assert "breach" not in "\n".join(body).lower()


def test_marker_at_threshold_keeps_the_breach_title_and_header(tmp_path, monkeypatch, capsys):
    events = _events((5, 5))
    log = _write_log(tmp_path, events)
    _write_marker(tmp_path, monkeypatch, [e["id"] for e in events])
    title, body = _dry_run(monkeypatch, capsys, ["--log", str(log)])
    assert title == BREACH_TITLE_PREFIX + "2 events, sev 10"
    assert body[:5] == [
        BREACH_HEADING,
        "",
        "Severity sum: **10** (threshold 10)",
        "Event count: 2",
        "Detected: 2026-04-15T12:30:00Z",
    ]


@pytest.mark.parametrize(
    ("threshold", "severities", "breach"),
    [(3, (4,), True), (20, (5, 5, 2), False)],
)
def test_breach_is_judged_against_the_marker_threshold(
    tmp_path, monkeypatch, capsys, threshold, severities, breach
):
    events = _events(severities)
    log = _write_log(tmp_path, events)
    _write_marker(tmp_path, monkeypatch, [e["id"] for e in events], threshold=threshold)
    title, body = _dry_run(monkeypatch, capsys, ["--log", str(log)])
    assert title.startswith(BREACH_TITLE_PREFIX) is breach
    assert (body[0] == BREACH_HEADING) is breach


@pytest.mark.parametrize("value", [7, 13])
def test_events_threshold_is_read_from_the_writer(tmp_path, monkeypatch, capsys, value):
    monkeypatch.setattr(cst, "THRESHOLD", value)
    _no_marker(tmp_path, monkeypatch)
    events = _events((1,))
    log = _write_log(tmp_path, events)
    _, body = _dry_run(monkeypatch, capsys, ["--events", events[0]["id"], "--log", str(log)])
    assert body[2] == f"Severity sum: **1** (threshold {value}; {EVENTS_NOTE})"


@pytest.mark.parametrize("bad", ["10", None, True, 10.0])
def test_load_marker_rejects_a_non_integer_threshold(tmp_path, monkeypatch, bad):
    event = _event(5, "gate_0")
    _write_marker(tmp_path, monkeypatch, [event["id"]], threshold=bad)
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    message = str(exc.value)
    assert "threshold" in message
    assert "expected an integer" in message
