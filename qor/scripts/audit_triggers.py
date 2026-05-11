"""Phase 61: structured trigger list for `/qor-audit` adversarial-mode.

Source of truth for which plans require independent-reviewer counter-review.
The prose enumeration in `qor/skills/governance/qor-audit/references/adversarial-mode.md`
MUST stay in sync; `tests/test_adversarial_mode_trigger_crossref.py` enforces.

Use ``matches_any_trigger(changed_files)`` to obtain the list of triggers that
fire for a given file set. An empty result means the audit may proceed solo
(L1 plans without a capability shortfall).
"""
from __future__ import annotations

from dataclasses import dataclass

from qor.scripts.path_match import matches_any


@dataclass(frozen=True)
class AdversarialTrigger:
    label: str
    prefixes: tuple[str, ...]
    reason: str


ADVERSARIAL_REVIEW_TRIGGERS: tuple[AdversarialTrigger, ...] = (
    AdversarialTrigger(
        label="governance-skills",
        prefixes=("qor/skills/governance/",),
        reason="L2/L3 audit surface; any change touches the gate ceremony itself",
    ),
    AdversarialTrigger(
        label="ledger",
        prefixes=(
            "docs/META_LEDGER.md",
            "qor/scripts/ledger_hash",
            "qor/scripts/ledger_fragment",
            "qor/scripts/ledger_entry_id",
            "qor/scripts/hash_guard",
        ),
        reason="chain-integrity surface; fabricated/regressed hashes invalidate the seal",
    ),
    AdversarialTrigger(
        label="schemas",
        prefixes=("qor/gates/schema/",),
        reason="gate-contract changes propagate to every downstream consumer",
    ),
    AdversarialTrigger(
        label="substantiate-core",
        prefixes=("qor/skills/governance/qor-substantiate/",),
        reason="seal ceremony; bypass surfaces aggregate here",
    ),
    AdversarialTrigger(
        label="audit-core",
        prefixes=("qor/skills/governance/qor-audit/",),
        reason="audit ceremony itself; meta-changes warrant counter-review",
    ),
)


def matches_any_trigger(changed_files: tuple[str, ...]) -> tuple[AdversarialTrigger, ...]:
    """Return triggers whose prefixes match at least one changed file."""
    fired: list[AdversarialTrigger] = []
    for trigger in ADVERSARIAL_REVIEW_TRIGGERS:
        for path in changed_files:
            if matches_any(path, trigger.prefixes):
                fired.append(trigger)
                break
    return tuple(fired)


def requires_adversarial_review(changed_files: tuple[str, ...]) -> bool:
    """Convenience: True iff any trigger fires for the file set."""
    return bool(matches_any_trigger(changed_files))
