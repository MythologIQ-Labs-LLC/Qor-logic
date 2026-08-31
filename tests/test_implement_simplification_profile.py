"""Phase 246 (GH #392, /qor-implement tranche): the changeset simplification
profile is wired as an invariant profile, not a nested ceremony."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENT = ROOT / "qor" / "skills" / "sdlc" / "qor-implement" / "SKILL.md"
SWEEP = ROOT / "qor" / "references" / "implementation-quality-sweep.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_profile_runs_after_verified_behavior_and_before_handoff():
    """The profile must sit between the complexity self-check and handoff so
    refinement happens on verified behavior; ordering, not mere presence."""
    text = _text(IMPLEMENT)
    self_check = text.index("### Step 9: Complexity Self-Check")
    profile = text.index("### Step 9.5: Changeset Simplification Profile")
    handoff = text.index("### Step 10: Handoff")
    assert self_check < profile < handoff


def test_profile_is_changeset_bounded_and_behavior_preserving():
    text = _text(IMPLEMENT)
    start = text.index("### Step 9.5: Changeset Simplification Profile")
    end = text.index("### Step 10: Handoff")
    section = text[start:end]
    assert "recently modified code only" in section  # prose-lint: ok=prose contract; the profile's changeset containment rule
    assert "unrelated legacy defects are reported, not modified" in section  # prose-lint: ok=prose contract; containment against opportunistic cleanup
    assert "gate every proposed refinement through" in section.lower()  # prose-lint: ok=prose contract; pins the Simplification Test as the GATE (the word "through" is what makes it a gate, not a mention)
    assert "behavior preservation is the invariant" in section  # prose-lint: ok=prose contract; GH #392 primary invariant carried into the profile
    assert "No justified refinement is a successful result" in section  # prose-lint: ok=prose contract; abstention-as-success carried into the profile


def test_profile_reuses_the_shared_protocol_without_nested_ceremony():
    """GH #392: the profile reuses the sweep's lenses by reference and forbids
    a nested /qor-refactor ceremony for routine changeset refinement, while
    the sweep's own /qor-implement prevention profile exists to be reused."""
    text = _text(IMPLEMENT)
    start = text.index("### Step 9.5: Changeset Simplification Profile")
    section = text[start:text.index("### Step 10: Handoff")]
    for lens in ("IQ-COMPLEX", "IQ-CONTEXT", "IQ-MAINTAIN"):
        assert lens in section
    assert "NOT a nested `/qor-refactor` ceremony" in section  # prose-lint: ok=prose contract; the anti-ceremonial-delegation rule from the delegation table
    assert "implementation-quality-sweep.md" in section  # prose-lint: ok=prose contract; binds the profile to the canonical protocol home
    sweep = _text(SWEEP)
    assert "### `/qor-implement` prevention profile" in sweep  # prose-lint: ok=prose contract; the profile this step implements must exist at its canonical home


def test_step9_routes_violations_through_the_gate_not_forced_decomposition():
    """Phase 246 audit F1: Step 9's pre-existing 'Apply: Automatic
    splitting/flattening' ran BEFORE the Step 9.5 gate and negated the
    primary invariant for the most common trigger class (Section 4
    breaches), contradicting /qor-refactor's Phase 245 contract and the
    delegation table's inline-enforcement anti-pattern."""
    text = _text(IMPLEMENT)
    assert "Apply: Automatic splitting/flattening" not in text
    start = text.index("### Step 9: Complexity Self-Check")
    section = text[start:text.index("### Step 9.5")]
    assert "Simplification Test" in section  # prose-lint: ok=prose contract; Step 9 must route into the gate rather than act unconditionally
    assert "NO REFACTOR REQUIRED" in section  # prose-lint: ok=prose contract; the abstention off-ramp must exist on the Step 9 path
    assert "/qor-refactor" in section  # prose-lint: ok=prose contract; bounded structural passes delegate per the table
