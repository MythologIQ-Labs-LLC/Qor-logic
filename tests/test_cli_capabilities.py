"""Phase 58 CLI capabilities tests."""
from __future__ import annotations

import json

import pytest

from qor.cli import main as cli_main


def test_cli_capabilities_inventory_prints_json(capsys):
    rc = cli_main(["capabilities", "inventory"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    ids = {row["id"] for row in data}
    assert "hash-integrity" in ids
    assert "audit-tribunal" in ids


def test_cli_capabilities_context_prints_json(capsys):
    rc = cli_main(["capabilities", "context", "--target", "docs/plan-x.md"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["target"] == "docs/plan-x.md"
    assert "doctrines" in payload
    assert "recommended_checks" in payload


def test_cli_capabilities_route_risk_accepts_multiple_files(capsys):
    rc = cli_main([
        "capabilities", "route-risk",
        "--changed-file", "qor/skills/governance/qor-substantiate/SKILL.md",
        "--changed-file", "pyproject.toml",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["risk_grade"] == "L3"
    assert "hash-integrity" in payload["required_skills"]
    assert "sdk-alignment" in payload["required_skills"]


def test_cli_capabilities_verification_request_prints_json(capsys):
    rc = cli_main([
        "capabilities", "verification-request",
        "--target", "docs/plan-x.md",
        "--confidence", "targeted",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["target"] == "docs/plan-x.md"
    assert payload["required_confidence"] == "targeted"
    assert "context_packet" in payload
    assert "risk_routing" in payload


def test_cli_capabilities_verification_request_write_gate_is_opt_in(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = cli_main([
        "capabilities", "verification-request",
        "--target", "docs/plan-x.md",
        "--write-gate",
    ])
    assert rc == 0
    expected = tmp_path / ".qor" / "gates" / "verification-requests" / "docs_plan-x_md.json"
    assert expected.exists()


def test_cli_capabilities_verification_request_default_does_not_write_gate(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = cli_main([
        "capabilities", "verification-request",
        "--target", "docs/plan-x.md",
    ])
    assert rc == 0
    assert not (tmp_path / ".qor" / "gates" / "verification-requests").exists()
