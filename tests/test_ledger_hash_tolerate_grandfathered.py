"""Phase 91: behavior tests for verify-ledger --tolerate-known-grandfathered (GH #85).

Tests use tmp-path fixture ledgers reconstructing the SG-ConcurrentLedgerRace-A
pattern (entries sharing previous_hash; downstream chain-math mismatch).
Per qor/references/doctrine-test-functionality.md, assertions verify operative
outcomes (return code, stderr/stdout content, returned set members) -- never
header or section presence.
"""
from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from qor.scripts import ledger_hash
from qor.scripts.ledger_hash import (
    chain_hash,
    find_grandfathered_entries,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_entry(
    num: int,
    content: str,
    previous: str,
    *,
    chain_override: str | None = None,
) -> str:
    """Construct a minimal ledger-entry block.

    The Chain Hash is computed canonically unless chain_override is provided,
    which lets tests construct deliberate chain-math failures.
    """
    chain = chain_override if chain_override is not None else chain_hash(content, previous)
    return textwrap.dedent(
        f"""

        ### Entry #{num}: TEST

        **Content Hash**: `{content}`

        **Previous Hash**: `{previous}`

        **Chain Hash**: `{chain}`
        """
    )


def _make_ledger(entries: list[str]) -> str:
    """Wrap entry blocks in a minimal ledger header."""
    return "# META_LEDGER\n" + "".join(entries)


def _hex(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _capture_verify(
    ledger_path: Path,
    *,
    tolerate: bool = False,
    cutoff: int = 207,
) -> tuple[int, str, str]:
    """Invoke verify() in-process; return (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = verify(
            ledger_path,
            tolerate_known_grandfathered=tolerate,
            grandfather_cutoff=cutoff,
        )
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# find_grandfathered_entries
# ---------------------------------------------------------------------------


def test_find_grandfathered_returns_entries_with_duplicate_previous_hash_below_cutoff(tmp_path):
    shared = _hex("shared-prev")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(100, _hex("c100"), shared),
        _make_entry(102, _hex("c102"), shared),
        _make_entry(104, _hex("c104"), shared),
    ]), encoding="utf-8")
    assert find_grandfathered_entries(ledger, cutoff=207) == frozenset({100, 102, 104})


def test_find_grandfathered_excludes_entries_above_cutoff(tmp_path):
    shared = _hex("shared-post-cutoff")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(208, _hex("c208"), shared),
        _make_entry(210, _hex("c210"), shared),
    ]), encoding="utf-8")
    assert find_grandfathered_entries(ledger, cutoff=207) == frozenset()


def test_find_grandfathered_excludes_unique_previous_hash_entries(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(100, _hex("c100"), _hex("p100-unique")),
        _make_entry(101, _hex("c101"), _hex("p101-unique")),
    ]), encoding="utf-8")
    assert find_grandfathered_entries(ledger, cutoff=207) == frozenset()


def test_find_grandfathered_handles_mixed_pre_and_post_cutoff_group(tmp_path):
    shared = _hex("shared-mixed")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(105, _hex("c105"), shared),
        _make_entry(207, _hex("c207"), shared),
        _make_entry(208, _hex("c208"), shared),
    ]), encoding="utf-8")
    # Only entries <= 207 are grandfathered; #208 is above the cutoff and
    # remains a FAIL candidate (preserves forward-only invariant).
    assert find_grandfathered_entries(ledger, cutoff=207) == frozenset({105, 207})


# ---------------------------------------------------------------------------
# verify() with the flag
# ---------------------------------------------------------------------------


def test_verify_without_flag_still_fails_on_grandfathered_chain_mismatch(tmp_path):
    shared = _hex("shared-fail")
    bad_chain = _hex("totally-wrong-chain-hash")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(100, _hex("c100"), shared, chain_override=bad_chain),
        _make_entry(102, _hex("c102"), shared),
    ]), encoding="utf-8")
    rc, _, err = _capture_verify(ledger, tolerate=False)
    assert rc == 1, "expected non-zero exit when grandfathered entry fails without flag"
    assert "FAIL Entry #100" in err, f"expected FAIL line in stderr, got: {err!r}"


def test_verify_with_flag_reports_disclosed_grandfathered_not_fail(tmp_path):
    shared = _hex("shared-tolerated")
    bad_chain = _hex("wrong-chain")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(100, _hex("c100"), shared, chain_override=bad_chain),
        _make_entry(102, _hex("c102"), shared),
    ]), encoding="utf-8")
    rc, out, err = _capture_verify(ledger, tolerate=True)
    assert rc == 0, f"expected zero exit with flag; got rc={rc}, err={err!r}"
    assert "DISCLOSED_GRANDFATHERED Entry #100" in out, (
        f"expected DISCLOSED_GRANDFATHERED line in stdout, got: {out!r}"
    )
    assert "FAIL Entry #100" not in err


def test_verify_with_flag_does_not_propagate_taint_from_grandfathered_failure(tmp_path):
    shared = _hex("shared-taint-test")
    bad_chain = _hex("wrong-chain")
    # Build a chain where #102 follows #100 cleanly (its previous_hash is
    # #100's recorded chain hash), so #102 should be OK.
    e100 = _make_entry(100, _hex("c100"), shared, chain_override=bad_chain)
    e101 = _make_entry(101, _hex("c101"), shared)  # also in the duplicate group
    # #102 anchors off the bad chain (the recorded one), so its math verifies
    # against the recorded chain.
    e102_content = _hex("c102")
    e102_prev = bad_chain
    e102 = _make_entry(102, e102_content, e102_prev)
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([e100, e101, e102]), encoding="utf-8")
    rc, out, err = _capture_verify(ledger, tolerate=True)
    assert rc == 0, f"expected zero exit; got rc={rc}, err={err!r}"
    assert "TAINTED Entry #102" not in err, (
        f"#102 must not be tainted by a tolerated grandfathered failure; got err: {err!r}"
    )
    assert "OK   Entry #102" in out or "OK Entry #102" in out, (
        f"expected #102 to be OK after grandfathered tolerance; got: {out!r}"
    )


def test_verify_with_flag_still_fails_on_post_cutoff_chain_mismatch(tmp_path):
    """Critical guard: the flag must NOT mask novel failures above the cutoff."""
    shared_pre = _hex("shared-pre-cutoff")
    bad_chain_post = _hex("wrong-chain-post")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        # Grandfathered failure (tolerated)
        _make_entry(100, _hex("c100"), shared_pre, chain_override=_hex("bad-pre")),
        _make_entry(102, _hex("c102"), shared_pre),
        # Post-cutoff entry with a real chain mismatch; previous_hash is
        # unique (not in any duplicate group), so it is NOT grandfathered.
        _make_entry(220, _hex("c220"), _hex("unique-prev-220"), chain_override=bad_chain_post),
    ]), encoding="utf-8")
    rc, out, err = _capture_verify(ledger, tolerate=True, cutoff=207)
    assert rc == 1, f"expected non-zero exit when post-cutoff failure present; rc={rc}"
    assert "FAIL Entry #220" in err, (
        f"post-cutoff failure must NOT be masked; expected FAIL in stderr: {err!r}"
    )
    # #100 should still be tolerated
    assert "DISCLOSED_GRANDFATHERED Entry #100" in out


def test_verify_with_custom_cutoff_overrides_default(tmp_path):
    shared = _hex("shared-wide-cutoff")
    bad_chain = _hex("wrong")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(150, _hex("c150"), shared, chain_override=bad_chain),
        _make_entry(220, _hex("c220"), shared, chain_override=bad_chain),
    ]), encoding="utf-8")
    # With default cutoff (207), #220 is NOT grandfathered (fails).
    rc_default, _, err_default = _capture_verify(ledger, tolerate=True, cutoff=207)
    assert rc_default == 1
    assert "FAIL Entry #220" in err_default
    # With cutoff raised to 250, both #150 and #220 are grandfathered.
    rc_wide, out_wide, err_wide = _capture_verify(ledger, tolerate=True, cutoff=250)
    assert rc_wide == 0, f"expected zero exit with wider cutoff; rc={rc_wide}, err={err_wide!r}"
    assert "DISCLOSED_GRANDFATHERED Entry #150" in out_wide
    assert "DISCLOSED_GRANDFATHERED Entry #220" in out_wide


# ---------------------------------------------------------------------------
# CLI flag plumbing
# ---------------------------------------------------------------------------


def test_cli_flag_parses_and_propagates(tmp_path):
    shared = _hex("cli-shared")
    bad_chain = _hex("cli-bad")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(100, _hex("c100"), shared, chain_override=bad_chain),
        _make_entry(101, _hex("c101"), shared),
    ]), encoding="utf-8")
    # Without flag: exit 1, stderr contains FAIL
    without = subprocess.run(
        [sys.executable, "-m", "qor.cli", "verify-ledger", "--ledger", str(ledger)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert without.returncode == 1, (
        f"without flag, expected exit 1; got {without.returncode} "
        f"stdout={without.stdout!r} stderr={without.stderr!r}"
    )
    assert "FAIL Entry #100" in without.stderr
    # With flag: exit 0, stdout contains DISCLOSED_GRANDFATHERED
    with_ = subprocess.run(
        [
            sys.executable, "-m", "qor.cli", "verify-ledger",
            "--ledger", str(ledger), "--tolerate-known-grandfathered",
        ],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert with_.returncode == 0, (
        f"with flag, expected exit 0; got {with_.returncode} "
        f"stdout={with_.stdout!r} stderr={with_.stderr!r}"
    )
    assert "DISCLOSED_GRANDFATHERED Entry #100" in with_.stdout


def test_cli_grandfather_cutoff_arg_parses(tmp_path):
    shared = _hex("cli-cutoff-shared")
    bad_chain = _hex("cli-cutoff-bad")
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_make_ledger([
        _make_entry(220, _hex("c220"), shared, chain_override=bad_chain),
        _make_entry(221, _hex("c221"), shared),
    ]), encoding="utf-8")
    # With wide cutoff: tolerated
    result = subprocess.run(
        [
            sys.executable, "-m", "qor.cli", "verify-ledger",
            "--ledger", str(ledger),
            "--tolerate-known-grandfathered",
            "--grandfather-cutoff", "250",
        ],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"with wide cutoff, expected exit 0; got {result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "DISCLOSED_GRANDFATHERED Entry #220" in result.stdout


# ---------------------------------------------------------------------------
# Canonical-ledger forward-only guards
# ---------------------------------------------------------------------------


def test_canonical_ledger_unchanged_without_flag():
    """Phase 91 must not change observable behavior on the canonical
    Qor-logic META_LEDGER when the flag is not set."""
    rc, _, _ = _capture_verify(
        REPO_ROOT / "docs" / "META_LEDGER.md",
        tolerate=False,
    )
    assert rc == 0, (
        "canonical ledger must verify clean without the flag (forward-only guard); "
        f"got rc={rc}"
    )


def test_canonical_ledger_clean_with_flag():
    """The flag must add zero noise on a ledger that is already clean."""
    rc, out, _ = _capture_verify(
        REPO_ROOT / "docs" / "META_LEDGER.md",
        tolerate=True,
    )
    assert rc == 0, f"canonical ledger must remain clean with flag set; got rc={rc}"
    # No DISCLOSED_GRANDFATHERED lines because the canonical ledger has no
    # chain-math failures (the #109/#111/#113 duplicate-previous_hash entries
    # each verify in isolation).
    assert "DISCLOSED_GRANDFATHERED" not in out, (
        f"canonical ledger has no chain-math failures to disclose; "
        f"the flag should produce no DISCLOSED lines; got: {out!r}"
    )
