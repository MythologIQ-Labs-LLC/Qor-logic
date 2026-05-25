"""Phase 105: tests for the dep-admit-override re-evaluation tracker."""
from __future__ import annotations

import textwrap
from datetime import datetime, timezone

import pytest

from qor.scripts import dep_admit_override_tracker as tracker


@pytest.fixture
def fixed_now(monkeypatch):
    """Pin tracker's notion of 'now' so age calculations are deterministic."""
    fixed = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(tracker, "_now_utc", lambda: fixed)
    return fixed


@pytest.fixture
def mixed_ledger(fixed_now):
    """Synthetic ledger with one 35-day-old override (due) and one 10-day-old (pending)."""
    return textwrap.dedent("""\
        ### Entry #900

        **Timestamp**: 2026-04-20T00:00:00Z

        **Dependency admission override**: old-pkg@1.0.0; upload_age_days=2; justification=CVE-2026-1111 critical.

        ---

        ### Entry #910

        **Timestamp**: 2026-05-15T00:00:00Z

        **Dependency admission override**: recent-pkg@2.0.0; upload_age_days=3; justification=upstream maintainer security release.

        ---
        """)


def test_tracker_marks_overrides_older_than_30_days_as_due(mixed_ledger):
    """Override entry timestamped 35 days ago -> 'due'; 10 days ago -> 'pending'."""
    rows = tracker.build_rows(mixed_ledger, follow_up_days=30)
    by_pkg = {r.package: r for r in rows}

    assert by_pkg["old-pkg"].status == "due"
    assert by_pkg["old-pkg"].age_days == 35

    assert by_pkg["recent-pkg"].status == "pending"
    assert by_pkg["recent-pkg"].age_days == 10


def test_tracker_filter_due_excludes_pending_entries(mixed_ledger):
    """With status filter 'due', only overdue entries appear in output."""
    rows = tracker.build_rows(mixed_ledger, follow_up_days=30)
    filtered = tracker.apply_filter(rows, filter_state="due")

    assert len(filtered) == 1
    assert filtered[0].package == "old-pkg"


def test_tracker_markdown_output_has_required_columns(mixed_ledger):
    """Output contains the column headers operator expects (operator-facing contract)."""
    rows = tracker.build_rows(mixed_ledger, follow_up_days=30)
    md = tracker.render_markdown(rows)

    required_headers = ("Package", "Version", "Entry timestamp", "Age (days)", "Status", "Justification")
    for header in required_headers:
        assert header in md, f"output missing column header {header!r}; got:\n{md}"
    # And the data rows show the synthetic package names
    assert "old-pkg" in md
    assert "recent-pkg" in md
