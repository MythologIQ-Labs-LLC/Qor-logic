"""Phase 137: SYSTEM_STATE.md header-freshness drift guard.

`test_system_state_phase_coverage.py` only enforces per-phase sections for ledger
entries phrased "Phase N feature substantiated"; recent entries use other
phrasing, so the header silently drifted 61 phases (stuck at Phase 75 while the
ledger reached Phase 136). This guard derives the latest sealed phase from the
ledger and the phase recorded in the SYSTEM_STATE header, and fails when the
header falls 2+ phases behind.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "docs" / "META_LEDGER.md"
SYSTEM_STATE = REPO / "docs" / "SYSTEM_STATE.md"

_SEAL_RE = re.compile(r"^### Entry #\d+: SESSION SEAL -- Phase (\d+)", re.MULTILINE)
_HEADER_PHASE_RE = re.compile(r"^\*\*Phase\*\*:\s*Phase (\d+)", re.MULTILINE)
_SNAPSHOT_RE = re.compile(r"^\*\*Snapshot\*\*:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def _latest_sealed_phase() -> int:
    phases = [int(m) for m in _SEAL_RE.findall(LEDGER.read_text(encoding="utf-8"))]
    assert phases, "no SESSION SEAL entries found in META_LEDGER"
    return max(phases)


def _header_phase() -> int:
    m = _HEADER_PHASE_RE.search(SYSTEM_STATE.read_text(encoding="utf-8"))
    assert m, "SYSTEM_STATE.md header has no '**Phase**: Phase N' line"
    return int(m.group(1))


def test_header_phase_within_one_of_latest_seal() -> None:
    latest = _latest_sealed_phase()
    header = _header_phase()
    assert header >= latest - 1, (
        f"SYSTEM_STATE.md header is stale: header records Phase {header} but the "
        f"latest sealed ledger phase is {latest} (drift {latest - header}). "
        f"Refresh the header during /qor-substantiate Step 6."
    )


def test_header_has_parseable_snapshot_date() -> None:
    m = _SNAPSHOT_RE.search(SYSTEM_STATE.read_text(encoding="utf-8"))
    assert m, "SYSTEM_STATE.md header has no '**Snapshot**: YYYY-MM-DD' line"
    _dt.date.fromisoformat(m.group(1))  # raises ValueError on a malformed date


def test_existing_phase_coverage_helpers_still_resolve() -> None:
    # Guards that the historical per-phase sections remain (no regression of the
    # existing coverage contract from this resync).
    from test_system_state_phase_coverage import (
        _phases_in_system_state,
        _sealed_phases_from_ledger,
    )
    in_state = _phases_in_system_state()
    assert 57 in in_state, "historical Phase 57 section disappeared from SYSTEM_STATE"
    assert not (_sealed_phases_from_ledger() - in_state), "feature-substantiated coverage regressed"
