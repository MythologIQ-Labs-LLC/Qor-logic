"""Phase 106: tests for the session ID convention lint (WARN-only at substantiate)."""
from __future__ import annotations

import pytest

from qor.scripts import session_id_lint


def test_session_id_lint_emits_warn_when_pattern_mismatch(tmp_path, capsys):
    """Non-conforming session marker -> stderr WARN + exit 0 (non-blocking)."""
    marker = tmp_path / "current"
    marker.write_text("2026-05-25T0400-phase105-deps", encoding="utf-8")

    exit_code = session_id_lint.main(["--marker", str(marker)])
    captured = capsys.readouterr()

    assert exit_code == 0  # non-blocking
    assert "WARN" in captured.err
    assert "phase105-deps" in captured.err
    assert "SESSION_ID_PATTERN" in captured.err
    assert "session.rotate()" in captured.err


def test_session_id_lint_silent_when_pattern_matches(tmp_path, capsys):
    """Conforming session marker -> no stderr + exit 0."""
    marker = tmp_path / "current"
    marker.write_text("2026-05-25T2035-c8f105", encoding="utf-8")

    exit_code = session_id_lint.main(["--marker", str(marker)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""


def test_session_id_lint_silent_when_marker_missing(tmp_path, capsys):
    """No marker file -> no stderr + exit 0 (nothing to lint)."""
    marker = tmp_path / "current"  # does not exist
    exit_code = session_id_lint.main(["--marker", str(marker)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
