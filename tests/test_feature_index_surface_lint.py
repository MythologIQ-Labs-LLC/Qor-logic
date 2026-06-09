"""Phase 138 (GH #196 V1): surface-tag WARN-only lint behavior tests.

Behavioral: invoke index_has_surface_column / surface_lint / main(--surface-lint)
and assert on returned values + the emitted shadow event (monkeypatched append_event,
so the real Process Shadow Genome is untouched).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import feature_index_verify as fiv

_HEADER_6 = (
    "| ID | Name | Source-of-truth file:line | Doc citation | Test path | Verification status |\n"
    "|---|---|---|---|---|---|\n"
)
_HEADER_7 = (
    "| ID | Name | Source-of-truth file:line | Doc citation | Test path | Surface | Verification status |\n"
    "|---|---|---|---|---|---|---|\n"
)

# 7-col table: FX001 tagged+verified, FX002 untagged+verified, FX003 untagged+n/a.
_INDEX_7_UNTAGGED = _HEADER_7 + (
    "| FX001 | Foo | src/foo.py:10 | docs/foo.md | tests/test_foo.py | route | verified |\n"
    "| FX002 | Bar | src/bar.py:20 | docs/bar.md | tests/test_bar.py |  | verified |\n"
    "| FX003 | Baz | src/baz.py:30 | docs/baz.md | — |  | n/a |\n"
)
# 7-col table: every non-n/a row tagged.
_INDEX_7_CLEAN = _HEADER_7 + (
    "| FX001 | Foo | src/foo.py:10 | docs/foo.md | tests/test_foo.py | route | verified |\n"
    "| FX002 | Bar | src/bar.py:20 | docs/bar.md | tests/test_bar.py | voice | verified |\n"
    "| FX003 | Baz | src/baz.py:30 | docs/baz.md | — |  | n/a |\n"
)
# 6-col table: no Surface column at all.
_INDEX_6 = _HEADER_6 + (
    "| FX001 | Foo | src/foo.py:10 | docs/foo.md | tests/test_foo.py | verified |\n"
)


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "FEATURE_INDEX.md"
    p.write_text(body, encoding="utf-8")
    return p


# --- index_has_surface_column ---

def test_header_detector_true_when_surface_column_present():
    assert fiv.index_has_surface_column(_INDEX_7_UNTAGGED) is True


def test_header_detector_false_for_canonical_six_column_header():
    assert fiv.index_has_surface_column(_INDEX_6) is False


# --- surface_lint ---

def test_surface_lint_flags_untagged_non_na_row(tmp_path: Path):
    _write(tmp_path, _INDEX_7_UNTAGGED)
    result = fiv.surface_lint(tmp_path, index_path="FEATURE_INDEX.md")
    assert result.column_present is True
    # FX002 (verified, empty surface) flagged; FX003 (n/a, empty surface) NOT flagged.
    assert result.untagged == ("FX002",)


def test_surface_lint_clean_when_all_non_na_tagged(tmp_path: Path):
    _write(tmp_path, _INDEX_7_CLEAN)
    result = fiv.surface_lint(tmp_path, index_path="FEATURE_INDEX.md")
    assert result.column_present is True
    assert result.untagged == ()


def test_surface_lint_skips_when_no_surface_column(tmp_path: Path):
    _write(tmp_path, _INDEX_6)
    result = fiv.surface_lint(tmp_path, index_path="FEATURE_INDEX.md")
    assert result.column_present is False
    assert result.untagged == ()


def test_surface_lint_missing_index_flag(tmp_path: Path):
    result = fiv.surface_lint(tmp_path, index_path="FEATURE_INDEX.md")
    assert result.missing_index is True
    assert result.column_present is False


# --- CLI --surface-lint mode (always WARN; exit 0) ---

def _cli(tmp_path: Path, *extra: str) -> list[str]:
    return ["--surface-lint", "--repo-root", str(tmp_path),
            "--index-path", "FEATURE_INDEX.md", "--session", "2026-01-01T0000-sess00", *extra]


def test_cli_surface_lint_warns_and_emits_degradation_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _write(tmp_path, _INDEX_7_UNTAGGED)
    events: list[dict] = []
    monkeypatch.setattr(fiv.shadow_process, "append_event",
                        lambda event, **kw: events.append(event) or "id")
    rc = fiv.main(_cli(tmp_path))
    assert rc == 0
    assert len(events) == 1
    assert events[0]["event_type"] == "degradation"
    assert events[0]["details"]["gate"] == "feature_index_surface_lint"
    assert "FX002" in events[0]["details"]["untagged"]


def test_cli_surface_lint_skip_emits_prerequisite_absent_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _write(tmp_path, _INDEX_6)
    events: list[dict] = []
    monkeypatch.setattr(fiv.shadow_process, "append_event",
                        lambda event, **kw: events.append(event) or "id")
    rc = fiv.main(_cli(tmp_path))
    assert rc == 0
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_skipped_prerequisite_absent"
    assert events[0]["details"]["gate"] == "feature_index_surface_lint"


def test_cli_surface_lint_clean_no_event_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _write(tmp_path, _INDEX_7_CLEAN)
    events: list[dict] = []
    monkeypatch.setattr(fiv.shadow_process, "append_event",
                        lambda event, **kw: events.append(event) or "id")
    rc = fiv.main(_cli(tmp_path))
    assert rc == 0
    assert events == []


def test_cli_surface_lint_missing_index_no_event_exit_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    events: list[dict] = []
    monkeypatch.setattr(fiv.shadow_process, "append_event",
                        lambda event, **kw: events.append(event) or "id")
    rc = fiv.main(_cli(tmp_path))
    assert rc == 0
    assert events == []
