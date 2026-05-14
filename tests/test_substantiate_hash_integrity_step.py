"""Phase 64 (#48): substantiate SKILL.md Step 6.8 wiring tests.

Locks the prose contract for the Seal Hash Integrity Gate. These tests do
NOT execute the skill at runtime (LLM-driven skill behavior cannot be
asserted from a pytest harness). Instead they assert the canonical SKILL.md
prose carries the binding instructions an LLM operator would follow:

1. Step 6.8 exists with its canonical heading.
2. Step 6.8 invokes both `require_toolkit_modules` and `validate_sha256`.
3. Step 6.8 precedes Step 7 (Final Merkle Seal) in document order.
4. The abort-semantics sentence binds ABORT to the failure clause.
5. All four ledger hash fields (merkle_seal, content_hash, previous_hash,
   chain_hash) appear as `validate_sha256` arguments.

Acceptance question: "If the unit's behavior were silently broken but the
artifact still existed, would this test fail?" - yes. Removing the call
sites, reordering, weakening abort semantics, or dropping a hash field
each fail at least one of these tests.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_PATH = Path("qor/skills/governance/qor-substantiate/SKILL.md")
STEP_6_8_HEADING = "### Step 6.8: Seal Hash Integrity Gate"
STEP_7_HEADING = "### Step 7: Final Merkle Seal"


def _read_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _extract_step_6_8_body(text: str) -> str:
    """Return the body between the Step 6.8 heading and the next `### ` heading."""
    start = text.find(STEP_6_8_HEADING)
    if start < 0:
        return ""
    after_heading = text.index("\n", start) + 1
    next_heading = text.find("\n### ", after_heading)
    if next_heading < 0:
        return text[after_heading:]
    return text[after_heading:next_heading]


def test_substantiate_skill_has_seal_hash_integrity_gate():
    text = _read_skill()
    body = _extract_step_6_8_body(text)
    assert body, f"Step 6.8 heading {STEP_6_8_HEADING!r} not found in {SKILL_PATH}"
    assert "require_toolkit_modules" in body, (
        "Step 6.8 must invoke require_toolkit_modules to fail closed on missing toolkit"
    )
    assert "validate_sha256" in body, (
        "Step 6.8 must invoke validate_sha256 to reject fabricated hash strings"
    )


def test_hash_gate_precedes_final_merkle_seal():
    text = _read_skill()
    pos_6_8 = text.find(STEP_6_8_HEADING)
    pos_7 = text.find(STEP_7_HEADING)
    assert pos_6_8 >= 0, f"Step 6.8 heading {STEP_6_8_HEADING!r} missing"
    assert pos_7 >= 0, f"Step 7 heading {STEP_7_HEADING!r} missing"
    assert pos_6_8 < pos_7, (
        f"Step 6.8 (offset {pos_6_8}) must precede Step 7 (offset {pos_7}); "
        "validating after seal commits the very fabricated hashes the gate guards"
    )


_FAILURE_CONDITION_TOKENS = (
    "missing toolkit",
    "ValueError",
    "RuntimeError",
    "invalid hash",
)


def _split_sentences(text: str) -> list[str]:
    """Split prose text on sentence-terminating periods.

    Strips fenced code blocks first so '`module.func()`' periods do not
    fragment a sentence. The skill prose mixes code fences with narrative;
    only narrative sentences are inspected for the abort-semantics binding.
    """
    stripped = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return [s.strip() for s in stripped.split(".") if s.strip()]


def test_hash_gate_abort_co_occurs_with_toolkit_failure_clause():
    text = _read_skill()
    body = _extract_step_6_8_body(text)
    sentences = _split_sentences(body)
    matching = [
        s for s in sentences
        if any(tok in s for tok in _FAILURE_CONDITION_TOKENS)
    ]
    assert matching, (
        "Step 6.8 prose must name at least one failure condition "
        f"(any of {_FAILURE_CONDITION_TOKENS})"
    )
    for sentence in matching:
        assert "ABORT" in sentence, (
            f"failure-condition sentence must bind ABORT: {sentence!r}"
        )
        lowered = sentence.lower()
        assert "skip" not in lowered, (
            f"abort sentence must not also describe skip semantics: {sentence!r}"
        )
        assert "warn" not in lowered, (
            f"abort sentence must not also describe warn semantics: {sentence!r}"
        )


_HASH_LABELS = ("merkle_seal", "content_hash", "previous_hash", "chain_hash")


def test_hash_gate_mentions_all_ledger_hash_fields():
    text = _read_skill()
    body = _extract_step_6_8_body(text)
    missing = [label for label in _HASH_LABELS if label not in body]
    assert not missing, (
        f"Step 6.8 must pass all four hash labels to validate_sha256; "
        f"missing: {missing}"
    )
    for label in _HASH_LABELS:
        pattern = rf"validate_sha256\([^)]*\blabel\s*=\s*[\"']{re.escape(label)}[\"']"
        assert re.search(pattern, body), (
            f"label '{label}' must be passed as the label keyword argument "
            "of validate_sha256, not just mentioned in prose"
        )


_PREP_HELPERS = (
    "hash_guard.hash_file",
    "ledger_hash.content_hash",
    "ledger_hash.chain_hash",
)


def test_hash_gate_preparation_names_canonical_helpers():
    """The Preparation prose must cite the helpers an operator uses to compute
    real digests, so the four hash variables exist before the validation block
    runs. Without this guidance the gate validates undefined variables and
    Step 6.8 becomes order-dependent dead code."""
    text = _read_skill()
    body = _extract_step_6_8_body(text)
    assert "Preparation" in body or "preparation" in body.lower(), (
        "Step 6.8 must include a Preparation paragraph telling the operator "
        "to compute the four hashes before validation"
    )
    missing = [helper for helper in _PREP_HELPERS if helper not in body]
    assert not missing, (
        f"Step 6.8 Preparation must name canonical hash-producing helpers; "
        f"missing: {missing}"
    )
