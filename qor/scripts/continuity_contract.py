"""Execution-continuity vocabulary owned by Qor-logic (Phase 216; GH #285).

Qor-logic routes on continuity evidence. It does not define the checkpoint,
reconstruction, or verification-receipt schemas -- those belong to the upstream
execution-continuity contract and are referenced here by version only.

The pin is asserted, not verified. This module records which contract version an
operator declares compatibility with; it cannot check that a received artifact
conforms to that version, because doing so would require holding the upstream
schema. Naming the ceiling is deliberate: a declaration that reads like a
guarantee while delivering an assertion is the failure shape catalogued in
GH #314.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qor.scripts import qorlogic_config

CONFIG_SECTION = "execution_continuity"

#: The complete set of keys Qor-logic owns in a plan's continuity declaration.
#: Closed by construction: anything outside this set is upstream vocabulary that
#: does not belong here.
QOR_OWNED_KEYS = frozenset({
    "contract_version",
    "base_revision",
    "target_revision",
    "successor_actor_classes",
    "checkpoint_points",
    "receipt_required",
})

REVISION_KEYS = ("base_revision", "target_revision")

#: Distinct from any existing status vocabulary. `skip` (Phase 75) means a gate
#: deliberately did not run and is acceptable to seal; `inconclusive` means the
#: gate ran and the environment denied it a conclusion, which routes to evidence
#: repair instead.
OUTCOMES = ("verified", "rejected", "inconclusive")


@dataclass(frozen=True)
class Finding:
    """One declaration defect, coded so callers can branch on the kind."""

    code: str
    detail: str


def load_pin(repo_root: Path | None) -> str | None:
    """Return the operator-declared contract version, or None if unpinned.

    Absence is a disclosed state rather than an error: a repository that does
    not use execution continuity has nothing to pin. Delegates all I/O and
    tolerance to ``qorlogic_config.load_section``.
    """
    section = qorlogic_config.load_section(repo_root, CONFIG_SECTION)
    version = section.get("contract_version")
    if isinstance(version, str) and version:
        return version
    return None
