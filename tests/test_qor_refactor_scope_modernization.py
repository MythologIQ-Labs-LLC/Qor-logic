"""GH #392: /qor-refactor scope modernization (Tranche A).

Asserts the behavior-preserving simplification contract - scope modes,
the Simplification Test, post-refactor verification fields, and the
NO REFACTOR REQUIRED outcome - is present, and that the SKILL.md no
longer states a specific language/framework as a mandatory requirement.
"""
from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor/skills/sdlc/qor-refactor/SKILL.md"
EXAMPLES = REPO_ROOT / "qor/skills/sdlc/qor-refactor/references/qor-refactor-examples.md"


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _examples_text() -> str:
    return EXAMPLES.read_text(encoding="utf-8")


def test_declares_all_four_scope_modes():
    text = _skill_text()
    for mode in ("`changeset`", "`focused`", "`component`", "`explicit`"):
        assert mode in text, f"missing scope mode {mode}"


def test_changeset_is_recommended_default():
    text = _skill_text()
    assert "recommended default" in text
    assert "changeset" in text.split("recommended default")[0][-40:]


def test_simplification_test_has_seven_questions():
    text = _skill_text()
    assert "### Simplification Test" in text
    section = text.split("### Simplification Test", 1)[1].split("---", 1)[0]
    for n in range(1, 8):
        assert f"{n}. " in section, f"missing question {n}"


def test_no_refactor_required_is_a_valid_outcome():
    text = _skill_text()
    assert "NO REFACTOR REQUIRED" in text
    assert "valid, successful outcome" in text


def test_post_refactor_verification_fields_present():
    text = _skill_text()
    for field in (
        "behavior preserved",
        "complexity reduced",
        "clarity improved",
        "contract weakened",
        "scope exceeded",
    ):
        assert field in text, f"missing verification field: {field}"
    assert "INCONCLUSIVE" in text


def test_no_hard_requirement_on_js_ts_entry_points_or_manifest():
    text = _skill_text()
    # These file names may still appear as *examples* of what NOT to assume,
    # but must not appear as an unqualified mandatory `Read:`/`Discover:` step.
    assert "Read: package.json\n" not in text
    assert "Read: [entry point - main.tsx, index.ts]" not in text
    assert "do not assume main.tsx/index.ts" in text
    assert "package.json, Cargo.toml, pyproject.toml, go.mod, pom.xml" in text


def test_dependency_audit_uses_stdlib_not_vanilla_js_ts():
    text = _skill_text()
    assert "vanilla JS/TS" not in text
    assert "standard library" in text


def test_console_log_cleanup_step_generalized():
    text = _skill_text()
    assert "Remove all `console.log` artifacts" not in text
    assert "console.log" in text  # retained as one illustrative example, not the rule
    assert "discover the convention rather than assuming one" in text


def test_examples_file_discloses_illustrative_language_choice():
    text = _examples_text()
    assert "illustrative" in text.lower()


def test_examples_file_has_simplification_test_and_verification_templates():
    text = _examples_text()
    assert "## Simplification Test Finding (Template)" in text
    assert "## Post-Refactor Verification Report (Template)" in text
    assert "## NO REFACTOR REQUIRED Report (Template)" in text


def test_refactor_declares_the_harden_authority_boundary():
    """GH #392 acceptance: /qor-harden routes confirmed structural findings to
    /qor-refactor without duplicating its process. Written once /qor-harden
    landed (Phase 244) -- the relay's Tranche A predated it. Binds the skill's
    boundary prose to the canonical sweep's remediation profile so the two
    surfaces cannot drift apart silently."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    refactor = (root / "qor" / "skills" / "sdlc" / "qor-refactor" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    sweep = (root / "qor" / "references" / "implementation-quality-sweep.md").read_text(
        encoding="utf-8"
    )
    for dim in ("IQ-COMPLEX", "IQ-CONTEXT", "IQ-MAINTAIN"):
        assert dim in refactor, f"refactor boundary omits {dim}"
        assert dim in sweep
    assert "implementation-quality-sweep.md" in refactor
    assert "/qor-refactor` remediation profile" in sweep or "qor-refactor` remediation profile" in sweep


def test_completion_gate_blocks_on_the_bad_outcomes():
    """Phase 245 promotion audit F1: the shipped gate read 'a NO on contract
    weakened ... blocks completion' -- inverted, so a run that DID weaken a
    contract completed while a clean run blocked. Assert the blocking polarity
    (the property), not the field names."""
    import re
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "qor" / "skills" / "sdlc" / "qor-refactor" / "SKILL.md"
    ).read_text(encoding="utf-8")
    match = re.search(r"^A .*blocks completion.*$", text, re.MULTILINE)
    assert match, "completion-gate sentence missing"
    gate = match.group(0)
    assert '`YES` on "contract weakened"' in gate, (
        "the gate must block on contract-weakened YES (the bad outcome)"
    )
    assert '`NO` on "contract weakened"' not in gate, (
        "inverted polarity: blocking on contract-weakened NO lets a weakened "
        "contract complete"
    )
    assert '`YES` on "scope exceeded"' in gate
    assert '`NO`/`INCONCLUSIVE` on "behavior preserved"' in gate, (
        "the primary invariant must block on its bad outcomes "
        "(NO/INCONCLUSIVE), not merely appear in the sentence"
    )


def test_threshold_steps_route_through_the_simplification_test():
    """Phase 245 promotion audit F2: the Section 4 sub-steps were unconditional
    imperatives ('split into cohesive sub-functions') contradicting the
    document's own examination-not-forced-decomposition rule."""
    from pathlib import Path

    text = (
        Path(__file__).resolve().parents[1]
        / "qor" / "skills" / "sdlc" / "qor-refactor" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "triggers the Simplification Test; split into cohesive sub-functions only when" in text
    assert "triggers the Simplification Test; split into cohesive modules only when" in text
    assert "For each function exceeding 40 lines, split" not in text
    assert "For files exceeding 250 lines, split" not in text
    # the Step 4e boundary sentence was the third F2 imperative; pin its
    # conditional form and the absence of the unconditional one
    assert "Any finding here triggers the Simplification Test" in text
    assert "If any violation is found, refactor to restore" not in text
