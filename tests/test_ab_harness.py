"""Tests for qor/scripts/ab_harness.py (Phase 39 B2). All Anthropic calls mocked."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import unittest.mock as mock

import pytest

from qor.scripts import ab_harness


_CORPUS = pathlib.Path("tests/fixtures/ab_corpus")


def _mock_client(response_text: str):
    client = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.content = [mock.MagicMock(text=response_text)]
    client.messages.create.return_value = mock_response
    return client


def test_corpus_manifest_declares_20_defects():
    defects = ab_harness.load_manifest(_CORPUS)
    assert len(defects) == 20


def test_corpus_categories_are_all_valid_enum_values():
    valid = {
        "razor-overage", "ghost-ui", "security-l3", "owasp-violation",
        "orphan-file", "macro-architecture", "dependency-unjustified",
        "schema-migration-missing", "specification-drift", "test-failure",
        "coverage-gap", "infrastructure-mismatch",
    }
    defects = ab_harness.load_manifest(_CORPUS)
    for d in defects:
        assert d["category"] in valid, f"unknown category: {d['category']}"


def test_corpus_files_exist():
    defects = ab_harness.load_manifest(_CORPUS)
    for d in defects:
        assert (_CORPUS / d["file"]).is_file(), f"missing fixture: {d['file']}"


def test_corpus_files_carry_seeded_defect_marker():
    defects = ab_harness.load_manifest(_CORPUS)
    marker = "SEEDED TEST DEFECT"
    for d in defects:
        content = (_CORPUS / d["file"]).read_text(encoding="utf-8")
        assert marker in content.splitlines()[0], (
            f"{d['file']}: first line missing marker '{marker}'"
        )


def test_manifest_line_range_fields_present():
    defects = ab_harness.load_manifest(_CORPUS)
    for d in defects:
        assert "line_start" in d
        assert "line_end" in d
        assert d["line_start"] <= d["line_end"]


def test_scorer_counts_category_superset_as_detection():
    resp = '{"findings_categories": ["razor-overage", "other-extra"]}'
    assert ab_harness.score_response(resp, "razor-overage") is True


def test_scorer_counts_missing_category_as_miss():
    resp = '{"findings_categories": ["specification-drift"]}'
    assert ab_harness.score_response(resp, "razor-overage") is False


def test_scorer_counts_json_parse_failure_as_miss():
    resp = "not a json response"
    assert ab_harness.score_response(resp, "razor-overage") is False


def test_compare_reports_winner_stance_above_5pp():
    persona = {"detection_rate": 0.50}
    stance = {"detection_rate": 0.60}
    result = ab_harness.compare(persona, stance)
    assert result["winner"] == "stance"
    assert result["delta"] == pytest.approx(0.10)


def test_compare_reports_winner_persona_above_5pp():
    persona = {"detection_rate": 0.70}
    stance = {"detection_rate": 0.60}
    result = ab_harness.compare(persona, stance)
    assert result["winner"] == "persona"


def test_compare_reports_tie_below_5pp():
    persona = {"detection_rate": 0.50}
    stance = {"detection_rate": 0.53}
    result = ab_harness.compare(persona, stance)
    assert result["winner"] == "tie"


def test_run_uses_injected_client_not_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = _mock_client('{"findings_categories": ["razor-overage"]}')
    result = ab_harness.run("persona", "qor-audit", client=client, corpus_root=_CORPUS)
    assert result["total"] == 20
    # If the function read env, it would fail without the key. It doesn't.


def test_run_submits_variant_system_prompt():
    client = _mock_client('{"findings_categories": []}')
    ab_harness.run("stance", "qor-audit", client=client, corpus_root=_CORPUS)
    calls = client.messages.create.call_args_list
    assert calls, "no API calls made"
    system_prompt = calls[0].kwargs["system"]
    # The stance variant file has a Stance header; persona has Identity Activation.
    assert "Stance" in system_prompt
    assert "Identity Activation" not in system_prompt.split("\n", 1)[0]


def test_aggregate_runs_reports_mean_and_stddev():
    runs = [
        {"detection_rate": 0.50}, {"detection_rate": 0.60},
        {"detection_rate": 0.55}, {"detection_rate": 0.52}, {"detection_rate": 0.58},
    ]
    agg = ab_harness.aggregate_runs(runs)
    assert agg["n"] == 5
    assert agg["mean_detection_rate"] == pytest.approx(0.55, abs=0.001)
    assert agg["stddev_pp"] > 0


def test_variants_load_strips_persona_names():
    persona_names = ("Judge", "Specialist", "Analyst", "Governor", "Technical Writer")
    for skill in ("qor-audit", "qor-substantiate"):
        stance = ab_harness.load_variant(skill, "stance", _CORPUS)
        for name in persona_names:
            assert name not in stance, f"{skill}.stance contains persona name {name!r}"


def test_variants_load_preserves_stance_modifier():
    audit_persona = ab_harness.load_variant("qor-audit", "persona", _CORPUS)
    audit_stance = ab_harness.load_variant("qor-audit", "stance", _CORPUS)
    # "adversarial" appears in both variants for qor-audit.
    assert "adversarial" in audit_persona
    assert "adversarial" in audit_stance


def test_ab_live_run_exits_clearly_without_api_key(monkeypatch, capsys):
    from qor.scripts import ab_live_run
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(SystemExit) as exc:
        ab_live_run._require_api_key()
    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in captured.err
