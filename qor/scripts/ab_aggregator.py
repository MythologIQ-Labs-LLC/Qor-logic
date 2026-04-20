#!/usr/bin/env python3
"""A/B result aggregator (Phase 39b).

Pure Python — no LLM coupling. Consumes subagent trial responses (via
``parse_trial``), groups by ``(skill, variant)``, computes mean + stddev
detection rates, declares winner per skill against the ±5pp tie threshold,
and renders the canonical ``docs/phase39-ab-results.md`` body.

The ``/qor-ab-run`` skill orchestrates the LLM side (Task-tool parallel
dispatch); this module handles the data reduction and markdown emission.
"""
from __future__ import annotations

import json
import re
import statistics


TIE_THRESHOLD_PP = 5.0


def parse_trial(raw_response: str, defect_ids: list[int]) -> list[dict]:
    """Extract ``{"trials": [...]}`` JSON from a subagent response text.

    Tolerates malformed responses: returns trials with empty
    ``findings_categories`` (counted as missed detections) rather than raising.
    """
    payload = _extract_trials_object(raw_response)
    if payload is None:
        return [{"defect_id": did, "findings_categories": []} for did in defect_ids]
    declared = {t["defect_id"]: t.get("findings_categories", []) for t in payload.get("trials", [])}
    return [{"defect_id": did, "findings_categories": declared.get(did, [])} for did in defect_ids]


def _extract_trials_object(raw: str) -> dict | None:
    """Walk brace-balanced candidates; return the first parseable object with 'trials' key."""
    starts = [i for i, ch in enumerate(raw) if ch == "{"]
    for start in starts:
        depth = 0
        for end in range(start, len(raw)):
            if raw[end] == "{":
                depth += 1
            elif raw[end] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(raw[start : end + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(candidate, dict) and "trials" in candidate:
                        return candidate
                    break
    return None


def _detection_rate(trials: list[dict], manifest_by_id: dict[int, str]) -> float:
    total = len(trials)
    if not total:
        return 0.0
    hits = sum(1 for t in trials if manifest_by_id.get(t["defect_id"]) in t["findings_categories"])
    return hits / total


def aggregate(
    trial_batches: list[dict],
    manifest_by_id: dict[int, str],
) -> dict:
    """Group trial batches by ``(skill, variant)``; return per-skill aggregate."""
    groups: dict[tuple[str, str], list[float]] = {}
    for batch in trial_batches:
        key = (batch["skill"], batch["variant"])
        groups.setdefault(key, []).append(_detection_rate(batch["trials"], manifest_by_id))

    per_skill: dict[str, dict] = {}
    for (skill, variant), rates in groups.items():
        per_skill.setdefault(skill, {})[variant] = {
            "mean_detection_rate": statistics.mean(rates),
            "stddev_pp": statistics.stdev(rates) * 100 if len(rates) > 1 else 0.0,
            "n": len(rates),
        }
    for skill, variants in per_skill.items():
        if "persona" in variants and "stance" in variants:
            variants["comparison"] = _compare(
                variants["persona"]["mean_detection_rate"],
                variants["stance"]["mean_detection_rate"],
            )
    return {"per_skill": per_skill}


def _compare(persona_rate: float, stance_rate: float) -> dict:
    delta = stance_rate - persona_rate
    if abs(delta) * 100 < TIE_THRESHOLD_PP:
        winner = "tie"
    elif delta > 0:
        winner = "stance"
    else:
        winner = "persona"
    return {"persona_rate": persona_rate, "stance_rate": stance_rate,
            "delta": delta, "winner": winner}


def render_markdown(aggregated: dict, model: str = "(model not recorded)") -> str:
    """Render the canonical docs/phase39-ab-results.md body."""
    lines = [
        "# Phase 39 A/B Harness Results",
        "",
        f"**Model**: `{model}` (subagent inheritance from main Claude Code session)",
        "**Corpus**: 20 seeded defects across 10 findings_categories",
        "**Orchestration**: /qor-ab-run skill, parallel Task-tool subagent dispatch",
        f"**Comparison threshold**: ±{TIE_THRESHOLD_PP:.0f}pp = tie",
        "",
    ]
    for skill in sorted(aggregated["per_skill"].keys()):
        variants = aggregated["per_skill"][skill]
        persona = variants.get("persona", {})
        stance = variants.get("stance", {})
        comparison = variants.get("comparison", {})
        lines += [
            f"## /{skill}",
            "",
            "| Variant | Detection rate (mean) | Std dev (pp) | Runs |",
            "|---|---|---|---|",
            f"| persona | {persona.get('mean_detection_rate', 0):.1%} | {persona.get('stddev_pp', 0):.1f} | {persona.get('n', 0)} |",
            f"| stance | {stance.get('mean_detection_rate', 0):.1%} | {stance.get('stddev_pp', 0):.1f} | {stance.get('n', 0)} |",
            "",
            f"**Delta**: {comparison.get('delta', 0) * 100:+.1f} pp. **Winner**: {comparison.get('winner', 'n/a')}.",
            "",
        ]
    return "\n".join(lines)
