"""Phase 224 (GH #334): the seal-artifact gate must read post-append state.

`/qor-substantiate` regenerated the README badges at Step 6 and graded their
currency at Step 6.5, both before Step 7 appended the SESSION SEAL entry that
the ledger badge counts. The gate therefore compared an artifact against the
state that produced it, passed, and shipped a badge one behind on every seal.

These tests hold the two directions of that claim against the generators
themselves, so the defect and its fix are demonstrable without a seal ceremony:
the gate passes over a badge that is about to be wrong, and the reordered
sequence leaves it nothing to miss. Synthetic fixtures throughout -- no
subprocess, no clock, no repository state.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts.seal_artifacts import check_files, collect_counts, update_files

_README = """<p align="center">
  <img src="https://img.shields.io/badge/Tests-12%20passing-brightgreen" alt="Tests: 12 passing">
  <img src="https://img.shields.io/badge/Skills-0-blue" alt="Skills: 0">
  <img src="https://img.shields.io/badge/Agents-0-blue" alt="Agents: 0">
  <img src="https://img.shields.io/badge/Doctrines-0-blue" alt="Doctrines: 0">
  <img src="https://img.shields.io/badge/Ledger-2%20entries%20sealed-green" alt="Ledger: 2 entries sealed">
</p>
"""

_SYSTEM_STATE = """# Qor-logic System State

**Snapshot**: 2026-06-10
**Chain Status**: ACTIVE.
**Phase**: Phase 41 (hotfix; narrative preserved verbatim).
"""

_LEDGER = """# META LEDGER

### Entry #1: GENESIS

x

### Entry #2: SESSION SEAL -- Phase 41 prior work (v0.1.0)

x
"""

# The entry Step 7 appends. Phase 42 is the phase being sealed.
_SEAL_ENTRY = """
### Entry #3: SESSION SEAL -- Phase 42 the phase under seal (v0.2.0)

x
"""

_SNAPSHOT = "2026-08-12"
_PHASE = 42


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    # Declare the default layout explicitly and leave it empty: a zero count
    # here means "declared and empty", never "root unresolved" (#293).
    for root in ("qor/skills", "qor/agents", "qor/references"):
        (tmp_path / root).mkdir(parents=True)
    (tmp_path / "README.md").write_text(_README, encoding="utf-8")
    (tmp_path / "docs" / "SYSTEM_STATE.md").write_text(_SYSTEM_STATE, encoding="utf-8")
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    return tmp_path


def _append_seal_entry(root: Path) -> None:
    """Model Step 7: append the SESSION SEAL entry for the phase being sealed."""
    ledger = root / "docs" / "META_LEDGER.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8") + _SEAL_ENTRY, encoding="utf-8"
    )


def _ledger_mismatches(root: Path) -> list[str]:
    return [m for m in check_files(root, skip_tests=True) if m.startswith("ledger:")]


def _regenerate(root: Path) -> None:
    """Model the seal-artifact write: resolve truth, then render it."""
    counts = collect_counts(root, skip_tests=True)
    update_files(root, phase=_PHASE, snapshot=_SNAPSHOT, counts=counts)


def test_check_before_append_passes_over_a_badge_that_is_about_to_be_stale(tmp_path):
    """The gate's blindness: it passes, and it was wrong to.

    Writing from pre-append truth and grading immediately -- the Step 6 /
    Step 6.5 order -- reports current, because the entry the badge will have to
    count does not exist yet. The append then makes the shipped badge wrong by
    exactly one, which is what CI saw and the gate could not.
    """
    root = _make_repo(tmp_path)

    _regenerate(root)
    # The ledger dimension -- the one this phase exists for -- reports current,
    # because the entry it will have to count does not exist yet.
    assert _ledger_mismatches(root) == []

    _append_seal_entry(root)

    # ...and is wrong by exactly one the moment Step 7 appends. This is what CI
    # saw on the branch tip and what Step 6.5 structurally could not.
    assert _ledger_mismatches(root) == ["ledger: README declares 2, truth 3"]


def test_the_header_dimension_catches_the_pre_append_write(tmp_path):
    """Phase 224 side effect worth pinning: the header is no longer blind either.

    `_check_header` compared `latest <= got <= latest + 1` before this phase, so
    a header written for the phase being sealed passed while its entry was still
    absent. Under equality that same state is drift. The ledger badge was the
    dimension that shipped wrong; the header was the dimension that had been
    taught to expect it.
    """
    root = _make_repo(tmp_path)

    _regenerate(root)
    assert [m for m in check_files(root, skip_tests=True) if m.startswith("header:")] == [
        f"header: SYSTEM_STATE records Phase {_PHASE}, latest seal is Phase 41"
    ]

    _append_seal_entry(root)
    _regenerate(root)
    assert check_files(root, skip_tests=True) == []


def test_write_after_append_leaves_no_mismatch(tmp_path):
    """The fix: regenerating after the append leaves nothing to report.

    Same fixture, same generators, only the order differs. Invert the fix and
    this test fails while the one above still passes, which is what makes the
    pair a proof rather than a restatement.
    """
    root = _make_repo(tmp_path)

    _append_seal_entry(root)
    _regenerate(root)

    assert check_files(root, skip_tests=True) == []
