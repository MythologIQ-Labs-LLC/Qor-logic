"""Phase 87: tests for the author-momentum risk score (GH #82)."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.audit_risk_score import score_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def _grep_lines(n: int) -> str:
    """n grep-evidence statements in the /qor-plan Step 2 canonical form."""
    return "\n".join(
        f"- LD{i}: git show abc{i}:src/file{i}.ts | grep -nE 'sym{i}' -> observed{i}"
        for i in range(1, n + 1)
    )


def _run_cli(plan: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.audit_risk_score", "--plan", str(plan)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def test_config_file_cite_flags_option_b(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        ## Phase 1
        ### Affected Files
        - `vitest.config.ts` - cited config file.
    """)
    a = score_plan(plan)
    assert "config-file-cite" in a.flags
    assert a.option_b_required is True


def test_high_citation_surface_flags_option_b(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\n" + _grep_lines(5) + "\n")
    a = score_plan(plan)
    assert "high-citation-surface" in a.flags
    assert a.option_b_required is True


def test_four_grep_evidence_below_threshold(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\n" + _grep_lines(4) + "\n")
    a = score_plan(plan)
    assert "high-citation-surface" not in a.flags


def test_clean_plan_requires_no_option_b(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        ## Phase 1
        ### Changes
        Add a pure helper. No cited config files, no sealed-infra grep evidence.
    """)
    a = score_plan(plan)
    assert a.flags == ()
    assert a.option_b_required is False


def test_both_signals_fire_independently(tmp_path):
    plan = _write_plan(
        tmp_path, "# Plan\n\n- `webpack.config.js` cited.\n\n" + _grep_lines(5) + "\n")
    a = score_plan(plan)
    assert "config-file-cite" in a.flags
    assert "high-citation-surface" in a.flags


def test_missing_plan_scores_no_risk(tmp_path):
    a = score_plan(tmp_path / "missing.md")
    assert a.flags == ()
    assert a.option_b_required is False


def test_cli_reports_option_b_required_with_flags(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\n- `vite.config.ts` cited.\n")
    proc = _run_cli(plan)
    assert proc.returncode == 0
    assert "option_b_required: true" in proc.stdout
    assert "config-file-cite" in proc.stdout


def test_cli_reports_no_risk_for_clean_plan(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nNothing risky here.\n")
    proc = _run_cli(plan)
    assert proc.returncode == 0
    assert "option_b_required: false" in proc.stdout


# --- Phase 110 (#135): SG-AffectedFilesContract-A cascade signals ------------

def _repo_with_n_callers(tmp_path, fn, n):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    for i in range(n):
        (src / f"c{i}.rs").write_text(f"fn caller{i}() {{ {fn}(a, b); }}\n", encoding="utf-8")


def test_signature_widening_3plus_callers_flags_option_b(tmp_path):
    fn = "persist_distraction_block_state"
    _repo_with_n_callers(tmp_path, fn, 3)
    plan = _write_plan(tmp_path, f"# Plan\n\nWiden `{fn}` to add an arg.\n")
    a = score_plan(plan, repo_root=tmp_path)
    assert "signature-widening-cascade" in a.flags
    assert a.option_b_required is True


def test_signature_widening_2_callers_does_not_flag(tmp_path):
    fn = "persist_distraction_block_state"
    _repo_with_n_callers(tmp_path, fn, 2)
    plan = _write_plan(tmp_path, f"# Plan\n\nWiden `{fn}` to add an arg.\n")
    a = score_plan(plan, repo_root=tmp_path)
    assert "signature-widening-cascade" not in a.flags


def test_struct_field_addition_with_persistence_flags(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "model.rs").write_text("#[derive(FromRow)]\nstruct BlockState { id: String }\n", encoding="utf-8")
    plan = _write_plan(tmp_path, "# Plan\n\nWiden `BlockState` to add field `enforcement_active`.\n")
    a = score_plan(plan, repo_root=tmp_path)
    assert "struct-field-cross-persistence-boundary" in a.flags
    assert a.option_b_required is True


def test_struct_field_addition_no_persistence_does_not_flag(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "model.rs").write_text("struct BlockState { id: String }\n", encoding="utf-8")  # no FromRow, no CREATE TABLE
    plan = _write_plan(tmp_path, "# Plan\n\nWiden `BlockState` to add field `enforcement_active`.\n")
    a = score_plan(plan, repo_root=tmp_path)
    assert "struct-field-cross-persistence-boundary" not in a.flags


def test_scope_narrowing_in_multi_entrypoint_file_flags(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "commands.rs").write_text(
        "pub fn alice_start_deep_work_session() {}\n"
        "pub fn alice_stop_deep_work_session() {}\n"
        "pub fn alice_start_deep_work() {}\n"
        "pub fn alice_stop_deep_work() {}\n",
        encoding="utf-8",
    )
    plan = _write_plan(
        tmp_path,
        "# Plan\n\nUpdate `alice_start_deep_work_session` and `alice_stop_deep_work_session`.\n\n"
        "### Affected Files\n\n- `src/commands.rs` - MODIFY\n",
    )
    a = score_plan(plan, repo_root=tmp_path)
    assert "scope-narrowing-prose-in-multi-entrypoint-file" in a.flags


def test_no_new_signals_preserves_existing_behavior(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nAdd a pure helper. No cascades.\n")
    a = score_plan(plan, repo_root=tmp_path)
    assert a.flags == ()
    assert a.option_b_required is False


def test_repo_root_default_to_cwd(tmp_path):
    # API compatibility: score_plan(plan) callable without repo_root.
    plan = _write_plan(tmp_path, "# Plan\n\nAdd a pure helper.\n")
    a = score_plan(plan)
    assert a.option_b_required is False
