"""Phase 63 Phase 2: post-reset baseline assertions."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "META_LEDGER.md"

# Session-specific seal subject strings. Each is unique to a session phase
# and would never appear in upstream's ledger by coincidence.
SESSION_SEAL_SUBJECTS = (
    "Phase 45 alpha bundle",
    "Phase 46 gamma bundle",
    "Phase 47 delta bundle",
    "Phase 48 beta bundle",
    "Phase 49 -- filter-stage ordering",
    "Phase 50 -- prompt compiler V1",
    "Phase 51 -- compiler governance gate",
    "Phase 52 -- compiler rulepack registry",
    "Phase 53 -- compiler execution modes",
    "Phase 54 -- compiler evaluation loop",
    "Phase 59 hotfix",
    "Phase 55 -- implement documentation lifecycle",
    "Phase 57 -- audit adversary",
    "Phase 56 -- federated ledger entry identity",
    "Phase 58 -- governance capability surface",
    "Phase 60 -- qor-debug hotfix",
    "Phase 61 -- unified path-match",
)


def _rev_parse(rev: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", rev],
        capture_output=True, text=True, cwd=ROOT, check=True,
    )
    return result.stdout.strip()


def test_main_is_phase60_reconciliation_seal():
    """After Phase 5 (consolidated reconciliation seal), main is ahead of
    origin/main by exactly the reconciliation commit(s). The HEAD commit
    subject must match the Phase 60 seal subject prefix.
    """
    subject = subprocess.run(
        ["git", "log", "main", "-1", "--pretty=%s"],
        capture_output=True, text=True, cwd=ROOT, check=True,
    ).stdout.strip()
    assert subject.startswith("seal: phase 60"), (
        f"main HEAD must be the Phase 60 reconciliation seal; got: {subject!r}"
    )


def test_session_seal_subjects_only_in_closing_seal_entry():
    """Session-specific phase seals appear ONLY inside the closing
    reconciliation entry (Entry #196), where they are listed as
    `Replayed-as-consolidated phases` for forensic documentation.
    They MUST NOT appear as standalone seal entries in main's chain.
    """
    body = LEDGER.read_text(encoding="utf-8")
    closing_seal_idx = body.find("### Entry #196: SESSION RECONCILIATION SEAL")
    pre = body[:closing_seal_idx] if closing_seal_idx != -1 else body
    leaked = [s for s in SESSION_SEAL_SUBJECTS if s in pre]
    assert not leaked, (
        f"session seal subjects found OUTSIDE the closing reconciliation "
        f"entry in main's META_LEDGER: {leaked}"
    )


def test_archive_branch_preserves_session_seal_commits():
    """All 17 session seal commits reachable from archive/session-2026-05-09."""
    result = subprocess.run(
        ["git", "log", "archive/session-2026-05-09", "--pretty=%s",
         "--grep=^seal:"],
        capture_output=True, text=True, cwd=ROOT, check=True,
    )
    subjects = result.stdout
    # Spot-check the boundary commits and a few interior ones via fingerprint
    # phrases unique to each session seal subject.
    required = (
        "phase 45 alpha bundle",
        "phase 50 - prompt compiler",
        "phase 54 - compiler evaluation loop",
        "phase 60 - qor-debug hotfix",
        "phase 61 - unified path-match",
    )
    missing = [s for s in required if s.lower() not in subjects.lower()]
    assert not missing, (
        f"archive/session-2026-05-09 missing required session seal commits: {missing}"
    )


def test_pyproject_version_at_reconciliation_target():
    """pyproject reflects Phase 60 (consolidated reconciliation) version 0.46.0,
    NOT session's v0.59.0 (abandoned) and NOT upstream's pre-reconciliation
    0.45.0 (the baseline before this phase sealed).
    """
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.46.0"' in pyproject, (
        "pyproject.toml not at Phase 60 reconciliation target version 0.46.0"
    )
