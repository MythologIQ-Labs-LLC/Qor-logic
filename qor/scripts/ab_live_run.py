#!/usr/bin/env python3
"""Operator CLI: run the Phase 39 A/B cycle live against Anthropic API.

This is the ONLY entry point that actually hits the API. It reads
``ANTHROPIC_API_KEY`` from env, instantiates a real ``anthropic.Anthropic``
client, and runs 400 serial calls (~$32, ~10-15 min at Opus 4.7 pricing).
Produces ``docs/phase39-ab-results.md`` + per-run raw data in the gitignored
``.qor/gates/<session>/ab-run.json``.

Usage:
    ANTHROPIC_API_KEY=sk-... python qor/scripts/ab_live_run.py

The CLI exits non-zero if the env var is absent BEFORE doing any work.

Library functions (``ab_harness.run`` etc.) accept an injected client and
never read env directly; they are CI-testable with mocks.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from qor.scripts import ab_harness
from qor.scripts import session as _session


RUNS_PER_VARIANT = 5
TARGET_SKILLS = ("qor-audit", "qor-substantiate")


def _require_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print(
            "error: ANTHROPIC_API_KEY environment variable is required but not set. "
            "Set it before running the live A/B cycle. See qor/scripts/ab_harness.py "
            "docstring for cost expectations (~$32 per full cycle).",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _build_client():
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError:
        print(
            "error: anthropic SDK is not installed. Install via "
            "`pip install -e .[ab-harness]` before running the live cycle.",
            file=sys.stderr,
        )
        sys.exit(1)
    return anthropic.Anthropic()


def _run_variant(client, skill: str, variant: str) -> list[dict]:
    return [ab_harness.run(variant, skill, client) for _ in range(RUNS_PER_VARIANT)]


def main() -> int:
    _require_api_key()
    client = _build_client()
    results: dict = {}
    for skill in TARGET_SKILLS:
        results[skill] = {
            "persona": _run_variant(client, skill, "persona"),
            "stance": _run_variant(client, skill, "stance"),
        }
    _write_artifacts(results)
    return 0


def _write_artifacts(results: dict) -> None:
    sid = _session.get_or_create()
    raw_dir = Path(".qor") / "gates" / sid
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "ab-run.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    _write_results_markdown(results)


def _write_results_markdown(results: dict) -> None:
    lines = ["# Phase 39 A/B Harness Results", "",
             "**Corpus**: 20 seeded defects across 10 findings_categories",
             f"**Runs per variant**: {RUNS_PER_VARIANT}",
             "**Comparison threshold**: ±5 percentage points = tie", ""]
    for skill in TARGET_SKILLS:
        persona_runs = results[skill]["persona"]
        stance_runs = results[skill]["stance"]
        persona_agg = ab_harness.aggregate_runs(persona_runs)
        stance_agg = ab_harness.aggregate_runs(stance_runs)
        comparison = ab_harness.compare(
            {"detection_rate": persona_agg["mean_detection_rate"]},
            {"detection_rate": stance_agg["mean_detection_rate"]},
        )
        lines += [
            f"## /{skill}", "",
            "| Variant | Detection rate (mean) | Std dev (pp) |",
            "|---|---|---|",
            f"| persona | {persona_agg['mean_detection_rate']:.1%} | {persona_agg['stddev_pp']:.1f} |",
            f"| stance | {stance_agg['mean_detection_rate']:.1%} | {stance_agg['stddev_pp']:.1f} |",
            "",
            f"**Delta**: {comparison['delta'] * 100:+.1f} pp. **Winner**: {comparison['winner']}.",
            "",
        ]
    Path("docs/phase39-ab-results.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
