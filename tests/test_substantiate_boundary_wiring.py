"""Phase 219 (GH #309): the seal must run the boundary lint, fail-closed.

Before this phase the lint ran WARN-only at `/qor-audit` Step 0.6 over a tree
predating implementation, and fail-closed in CI but structural-only. Nothing in
between saw implementation's new files before they were committed.

The step is pinned here because it is prose: nothing mechanical fails if it is
deleted, and its absence looks exactly like its presence to every other gate.
"""
from __future__ import annotations

from pathlib import Path

from tests import ladder_helpers as lh

from tests.test_substantiate_staging_gates import HEADROOM_BYTES

REPO_ROOT = Path(__file__).resolve().parents[1]
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
LADDER = SEAL_SKILL.parent / "references" / "seal-gate-ladder.md"


def _body() -> str:
    return SEAL_SKILL.read_text(encoding="utf-8")


def test_seal_step_runs_the_boundary_lint():
    """The producer must exist wherever the seal claims boundary coverage."""
    body = _body()
    assert "publication_boundary_lint" in body  # prose-lint: ok=wiring-contract for a prompt-only unit
    assert "boundary_scope" in body  # prose-lint: ok=wiring-contract for a prompt-only unit


def test_boundary_step_is_fail_closed():
    r"""Phase 222: read from the 4.6.14 ladder row.

    `row.commands` unescapes the table's `\|\|`, so this asserts on the shell
    operator the ceremony runs, not on the markdown escape.
    """
    row = lh.row("4.6.14")
    assert row is not None, "no gate ladder row for Step 4.6.14"
    invocation = "\n".join(row.commands)
    assert "|| ABORT" in invocation, invocation
    assert "|| true" not in invocation, invocation
    assert row.policy == "ABORT"


def test_boundary_step_runs_after_staging():
    row = lh.row("4.6.14")
    assert row is not None
    assert "AFTER Step 9.5" in row.notes, (
        "the 4.6.14 row must state that it runs after staging"
    )


def test_seal_skill_stays_under_the_headroom_lock():
    """The disclosure pass ran first, per LD-3. Measured, not assumed."""
    size = len(SEAL_SKILL.read_bytes().decode("utf-8").replace("\r\n", "\n").encode())
    assert size <= HEADROOM_BYTES, f"qor-substantiate at {size} B breaches the lock"


def test_relocated_prose_is_reachable():
    """A disclosure pass must not orphan the rationale it moves.

    Each relocated block gets a destination subsection; if the pointer and the
    subsection drift apart, the prose is gone rather than moved.
    """
    ladder = LADDER.read_text(encoding="utf-8")
    assert "Step 4.6.14 publication boundary" in ladder
    assert "Step 4.6.12 execution-continuity" in ladder
    assert "references/seal-gate-ladder.md" in _body()
