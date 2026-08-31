"""Phase 164: behavioral tests for the seal-artifact generators.

Generate-not-assert (research entry #378, rec 2): the pytest suite tests the
GENERATORS against synthetic fixtures; live repo-state currency is enforced by
the substantiate Step 7.7.5 gate and the CI `seal-artifacts currency` step, where
repo state is stable. No test here asserts on the real README/SYSTEM_STATE.
"""
from __future__ import annotations

import pathlib
import re

from pathlib import Path

from qor.scripts.seal_artifacts import (
    check_files,
    main,
    render_readme_badges,
    render_system_state_header,
    update_files,
)

_README = """<p align="center">
  <a href="https://pypi.org/project/qor-logic/"><img src="https://img.shields.io/pypi/v/qor-logic?color=blue&label=PyPI" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-BSL--1.1-orange" alt="License: BSL-1.1">
  <img src="https://img.shields.io/badge/Tests-2500%20passing-brightgreen" alt="Tests: 2500 passing">
  <img src="https://img.shields.io/badge/Skills-30-blue" alt="Skills: 30">
  <img src="https://img.shields.io/badge/Agents-13-blue" alt="Agents: 13">
  <img src="https://img.shields.io/badge/Doctrines-36-blue" alt="Doctrines: 36">
  <img src="https://img.shields.io/badge/Ledger-377%20entries%20sealed-green" alt="Ledger: 377 entries sealed">
</p>
"""

_SYSTEM_STATE = """# Qor-logic System State

**Snapshot**: 2026-06-10
**Chain Status**: ACTIVE. Narrative here.
**Phase**: Phase 7 (hotfix; some narrative that must be preserved verbatim).
**Prior phase**: Phase 6 (feature).
"""

_LEDGER = """# META LEDGER

### Entry #1: GENESIS

x

### Entry #2: GATE TRIBUNAL -- Phase 7 plan PASS

x

### Entry #3: SESSION SEAL -- Phase 8 something (v0.1.0)

x
"""

_COUNTS = {"tests": 12, "skills": 4, "agents": 2, "doctrines": 9, "ledger": 3}


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


def test_render_readme_badges_updates_all_five_counts():
    out = render_readme_badges(_README, _COUNTS)
    assert "badge/Tests-12%20passing" in out
    assert 'alt="Tests: 12 passing"' in out
    assert "badge/Skills-4-blue" in out
    assert 'alt="Skills: 4"' in out
    assert "badge/Agents-2-blue" in out
    assert 'alt="Agents: 2"' in out
    assert "badge/Doctrines-9-blue" in out
    assert 'alt="Doctrines: 9"' in out
    assert "badge/Ledger-3%20entries%20sealed" in out
    assert 'alt="Ledger: 3 entries sealed"' in out


def test_render_readme_badges_is_idempotent():
    once = render_readme_badges(_README, _COUNTS)
    twice = render_readme_badges(once, _COUNTS)
    assert once == twice


def test_render_readme_badges_preserves_unknown_badges():
    out = render_readme_badges(_README, _COUNTS)
    for line in ("label=PyPI", "Python-3.11%2B-blue", "License-BSL--1.1-orange"):
        assert line in out
    assert out.count("img.shields.io") == _README.count("img.shields.io")


def test_render_system_state_header_updates_number_and_date():
    out = render_system_state_header(_SYSTEM_STATE, phase=8, snapshot="2026-07-04")
    assert "**Snapshot**: 2026-07-04" in out
    assert "**Phase**: Phase 8 (hotfix; some narrative that must be preserved verbatim)." in out
    assert "**Prior phase**: Phase 6 (feature)." in out


def test_render_system_state_header_seeds_missing_markers():
    """GH #311: this asserted `raises(ValueError)` and encoded the defect as a
    contract.

    `--check` tells the operator to re-run `--write` when markers are missing,
    and `--write` was the raiser, so the documented remediation could not close
    its own loop. A repository adopting the toolkit could not bootstrap out.
    Seeding is the same substitution over an empty prior state.

    Argument validation is unaffected -- see
    `test_seal_artifacts_marker_seeding.py::test_malformed_snapshot_still_raises`.
    """
    out = render_system_state_header("no header markers here", phase=8, snapshot="2026-07-04")

    assert "**Snapshot**: 2026-07-04" in out
    assert "**Phase**: Phase 8" in out
    assert "no header markers here" in out


def test_update_files_writes_and_reports_changed_paths(tmp_path):
    root = _make_repo(tmp_path)
    changed = update_files(root, phase=8, snapshot="2026-07-04", counts=_COUNTS)
    assert sorted(Path(c).name for c in changed) == ["README.md", "SYSTEM_STATE.md"]
    again = update_files(root, phase=8, snapshot="2026-07-04", counts=_COUNTS)
    assert again == []


def test_check_files_clean_after_write(tmp_path):
    root = _make_repo(tmp_path)
    truth = {"tests": 12, "skills": 0, "agents": 0, "doctrines": 0, "ledger": 3}
    update_files(root, phase=8, snapshot="2026-07-04", counts=truth)
    assert check_files(root, skip_tests=True) == []


def test_check_files_reports_stale_badge_and_header(tmp_path):
    root = _make_repo(tmp_path)
    mismatches = check_files(root, skip_tests=True)
    joined = "\n".join(mismatches)
    assert "skills" in joined  # README declares 30, tmp-repo truth is 0
    # Header drift: rewrite header far behind the latest sealed phase (8)
    ss = root / "docs" / "SYSTEM_STATE.md"
    ss.write_text(ss.read_text(encoding="utf-8").replace("Phase 7 (", "Phase 3 ("), encoding="utf-8")
    mismatches = check_files(root, skip_tests=True)
    assert any("header" in m for m in mismatches)


def test_main_write_then_check_exit_codes(tmp_path, capsys):
    root = _make_repo(tmp_path)
    # Align README badges with tmp-repo truth (0 skills/agents/doctrines, 3 ledger)
    rc = main(["--write", "--phase", "8", "--snapshot", "2026-07-04",
               "--repo-root", str(root), "--skip-tests"])
    assert rc == 0
    rc = main(["--check", "--repo-root", str(root), "--skip-tests"])
    assert rc == 0
    # Synthetic drift: append a ledger entry so the Ledger badge goes stale
    ledger = root / "docs" / "META_LEDGER.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8") + "\n### Entry #4: SESSION SEAL -- Phase 8 x\n",
        encoding="utf-8",
    )
    rc = main(["--check", "--repo-root", str(root), "--skip-tests"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "ledger" in out


def _state(root: pathlib.Path) -> pathlib.Path:
    return root / "docs" / "SYSTEM_STATE.md"


def _set_header_phase(root: pathlib.Path, phase: int) -> None:
    path = _state(root)
    path.write_text(
        re.sub(r"^\*\*Phase\*\*: Phase \d+", f"**Phase**: Phase {phase}",
               path.read_text(encoding="utf-8"), count=1, flags=re.MULTILINE),
        encoding="utf-8",
    )


def _header_mismatches(root: pathlib.Path) -> list[str]:
    return [m for m in check_files(root, skip_tests=True) if m.startswith("header:")]


def test_header_one_phase_ahead_of_latest_seal_is_a_mismatch(tmp_path):
    """Phase 224: the slack the pre-append write required is retired.

    Before this phase `_check_header` accepted `latest <= got <= latest + 1`,
    because Step 6 wrote the header for the phase being sealed before its entry
    existed. With regeneration at Step 7.7.5 that state is unreachable, so a
    header one ahead of the latest seal is drift and must be reported.
    """
    root = _make_repo(tmp_path)          # latest sealed phase is 8
    _set_header_phase(root, 9)

    assert _header_mismatches(root) == [
        "header: SYSTEM_STATE records Phase 9, latest seal is Phase 8"
    ]


def test_header_equal_to_latest_seal_is_current(tmp_path):
    """The tightening did not invert the comparison."""
    root = _make_repo(tmp_path)
    _set_header_phase(root, 8)

    assert _header_mismatches(root) == []


def test_header_behind_latest_seal_is_a_mismatch(tmp_path):
    """The lower bound survived the edit; the previous form rejected this too."""
    root = _make_repo(tmp_path)
    _set_header_phase(root, 7)

    assert _header_mismatches(root) == [
        "header: SYSTEM_STATE records Phase 7, latest seal is Phase 8"
    ]


def test_header_tracks_file_order_latest_seal_not_max_phase(tmp_path):
    """Phase 243 regression guard: phases do not always seal in ascending
    numeric order (Phase 244 merged before Phase 243). The ledger is
    append-only, so the MOST RECENT seal is the last SESSION SEAL entry in
    file order -- the header must match that entry, not the numeric maximum.
    Under the old ``max(sealed)`` proxy the truthful header for a
    lower-numbered later seal was reported as drift."""
    root = _make_repo(tmp_path)
    ledger = root / "docs" / "META_LEDGER.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        + "\n### Entry #4: SESSION SEAL -- Phase 7 out-of-order later seal (v0.2.0)\n\nx\n",
        encoding="utf-8",
    )

    _set_header_phase(root, 7)
    assert _header_mismatches(root) == []

    _set_header_phase(root, 8)
    assert _header_mismatches(root) == [
        "header: SYSTEM_STATE records Phase 8, latest seal is Phase 7"
    ]
