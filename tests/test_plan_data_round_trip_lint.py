"""Behavioral tests for plan_data_round_trip_lint (Phase 110, #134)."""
from __future__ import annotations

import io
import contextlib

from qor.scripts.plan_data_round_trip_lint import check_plan


def _persistence_repo(tmp_path, with_column=False):
    """A repo where DistractionBlockState is FromRow-backed by a table that
    does (or does not) carry the enforcement_active column."""
    src = tmp_path / "src"
    src.mkdir()
    cols = "user_id TEXT, enabled INTEGER" + (", enforcement_active INTEGER" if with_column else "")
    (src / "schema.rs").write_text(f"// CREATE TABLE alice_blocks ({cols})\n", encoding="utf-8")
    (src / "model.rs").write_text(
        "#[derive(FromRow)]\nstruct DistractionBlockState { user_id: String }\n", encoding="utf-8"
    )


def _plan(tmp_path, body):
    p = tmp_path / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_field_added_with_schema_update_in_affected_files_passes(tmp_path):
    _persistence_repo(tmp_path, with_column=False)
    plan = _plan(
        tmp_path,
        "# Plan\n\nWiden `DistractionBlockState` to add field `enforcement_active`.\n\n"
        "### Affected Files\n\n- `src/schema.rs` - MODIFY\n- `src/model.rs` - MODIFY\n",
    )
    assert check_plan(plan, tmp_path) == []


def test_field_added_without_schema_update_warns(tmp_path):
    _persistence_repo(tmp_path, with_column=False)
    plan = _plan(
        tmp_path,
        "# Plan\n\nWiden `DistractionBlockState` to add field `enforcement_active`.\n\n"
        "### Affected Files\n\n- `docs/notes.md` - NEW\n",
    )
    warnings = check_plan(plan, tmp_path)
    files = {w.persistence_file for w in warnings}
    assert "src/model.rs" in files or "src/schema.rs" in files


def test_transient_field_escape_hatch_suppresses(tmp_path):
    _persistence_repo(tmp_path, with_column=False)
    plan = _plan(
        tmp_path,
        "# Plan\n\nWiden `DistractionBlockState` to add field `enforcement_active`.\n"
        "<!-- transient-field: DistractionBlockState.enforcement_active reason: runtime-probe -->\n\n"
        "### Affected Files\n\n- `docs/notes.md` - NEW\n",
    )
    assert check_plan(plan, tmp_path) == []


def test_field_added_with_explicit_transient_prose(tmp_path):
    _persistence_repo(tmp_path, with_column=False)
    plan = _plan(
        tmp_path,
        "# Plan\n\nAdd field `enforcement_active` to `DistractionBlockState`; "
        "`enforcement_active` is transient (computed at runtime, not persisted).\n\n"
        "### Affected Files\n\n- `docs/notes.md` - NEW\n",
    )
    assert check_plan(plan, tmp_path) == []


def test_no_field_addition_passes(tmp_path):
    _persistence_repo(tmp_path, with_column=False)
    plan = _plan(tmp_path, "# Plan\n\nRefactor the module.\n\n### Affected Files\n\n- `src/model.rs` - MODIFY\n")
    assert check_plan(plan, tmp_path) == []


def test_unparseable_sql_emits_skip_note(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    # CREATE TABLE built via string concat -> no literal column-list parens to parse.
    (src / "schema.rs").write_text('let q = "CREATE TABLE " + name + " from macro";\n', encoding="utf-8")
    (src / "model.rs").write_text(
        "#[derive(FromRow)]\nstruct DistractionBlockState { user_id: String }\n", encoding="utf-8"
    )
    plan = _plan(
        tmp_path,
        "# Plan\n\nWiden `DistractionBlockState` to add field `enforcement_active`.\n\n"
        "### Affected Files\n\n- `docs/notes.md` - NEW\n",
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        warnings = check_plan(plan, tmp_path)
    assert "skipping" in buf.getvalue().lower()
    assert warnings == []
