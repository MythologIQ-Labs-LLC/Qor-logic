"""Phase 267 (GH #441): the discarded validation, and what each side does with it.

`validate_gate_artifact._validate_data` returns a list of errors and never
raises. `audit_history.append` called it bare and discarded the result;
`audit_history.read` wrapped the same non-raising call in a `try/except` whose
handler could never fire. Neither validated.

The repair is deliberately asymmetric, and these tests pin both halves:

- `append` fails closed, because nothing should create a row the schema rejects.
- `read` does NOT validate and no longer pretends to, because
  `findings_signature.LEGACY_SENTINEL` exists to recognise pre-Phase-37 rows
  that the current schema rejects. A strict reader would make that control
  unreachable.
"""
from __future__ import annotations

import json
import unittest.mock as mock

import pytest

from qor.scripts import audit_history, findings_signature, stall_walk


def _valid(sid, ts="2026-04-20T12:00:00Z", verdict="VETO", cats=("razor-overage",)):
    rec = {
        "phase": "audit",
        "ts": ts,
        "session_id": sid,
        "target": "docs/plan.md",
        "verdict": verdict,
    }
    if verdict == "VETO" and cats is not None:
        rec["findings_categories"] = list(cats)
    return rec


def _write_raw(tmp_path, sid, records):
    path = tmp_path / sid / "audit_history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, separators=(",", ":"), sort_keys=True) + chr(10))


def _append(tmp_path, sid, rec):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        return audit_history.append(rec, session_id=sid)


def _read(tmp_path, sid):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        return audit_history.read(sid)


# --- T1-T3: append fails closed -------------------------------------------

def test_append_rejects_a_veto_without_findings_categories(tmp_path):
    """The schema requires categories when verdict is VETO (conditional allOf)."""
    rec = _valid("s-t1")
    rec.pop("findings_categories")
    with pytest.raises(ValueError) as exc:
        _append(tmp_path, "s-t1", rec)
    assert "findings_categories" in str(exc.value)


def test_append_rejects_a_malformed_ts(tmp_path):
    """Presence is not enough; the value must match the pinned pattern."""
    rec = _valid("s-t2", ts="20 April 2026")
    with pytest.raises(ValueError) as exc:
        _append(tmp_path, "s-t2", rec)
    assert "ts" in str(exc.value)


def test_append_rejects_a_short_session_id(tmp_path):
    """The class the derived red set surfaced: minLength 3, fixtures used 's1'."""
    rec = _valid("s1")
    with pytest.raises(ValueError) as exc:
        _append(tmp_path, "s1", rec)
    assert "session_id" in str(exc.value)


# --- T4-T5: read stays permissive, and the legacy control survives ---------

def test_read_tolerates_a_row_that_append_would_reject(tmp_path):
    """The asymmetry, pinned deliberately.

    Green before this phase for the wrong reason -- `read`'s handler was inert.
    Green after for the right one -- tolerance is the documented contract.
    Fails if a later change makes `read` strict.
    """
    sid = "s-t4"
    legacy = _valid(sid)
    legacy.pop("findings_categories")
    _write_raw(tmp_path, sid, [legacy])
    records = _read(tmp_path, sid)
    assert len(records) == 1
    assert "findings_categories" not in records[0]


def test_legacy_row_written_directly_still_classifies_legacy(tmp_path):
    """`append` failing closed must not make LEGACY_SENTINEL unreachable."""
    sid = "s-t5"
    legacy = _valid(sid)
    legacy.pop("findings_categories")
    _write_raw(tmp_path, sid, [legacy])
    record = _read(tmp_path, sid)[0]
    assert findings_signature.compute_record(record) == findings_signature.LEGACY_SENTINEL


# --- T6-T7: the accessors are allowed to disagree -------------------------

def _stamps_and_totals(tmp_path, sid):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        return (
            stall_walk.session_signature_timestamps(sid),
            stall_walk.count_session_signature_totals(sid),
        )


def test_a_veto_without_ts_still_counts_but_yields_no_timestamp(tmp_path):
    """D2's asymmetry.

    The counter never touches `ts` and counts the row today; making the two
    accessors agree by filtering the counter would drop a signature below the
    escalation threshold and silence a firing that occurs now. So they disagree,
    and this pins it. Fails if a future change filters the counter.
    """
    sid = "s-t6"
    no_ts = _valid(sid)
    no_ts.pop("ts")
    _write_raw(tmp_path, sid, [_valid(sid, ts="2026-04-20T12:00:00Z"), no_ts])
    stamps, totals = _stamps_and_totals(tmp_path, sid)
    sig = next(iter(totals))
    assert totals[sig] == 2
    assert len(stamps[sig]) == 1


def test_a_malformed_ts_value_is_omitted_not_sorted(tmp_path):
    """'Usable' means present AND matching the pattern.

    The list is sorted lexicographically and indexed positionally, so a
    malformed value would sort and anchor wrongly rather than merely being
    extra. A presence-only check would let "20 April 2026" in and place it
    first.
    """
    sid = "s-t7"
    bad = _valid(sid, ts="20 April 2026")
    _write_raw(tmp_path, sid, [bad, _valid(sid, ts="2026-04-20T12:00:00Z")])
    stamps, totals = _stamps_and_totals(tmp_path, sid)
    sig = next(iter(totals))
    assert totals[sig] == 2
    assert stamps[sig] == ["2026-04-20T12:00:00Z"]
