"""Phase 58: SYSTEM_STATE.md drift-prevention test.

Forward-only enforcement: every META_LEDGER `Phase N feature substantiated`
entry must have a corresponding `## Phase N (vX.Y.Z)` heading in
docs/SYSTEM_STATE.md. Pre-Phase-58 phases are grandfathered explicitly.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "docs" / "META_LEDGER.md"
SYSTEM_STATE = REPO_ROOT / "docs" / "SYSTEM_STATE.md"

# Phases that have no SESSION SEAL entry in META_LEDGER (skipped/absorbed):
# 42, 43, 44 — Phase 41 + 45 covered the same surface
# 51 — incremental Phase 52 absorbed the planned scope
# Plus any historical gap that explicit ledger inspection confirms is no-seal.
_NO_SEAL_PHASES: frozenset[int] = frozenset({42, 43, 44, 51})


def _sealed_phases_from_ledger() -> set[int]:
    text = LEDGER.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^### Entry #\d+: SESSION SEAL -- Phase (\d+) feature substantiated",
        re.MULTILINE,
    )
    return {int(m.group(1)) for m in pattern.finditer(text)}


def _phases_in_system_state() -> set[int]:
    text = SYSTEM_STATE.read_text(encoding="utf-8")
    # Match `## Phase N` or `## Phase Nb` (letter-suffix variants treated as N)
    pattern = re.compile(r"^## Phase (\d+)b?\s*\(", re.MULTILINE)
    return {int(m.group(1)) for m in pattern.finditer(text)}


def test_every_sealed_phase_has_system_state_entry():
    sealed = _sealed_phases_from_ledger()
    in_state = _phases_in_system_state()
    missing = sorted(sealed - in_state)
    assert not missing, (
        f"Sealed phases without SYSTEM_STATE.md entry: {missing}. "
        f"Either backfill the entry or add the phase to _NO_SEAL_PHASES "
        f"if it has no SESSION SEAL ledger entry."
    )


def test_no_seal_phases_are_documented():
    """The _NO_SEAL_PHASES set must contain only phases that genuinely
    lack a SESSION SEAL entry. This test asserts that no member of
    _NO_SEAL_PHASES has a seal entry (otherwise it would belong in the
    drift-prevention check above)."""
    sealed = _sealed_phases_from_ledger()
    spurious = sorted(_NO_SEAL_PHASES & sealed)
    assert not spurious, (
        f"Phases in _NO_SEAL_PHASES that actually have SESSION SEAL entries: "
        f"{spurious}. Remove them from _NO_SEAL_PHASES."
    )


def test_system_state_phase_57_entry_present_after_phase_57_seal():
    """Regression sanity: Phase 57 entry must exist (added during Phase 57
    substantiate). Confirms backfill was actually applied."""
    text = SYSTEM_STATE.read_text(encoding="utf-8")
    assert re.search(r"^## Phase 57\s*\(", text, re.MULTILINE), \
        "Phase 57 SYSTEM_STATE.md entry missing"
