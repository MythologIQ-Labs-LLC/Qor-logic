"""Phase 59: /qor-ideate handoff matrix integrity."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DELEGATION = REPO_ROOT / "qor" / "gates" / "delegation-table.md"


def test_qor_ideate_handoff_targets_research_and_plan():
    """Phase 50 co-occurrence: delegation table must list qor-ideate handoffs."""
    body = DELEGATION.read_text(encoding="utf-8")
    # qor-ideate row(s) present
    assert re.search(r"\| `qor-ideate` \|", body), \
        "delegation-table.md missing qor-ideate row"
    # Routes to both research and plan
    assert "/qor-research" in body  # baseline
    assert "/qor-plan" in body  # baseline
    # qor-ideate-specific routing visible
    ideate_rows = [line for line in body.splitlines() if line.startswith("| `qor-ideate`")]
    assert len(ideate_rows) >= 2, f"expected >=2 qor-ideate routing rows; got {len(ideate_rows)}"
    combined = "\n".join(ideate_rows)
    assert "/qor-research" in combined
    assert "/qor-plan" in combined


def test_qor_ideate_in_gate_skill_matrix_with_zero_broken_handoffs():
    """Reliability sweep: gate_skill_matrix must enumerate qor-ideate."""
    import subprocess
    import sys
    proc = subprocess.run(
        [sys.executable, "-m", "qor.reliability.gate_skill_matrix"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    # Output mentions qor-ideate AND zero broken handoffs
    assert "qor-ideate" in proc.stdout
    # The "Broken: 0" assertion sanity
    assert re.search(r"Broken:\s*0", proc.stdout), \
        f"gate-skill matrix shows broken handoffs: {proc.stdout}"
