"""Phase 109 D-109.3: governance-health CLI exit-code contract.

0 == all OK, 1 == MISSING/INCOMPLETE/UNINITIALIZED, 2 == DAMAGED. Tests invoke
the module CLI as a subprocess and assert on its real exit code.
"""
from __future__ import annotations

import subprocess
import sys

_HEALTHY = {
    "META_LEDGER.md": "# QoreLogic Meta Ledger\n\n### Entry #1: SEAL\nsealed.\n",
    "CONCEPT.md": "# Project Concept\n\nWhy: ship governed software safely.\n",
    "ARCHITECTURE_PLAN.md": "# Architecture Plan\n\nRisk Grade L2. Modules: cli, scripts.\n",
    "SYSTEM_STATE.md": "# System State\n\nGovernance surfaces documented here.\n",
    "SHADOW_GENOME.md": "# Shadow Genome\n\nNo open failures.\n",
    "BACKLOG.md": "# Backlog\n\nNo open blockers.\n",
    "FEATURE_INDEX.md": "# Feature Index\n\nNo user-facing features yet.\n",
}


def _run(repo_root):
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.governance_health", "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
    )


def test_cli_exit_zero_for_healthy_workspace(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, body in _HEALTHY.items():
        (docs / name).write_text(body, encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode == 0, (result.returncode, result.stdout)


def test_cli_exit_two_for_damaged_workspace(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text("%%% not a ledger %%%\ngarbage\n", encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode == 2, (result.returncode, result.stdout)
