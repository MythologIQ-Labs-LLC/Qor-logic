"""Behavioral tests for plan_signature_widening_caller_lint (Phase 110, #133).

Each test builds a synthetic repo (source files with calls) + a plan, invokes
check_plan, and asserts on the returned LintWarning list.
"""
from __future__ import annotations

from qor.scripts.plan_signature_widening_caller_lint import check_plan


def _repo_with_callers(tmp_path, fn="persist_distraction_block_state"):
    src = tmp_path / "src"
    src.mkdir()
    (src / "commands.rs").write_text(f"fn a() {{ {fn}(db, u); }}\n", encoding="utf-8")
    (src / "legacy.rs").write_text(f"fn b() {{ {fn}(db, u); }}\n", encoding="utf-8")
    return fn


def _write_plan(tmp_path, body):
    p = tmp_path / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_widening_with_complete_caller_enumeration_passes(tmp_path):
    fn = _repo_with_callers(tmp_path)
    plan = _write_plan(
        tmp_path,
        f"# Plan\n\nWiden `{fn}` to add an arg.\n\n### Affected Files\n\n- `src/commands.rs` - MODIFY\n- `src/legacy.rs` - MODIFY\n",
    )
    assert check_plan(plan, tmp_path) == []


def test_widening_with_missing_caller_file_warns(tmp_path):
    fn = _repo_with_callers(tmp_path)
    plan = _write_plan(
        tmp_path,
        f"# Plan\n\nWiden `{fn}` to add an arg.\n\n### Affected Files\n\n- `src/commands.rs` - MODIFY\n",
    )
    warnings = check_plan(plan, tmp_path)
    files = {w.caller_file for w in warnings}
    assert "src/legacy.rs" in files
    assert "src/commands.rs" not in files


def test_escape_hatch_comment_suppresses_warning(tmp_path):
    fn = _repo_with_callers(tmp_path)
    plan = _write_plan(
        tmp_path,
        f"# Plan\n\nWiden `{fn}` to add an arg.\n<!-- signature-widening-exempt: {fn} -->\n\n### Affected Files\n\n- `src/commands.rs` - MODIFY\n",
    )
    assert check_plan(plan, tmp_path) == []


def test_stop_listed_name_skipped(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.rs").write_text("fn z() { new(x); }\n", encoding="utf-8")
    plan = _write_plan(tmp_path, "# Plan\n\nWiden `new` to add an arg.\n\n### Affected Files\n\n- `docs/x.md` - NEW\n")
    assert check_plan(plan, tmp_path) == []


def test_short_function_name_skipped(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.rs").write_text("fn z() { run(x); }\n", encoding="utf-8")
    plan = _write_plan(tmp_path, "# Plan\n\nWiden `run` to add an arg.\n\n### Affected Files\n\n- `docs/x.md` - NEW\n")
    assert check_plan(plan, tmp_path) == []  # 'run' < 8 chars


def test_no_widening_prose_passes(tmp_path):
    _repo_with_callers(tmp_path)
    plan = _write_plan(tmp_path, "# Plan\n\nRefactor things.\n\n### Affected Files\n\n- `src/commands.rs` - MODIFY\n")
    assert check_plan(plan, tmp_path) == []


def test_macro_caller_skipped(tmp_path):
    fn = "persist_distraction_block_state"
    src = tmp_path / "src"
    src.mkdir()
    (src / "real.rs").write_text(f"fn a() {{ {fn}(db); }}\n", encoding="utf-8")
    (src / "asserted.rs").write_text(f"fn b() {{\n    assert!({fn}(db));\n}}\n", encoding="utf-8")
    plan = _write_plan(
        tmp_path,
        f"# Plan\n\nWiden `{fn}` to add an arg.\n\n### Affected Files\n\n- `src/real.rs` - MODIFY\n",
    )
    warnings = check_plan(plan, tmp_path)
    files = {w.caller_file for w in warnings}
    assert "src/asserted.rs" not in files  # assert! line skipped
