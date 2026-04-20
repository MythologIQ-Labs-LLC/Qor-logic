"""Unit tests for qor/scripts/ab_aggregator.py (Phase 39b Phase 1)."""
from __future__ import annotations

import pytest

from qor.scripts import ab_aggregator


def _synthetic_manifest():
    return {
        1: "razor-overage",
        2: "razor-overage",
        3: "ghost-ui",
        4: "specification-drift",
    }


def _perfect_trials(manifest_by_id):
    return [{"defect_id": did, "findings_categories": [cat]}
            for did, cat in manifest_by_id.items()]


def _zero_trials(manifest_by_id):
    return [{"defect_id": did, "findings_categories": []} for did in manifest_by_id]


# ===== parse_trial =====

def test_parse_trial_extracts_valid_json():
    raw = 'Some preamble\n{"trials": [{"defect_id": 1, "findings_categories": ["razor-overage"]}, {"defect_id": 2, "findings_categories": []}]}\ntrailing'
    trials = ab_aggregator.parse_trial(raw, [1, 2])
    assert trials == [
        {"defect_id": 1, "findings_categories": ["razor-overage"]},
        {"defect_id": 2, "findings_categories": []},
    ]


def test_parse_trial_tolerates_malformed_as_empty():
    raw = "model emitted prose, not JSON"
    trials = ab_aggregator.parse_trial(raw, [1, 2, 3])
    assert all(t["findings_categories"] == [] for t in trials)
    assert [t["defect_id"] for t in trials] == [1, 2, 3]


def test_parse_trial_fills_missing_defect_ids():
    # Subagent only returned 1 of 3 declared defects.
    raw = '{"trials": [{"defect_id": 1, "findings_categories": ["razor-overage"]}]}'
    trials = ab_aggregator.parse_trial(raw, [1, 2, 3])
    assert len(trials) == 3
    assert trials[0]["findings_categories"] == ["razor-overage"]
    assert trials[1]["findings_categories"] == []
    assert trials[2]["findings_categories"] == []


# ===== aggregate =====

def test_aggregate_groups_by_skill_and_variant():
    manifest = _synthetic_manifest()
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": _perfect_trials(manifest)},
        {"skill": "qor-audit", "variant": "stance", "trials": _zero_trials(manifest)},
        {"skill": "qor-substantiate", "variant": "persona", "trials": _zero_trials(manifest)},
    ]
    result = ab_aggregator.aggregate(batches, manifest)
    assert "qor-audit" in result["per_skill"]
    assert "qor-substantiate" in result["per_skill"]
    assert "persona" in result["per_skill"]["qor-audit"]
    assert "stance" in result["per_skill"]["qor-audit"]


def test_aggregate_computes_mean_and_stddev_per_group():
    manifest = _synthetic_manifest()
    perfect = _perfect_trials(manifest)
    zero = _zero_trials(manifest)
    # 3 perfect + 2 zero runs → mean 0.6, stddev nonzero
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": perfect},
        {"skill": "qor-audit", "variant": "persona", "trials": perfect},
        {"skill": "qor-audit", "variant": "persona", "trials": perfect},
        {"skill": "qor-audit", "variant": "persona", "trials": zero},
        {"skill": "qor-audit", "variant": "persona", "trials": zero},
    ]
    result = ab_aggregator.aggregate(batches, manifest)
    persona = result["per_skill"]["qor-audit"]["persona"]
    assert persona["n"] == 5
    assert persona["mean_detection_rate"] == pytest.approx(0.6, abs=0.001)
    assert persona["stddev_pp"] > 0


def test_aggregate_declares_winner_stance_above_5pp():
    manifest = _synthetic_manifest()
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": _zero_trials(manifest)},
        {"skill": "qor-audit", "variant": "stance", "trials": _perfect_trials(manifest)},
    ]
    result = ab_aggregator.aggregate(batches, manifest)
    comparison = result["per_skill"]["qor-audit"]["comparison"]
    assert comparison["winner"] == "stance"
    assert comparison["delta"] == pytest.approx(1.0)


def test_aggregate_declares_winner_persona_above_5pp():
    manifest = _synthetic_manifest()
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": _perfect_trials(manifest)},
        {"skill": "qor-audit", "variant": "stance", "trials": _zero_trials(manifest)},
    ]
    result = ab_aggregator.aggregate(batches, manifest)
    assert result["per_skill"]["qor-audit"]["comparison"]["winner"] == "persona"


def test_aggregate_declares_tie_below_5pp():
    manifest = _synthetic_manifest()
    # 3 hits (75%) persona vs 3 hits (75%) stance → delta 0 → tie
    three_hits = [
        {"defect_id": 1, "findings_categories": ["razor-overage"]},
        {"defect_id": 2, "findings_categories": ["razor-overage"]},
        {"defect_id": 3, "findings_categories": ["ghost-ui"]},
        {"defect_id": 4, "findings_categories": []},
    ]
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": three_hits},
        {"skill": "qor-audit", "variant": "stance", "trials": three_hits},
    ]
    result = ab_aggregator.aggregate(batches, manifest)
    assert result["per_skill"]["qor-audit"]["comparison"]["winner"] == "tie"


# ===== render_markdown =====

def test_render_markdown_includes_per_skill_section():
    manifest = _synthetic_manifest()
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": _perfect_trials(manifest)},
        {"skill": "qor-audit", "variant": "stance", "trials": _zero_trials(manifest)},
    ]
    aggregated = ab_aggregator.aggregate(batches, manifest)
    md = ab_aggregator.render_markdown(aggregated, model="claude-opus-4-7")
    assert "/qor-audit" in md
    assert "claude-opus-4-7" in md


def test_render_markdown_includes_winner_declaration():
    manifest = _synthetic_manifest()
    batches = [
        {"skill": "qor-audit", "variant": "persona", "trials": _zero_trials(manifest)},
        {"skill": "qor-audit", "variant": "stance", "trials": _perfect_trials(manifest)},
    ]
    aggregated = ab_aggregator.aggregate(batches, manifest)
    md = ab_aggregator.render_markdown(aggregated)
    assert "**Winner**" in md
    assert "stance" in md
