"""Phase 49/164/224: seal-artifact wiring lock for /qor-substantiate.

Skill prose has no invokable unit; the behavioral coverage lives in
tests/test_seal_artifacts.py and tests/test_seal_artifacts_ordering.py. What is
locked here is the one property those cannot express: WHERE the generate/check
pair sits in the ceremony.

Phase 224 (GH #334) moved the pair out of Steps 6 / 6.5 into Step 7.7.5. The
superseded form of this file pinned it to Steps 6 and 6.5 -- the defective
order -- so eight phases of green did not mean the sequence was right. The
assertions below carry both bounds, because a lower bound alone is satisfied by
any later placement, including one past the staging block where the regenerated
README would miss the commit entirely.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def _read() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_seal_artifact_regeneration_follows_the_step_that_verifies_the_entry_exists():
    # prose-lint: ok=wiring regression lock; step ordering has no invokable unit
    text = _read()
    write = re.search(r"seal_artifacts --write --phase", text)
    step_7_7 = re.search(r"^### Step 7\.7:", text, re.MULTILINE)
    staging = re.search(r"^  git add CHANGELOG\.md", text, re.MULTILINE)

    assert write, "Step 7.7.5 must regenerate via 'seal_artifacts --write --phase ...'"
    assert step_7_7 and staging, "Step 7.7 and the staging block must both be present"

    # Lower bound: Step 7.7 is the first step that asserts the appended SESSION
    # SEAL entry exists. Steps 7.4/7.5 are numbered later but run earlier -- they
    # produce content the entry carries -- so an assertion against '### Step 7:'
    # would have accepted the pre-append placement this phase removed.
    assert write.start() > step_7_7.start(), (
        "seal_artifacts --write must follow Step 7.7, which verifies the appended "
        "entry exists; earlier placements regenerate the ledger badge before the "
        "entry it counts"
    )
    # Upper bound: the regenerated README has to reach the seal commit.
    assert write.start() < staging.start(), (
        "seal_artifacts --write must precede the staging block, or the regenerated "
        "artifacts never enter the seal commit"
    )


def test_step_7_7_5_retains_abort_and_the_hotfix_exemption():
    # prose-lint: ok=wiring regression lock; gate semantics carried across a move
    text = _read()
    start = text.index("### Step 7.7.5:")
    region = text[start : text.index("### Step 7.8")]

    assert re.search(r"seal_artifacts --check", region), (
        "Step 7.7.5 must gate on 'seal_artifacts --check'"
    )
    assert re.search(r"ABORT", region), "Step 7.7.5 must retain ABORT semantics"
    assert re.search(r"hotfix exempt", region), (
        "Step 7.7.5 must retain the hotfix exemption"
    )


def test_step_6_no_longer_regenerates_seal_artifacts():
    # prose-lint: ok=wiring regression lock; guards against a duplicated write
    text = _read()
    step6 = text[text.index("### Step 6: Sync System State") : text.index("### Step 6.8")]

    assert "seal_artifacts" not in step6, (
        "Steps 6 and 6.5 must not invoke seal_artifacts; a surviving --write there "
        "regenerates from pre-append truth and masks the relocation"
    )
