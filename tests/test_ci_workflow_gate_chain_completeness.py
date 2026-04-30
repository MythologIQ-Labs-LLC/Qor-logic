"""Phase 52: ci.yml declares the gate-chain-completeness job."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_yml_declares_gate_chain_completeness_job():
    """Parse ci.yml; assert jobs.gate-chain-completeness exists with non-empty steps."""
    data = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    assert "jobs" in data
    assert "gate-chain-completeness" in data["jobs"], (
        f"jobs must include 'gate-chain-completeness'; found {list(data['jobs'].keys())}"
    )
    job = data["jobs"]["gate-chain-completeness"]
    assert job.get("runs-on") == "ubuntu-latest"
    assert isinstance(job.get("steps"), list) and len(job["steps"]) >= 3


def test_ci_gate_chain_job_invokes_canonical_module():
    """At least one step must invoke `python -m qor.reliability.gate_chain_completeness`."""
    data = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    job = data["jobs"]["gate-chain-completeness"]
    runs = []
    for step in job["steps"]:
        if isinstance(step, dict) and "run" in step:
            runs.append(step["run"])
    combined = "\n".join(runs)
    assert "python -m qor.reliability.gate_chain_completeness" in combined, (
        f"gate-chain-completeness job must invoke the canonical module; "
        f"steps run blocks: {runs}"
    )
    assert "--phase-min 52" in combined, (
        "job must constrain to phase >= 52 (forward-only enforcement)"
    )
