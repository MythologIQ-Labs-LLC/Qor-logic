"""Phase 31 Phase 2: ad-hoc drift report CLI smoke test."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_cli_runs_against_live_repo():
    """Operator runs `python -m qor.scripts.doc_integrity_drift_report` and
    gets a Markdown drift report. Exit 0 even when findings exist (lenient)."""
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.doc_integrity_drift_report"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert result.stdout.startswith("# Documentation Drift Report"), (
        f"Unexpected CLI output header:\n{result.stdout[:300]}"
    )


def test_cli_has_both_check_sections():
    """Output must include sections for Check Surface D and E."""
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.doc_integrity_drift_report"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "## Check Surface D" in result.stdout
    assert "## Check Surface E" in result.stdout
