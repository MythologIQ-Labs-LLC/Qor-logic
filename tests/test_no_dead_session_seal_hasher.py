"""Phase 151 (GAP-GOV-02): the dead placeholder session-seal hasher is gone.

`qor/scripts/calculate-session-seal.py` was a non-importable __main__ script
with a literal `previous_hash = "PREVIOUS_LEDGER_HASH"` placeholder; the audit
flagged it as misleading about how seals are computed. These guards keep it
(and any other placeholder hasher) out of the shipped script corpus.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / "qor" / "scripts"


def test_no_placeholder_hasher_in_scripts():
    offenders = []
    for py in _SCRIPTS.glob("*.py"):
        if "PREVIOUS_LEDGER_HASH" in py.read_text(encoding="utf-8"):
            offenders.append(py.name)
    assert not offenders, f"placeholder-hasher literal found in qor/scripts: {offenders}"


def test_calculate_session_seal_removed():
    assert not (_SCRIPTS / "calculate-session-seal.py").exists(), (
        "the dead placeholder hasher must be deleted"
    )


def test_substantiate_skill_does_not_cite_dead_hasher():
    skill = _REPO / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
    assert "calculate-session-seal" not in skill.read_text(encoding="utf-8"), (
        "the qor-substantiate skill must not point operators at the dead hasher"
    )
