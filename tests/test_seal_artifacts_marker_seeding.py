"""Phase 219 (GH #311): --write must be able to seed the markers it requires.

`render_system_state_header` raises when either header marker is absent. The
remediation the sibling `--check` prints on failure is *re-run Step 6 --write* --
and `--write` is the raiser. A repository adopting the toolkit whose
`SYSTEM_STATE.md` never carried the markers cannot bootstrap out, so the
documented remediation does not close its own loop.

Seeding is the same substitution over an empty prior state. `--write` already
receives `--phase` and `--snapshot` and already rewrites both lines; refusing to
write them when absent was a substitution implementation assuming its own
precondition, not a design stance.
"""
from __future__ import annotations

import pytest

from qor.scripts.seal_artifacts import render_system_state_header

TITLE = "# Qor-logic System State\n"
BODY = "\nSome authored narrative that must survive untouched.\n"


def test_write_seeds_missing_markers():
    """THE COUNTERFACTUAL. Fails at HEAD, which raises."""
    out = render_system_state_header(TITLE + BODY, phase=219, snapshot="2026-08-11")

    assert "**Snapshot**: 2026-08-11" in out
    assert "**Phase**: Phase 219" in out
    assert "Some authored narrative that must survive untouched." in out


def test_markers_are_inserted_under_the_title_not_appended():
    """Position matters, because the patterns are line-anchored.

    A marker written at end-of-file satisfies `re.MULTILINE` while producing a
    document whose header block is not its header. The next `--write` would then
    find and rewrite a 'header' sitting below the narrative.
    """
    out = render_system_state_header(TITLE + BODY, phase=219, snapshot="2026-08-11")
    lines = [ln for ln in out.splitlines() if ln.strip()]

    assert lines[0].startswith("# "), lines[0]
    snapshot_at = next(i for i, ln in enumerate(lines) if ln.startswith("**Snapshot**"))
    narrative_at = next(i for i, ln in enumerate(lines) if "authored narrative" in ln)
    assert snapshot_at < narrative_at, (
        f"markers must precede the narrative; got {lines[:4]}")


@pytest.mark.parametrize("present,absent", [
    ("**Snapshot**: 2020-01-01", "**Phase**"),
    ("**Phase**: Phase 1", "**Snapshot**"),
])
def test_only_the_missing_marker_is_seeded(present: str, absent: str):
    """A half-migrated document is not an error; the existing marker keeps place."""
    text = f"{TITLE}\n{present}\n{BODY}"

    out = render_system_state_header(text, phase=219, snapshot="2026-08-11")

    assert out.count("**Snapshot**") == 1, out
    assert out.count("**Phase**: Phase") == 1, out
    assert absent in out


def test_existing_markers_are_rewritten_not_duplicated():
    """REGRESSION. The original substitution behavior is unchanged."""
    text = f"{TITLE}\n**Snapshot**: 2020-01-01\n**Phase**: Phase 1\n{BODY}"

    out = render_system_state_header(text, phase=219, snapshot="2026-08-11")

    assert "**Snapshot**: 2026-08-11" in out
    assert "**Phase**: Phase 219" in out
    assert "2020-01-01" not in out
    assert out.count("**Snapshot**") == 1


def test_malformed_snapshot_still_raises():
    """REGRESSION. That check validates the caller's argument, not the document.

    Seeding relaxes a precondition about the file. It must not relax argument
    validation -- a bad date is a caller error either way.
    """
    with pytest.raises(ValueError):
        render_system_state_header(TITLE + BODY, phase=219, snapshot="not-a-date")
