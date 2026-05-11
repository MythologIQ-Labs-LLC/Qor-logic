"""Phase 46 integration: feature-inventory verification scenarios."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.feature_index_verify import tally, write_seal_snapshot, parse_index_rows


_INDEX_3_VERIFIED = """| ID | Name | Source | Doc | Test | Verification status |
|---|---|---|---|---|---|
| FX001 | A | src/a.py:1 |  | tests/a.py | verified |
| FX002 | B | src/b.py:1 |  | tests/b.py | verified |
| FX003 | C | src/c.py:1 |  | tests/c.py | verified |
"""

_INDEX_FX001_REGRESSED = """| ID | Name | Source | Doc | Test | Verification status |
|---|---|---|---|---|---|
| FX001 | A | src/a.py:1 |  | — | unverified |
| FX002 | B | src/b.py:1 |  | tests/b.py | verified |
| FX003 | C | src/c.py:1 |  | tests/c.py | verified |
"""

_INDEX_FX002_TO_N_A = """| ID | Name | Source | Doc | Test | Verification status |
|---|---|---|---|---|---|
| FX001 | A | src/a.py:1 |  | tests/a.py | verified |
| FX002 | B | src/b.py:1 |  | — | n/a |
| FX003 | C | src/c.py:1 |  | tests/c.py | verified |
"""


def test_scenario_1_fresh_repo_no_index(tmp_path):
    s = tally(repo_root=tmp_path, index_path="docs/FEATURE_INDEX.md")
    assert s.missing_index is True


def test_scenario_2_index_with_3_verified_no_prior(tmp_path):
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_3_VERIFIED, encoding="utf-8")
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md")
    assert s.total == 3
    assert s.verified == 3
    assert s.newly_unverified == ()


def test_scenario_3_index_same_as_prior_no_regression(tmp_path):
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_3_VERIFIED, encoding="utf-8")
    prior = {"FX001": "verified", "FX002": "verified", "FX003": "verified"}
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert s.newly_unverified == ()


def test_scenario_4_fx001_flipped_to_unverified_appears_in_regression(tmp_path):
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_FX001_REGRESSED, encoding="utf-8")
    prior = {"FX001": "verified", "FX002": "verified", "FX003": "verified"}
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert "FX001" in s.newly_unverified
    assert s.verified == 2
    assert s.unverified == 1


def test_scenario_5_fx002_intentionally_moved_to_n_a_not_regression(tmp_path):
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_FX002_TO_N_A, encoding="utf-8")
    prior = {"FX001": "verified", "FX002": "verified", "FX003": "verified"}
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert "FX002" not in s.newly_unverified
    assert s.n_a == 1


def test_full_seal_cycle_snapshot_then_diff(tmp_path):
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_3_VERIFIED, encoding="utf-8")
    rows = parse_index_rows(_INDEX_3_VERIFIED)
    write_seal_snapshot(repo_root=tmp_path, sid="seal-1", rows=rows)
    # Next session: FX001 regresses
    (tmp_path / "FEATURE_INDEX.md").write_text(_INDEX_FX001_REGRESSED, encoding="utf-8")
    from qor.scripts.feature_index_verify import read_seal_snapshot
    prior = read_seal_snapshot(repo_root=tmp_path, sid="seal-1")
    s = tally(repo_root=tmp_path, index_path="FEATURE_INDEX.md", prior_snapshot=prior)
    assert s.newly_unverified == ("FX001",)
