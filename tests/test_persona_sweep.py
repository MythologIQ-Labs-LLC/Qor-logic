"""Persona sweep enforcement (Phase 39b Phase 2).

Asserts the doctrine-context-discipline.md §5 verification protocol: every
`<persona>` tag in `qor/skills/**/SKILL.md` must either carry a
`<persona-evidence>` pointer line or a `<persona-pending>` placeholder
marking it as awaiting measurement, OR belong to the doctrine-registered
load-bearing list below.

Also enforces R3 conditional rewrite (Identity Activation): if
`docs/phase39-ab-results.md` exists and declares winner="stance" for a
stance-critical skill, that skill's body must not contain the persona-named
"You are now operating as" opener.
"""
from __future__ import annotations

import pathlib
import re


_SKILLS_ROOT = pathlib.Path("qor/skills")
_RESULTS = pathlib.Path("docs/phase39-ab-results.md")

# Skills that have been affirmatively evaluated as load-bearing by doctrine
# judgment pending A/B evidence. Governor-curated; entries here document that
# a persona is retained as a context-prioritization scaffold for edge-case
# determinations AND is currently awaiting A/B evidence.
#
# Once A/B evidence lands in docs/phase39-ab-results.md, the corresponding
# skills should gain a <persona-evidence> pointer in their SKILL.md and be
# removed from this list.
LOAD_BEARING_PENDING_EVIDENCE = {
    "qor-audit",             # adversarial stance; target of Phase 39 A/B
    "qor-substantiate",      # prove-not-improve stance; target of Phase 39 A/B
    "qor-validate",          # judicial/verification stance
    "qor-plan",              # governance-authoring stance (Simple Made Easy)
    "qor-implement",         # precision-build specialist
    "qor-refactor",          # precision structural changes
    "qor-debug",             # systematic root-cause diagnostician
    "qor-research",          # analyst stance
    "qor-remediate",         # process-level governor
    "qor-organize",          # topology specialist
    "qor-tone",              # tone-selection stance
    "qor-shadow-process",    # event-recording stance
    "qor-process-review-cycle",  # adversarial audit of cycles
    "qor-deep-audit",            # deep-audit persona
    "qor-deep-audit-recon",      # recon persona
    "qor-deep-audit-remediate",  # remediate persona
    "qor-onboard-codebase",      # onboarding specialist
    "qor-repo-audit",            # repo-level auditor
    "qor-repo-release",          # release engineer
}


def _skill_files():
    return sorted(_SKILLS_ROOT.rglob("SKILL.md"))


def _skill_name(path: pathlib.Path) -> str:
    return path.parent.name


def _has_persona_tag(text: str) -> bool:
    return bool(re.search(r"<persona>[^<]+</persona>", text))


def _has_evidence_pointer(text: str) -> bool:
    return "<persona-evidence>" in text


def test_every_persona_tag_has_evidence_or_is_load_bearing_pending():
    """Phase 39b verification protocol (doctrine §5)."""
    violations = []
    for skill_path in _skill_files():
        text = skill_path.read_text(encoding="utf-8")
        if not _has_persona_tag(text):
            continue
        name = _skill_name(skill_path)
        if _has_evidence_pointer(text):
            continue
        if name in LOAD_BEARING_PENDING_EVIDENCE:
            continue
        violations.append(name)
    assert not violations, (
        f"Skills with <persona> tag lacking evidence or pending-load-bearing "
        f"registration: {violations}. Per doctrine §5, either remove the tag, "
        f"add a <persona-evidence> pointer, or register the skill in "
        f"LOAD_BEARING_PENDING_EVIDENCE."
    )


def test_decorative_targets_removed():
    """Phase 39b S3: 5 decorative targets no longer carry <persona> frontmatter."""
    decorative = [
        ("qor-status", "qor/skills/memory/qor-status/SKILL.md"),
        ("qor-help", "qor/skills/meta/qor-help/SKILL.md"),
        ("qor-repo-scaffold", "qor/skills/meta/qor-repo-scaffold/SKILL.md"),
        ("qor-bootstrap", "qor/skills/meta/qor-bootstrap/SKILL.md"),
        ("qor-document", "qor/skills/memory/qor-document/SKILL.md"),
    ]
    for name, path_str in decorative:
        text = pathlib.Path(path_str).read_text(encoding="utf-8")
        assert not _has_persona_tag(text), (
            f"{name}: still carries <persona> tag; should be removed per Phase 39b S3 "
            f"(decorative — not load-bearing per doctrine §2)."
        )


def test_qor_debug_references_context_discipline_doctrine():
    """R4: qor-debug constraint cites doctrine §4."""
    text = pathlib.Path("qor/skills/sdlc/qor-debug/SKILL.md").read_text(encoding="utf-8")
    assert "doctrine-context-discipline" in text
    assert "§4" in text or "Section 4" in text or "Subagent invocation rule" in text


def test_qor_document_disambiguates_persona_and_agent():
    """R5: qor-document splits Identity Activation stance from subagent pairing."""
    text = pathlib.Path("qor/skills/memory/qor-document/SKILL.md").read_text(encoding="utf-8")
    # Two distinct sentences: one for main-thread stance, one for subagent pairing
    assert "Identity Activation stance" in text
    assert "Subagent pairing" in text
    # Must explicitly cite the doctrine distinction
    assert "doctrine-context-discipline" in text


def test_identity_activation_matches_ab_winner_if_results_exist():
    """R3 conditional: if A/B results declare winner='stance', Identity Activation uses stance-directive-first."""
    if not _RESULTS.is_file():
        # Phase 3 not yet run by operator; R3 is skipped per plan doctrine.
        return
    results_text = _RESULTS.read_text(encoding="utf-8")
    # Parse per-skill winner declarations from the results artifact
    # Format: "## /qor-audit\n...**Winner**: stance"
    for skill in ("qor-audit", "qor-substantiate"):
        skill_path = pathlib.Path(f"qor/skills/governance/{skill}/SKILL.md")
        skill_text = skill_path.read_text(encoding="utf-8")
        section_match = re.search(
            rf"## /{re.escape(skill)}.*?\*\*Winner\*\*:\s*(\w+)",
            results_text, re.DOTALL,
        )
        if not section_match:
            continue
        winner = section_match.group(1).lower()
        has_persona_opener = "You are now operating as" in skill_text
        if winner == "stance":
            assert not has_persona_opener, (
                f"{skill}: A/B declared stance winner but persona opener retained. "
                f"Apply R3 rewrite."
            )
