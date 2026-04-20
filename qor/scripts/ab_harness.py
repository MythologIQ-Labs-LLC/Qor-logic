#!/usr/bin/env python3
"""A/B harness for persona-vs-stance Identity Activation (Phase 39 B20b).

Measures detection rate on a 20-defect seeded corpus under two Identity
Activation variants (persona-named vs stance-directive-only) for stance-critical
skills. Uses the Anthropic SDK for invocation (V1 resolution from Phase 39
Pass 1 audit).

**Library contract**: ``ab_harness.py`` functions are pure and mockable. They
accept an injected ``client`` parameter and never read environment variables
directly. CI tests pass a mock Anthropic client; operators running the live
cycle use ``qor/scripts/ab_live_run.py`` which creates a real client from
``ANTHROPIC_API_KEY``.

**Cost awareness** (corrected from plan docstring O1):
Each A/B call submits the skill SKILL.md body (~4,000-4,500 input tokens)
plus the fixture content plus instructions. Full cycle = 400 API calls
(2 skills × 2 variants × 5 runs × 20 defects). At Opus 4.7 pricing
(~$15/M input, ~$75/M output) and observed per-call usage: **~$32 per full
cycle**, not the earlier estimate of $4. ~10-15 min wall-time serial.

**Non-determinism**: LLM responses vary across runs even at temperature 0.
N=5 runs per (skill, variant) samples this variance. ``aggregate_runs``
reports mean AND stddev so readers can distinguish real effects from noise.
"""
from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_CORPUS_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "ab_corpus"
_VALID_CATEGORIES = frozenset({
    "razor-overage", "ghost-ui", "security-l3", "owasp-violation",
    "orphan-file", "macro-architecture", "dependency-unjustified",
    "schema-migration-missing", "specification-drift", "test-failure",
    "coverage-gap", "infrastructure-mismatch",
})


def load_manifest(corpus_root: Path = _CORPUS_ROOT) -> list[dict]:
    """Return the list of defect records from MANIFEST.json."""
    manifest_path = corpus_root / "MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data["defects"]


def load_variant(skill: str, variant: str, corpus_root: Path = _CORPUS_ROOT) -> str:
    """Read the Identity Activation block for a (skill, variant) pair."""
    if variant not in ("persona", "stance"):
        raise ValueError(f"variant must be 'persona' or 'stance', got {variant!r}")
    path = corpus_root / "variants" / f"{skill}.{variant}.md"
    return path.read_text(encoding="utf-8")


def score_response(response_text: str, planted_category: str) -> bool:
    """Return True iff the model's response JSON lists the planted category."""
    match = re.search(r'\{[^{}]*"findings_categories"\s*:\s*\[[^\]]*\][^{}]*\}', response_text, re.DOTALL)
    if not match:
        return False
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return False
    categories = payload.get("findings_categories", [])
    return planted_category in categories


def run(
    variant: str,
    skill: str,
    client: Any,
    corpus_root: Path = _CORPUS_ROOT,
    model: str = "claude-opus-4-7",
    max_tokens: int = 800,
) -> dict:
    """Run one A/B pass for (variant, skill); return detection rate + per-defect."""
    defects = load_manifest(corpus_root)
    variant_prose = load_variant(skill, variant, corpus_root)
    per_defect = []
    detections = 0
    for defect in defects:
        fixture_path = corpus_root / defect["file"]
        fixture_content = fixture_path.read_text(encoding="utf-8")
        system_prompt = _system_prompt(variant_prose)
        user_prompt = _user_prompt(fixture_content, defect["file"])
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        response_text = _extract_text(response)
        detected = score_response(response_text, defect["category"])
        if detected:
            detections += 1
        per_defect.append({
            "id": defect["id"], "category": defect["category"],
            "detected": detected, "file": defect["file"],
        })
    total = len(defects)
    return {
        "variant": variant, "skill": skill, "model": model,
        "detections": detections, "total": total,
        "detection_rate": detections / total if total else 0.0,
        "per_defect": per_defect,
    }


def compare(persona_result: dict, stance_result: dict) -> dict:
    """Declare winner between persona and stance results (tie threshold 5pp)."""
    persona_rate = persona_result["detection_rate"]
    stance_rate = stance_result["detection_rate"]
    delta = stance_rate - persona_rate
    if abs(delta) < 0.05:
        winner = "tie"
    elif delta > 0:
        winner = "stance"
    else:
        winner = "persona"
    return {
        "persona_rate": persona_rate,
        "stance_rate": stance_rate,
        "delta": delta,
        "winner": winner,
    }


def aggregate_runs(results: list[dict]) -> dict:
    """Aggregate N per-run results for one (skill, variant) into mean + stddev."""
    rates = [r["detection_rate"] for r in results]
    n = len(rates)
    mean = sum(rates) / n if n else 0.0
    stddev = statistics.stdev(rates) if n > 1 else 0.0
    return {"mean_detection_rate": mean, "stddev_pp": stddev * 100, "n": n}


def _system_prompt(variant_prose: str) -> str:
    return (
        f"{variant_prose}\n\n"
        "You are reviewing a source-code fixture for defects. The fixture may "
        "contain one or more planted defects from this closed enum: "
        f"{sorted(_VALID_CATEGORIES)}. Respond with ONE JSON object exactly "
        'matching {"findings_categories": ["..."]}. No prose outside the JSON.'
    )


def _user_prompt(fixture_content: str, file_path: str) -> str:
    return (
        f"File: {file_path}\n\n"
        f"```\n{fixture_content}\n```\n\n"
        'Emit {"findings_categories": [...]} with any defect categories '
        "this file exhibits. Empty list if none."
    )


def _extract_text(response: Any) -> str:
    if hasattr(response, "content") and response.content:
        first = response.content[0]
        if hasattr(first, "text"):
            return first.text
        if isinstance(first, dict):
            return first.get("text", "")
    if isinstance(response, dict):
        content = response.get("content", [])
        if content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(response)
