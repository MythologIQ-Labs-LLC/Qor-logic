"""Phase 222 (GH #327): the seal gate ladder is data, so it is checkable.

Ten gate steps sat in `qor-substantiate/SKILL.md` as ten hand-written prose
blocks, 6,194 B of a file with 24 B of headroom. Their order, completeness, and
halt semantics were reviewable but not checkable, and Phase 221 found a
fail-closed gate that had drifted to a position no reader reached.

These tests define the parser contract before it exists. Every negative case here
exists because the positive cases alone are satisfied by a parser that returns
nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"

#: The revision the ladder is bound to for relocation-fidelity purposes. Pinned
#: rather than floating: a moving baseline would let a lost token disappear from
#: both sides of the comparison at once.
BASELINE_REV = "6424413"

#: Executed at 6424413 over lines 227-345: 12 non-comment commands inside fenced
#: blocks (one of them a joined backslash continuation) unioned with 42
#: backticked spans. A continuation is one command; splitting it would leave a
#: fragment that cannot match once the command lands in a single table cell.
BASELINE_TOKEN_COUNT = 54

EXPECTED_STEPS = {
    "4.6", "4.6.5", "4.6.6", "4.6.7", "4.6.8",
    "4.6.9", "4.6.10", "4.6.12", "4.6.13", "4.6.14",
}


def _baseline_skill_text() -> str:
    out = subprocess.run(
        ["git", "show", f"{BASELINE_REV}:qor/skills/governance/qor-substantiate/SKILL.md"],
        cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        pytest.skip(f"baseline revision {BASELINE_REV} unreachable (shallow clone?)")
    return out.stdout


# --------------------------------------------------------------------------
# parse_ladder
# --------------------------------------------------------------------------

def test_parse_ladder_returns_every_declared_row():
    """The live ladder yields exactly the ten steps the ceremony runs."""
    rows = sg.parse_ladder(SEAL_SKILL)
    assert {r.step for r in rows} == EXPECTED_STEPS


def test_rows_are_returned_in_ascending_numeric_order():
    """Ordered by integer tuple, not decimal encoding.

    Packing the sub-step into a decimal makes 4.6.9 (4.69) sort after 4.6.10
    (4.61). Phase 221 shipped that bug in its first ladder-order key and caught
    it against a correctly ordered ladder.
    """
    rows = sg.parse_ladder(SEAL_SKILL)
    keys = [tuple(int(p) for p in r.step.split(".")) for r in rows]
    assert keys == sorted(keys), " -> ".join(r.step for r in rows)


def test_every_row_carries_a_runnable_command():
    rows = sg.parse_ladder(FIXTURES / "seal_ladder_complete.md")
    for row in rows:
        assert row.commands, f"step {row.step} parsed to zero commands"
        assert all(c.strip() for c in row.commands)


def test_multi_command_cells_split_on_the_row_separator():
    """Step 4.6 runs several reliability gates; one row, several commands."""
    rows = {r.step: r for r in sg.parse_ladder(FIXTURES / "seal_ladder_complete.md")}
    assert len(rows["4.6"].commands) == 2
    assert rows["4.6"].commands[0].startswith("qor-logic reliability intent_lock verify")
    assert len(rows["4.6.5"].commands) == 1


def test_a_removed_row_is_detected():
    """THE COUNTERFACTUAL for completeness.

    Without this the parser could return the empty list and every other
    assertion in this file would still hold.
    """
    complete = sg.required_gates(sg.parse_ladder(FIXTURES / "seal_ladder_complete.md"))
    reduced = sg.required_gates(sg.parse_ladder(FIXTURES / "seal_ladder_row_removed.md"))

    assert "skill_size_budget_lint" in complete
    assert complete - reduced == {"skill_size_budget_lint"}


def test_a_malformed_row_raises_rather_than_being_skipped():
    with pytest.raises(sg.LadderError) as exc:
        sg.parse_ladder(FIXTURES / "seal_ladder_malformed.md")
    assert "4.6.5" in str(exc.value), "the raise must name the offending step"


def test_policy_values_are_closed():
    """An open policy vocabulary turns a fail-closed gate advisory by typo."""
    assert sg.POLICY_VALUES == frozenset({"ABORT", "WARN", "disclose"})

    body = (FIXTURES / "seal_ladder_malformed.md").read_text(encoding="utf-8")
    only_bad_policy = body.replace("| 4.6.5 | secret_scanner |  | ABORT |",
                                   "| 4.6.5 | secret_scanner | `x` | ABORT |")
    with pytest.raises(sg.LadderError) as exc:
        sg.parse_ladder_text(only_bad_policy)
    assert "advisory" in str(exc.value)


def test_live_ladder_policies_are_all_in_vocabulary():
    rows = sg.parse_ladder(SEAL_SKILL)
    assert {r.policy for r in rows} <= sg.POLICY_VALUES


def test_step_4_6_11_is_absent_as_a_row():
    """Phase 221 (ledger #563) decided the gap is the scar of GH #314.

    A table invites renumbering into a dense sequence; closing the gap would
    erase the record of a gate that was declared and never existed.
    """
    rows = sg.parse_ladder(SEAL_SKILL)
    assert "4.6.11" not in {r.step for r in rows}


def test_the_gap_at_4_6_11_is_explained_in_the_skill():
    """The absence must be recorded, not merely present.

    The plan specified `"4.6.11" not in SKILL.md`, which contradicts LD-5's own
    reasoning: a gap that says nothing is indistinguishable from a numbering
    slip, and the next editor closes it. What Phase 221 protected is the
    RECORD of the gap. So the token must appear -- as an explanation, never as
    a row -- and the row assertion above is what keeps the two apart.
    """
    body = SEAL_SKILL.read_text(encoding="utf-8")
    assert "Step 4.6.11 is deliberately absent" in body  # prose-lint: ok=LD-5, the recorded absence IS the property
    assert "Do not renumber" in body  # prose-lint: ok=LD-5, the instruction to a future editor IS the property


# --------------------------------------------------------------------------
# extract_ladder_tokens
# --------------------------------------------------------------------------

def test_extract_ladder_tokens_returns_the_pinned_baseline_count():
    """Pins the extractor against a fixed revision.

    Without a count assertion the extractor could return the empty set and
    every relocation-fidelity check downstream would pass vacuously.
    """
    tokens = sg.extract_ladder_tokens(_baseline_skill_text())
    assert len(tokens) == BASELINE_TOKEN_COUNT


def test_a_backslash_continuation_is_extracted_as_one_command():
    """Step 4.6.6 spans two source lines and is one command.

    Extracting the fragments separately would produce a token ending in `\\`
    that can never match the joined form a table cell holds.
    """
    tokens = sg.extract_ladder_tokens(_baseline_skill_text())
    joined = ('qor-logic scripts procedural_fidelity --session "$SESSION_ID" '
              '--out dist/procedural-fidelity.findings.json')
    assert joined in tokens
    assert not any(t.endswith("\\") for t in tokens)


def test_extracted_tokens_include_both_fenced_and_backticked_commands():
    """Two of the ten gate commands are backticked inline rather than fenced.

    The union, not either half, is the correct set -- the detail a hand-written
    list loses.
    """
    tokens = sg.extract_ladder_tokens(_baseline_skill_text())
    fenced = "qor-logic scripts secret_scanner --staged --out dist/secrets.findings.json || ABORT"
    inline = "qor-logic scripts install_drift_check --host claude --scope auto || true"
    assert fenced in tokens
    assert inline in tokens


def test_removing_a_command_shrinks_the_extracted_set():
    """Proves the extractor reads what it claims to read."""
    text = _baseline_skill_text()
    victim = "qor-logic scripts data_api_acl_lint --repo-root . || ABORT"
    assert victim in sg.extract_ladder_tokens(text)

    stripped = text.replace(victim + "\n", "")
    assert len(sg.extract_ladder_tokens(stripped)) == BASELINE_TOKEN_COUNT - 1


def test_extract_returns_empty_when_no_ladder_region_exists():
    assert sg.extract_ladder_tokens("# some other document\n\ntext\n") == set()


# --------------------------------------------------------------------------
# module entry point
# --------------------------------------------------------------------------

def test_entry_point_exits_zero_on_the_live_ladder():
    out = subprocess.run(
        [sys.executable, "-m", "qor.scripts.substantiate_gates", "--skill", str(SEAL_SKILL)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


def test_entry_point_exits_non_zero_on_a_malformed_ladder():
    """The wired ceremony command must be able to halt a seal."""
    out = subprocess.run(
        [sys.executable, "-m", "qor.scripts.substantiate_gates",
         "--skill", str(FIXTURES / "seal_ladder_malformed.md")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert out.returncode != 0
    assert "4.6.5" in (out.stderr + out.stdout)
