"""Phase 144: the FEATURE_INDEX artifact exists, parses, clears the health gate,
and the README 'Latest release' section carries no stale version pin.
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts import feature_index_verify as fiv, governance_health as gh

REPO = Path(__file__).resolve().parents[1]


def test_feature_index_is_recognized_and_parses():
    summary = fiv.tally(REPO)
    assert summary.missing_index is False
    assert summary.total > 0
    finding = gh._classify_one(REPO, "docs/FEATURE_INDEX.md", True)
    assert finding.status is gh.ArtifactStatus.OK, (finding.status.value, finding.reason)


def test_feature_index_rows_use_valid_status():
    rows = fiv.parse_index_rows((REPO / "docs" / "FEATURE_INDEX.md").read_text(encoding="utf-8"))
    assert rows
    for row in rows:
        assert row["status"] in fiv.STATUS_VALUES, row


def test_readme_latest_release_has_no_stale_version_pin():
    text = (REPO / "README.md").read_text(encoding="utf-8")
    m = re.search(r"## Latest release(.*?)(?:\n## )", text, re.DOTALL)
    section = m.group(1) if m else text
    assert "v0.19" not in section, "stale v0.19+ block still present in '## Latest release'"
