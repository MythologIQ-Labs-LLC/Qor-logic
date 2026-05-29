"""Behavioral tests for the governance-health checker (Phase 109, D-109.1).

Each test exercises ``check_governance_health`` against a synthetic workspace
and asserts on the returned ``ArtifactFinding`` status + legal_next, so a
silently-broken classifier fails the test (not mere artifact presence).
"""
from __future__ import annotations

from qor.scripts.governance_health import (
    ArtifactStatus,
    SCAFFOLD_OWNED,
    check_governance_health,
)


def _find(findings, path):
    return next(f for f in findings if f.path == path)


def _init_ledger(tmp_path, body="# QoreLogic Meta Ledger\n\nGenesis 2026-01-01. Chain Status ACTIVE.\n"):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "META_LEDGER.md").write_text(body, encoding="utf-8")
    return docs


def test_uninitialized_workspace_returns_bootstrap_next(tmp_path):
    findings = check_governance_health(tmp_path)
    led = _find(findings, "docs/META_LEDGER.md")
    assert led.status is ArtifactStatus.UNINITIALIZED
    assert "/qor-bootstrap" in led.legal_next


def test_missing_required_artifact_in_initialized_workspace_blocks(tmp_path):
    _init_ledger(tmp_path)
    findings = check_governance_health(tmp_path)
    arch = _find(findings, "docs/ARCHITECTURE_PLAN.md")
    assert arch.status is ArtifactStatus.MISSING
    assert arch.status is not ArtifactStatus.UNINITIALIZED


def test_damaged_ledger_blocks_seed_repair(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text("%%% not a ledger %%%\nrandom garbage\n", encoding="utf-8")
    findings = check_governance_health(tmp_path)
    led = _find(findings, "docs/META_LEDGER.md")
    assert led.status is ArtifactStatus.DAMAGED
    assert "/qor-remediate" in led.legal_next
    assert "never seeded" in led.legal_next.lower()


def test_placeholder_artifact_is_incomplete(tmp_path):
    _init_ledger(tmp_path)
    docs = tmp_path / "docs"
    (docs / "CONCEPT.md").write_text("# Project Concept\n\nTODO: write the why.\n", encoding="utf-8")
    findings = check_governance_health(tmp_path)
    concept = _find(findings, "docs/CONCEPT.md")
    assert concept.status is ArtifactStatus.INCOMPLETE


def test_healthy_seeded_and_completed_workspace_returns_ok(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    content = {
        "META_LEDGER.md": "# QoreLogic Meta Ledger\n\nGenesis 2026-01-01. Chain Status ACTIVE.\n",
        "CONCEPT.md": "# Project Concept\n\nWhy: ship governed software safely.\n",
        "ARCHITECTURE_PLAN.md": "# Architecture Plan\n\nRisk Grade L2. Modules: cli, scripts.\n",
        "SYSTEM_STATE.md": "# System State\n\nCurrent governance surfaces documented here.\n",
        "SHADOW_GENOME.md": "# Shadow Genome\n\nNo open failures recorded.\n",
        "BACKLOG.md": "# Backlog\n\nNo open blockers.\n",
        "FEATURE_INDEX.md": "# Feature Index\n\nNo user-facing features yet.\n",
    }
    for name, body in content.items():
        (docs / name).write_text(body, encoding="utf-8")
    findings = check_governance_health(tmp_path)
    offenders = [(f.path, f.status.value, f.reason) for f in findings if f.status is not ArtifactStatus.OK]
    assert offenders == []


def test_active_ledger_with_narrative_markers_is_ok(tmp_path):
    """A sealed ledger legitimately mentions grounding tags like ``{{verify}}``
    inside historical entries; the checker must not read those as live
    placeholders and flag the active ledger INCOMPLETE."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(
        "# QoreLogic Meta Ledger\n\n"
        "### Entry #1: SEAL\n\n"
        "Decision: closed a `{{verify: upstream}}` residual tag. TODO markers "
        "from the old plan were resolved.\n",
        encoding="utf-8",
    )
    led = _find(check_governance_health(tmp_path), "docs/META_LEDGER.md")
    assert led.status is ArtifactStatus.OK, (led.status.value, led.reason)


def test_bare_scaffold_ledger_is_incomplete(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(
        "# QoreLogic Meta Ledger\n\n## Chain Metadata\n\n| Genesis | [ISO 8601 timestamp] |\n",
        encoding="utf-8",
    )
    led = _find(check_governance_health(tmp_path), "docs/META_LEDGER.md")
    assert led.status is ArtifactStatus.INCOMPLETE
    assert "never seeded" in led.legal_next.lower()


def test_scaffold_owned_set_pinned_to_seed_targets():
    """LD3: scaffold-owned (seed-repairable) set equals seed file targets, so the
    two lists cannot drift. If they diverge, a MISSING artifact could be routed
    to seed when seed does not own it (or vice versa)."""
    from qor.seed import SEED_TARGETS

    seed_files = frozenset(t.rel_path for t in SEED_TARGETS if t.mode == "file")
    assert SCAFFOLD_OWNED == seed_files
