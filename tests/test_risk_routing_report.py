"""Phase 58 risk routing tests."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import jsonschema

from qor.capabilities.risk import RiskRoutingReport, route_risk


SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "risk_routing.schema.json"
)


def test_route_risk_substantiate_changes_to_hash_integrity_and_l3():
    r = route_risk(".", ("qor/skills/governance/qor-substantiate/SKILL.md",))
    assert "hash-integrity" in r.required_skills
    assert "ledger-verify" in r.required_skills
    assert r.risk_grade == "L3"


def test_route_risk_ledger_changes_to_federated_ledger_checks():
    r = route_risk(".", ("docs/META_LEDGER.md", "qor/scripts/ledger_fragment.py"))
    assert "federated-ledger-fragments" in r.required_skills


def test_route_risk_implement_skill_changes_to_documentation_lifecycle():
    r = route_risk(".", ("qor/skills/sdlc/qor-implement/SKILL.md",))
    assert "documentation-touches" in r.required_skills


def test_route_risk_dependency_changes_to_sdk_alignment():
    r = route_risk(".", ("pyproject.toml",))
    assert "sdk-alignment" in r.required_skills


def test_route_risk_unmatched_file_defaults_to_audit_tribunal():
    r = route_risk(".", ("random/path/x.txt",))
    assert "audit-tribunal" in r.required_skills
    assert r.risk_grade == "L1"


def test_route_risk_empty_changed_files_returns_l1():
    r = route_risk(".", ())
    assert r.risk_grade == "L1"


def test_route_risk_aggregates_to_highest_grade():
    r = route_risk(".", (
        "qor/skills/sdlc/qor-implement/SKILL.md",  # L2
        "qor/scripts/ledger_hash.py",              # L3
    ))
    assert r.risk_grade == "L3"


def test_route_risk_report_schema_accepts_output():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    r = route_risk(".", ("pyproject.toml",))
    payload = json.loads(json.dumps(asdict(r)))  # tuples -> lists
    jsonschema.validate(payload, schema)
