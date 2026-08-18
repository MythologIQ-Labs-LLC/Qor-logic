"""Phase 232 (GH #349): a claimed count is a citation and gets checked like one.

Two same-day VETOs (ledger #593, #611) shared one shape: a plan asserted an
exhaustive countable inventory the artifact surface contradicted, while every
citation-truth check passed because the citations were true and the enumeration
around them was not. Both fixtures here are verbatim transcriptions of the
recoverable failure texts -- the iteration-1 audit of this very plan vetoed
invented fixtures, which is the pattern this lint exists to catch.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from qor.scripts import plan_enumeration_lint as pel


def _repo_with_tests(tmp_path: Path, n_tests: int = 4) -> tuple[Path, str]:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "tests").mkdir()
    body = "\n\n".join(f"def test_{i}():\n    assert True" for i in range(n_tests))
    (tmp_path / "tests" / "test_x.py").write_text(body + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "f"], cwd=tmp_path, check=True, capture_output=True)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=tmp_path,
                         capture_output=True, text=True, check=True).stdout.strip()
    return tmp_path, sha


def _claims(findings) -> list[tuple[int, int]]:
    return [(f.claimed, f.derived) for f in findings]


def test_form_a_catches_the_phase_226_shape(tmp_path):
    """Verbatim historical shape: bare commit token, no git show string."""
    repo, sha = _repo_with_tests(tmp_path, n_tests=4)
    plan = (f"## Phase 1\n\n"
            f"- `tests/test_x.py` - NEW; cherry-pick of `{sha}` (10 behavioral tests: "
            f"per-event preservation, all-or-nothing validation).\n")
    findings = pel.check_plan_text(plan, repo_root=repo)
    assert _claims(findings) == [(10, 4)]


def test_form_a_passes_a_true_count(tmp_path):
    repo, sha = _repo_with_tests(tmp_path, n_tests=4)
    plan = f"## Phase 1\n\n- `tests/test_x.py` - NEW; cherry-pick of `{sha}` (4 behavioral tests).\n"
    assert pel.check_plan_text(plan, repo_root=repo) == []


def test_form_a_skips_singular_test_noun(tmp_path):
    """Audit O1: 'ten test unpacks' beside a test path and a tag must not fire;
    the trigger noun is the plural `tests`."""
    repo, sha = _repo_with_tests(tmp_path, n_tests=4)
    plan = (f"## Locked Decisions\n\n"
            f"ten test unpacks (`tests/test_x.py:1`) at `{sha}` update in the same phase.\n")
    assert pel.check_plan_text(plan, repo_root=repo) == []


def test_form_b_catches_the_historical_ld_shape(tmp_path):
    """Verbatim modifier phrase from the Phase 230 iteration-1 text."""
    plan = ("## Locked Decisions\n\n"
            "all eight enumerated call sites (`tests/test_a.py:63`) update in the same phase.\n")
    findings = pel.check_plan_text(plan, repo_root=tmp_path)
    assert _claims(findings) == [(8, 1)]


def test_form_b_counts_shorthand_continuations(tmp_path):
    """The sealed Phase 230 LD-3 shape: six full citations, six comma-separated
    continuations -- derived twelve, quiet."""
    plan = ("## Locked Decisions\n\n"
            "ALL TWELVE call sites update in the same phase: ten test unpacks "
            "(`tests/test_remediate.py:210`, `:237`, `:262`, `:446`; "
            "`tests/test_remediate_enforcer_edges.py:92`, `:123`; "
            "`tests/test_remediate_per_event_enforcers.py:52`, `:112`, `:133`; "
            "`tests/test_sg_closure_enforcement.py:63`) and two prose snippets "
            "(`qor/skills/sdlc/qor-remediate/SKILL.md:103` and `qor/skills/sdlc/qor-remediate/SKILL.md:130`).\n")
    assert pel.check_plan_text(plan, repo_root=tmp_path) == []


def test_form_b_ignores_non_ld_paragraphs(tmp_path):
    """A deliberately partial enumeration outside any LD region is legitimate prose."""
    plan = ("## Iteration 2 disposition\n\n"
            "The true surface is TWELVE two-unpack sites -- the eight previously "
            "counted plus `tests/test_remediate.py:210`, `:237`.\n")
    assert pel.check_plan_text(plan, repo_root=tmp_path) == []


def test_form_b_skips_enumeration_free_claims(tmp_path):
    plan = "## Locked Decisions\n\nall eight call sites update in the same phase.\n"
    assert pel.check_plan_text(plan, repo_root=tmp_path) == []


def test_non_inventory_numerics_do_not_trigger(tmp_path):
    plan = ("## Locked Decisions\n\n"
            "a bounded unified diff (first 40 diff lines) against the 250 ceiling "
            "for `qor/scripts/x.py:10`.\n")
    assert pel.check_plan_text(plan, repo_root=tmp_path) == []


def test_number_words_parse(tmp_path):
    plan = ("## Locked Decisions\n\n"
            "twelve unpack sites: "
            + ", ".join(f"`tests/t{i}.py:{i+1}`" for i in range(11)) + ".\n")
    findings = pel.check_plan_text(plan, repo_root=tmp_path)
    assert _claims(findings) == [(12, 11)]
