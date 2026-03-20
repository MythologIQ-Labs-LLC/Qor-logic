#!/usr/bin/env python3
"""Orchestrator: run process -> compile-claude -> compile-agent pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_stage(name: str, script: str) -> bool:
    """Run a pipeline stage and report result."""
    print(f"\n{'=' * 50}")
    print(f"Stage: {name}")
    print("=" * 50)

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)],
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\nFAILED: {name} (exit code {result.returncode})")
        return False

    print(f"OK: {name}")
    return True


def main() -> int:
    stages = [
        ("Process (ingest -> processed)", "process-skills.py", False),
        ("Compile Claude Code (processed -> .claude)", "compile-claude.py", True),
        ("Compile Agent Workflows (processed -> .agent)", "compile-agent.py", True),
    ]

    results = []
    for name, script, blocking in stages:
        ok = run_stage(name, script)
        results.append((name, ok))
        if not ok and blocking:
            print(f"\nPipeline stopped at: {name}")
            break

    print(f"\n{'=' * 50}")
    print("Pipeline Summary")
    print("=" * 50)
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    all_ok = all(ok for _, ok in results)
    print(f"\nResult: {'ALL STAGES PASSED' if all_ok else 'PIPELINE FAILED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
