"""Behavioral tests for the shared ledger-dialect parser (GH #282).

Proves the three hash-value forms parse identically, the separate `**Phase**:`
line is recognized, all three ledger consumers agree on a fenced+separate-Phase
fixture, and every rejection is preserved.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import ledger_dialect as ld
from qor.scripts import ledger_hash as lh
from qor.scripts import governance_health as gh
from qor.reliability import seal_entry_check as sec


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


# ---------- hash-value forms ----------

def test_three_hash_forms_extract_same_value():
    hexval = _digest(b"content")
    inline = f"**Content Hash**: `{hexval}`"
    eq_form = f"**Content Hash**:\n```\nSHA256(x)\n= {hexval}\n```"
    fenced_bare = f"**Content Hash**:\n```\n{hexval}\n```"
    for body in (inline, eq_form, fenced_bare):
        m = ld.CONTENT_HASH_RE.search(body)
        assert ld.hash_value(m) == hexval, body


def test_entry_phase_reads_header_and_separate_line():
    assert ld.entry_phase("### Entry #9: SESSION SEAL -- Phase 42 foo", "") == 42
    body = "**Phase**: SUBSTANTIATE (Phase 7; feature)\n\n**Content Hash**: `x`"
    assert ld.entry_phase("### Entry #9: SESSION SEAL", body) == 7
    assert ld.entry_phase("### Entry #9: SESSION SEAL", "no phase here") is None


def test_compat_boundary_is_single_valued():
    assert ld.MARKUP_COMPAT_BOUNDARY == 123


# ---------- three-consumer consistency ----------

def _fenced_entry(num: int, kind: str, content: str, prev: str, phase: int, plan_line: str = "") -> str:
    chain = lh.chain_hash(content, prev)
    plan = f"**Plan**: {plan_line}\n" if plan_line else ""
    return (
        f"### Entry #{num}: {kind}\n\n"
        f"**Phase**: {kind} (Phase {phase})\n"
        f"{plan}"
        f"\n**Content Hash**:\n```\n{content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{chain}\n```\n"
    )


def _fenced_ledger(tmp_path: Path) -> Path:
    c123, p123 = _digest(b"e123"), "0" * 64
    e123 = _fenced_entry(123, "IMPLEMENTATION", c123, p123, 50)
    c124, p124 = _digest(b"e124"), lh.chain_hash(c123, p123)
    e124 = _fenced_entry(124, "SESSION SEAL", c124, p124, 50)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + e123 + "\n" + e124 + "\n", encoding="utf-8")
    return ledger


def test_all_three_consumers_agree_on_fenced_separate_phase_fixture(tmp_path):
    ledger = _fenced_ledger(tmp_path)
    # 1. verify-ledger
    assert lh.verify(ledger) == 0
    # 2. governance-health's ledger verdict uses the same parser
    assert gh._verify_ledger_chain(ledger) == 0
    # 3. seal_entry_check parses + chain-verifies the latest fenced entry
    result = sec.check(ledger, phase_num=50)
    assert result.ok, result.errors


def test_seal_entry_parses_separate_phase_and_fenced_hashes(tmp_path):
    ledger = _fenced_ledger(tmp_path)
    latest = sec._parse_latest_entry(ledger.read_text(encoding="utf-8"))
    assert latest is not None
    assert latest["kind"] == "SESSION SEAL"
    assert latest["phase_num"] == 50
    assert latest["content_hash"] == _digest(b"e124")


# ---------- preserved rejections ----------

def test_malformed_hash_at_boundary_fails(tmp_path):
    bad = (
        "### Entry #123: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        "\n**Content Hash**:\n```\nnot-a-valid-hash\n```\n"
        "\n**Previous Hash**:\n```\n" + "0" * 64 + "\n```\n"
        "\n**Chain Hash**:\n```\n" + _digest(b"z") + "\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + bad + "\n", encoding="utf-8")
    assert lh.verify(ledger) != 0


def test_chain_mismatch_fails(tmp_path):
    content, prev = _digest(b"a"), "0" * 64
    wrong_chain = _digest(b"wrong")
    entry = (
        "### Entry #124: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        f"\n**Content Hash**:\n```\n{content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{wrong_chain}\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + entry + "\n", encoding="utf-8")
    assert lh.verify(ledger) != 0


def test_duplicate_previous_hash_post_boundary_fails(tmp_path):
    shared_prev = _digest(b"shared")
    e_a = _fenced_entry(300, "IMPLEMENTATION", _digest(b"a"), shared_prev, 60)
    e_b = _fenced_entry(301, "SESSION SEAL", _digest(b"b"), shared_prev, 60)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + e_a + "\n" + e_b + "\n", encoding="utf-8")
    res = sec.check_previous_hash_uniqueness(ledger, min_entry_num=207)
    assert not res.ok


def test_tampered_content_breaks_plan_binding(tmp_path):
    plan = tmp_path / "docs" / "plan-x.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("real plan bytes\n", encoding="utf-8")
    wrong_content = _digest(b"not the plan")
    prev = "0" * 64
    chain = lh.chain_hash(wrong_content, prev)
    entry = (
        "### Entry #124: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        "**Plan**: docs/plan-x.md\n"
        f"\n**Content Hash**:\n```\n{wrong_content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{chain}\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + entry + "\n", encoding="utf-8")
    res = sec.check(ledger, phase_num=1, repo_root=tmp_path)
    assert not res.ok


# --- GH #428: a hash label written in prose is not a field -------------------
#
# Shape names (S1, S4, ...) match the table in
# docs/plan-qor-phase281-dialect-prose-over-read.md.

_PROSE = "1" * 64          # a digest that appears only in narrative text
_FIELD = "2" * 64          # the digest an entry actually records


def _read(name: str, text: str):
    """Resolve one hash field the way every consumer does."""
    pattern = {
        "content": ld.CONTENT_HASH_RE,
        "previous": ld.PREV_HASH_RE,
        "chain": ld.CHAIN_HASH_RE,
    }[name]
    return ld.hash_value(pattern.search(text))


def test_prose_quoted_label_is_not_read_as_a_field():
    """S1: entry #741 verbatim -- a label quoted inside a sentence."""
    body = (
        "Entries #109, #111 and #113 carry an identical `**Previous Hash**` of\n"
        f"`{_PROSE}` at lines 4076, 4121 and 4166.\n"
    )
    assert _read("previous", body) is None


def test_prose_mention_does_not_displace_the_entrys_own_field():
    """S4: narrative names a hash before the entry's own field lines.

    The reported defect. Before the fix the reader returns the narrative
    digest; the entry's real field is never reached.
    """
    body = (
        f"We saw **Previous Hash**: `{_PROSE}` in the superseded entry.\n"
        "\n"
        f"**Previous Hash**: `{_FIELD}`\n"
    )
    assert _read("previous", body) == _FIELD


def test_prose_label_with_colon_is_not_a_field():
    """S2, S3, S5: a label written mid-line, with a colon after it."""
    s2 = f"Entry #109 records **Previous Hash**: `{_PROSE}` at line 4076.\n"
    s3 = f"The seal wrote **Chain Hash (Merkle seal)**: `{_PROSE}` before the fix.\n"
    s5 = f"- the stale **Previous Hash**: `{_PROSE}` recorded at #109\n"
    assert _read("previous", s2) is None
    assert _read("chain", s3) is None
    assert _read("previous", s5) is None


def test_prose_hex_between_label_and_value_is_rejected():
    """S6: narrative text between a label and its value.

    Rejected rather than guessed: an ambiguous line yields no value.
    """
    body = f"**Content Hash**: mentions `{_PROSE}` then `{_FIELD}`\n"
    assert _read("content", body) is None


def test_label_without_a_colon_is_not_a_field():
    """S16: line-start label, no colon. Isolates the colon constraint.

    S1 does not isolate it -- S1 is closed by the anchor, the colon and the
    connective independently, so it establishes the necessity of none of them.
    """
    body = f"**Previous Hash** `{_PROSE}` is stale, not ours.\n"
    assert _read("previous", body) is None


def test_every_legitimate_connective_form_still_matches():
    """The six field forms that occur in this repository must all survive.

    Over-tightening is the failure mode of this change, and a suite that only
    proved the defect gone would pass for a pattern matching nothing.
    """
    forms = {
        "plain": f"**Content Hash**: `{_FIELD}`\n",
        "value on next line": f"**Content Hash**:\n`{_FIELD}`\n",
        "fenced formula": (
            "**Chain Hash**:\n```\nSHA256(content_hash + previous_hash)\n"
            f"= `{_FIELD}`\n```\n"
        ),
        "bare hex alone on its line": (
            f"**Chain Hash**:\n```\nSHA256(x)\n{_FIELD}\n```\n"
        ),
        "qualifier inside markers": f"**Content Hash (session seal)**: `{_FIELD}`\n",
        "qualifier outside markers": f"**Chain Hash** (Merkle seal): `{_FIELD}`\n",
    }
    for label, text in forms.items():
        field = "chain" if "Chain" in text else "content"
        assert _read(field, text) == _FIELD, f"{label} stopped resolving"


def test_hash_value_still_reads_all_three_capture_groups():
    """``hash_value`` depends on _HASH_VALUE exposing three groups.

    A single-group value pattern raises IndexError in every consumer, and is
    also looser than production, whose third form requires a bare hex alone on
    its line precisely to avoid capturing inline prose hex.
    """
    for text in (
        f"**Content Hash**: `{_FIELD}`\n",
        f"**Content Hash**: SHA256(plan.md) = {_FIELD}\n",
        f"**Content Hash**:\n```\nSHA256(plan.md)\n{_FIELD}\n```\n",
    ):
        match = ld.CONTENT_HASH_RE.search(text)
        assert match is not None
        assert len(match.groups()) == 3
        assert ld.hash_value(match) == _FIELD


def test_live_ledger_gains_no_matches_and_loses_only_prose():
    """The change must not make anything newly resolve, anywhere.

    Counts are computed from the file under test, never hardcoded, so this
    stays green as the ledger grows.

    The gains half is the one that matters. A draft of this change was
    reported as a net loss and was in fact a net gain of six: it made seven
    unbackticked pre-boundary values resolve, moving those entries out of the
    migration-attestation rung into full chain math while the exit code stayed
    0. No rc-based check could have seen it.

    The loss half derives its expectation from the prose shape itself. It is
    NOT computed as ``old - new``, which is an identity that holds for any
    pattern whatsoever -- including one that matches nothing.
    """
    import re

    ledger = Path(__file__).resolve().parents[1] / "docs" / "META_LEDGER.md"
    text = ledger.read_text(encoding="utf-8")

    permissive = r"(?:(?!\n\s*\*\*[A-Z])[\s\S])*?"
    gains = 0
    losses = 0
    expected_losses = 0
    for name in ("Content Hash", "Previous Hash", "Chain Hash"):
        old = re.compile(
            r"\*\*" + name + ld._FIELD_SUFFIX + r"\*\*" + permissive + ld._HASH_VALUE
        )
        new = {
            "Content Hash": ld.CONTENT_HASH_RE,
            "Previous Hash": ld.PREV_HASH_RE,
            "Chain Hash": ld.CHAIN_HASH_RE,
        }[name]
        old_at = {m.start() for m in old.finditer(text)}
        new_at = {m.start() for m in new.finditer(text)}
        gains += len(new_at - old_at)
        losses += len(old_at - new_at)
        # Derived independently: a label with non-whitespace before it on its
        # own line is the prose-quoted shape, and nothing else in this ledger
        # stops resolving.
        for start in old_at:
            line_start = text.rfind("\n", 0, start) + 1
            if text[line_start:start].strip():
                expected_losses += 1

    assert gains == 0, f"{gains} field(s) newly resolve; the change must only narrow"
    assert losses == expected_losses, (
        f"lost {losses} match(es) but only {expected_losses} prose-quoted "
        "label(s) exist; something legitimate stopped resolving"
    )
