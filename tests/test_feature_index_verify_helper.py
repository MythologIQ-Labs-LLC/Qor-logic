"""Phase 46 feature_index_verify behavior tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts.feature_index_verify import (
    IndexSummary,
    parse_index_rows,
    tally,
    write_seal_snapshot,
    read_seal_snapshot,
)


_INDEX_BODY = """# FEATURE_INDEX

| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |
|---|---|---|---|---|---|
| FX001 | Foo | src/foo.py:10 | docs/foo.md | tests/test_foo.py | verified |
| FX002 | Bar | src/bar.py:20 | docs/bar.md | — | unverified |
| FX003 | Baz | src/baz.py:30 | docs/baz.md | — | n/a |
"""


def test_parse_index_rows_extracts_columns_from_markdown_table():
    rows = parse_index_rows(_INDEX_BODY)
    assert len(rows) == 3
    assert rows[0]["id"] == "FX001"
    assert rows[0]["status"] == "verified"
    assert rows[2]["status"] == "n/a"


def test_parse_index_rows_skips_separator_row():
    rows = parse_index_rows(_INDEX_BODY)
    statuses = [r["status"] for r in rows]
    assert "---" not in statuses


def test_tally_counts_each_status(tmp_path):
    p = tmp_path / "FEATURE_INDEX.md"
    p.write_text(_INDEX_BODY, encoding="utf-8")
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md")
    assert s.total == 3
    assert s.verified == 1
    assert s.unverified == 1
    assert s.n_a == 1
    assert s.newly_unverified == ()
    assert not s.missing_index


def test_tally_missing_index_returns_missing_flag(tmp_path):
    s = tally(repo_root=tmp_path, index_path="docs/FEATURE_INDEX.md")
    assert s.missing_index is True
    assert s.total == 0


def test_tally_detects_newly_unverified_against_prior_snapshot(tmp_path):
    p = tmp_path / "FEATURE_INDEX.md"
    p.write_text(_INDEX_BODY, encoding="utf-8")
    prior = {"FX001": "verified", "FX002": "verified", "FX003": "verified"}
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert "FX002" in s.newly_unverified


def test_tally_ignores_n_a_in_newly_unverified_set(tmp_path):
    p = tmp_path / "FEATURE_INDEX.md"
    p.write_text(_INDEX_BODY, encoding="utf-8")
    prior = {"FX001": "verified", "FX002": "verified", "FX003": "verified"}
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert "FX003" not in s.newly_unverified


def test_seal_snapshot_roundtrip(tmp_path):
    rows = parse_index_rows(_INDEX_BODY)
    snap_path = write_seal_snapshot(repo_root=tmp_path, sid="sess-abc", rows=rows)
    assert snap_path.exists()
    snap = read_seal_snapshot(repo_root=tmp_path, sid="sess-abc")
    assert snap["FX001"] == "verified"
    assert snap["FX002"] == "unverified"
    assert snap["FX003"] == "n/a"


def test_read_seal_snapshot_missing_returns_empty(tmp_path):
    snap = read_seal_snapshot(repo_root=tmp_path, sid="never-written")
    assert snap == {}
