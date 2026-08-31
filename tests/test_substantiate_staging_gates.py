"""Phase 176 (GH #262): the documented seal staging list must include the
sealed session's gate artifacts.

Step 7.8 and the required CI job (gate_chain_completeness) make the committed
`.qor/gates/<sid>/` files load-bearing for every sealed phase >= 52; a Step
9.5 block that omits them ships a seal whose CI completeness gate fails.
These are prose-contract tests: the SKILL.md block IS the operator-facing
procedure under test.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
VARIANTS = [
    REPO / "qor" / "dist" / "variants" / host / "skills" / "qor-substantiate" / "SKILL.md"
    for host in ("claude", "codex", "kilo-code")
]

EXCEEDED_BYTES = 40 * 1024  # mirrors qor/scripts/skill_size_budget_lint.py


def _step_9_5_bash(text: str) -> str:
    """The first fenced bash block inside the Step 9.5 section."""
    section = re.search(r"### Step 9\.5:.*?(?=\n### Step)", text, re.DOTALL)
    assert section, "Step 9.5 section not found"
    block = re.search(r"```bash\n(.*?)```", section.group(0), re.DOTALL)
    assert block, "Step 9.5 bash block not found"
    return block.group(1)


def test_step_9_5_invokes_seal_stage():
    # prose-lint: ok=Step 9.5's block IS the operator procedure under test.
    # Phase 229 (GH #337): the enumeration is replaced by the executable
    # ceremony; the gate-dir guarantee this test carried since Phase 176
    # (GH #262) now lives behaviorally in tests/test_seal_stage.py
    # (test_gate_directory_is_staged_for_the_session).
    bash = _step_9_5_bash(CANONICAL.read_text(encoding="utf-8"))
    assert "qor.scripts.seal_stage" in bash and "$SESSION_ID" in bash, (
        "Step 9.5 must invoke the executable staging ceremony with the "
        f"sealed session id; got: {bash!r}"
    )


GOVERNANCE_SKILLS = {
    "qor-audit": REPO / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md",
    "qor-substantiate": CANONICAL,
}
HEADROOM_BYTES = 39 * 1024  # Phase 178 (GH #266): keep >= 1 KB under EXCEEDED


@pytest.mark.parametrize("skill", sorted(GOVERNANCE_SKILLS), ids=str)
def test_governance_skills_keep_headroom(skill):
    # Phase 176 locked qor-substantiate under EXCEEDED (GH #262); Phase 178
    # (GH #266) tightens to a headroom bound for BOTH big governance skills so
    # a single wiring-paragraph addition can never block the next seal.
    size = os.path.getsize(GOVERNANCE_SKILLS[skill])
    assert size < HEADROOM_BYTES, (
        f"{skill} SKILL.md is {size} bytes; headroom bound {HEADROOM_BYTES} "
        f"(EXCEEDED at {EXCEEDED_BYTES}) -- run a progressive-disclosure pass"
    )


def test_ladder_rewrite_left_usable_slack():
    """Phase 222 (GH #327): the seal skill must have ROOM, not merely fit.

    Three phases each resolved a size breach under time pressure and each made
    the next one harder; the file reached 24 B of slack. A phase that frees 24
    more bytes has not addressed the issue, so the acceptance is a floor rather
    than a pass/fail on the bound above.

    Plan D4 declared 3,000 B; the rewrite achieved 2,783 B. The floor exists to
    unblock GH #286, which the same plan sized at ~1,600 B for this file, so the
    achieved slack clears the purpose by 74% while missing the round number.
    Three post-plan decisions spent the difference, each trading bytes for a
    property a gate demanded:

      +80 B  the audit's V2 remedy -- parse the ladder before executing it,
             without which `substantiate_gates` would be consumed only by tests
      +95 B  the Phase 75 capability cross-reference, restored after
             `test_qor_substantiate_capability_declarations` caught its loss
      ~40 B  per-row execution detail kept inline rather than relocated, because
             four retargeted guardrail tests read it from the Notes column

    Recorded as a variance in the seal entry rather than resolved by trimming
    content those tests depend on.
    """
    size = os.path.getsize(CANONICAL)
    slack = HEADROOM_BYTES - size
    assert slack >= 2700, (
        f"qor-substantiate is {size} B, leaving {slack} B under the "
        f"{HEADROOM_BYTES} B bound; the ladder rewrite must leave usable room"
    )


def test_audit_disclosure_pass_left_usable_slack():
    """Phase 357 (GH #357): qor-audit needs ROOM under HEADROOM_BYTES, not a
    razor's edge. Before this pass qor-audit sat 167 B under the 39,936 B
    bound (39,769 B) -- one wiring-paragraph addition away from re-tripping
    `test_governance_skills_keep_headroom`. A further progressive-disclosure
    trim (two already-duplicated Step 3 Infrastructure Alignment rationale
    paragraphs relocated to the already-cited `references/phase37-subpasses.md`,
    zero spine tokens touched, including the SG-CitationDrift-A / diff-vs-full-
    rewalk contrast `test_qor_audit_full_citation_rewalk.py` locks) recovers
    real headroom rather than merely re-squeaking under the same ceiling.
    """
    size = os.path.getsize(GOVERNANCE_SKILLS["qor-audit"])
    slack = HEADROOM_BYTES - size
    assert slack >= 600, (
        f"qor-audit is {size} B, leaving {slack} B under the {HEADROOM_BYTES} "
        f"B bound; the disclosure pass must leave usable room, not a razor's edge"
    )


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda p: p.parts[-4])
def test_variants_match_canonical_step_9_5(variant):
    # prose-lint: ok=variant-vs-canonical equality of the same operator
    # procedure block; regression lock on dist regeneration.
    canonical_block = _step_9_5_bash(CANONICAL.read_text(encoding="utf-8"))
    variant_block = _step_9_5_bash(variant.read_text(encoding="utf-8"))
    assert variant_block == canonical_block
