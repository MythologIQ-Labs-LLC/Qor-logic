"""Phase 59: skill registry rollup test."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_qor_ideate_listed_by_gate_skill_matrix():
    proc = subprocess.run(
        [sys.executable, "-m", "qor.reliability.gate_skill_matrix"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "qor-ideate" in proc.stdout


def test_qor_ideate_skill_dir_structure():
    skill_dir = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-ideate"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "references" / "dialogue-protocol.md").exists()
