"""Phase 147 (GAP-CLI-02 / GAP-ARCH-04 regression floor): every FEATURE_INDEX
row must cite a source file and a test file that actually exist on disk. This
catches the missing-file citation class (a citation naming a path that does not
resolve); it does not verify semantic test correctness (that remains the
feature_index_verify acceptance question), so it is a floor, not a ceiling.
"""
from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_ROW = re.compile(r"^\|\s*FX\d+\s*\|")


def _rows() -> list[list[str]]:
    text = (_REPO / "docs" / "FEATURE_INDEX.md").read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if _ROW.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows


def _file_part(cell: str) -> str:
    # strip a trailing :line and a ::node id, and surrounding backticks
    cell = cell.strip().strip("`")
    cell = cell.split("::", 1)[0]
    cell = re.sub(r":\d+$", "", cell)
    return cell


def test_feature_index_has_rows():
    rows = _rows()
    assert len(rows) >= 17  # sanity: the table is populated


def test_every_source_file_exists():
    missing = []
    for cells in _rows():
        # cells: id, name, source(file:line), doc, test, status
        src = _file_part(cells[2])
        if src and not (_REPO / src).is_file():
            missing.append((cells[0], src))
    assert not missing, f"FEATURE_INDEX source citations do not resolve: {missing}"


def test_every_cited_test_path_file_exists():
    missing = []
    for cells in _rows():
        test_cell = cells[4]
        if not test_cell:
            continue
        path = _file_part(test_cell)
        if not (_REPO / path).is_file():
            missing.append((cells[0], test_cell))
    assert not missing, f"FEATURE_INDEX test citations do not resolve: {missing}"
