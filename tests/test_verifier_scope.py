"""Phase 287: a verifier reports what it examined, and examining nothing is not a pass.

Phase 219 established this for the publication-boundary lint -- a green result
carries its own scope, because an unqualified "0 findings" from a narrow run and
from a thorough one are indistinguishable. Three verifiers lacked it.

Disclosure is universal; the floor is not. It belongs where an empty scope means
the examiner failed to look -- `ledger_commitment`, whose checked set the audited
party declares -- and not where zero means there was nothing to cite. A floor
drafted for `plan_grep_lint` over-flagged plans of pure design reasoning and was
unreachable for its own purpose, and an existing test caught it.

Each test names the implementation that would make it fail.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_HOUSE_PLAN = """# Plan: something

## Locked Decisions

### LD-1: a decision that cites infrastructure

> `grep -n 'def append_event' qor/scripts/shadow_process.py` -> `113:def append_event(`

Prose after the statement.
"""


# --- #487: the citation truth-checker examines the citations ---------------


def test_locked_decision_bodies_are_inside_the_scanned_region(tmp_path):
    """Red before: `_ld_blocks` ends the block at the first `### LD-1`, so every
    decision body falls outside and one empty block is returned."""
    from qor.scripts import plan_evidence as pe

    blocks = pe._ld_blocks(_HOUSE_PLAN)
    parsed = sum(len(pe.parse_evidence_statements(b)) for _, b in blocks)
    assert parsed == 1, "the statement inside ### LD-1 must be reachable"


def test_the_truth_checker_reports_a_nonzero_count_on_a_house_convention_plan():
    """Red before: 0 on every plan written to the house convention."""
    from qor.scripts.plan_grep_lint import count_truth_checked

    plan = REPO / "docs" / "plan-qor-phase287-verifier-scope-disclosure.md"
    checked, _ = count_truth_checked(plan.read_text(encoding="utf-8"), repo_root=REPO)
    assert checked > 0, "this plan carries evidence statements; the count must see them"


# --- #461: an author-declared scope is disclosed and floored ---------------


def test_stale_commitments_reports_how_many_artifacts_it_examined(tmp_path):
    """Red before: a bare list is returned and the caller cannot tell one from none."""
    from qor.scripts import ledger_commitment as lc

    result = lc.stale_commitments_scoped(REPO, [])
    assert hasattr(result, "examined"), "the result must carry its examined count"
    assert result.examined == 0


def test_an_empty_touched_set_fails_rather_than_returning_clean():
    """Red before: `stale_commitments([])` returns `[]` and the gate passes."""
    from qor.scripts import ledger_commitment as lc

    result = lc.stale_commitments_scoped(REPO, [])
    assert result.examined == 0
    assert not result.passes, "an examination of nothing is not a pass"


def test_a_populated_touched_set_still_passes_when_nothing_is_stale():
    """The negative control. Red if the floor is implemented on the findings list
    rather than on the examined count, which would fail every clean run."""
    from qor.scripts import ledger_commitment as lc

    plan = "docs/plan-qor-phase287-verifier-scope-disclosure.md"
    result = lc.stale_commitments_scoped(REPO, [plan])
    assert result.examined >= 1
    assert result.passes, "a real examination finding nothing stale is a pass"


# --- #476: the sync gate covers the surface it claims ----------------------


def test_reference_files_are_compared_between_source_and_dist():
    """Red before: only SKILL.md is globbed, so a references/ difference is invisible."""
    from tests import test_install_sync_with_source as sync

    compared = sync._source_files()
    assert any(p.name != "SKILL.md" for p in compared), (
        "references/*.md must be in the compared set"
    )


def test_the_sync_gate_reports_how_many_files_it_compared():
    """Red before: nothing reports coverage, so 55 percent and 100 percent look
    identical."""
    from tests import test_install_sync_with_source as sync

    compared = sync._source_files()
    skills = [p for p in compared if p.name == "SKILL.md"]
    refs = [p for p in compared if p.name != "SKILL.md"]
    assert len(skills) > 0 and len(refs) > 0
    assert len(compared) == len(skills) + len(refs)


# --- #486: the seal gate's escape runs -------------------------------------


def test_merge_velocity_override_appends_its_event_and_passes(monkeypatch):
    """Red before: `append_event` is called with neither attribution nor log_path
    and raises ValueError, so the documented escape cannot complete."""
    from qor.scripts import merge_velocity_check as mvc, shadow_process

    appended: list[tuple] = []
    monkeypatch.setattr(shadow_process, "append_event",
                        lambda event, **kw: appended.append((event, kw)) or "id")

    exceeded = mvc.VelocityAssessment(
        prs_merged_in_window=99, additions_total=1, repair_density=0.0,
        shared_core_touch_count=0, stabilization_capacity="exceeded",
        recommended_action="hardening_only",
        evidence=["prs_merged_in_window=99 >= 10 threshold"], window_days=7,
    )
    monkeypatch.setattr(mvc, "assess_merge_velocity", lambda *a, **k: exceeded)

    rc = mvc.main(["--repo-root", str(REPO), "--window-days", "7", "--override"])
    assert rc == 0, "--override must pass on an exceeded grade"
    assert appended, "--override must append its gate_override event"
    event, kw = appended[0]
    assert event["event_type"] == "gate_override"
    assert kw.get("attribution") or kw.get("log_path"), (
        "append_event requires attribution= or log_path=; without one it raises"
    )


# --- Phase 3: the rule is written down where it is general -----------------


def test_the_doctrine_states_the_scope_rule():
    """Red before the change, and red if doctrine and implementation drift.

    Both halves must be stated: disclosure alone left plan_grep_lint reporting a
    faithful zero and exiting clean.
    """
    text = (REPO / "qor" / "references"
            / "doctrine-verification-closure-integrity.md").read_text(encoding="utf-8")
    section = text.split("## Scope disclosure", 1)[1].split("\n## ", 1)[0]
    # The doctrine is hard-wrapped, so assert against normalised whitespace:
    # a claim that spans a line break is still the claim.
    flat = " ".join(section.split())
    assert "examination of nothing is not a pass" in flat
    assert "floor" in flat
    assert "supplied by the party it audits" in flat
