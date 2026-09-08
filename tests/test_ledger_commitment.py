"""Phase 251 (GH #408): a ledger commitment must not go stale unnoticed.

A ledger entry binds an artifact by content hash. When a later phase corrects
that artifact -- which is what an audit VETO is for -- the commitment silently
stops describing the file. Chain integrity is unaffected and correctly so:
chain hashes commit to the recorded hex string, not to live bytes. That is the
gap, not a flaw in the chain.

The convention that closes it (append an AMENDMENT recording the superseded and
new hashes) was already practiced in this repository and codified nowhere.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import ledger_commitment as lc

_A = "a1" * 32
_B = "b2" * 32


def _entry(num: int, kind: str, artifact: str, content: str, superseded: str | None = None) -> str:
    sup = f"**Superseded Content Hash**: `{superseded}`\n" if superseded else ""
    return (
        f"### Entry #{num}: {kind}\n\n"
        f"**Artifact**: {artifact}\n"
        f"{sup}"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{_A}`\n"
        f"**Chain Hash (Merkle seal)**: `{_B}`\n\n"
        "**Decision**: recorded.\n\n"
    )


def _ledger(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text("# Meta Ledger\n\n" + body, encoding="utf-8")
    return p


def _artifact(tmp_path: Path, rel: str, text: str) -> str:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return rel


def test_latest_commitment_wins_over_the_superseded_one(tmp_path):
    """An AMENDMENT re-commits the artifact; the newer hash is authoritative."""
    rel = _artifact(tmp_path, "docs/brief.md", "v2\n")
    new = lc.content_hash(tmp_path / rel)
    ledger = _ledger(
        tmp_path,
        _entry(1, "RESEARCH BRIEF", rel, _A)
        + _entry(2, "AMENDMENT", rel, new, superseded=_A),
    )

    commitments = lc.latest_commitments(ledger)

    assert commitments[rel] == new


def test_stale_commitment_is_reported_when_the_file_changed(tmp_path):
    """The defect GH #408 reports: the entry names a hash the file no longer has."""
    rel = _artifact(tmp_path, "docs/brief.md", "corrected under audit\n")
    ledger = _ledger(tmp_path, _entry(1, "RESEARCH BRIEF", rel, _A))

    stale = lc.stale_commitments(tmp_path, [rel], ledger_path=ledger)

    assert [s.artifact for s in stale] == [rel]
    assert stale[0].committed == _A
    assert stale[0].actual == lc.content_hash(tmp_path / rel)


def test_disclosed_amendment_clears_the_staleness(tmp_path):
    """Disclosure is what makes the doctrine self-policing.

    The pair with the test above is the point: the same corrected file passes
    once an AMENDMENT records its new hash, and fails while it does not.
    """
    rel = _artifact(tmp_path, "docs/brief.md", "corrected under audit\n")
    new = lc.content_hash(tmp_path / rel)
    ledger = _ledger(
        tmp_path,
        _entry(1, "RESEARCH BRIEF", rel, _A)
        + _entry(2, "AMENDMENT", rel, new, superseded=_A),
    )

    assert lc.stale_commitments(tmp_path, [rel], ledger_path=ledger) == []


def test_untouched_artifacts_are_not_inspected(tmp_path):
    """Pins the declared limitation.

    The seal gate reads the implement gate's `files_touched`. Without this, the
    check would drift into a full-ledger sweep whose cost grows with ledger
    length -- a `/qor-validate` concern, not a seal one.
    """
    rel = _artifact(tmp_path, "docs/brief.md", "changed\n")
    ledger = _ledger(tmp_path, _entry(1, "RESEARCH BRIEF", rel, _A))

    assert lc.stale_commitments(tmp_path, [], ledger_path=ledger) == []
    assert lc.stale_commitments(tmp_path, ["docs/other.md"], ledger_path=ledger) == []


def test_malformed_superseded_hash_is_rejected(tmp_path):
    """A truncated superseded hash is not a valid supersession.

    Entry #682 of this repository's own ledger recorded an eight-character
    prefix. Accepting it would let a malformed amendment silently clear a real
    staleness.
    """
    rel = _artifact(tmp_path, "docs/brief.md", "v2\n")
    new = lc.content_hash(tmp_path / rel)
    ledger = _ledger(
        tmp_path,
        _entry(1, "RESEARCH BRIEF", rel, _A)
        + _entry(2, "AMENDMENT", rel, new, superseded="66347652"),
    )

    with pytest.raises(lc.MalformedCommitmentError, match="66347652"):
        lc.latest_commitments(ledger)


def test_the_live_ledger_parses_and_has_no_malformed_commitments():
    """Anti-recurrence binding: the doctrine's first subject is this repository.

    The parser must read the real 690+ entry ledger without raising, which also
    proves entry #682's truncated field was corrected rather than tolerated.
    """
    repo = Path(__file__).resolve().parents[1]
    commitments = lc.latest_commitments(repo / "docs" / "META_LEDGER.md")

    assert commitments, "the live ledger must yield at least one commitment"


def test_gate_tribunal_plan_citation_is_not_a_commitment(tmp_path):
    """Regression coverage, not TDD: found by running this gate on its own phase.

    A GATE TRIBUNAL entry cites `**Plan**:` but its `**Content Hash**` binds the
    AUDIT REPORT. Reading that citation as a commitment compares the plan bytes
    against the report digest and reports a stale commitment that does not exist
    -- a false abort at every seal that follows an audit.
    """
    rel = _artifact(tmp_path, "docs/plan-x.md", "plan body" + chr(10))
    plan_hash = lc.content_hash(tmp_path / rel)
    tribunal = (
        "### Entry #2: GATE TRIBUNAL" + chr(10) * 2
        + f"**Plan**: {rel}" + chr(10)
        # The tribunal commits the AUDIT REPORT digest, not the plan.
        + f"**Content Hash**: `{_B}`" + chr(10) * 2
        + "**Decision**: PASS." + chr(10) * 2
    )
    ledger = _ledger(tmp_path, _entry(1, "IMPLEMENTATION", rel, plan_hash) + tribunal)

    commitments = lc.latest_commitments(ledger)

    assert commitments[rel] == plan_hash, (
        "a tribunal Plan citation must not overwrite the real commitment"
    )
    assert lc.stale_commitments(tmp_path, [rel], ledger_path=ledger) == []


# ----- Phase 277 (GH #467): the narrow **Content Hash** pattern is deliberate -----
#
# Phase 277 proposed consolidating this module onto ledger_dialect, on the
# reasoning that its narrow pattern was an accident. It is not. _ARTIFACT_RE
# accepts Plan and Brief as well as Artifact (491 entries in the live ledger),
# so widening the hash pattern admits SESSION SEAL entries whose
# **Content Hash (session seal)** is the seal digest, NOT the cited plan's hash.
#
# Measured before the proposal was withdrawn: across the 45 suffixed seal
# entries citing an on-disk plan, the recorded value equals that plan's live
# hash 0 times; across the 147 plain-label seals it matches 99 times. Widening
# would take on-disk stale commitments from 74 to 116 -- 42 artifacts newly
# stale -- in a gate that hard-ABORTs the seal.
#
# The module's existing comment covers the KIND filter, not this pattern. This
# test guards the line itself, because a comment two definitions away did not
# stop the proposal and a failing test would have.


def test_a_suffixed_session_seal_hash_is_not_a_commitment(tmp_path):
    """A **Content Hash (session seal)** value must never become a commitment.

    It binds the seal digest; the entry's **Plan** cites a different file.
    Treating the two as a commitment compares a plan's bytes against a seal's
    digest -- a false stale reading in an ABORT gate.
    """
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(
        "### Entry #1: SESSION SEAL -- phase X\n\n"
        "**Plan**: docs/plan-qor-phaseX.md\n"
        "**Content Hash (session seal)**: `" + _A + "`\n\n",
        encoding="utf-8",
    )

    commitments = lc.latest_commitments(ledger)

    assert "docs/plan-qor-phaseX.md" not in commitments, (
        "the suffixed session-seal digest is not a commitment to the cited plan; "
        "admitting it would compare the plan's bytes against the seal's digest"
    )


def test_a_plain_content_hash_in_a_committing_entry_is_still_a_commitment(tmp_path):
    """The control: the narrowness must not be over-read as 'commit nothing'."""
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(
        "### Entry #1: IMPLEMENTATION -- phase X\n\n"
        "**Plan**: docs/plan-qor-phaseX.md\n"
        "**Content Hash**: `" + _A + "`\n\n",
        encoding="utf-8",
    )

    commitments = lc.latest_commitments(ledger)

    assert commitments.get("docs/plan-qor-phaseX.md") == _A
