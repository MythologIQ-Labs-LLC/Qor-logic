from __future__ import annotations

import json

from qor.scripts import roadmap_cli


def _call(tmp_path, *args: str) -> int:
    return roadmap_cli.main(["--repo-root", str(tmp_path), *args])


def test_vertical_pilot_across_fresh_loads(tmp_path, capsys) -> None:
    assert _call(tmp_path, "init", "--roadmap", "demo", "--objective", "Ship pilot") == 0
    assert _call(
        tmp_path, "add-node", "--roadmap", "demo", "--id", "fact",
        "--kind", "fact", "--title", "Verify API", "--resolver", "/qor-research",
    ) == 0
    assert _call(
        tmp_path, "add-node", "--roadmap", "demo", "--id", "decision",
        "--kind", "decision", "--title", "Choose contract", "--resolver", "authority",
        "--authority-required", "operator",
    ) == 0
    assert _call(
        tmp_path, "add-dependency", "--roadmap", "demo",
        "--predecessor", "fact", "--dependent", "decision",
    ) == 0
    capsys.readouterr()

    assert _call(tmp_path, "frontier", "--roadmap", "demo", "--authority", "operator") == 0
    frontier = json.loads(capsys.readouterr().out)
    assert frontier["frontier"] == ["fact"]

    assert _call(
        tmp_path, "resolve", "--roadmap", "demo", "--node", "fact",
        "--evidence", "docs/research.md", "--rationale", "verified",
    ) == 0
    capsys.readouterr()
    assert _call(tmp_path, "frontier", "--roadmap", "demo", "--authority", "operator") == 0
    assert json.loads(capsys.readouterr().out)["frontier"] == ["decision"]

    assert _call(
        tmp_path, "resolve", "--roadmap", "demo", "--node", "decision",
        "--authority", "operator", "--rationale", "selected",
    ) == 0
    assert _call(
        tmp_path, "add-scope", "--roadmap", "demo", "--id", "pilot",
        "--title", "Pilot scope", "--node", "fact", "--node", "decision",
    ) == 0
    capsys.readouterr()

    predecessor = tmp_path / ".qor/gates/session/research.json"
    predecessor.parent.mkdir(parents=True)
    predecessor.write_text(json.dumps({"phase": "research"}), encoding="utf-8")
    assert _call(
        tmp_path, "handoff", "--roadmap", "demo", "--scope", "pilot",
        "--predecessor-phase", "research",
        "--predecessor-artifact", ".qor/gates/session/research.json",
    ) == 0
    handoff = json.loads(capsys.readouterr().out)
    assert handoff["legal_next"] == "/qor-plan"
    assert handoff["implementation_tasks"] == []
    assert handoff["settled_context"]["facts"][0]["evidence_pointers"] == ["docs/research.md"]


def test_handoff_fails_without_legal_predecessor(tmp_path, capsys) -> None:
    assert _call(tmp_path, "init", "--roadmap", "demo", "--objective", "Ship") == 0
    assert _call(
        tmp_path, "add-node", "--roadmap", "demo", "--id", "p",
        "--kind", "prerequisite", "--title", "Ready", "--resolver", "external",
    ) == 0
    assert _call(
        tmp_path, "resolve", "--roadmap", "demo", "--node", "p", "--rationale", "done",
    ) == 0
    assert _call(
        tmp_path, "add-scope", "--roadmap", "demo", "--id", "pilot",
        "--title", "Pilot", "--node", "p",
    ) == 0
    capsys.readouterr()
    assert _call(
        tmp_path, "handoff", "--roadmap", "demo", "--scope", "pilot",
        "--predecessor-phase", "research",
        "--predecessor-artifact", ".qor/gates/missing/research.json",
    ) == 2
    assert "predecessor artifact not found" in capsys.readouterr().out


def test_handoff_fails_while_scope_blocked(tmp_path, capsys) -> None:
    assert _call(tmp_path, "init", "--roadmap", "demo", "--objective", "Ship") == 0
    assert _call(
        tmp_path, "add-node", "--roadmap", "demo", "--id", "fact",
        "--kind", "fact", "--title", "Fact", "--resolver", "/qor-research",
    ) == 0
    assert _call(
        tmp_path, "add-scope", "--roadmap", "demo", "--id", "pilot",
        "--title", "Pilot", "--node", "fact",
    ) == 0
    predecessor = tmp_path / ".qor/gates/session/research.json"
    predecessor.parent.mkdir(parents=True)
    predecessor.write_text(json.dumps({"phase": "research"}), encoding="utf-8")
    capsys.readouterr()
    assert _call(
        tmp_path, "handoff", "--roadmap", "demo", "--scope", "pilot",
        "--predecessor-phase", "research",
        "--predecessor-artifact", ".qor/gates/session/research.json",
    ) == 2
    assert "planning scope is not ready" in capsys.readouterr().out
