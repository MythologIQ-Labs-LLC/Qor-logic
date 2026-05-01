"""Phase 54: AI provenance helper tests."""
from __future__ import annotations

import os

import pytest

from qor.scripts import ai_provenance, validate_gate_artifact as vga
from qor.scripts.ai_provenance import HumanOversight


def _is_iso_utc(ts: str) -> bool:
    return len(ts) == 20 and ts.endswith("Z") and ts[10] == "T"


def test_build_manifest_returns_schema_valid_dict():
    manifest = ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="claude-opus-4-7",
        human_oversight=HumanOversight.PASS,
    )
    assert manifest["system"] == "Qor-logic"
    assert manifest["host"] == "claude-code"
    assert manifest["model_family"] == "claude-opus-4-7"
    assert manifest["human_oversight"] == "pass"
    assert _is_iso_utc(manifest["ts"])
    payload = {
        "phase": "audit", "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-sess", "target": "p.md", "verdict": "PASS",
        "ai_provenance": manifest,
    }
    assert vga._validate_data("audit", payload) == []


def test_build_manifest_reads_system_version_from_pyproject():
    manifest = ai_provenance.build_manifest(
        "audit", host="x", model_family="y",
        human_oversight=HumanOversight.PASS,
    )
    pyproject_version = ai_provenance._read_system_version()
    assert manifest["version"] == pyproject_version
    assert pyproject_version != "unknown", "pyproject.toml must declare version"


@pytest.mark.parametrize("phase", ["audit", "substantiate", "validate"])
def test_build_manifest_rejects_invalid_human_oversight_for_decision_phase(phase):
    with pytest.raises(ValueError, match="absent"):
        ai_provenance.build_manifest(
            phase, host="x", model_family="y",
            human_oversight=HumanOversight.ABSENT,
        )


@pytest.mark.parametrize("phase", ["research", "plan", "implement"])
def test_build_manifest_rejects_pass_for_non_decision_phase(phase):
    with pytest.raises(ValueError):
        ai_provenance.build_manifest(
            phase, host="x", model_family="y",
            human_oversight=HumanOversight.PASS,
        )


@pytest.mark.parametrize("phase,oversight", [
    ("audit", HumanOversight.PASS),
    ("audit", HumanOversight.VETO),
    ("audit", HumanOversight.OVERRIDE),
    ("substantiate", HumanOversight.PASS),
    ("validate", HumanOversight.PASS),
    ("research", HumanOversight.ABSENT),
    ("plan", HumanOversight.ABSENT),
    ("implement", HumanOversight.ABSENT),
    ("research", HumanOversight.OVERRIDE),
])
def test_build_manifest_accepts_valid_phase_oversight_combinations(phase, oversight):
    manifest = ai_provenance.build_manifest(
        phase, host="x", model_family="y", human_oversight=oversight,
    )
    assert manifest["human_oversight"] == oversight.value


def test_build_manifest_warns_once_on_missing_host(monkeypatch, capsys):
    # Force fallback by clearing detect path and warning state.
    monkeypatch.setattr(ai_provenance, "_detect_host", lambda: "unknown")
    monkeypatch.delenv(ai_provenance._QUIET_ENV, raising=False)
    ai_provenance._warned_keys.clear()

    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    out_first = capsys.readouterr().err
    assert "host fell back" in out_first

    # Second call same process: no duplicate warn
    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    out_second = capsys.readouterr().err
    assert "host fell back" not in out_second


def test_build_manifest_warning_suppressible_by_env(monkeypatch, capsys):
    monkeypatch.setattr(ai_provenance, "_detect_host", lambda: "unknown")
    monkeypatch.setenv(ai_provenance._QUIET_ENV, "1")
    ai_provenance._warned_keys.clear()

    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    err = capsys.readouterr().err
    assert "host fell back" not in err


def test_build_manifest_reads_model_family_from_env(monkeypatch):
    monkeypatch.setenv(ai_provenance._MODEL_ENV, "claude-sonnet-4-6")
    manifest = ai_provenance.build_manifest(
        "audit", host="x", human_oversight=HumanOversight.PASS,
    )
    assert manifest["model_family"] == "claude-sonnet-4-6"


def test_build_manifest_falls_back_to_unknown_model_when_env_unset(monkeypatch):
    monkeypatch.delenv(ai_provenance._MODEL_ENV, raising=False)
    monkeypatch.setenv(ai_provenance._QUIET_ENV, "1")
    manifest = ai_provenance.build_manifest(
        "audit", host="x", human_oversight=HumanOversight.PASS,
    )
    assert manifest["model_family"] == "unknown"
