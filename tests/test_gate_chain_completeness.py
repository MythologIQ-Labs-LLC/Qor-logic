"""Phase 52: gate_chain_completeness.check() — keystone of structural enforcement.

Each test invokes check() (or main()) with controlled synthetic fixtures
and asserts on returned CompletenessResult or exit code. Functionality
tests per Phase 46 doctrine; no self-exempting cutoffs (the production
phase_min cutoff is itself unit-tested via synthetic fixture).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _make_session_dir(gates_root: Path, sid: str, *artifacts: str) -> Path:
    sess = gates_root / sid
    sess.mkdir(parents=True, exist_ok=True)
    for art in artifacts:
        (sess / f"{art}.json").write_text("{}", encoding="utf-8")
    return sess


def _make_seal_entry(phase_num: int, sid: str) -> str:
    return (
        f"### Entry #{100 + phase_num}: SESSION SEAL -- Phase {phase_num} feature substantiated\n"
        f"\n"
        f"**Session**: `{sid}`\n"
        f"\n"
        f"**Content Hash (session seal)**: `aaa`\n"
        f"**Previous Hash**: `bbb`\n"
        f"**Chain Hash (Merkle seal)**: `ccc`\n"
        f"\n"
        f"---\n"
    )


def test_module_importable_with_canonical_api():
    from qor.reliability import gate_chain_completeness as gcc
    assert callable(gcc.check)
    assert callable(gcc.main)
    assert hasattr(gcc, "CompletenessResult")
    assert gcc.REQUIRED_PHASES == ("plan", "audit", "implement", "substantiate")


def test_check_returns_ok_for_clean_synthetic_session(tmp_path):
    from qor.reliability.gate_chain_completeness import check

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    _make_session_dir(gates, "s52", "plan", "audit", "implement", "substantiate")

    result = check(tmp_path, phase_min=52, ledger_path=ledger, gates_root=gates)
    assert result.ok is True
    assert result.missing == []
    assert "s52" in result.sessions_checked


def test_check_reports_missing_audit_artifact(tmp_path):
    from qor.reliability.gate_chain_completeness import check

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    _make_session_dir(gates, "s52", "plan", "implement", "substantiate")  # no audit

    result = check(tmp_path, phase_min=52, ledger_path=ledger, gates_root=gates)
    assert result.ok is False
    assert any("audit.json" in what for _, what in result.missing)


def test_check_reports_missing_implement_artifact(tmp_path):
    from qor.reliability.gate_chain_completeness import check

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    _make_session_dir(gates, "s52", "plan", "audit", "substantiate")  # no implement

    result = check(tmp_path, phase_min=52, ledger_path=ledger, gates_root=gates)
    assert result.ok is False
    assert any("implement.json" in what for _, what in result.missing)


def test_check_reports_missing_substantiate_artifact(tmp_path):
    from qor.reliability.gate_chain_completeness import check

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    _make_session_dir(gates, "s52", "plan", "audit", "implement")  # no substantiate

    result = check(tmp_path, phase_min=52, ledger_path=ledger, gates_root=gates)
    assert result.ok is False
    assert any("substantiate.json" in what for _, what in result.missing)


def test_check_skips_phases_below_phase_min(tmp_path):
    """Phase 50 SEAL with no artifacts -> grandfathered when phase_min=52."""
    from qor.reliability.gate_chain_completeness import check

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_make_seal_entry(50, "s50"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    # Deliberately no artifacts for s50

    result = check(tmp_path, phase_min=52, ledger_path=ledger, gates_root=gates)
    assert result.ok is True, f"Phase 50 should be grandfathered; got missing={result.missing}"
    assert result.sessions_checked == []


def test_check_handles_missing_ledger_gracefully(tmp_path):
    """If META_LEDGER.md absent, check returns ok=False with descriptive message."""
    from qor.reliability.gate_chain_completeness import check

    result = check(tmp_path, phase_min=52)
    assert result.ok is False
    assert result.missing
    assert any("ledger" in what.lower() for _, what in result.missing)


def test_main_exits_zero_on_clean_state(tmp_path):
    """CLI main() returns 0 when gate chain complete.

    Subprocess runs in REPO_ROOT (so qor package resolves) but uses
    --repo-root arg to target the synthetic tmp_path fixture. This avoids
    the editable-install-staleness gotcha where the subprocess's cwd-based
    sys.path[0] doesn't see the worktree's qor/ package.
    """
    repo_root = Path(__file__).resolve().parent.parent
    ledger = tmp_path / "docs" / "META_LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    gates = tmp_path / ".qor" / "gates"
    _make_session_dir(gates, "s52", "plan", "audit", "implement", "substantiate")

    result = subprocess.run(
        [sys.executable, "-m", "qor.reliability.gate_chain_completeness",
         "--phase-min", "52", "--repo-root", str(tmp_path)],
        capture_output=True, text=True, check=False,
        cwd=str(repo_root),
    )
    assert result.returncode == 0, f"expected exit 0; stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "OK" in result.stdout


def test_main_exits_one_on_missing_artifacts(tmp_path):
    """CLI main() returns 1 when gate chain incomplete."""
    repo_root = Path(__file__).resolve().parent.parent
    ledger = tmp_path / "docs" / "META_LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(_make_seal_entry(52, "s52"), encoding="utf-8")
    # No gate artifacts at all under tmp_path/.qor/gates/

    result = subprocess.run(
        [sys.executable, "-m", "qor.reliability.gate_chain_completeness",
         "--phase-min", "52", "--repo-root", str(tmp_path)],
        capture_output=True, text=True, check=False,
        cwd=str(repo_root),
    )
    assert result.returncode == 1, f"expected exit 1; stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FAIL" in result.stdout
