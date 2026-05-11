"""Phase 63 Phase 1: pre-flight inventory + branch preservation."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "docs" / "reconciliation-2026-05-11.md"

ALLOWED_DECISIONS = {"replay", "merge", "drop"}
EXPECTED_SESSION_PHASE_COUNT = 17


def _parse_matrix_rows() -> list[dict[str, str]]:
    """Parse the matrix markdown table into a list of row dicts.

    Functionality-test contract: this parser invokes the on-disk file and
    returns the structured row data the assertions then operate on. If the
    table were silently malformed (missing column, swapped headers, stray
    pipe), the parser would raise or return mis-shaped rows -- which is the
    behavior the suite verifies.
    """
    text = MATRIX.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("| Session phase")),
        None,
    )
    if header_idx is None:
        raise AssertionError("matrix has no `| Session phase` header row")

    header = [c.strip() for c in lines[header_idx].strip("|").split("|")]
    expected_cols = [
        "Session phase",
        "Session deliverable",
        "Upstream phase touching same surface",
        "Overlap?",
        "Decision",
        "New phase number",
        "New version",
    ]
    if header != expected_cols:
        raise AssertionError(f"matrix header mismatch: {header} != {expected_cols}")

    rows: list[dict[str, str]] = []
    # Skip header and separator row.
    for ln in lines[header_idx + 2:]:
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != len(expected_cols):
            continue
        rows.append(dict(zip(expected_cols, cells)))
    return rows


def test_matrix_lists_all_seventeen_session_phases():
    rows = _parse_matrix_rows()
    assert len(rows) == EXPECTED_SESSION_PHASE_COUNT, (
        f"expected {EXPECTED_SESSION_PHASE_COUNT} session-phase rows, "
        f"parser returned {len(rows)}"
    )


def test_matrix_decision_values_are_closed_enum():
    rows = _parse_matrix_rows()
    invalid = [r for r in rows if r["Decision"].lower() not in ALLOWED_DECISIONS]
    assert not invalid, (
        f"rows with decision outside {ALLOWED_DECISIONS}: "
        f"{[(r['Session phase'], r['Decision']) for r in invalid]}"
    )


def test_matrix_replay_rows_assign_unique_new_phase_numbers():
    rows = _parse_matrix_rows()
    replay_numbers = [
        r["New phase number"] for r in rows if r["Decision"].lower() == "replay"
    ]
    # Drop placeholders (`-`, `n/a`) so collisions of those don't false-fail.
    real = [n for n in replay_numbers if n and n not in {"-", "n/a", "N/A"}]
    duplicates = sorted({n for n in real if real.count(n) > 1})
    assert not duplicates, f"replayed phases share new phase numbers: {duplicates}"


def test_archive_branch_exists():
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "archive/session-2026-05-09"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, (
        f"archive/session-2026-05-09 not resolvable: {result.stderr.strip()}"
    )
    sha = result.stdout.strip()
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha), (
        f"git rev-parse returned non-SHA: {sha!r}"
    )
