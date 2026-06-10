"""Phase 47 Phase 1: behavioral tests for seal_entry_check helper.

Each test builds a synthetic META_LEDGER fixture in tmp_path, invokes
seal_entry_check.check() (or the CLI via subprocess), and asserts on the
returned SealEntryResult — never on artifact presence alone (per
qor/references/doctrine-test-functionality.md).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.reliability import seal_entry_check
from qor.scripts.ledger_hash import chain_hash


REPO_ROOT = Path(__file__).resolve().parent.parent


def _entry(
    num: int,
    kind: str,
    phase_num: int,
    content_hash: str,
    prev_hash: str,
) -> str:
    """Render a synthetic ledger entry block with self-consistent chain hash."""
    chain = chain_hash(content_hash, prev_hash)
    if kind == "GATE TRIBUNAL":
        title = f"### Entry #{num}: GATE TRIBUNAL -- Phase {phase_num} Pass 1 -- **PASS** (L1)"
    elif kind == "IMPLEMENTATION":
        title = f"### Entry #{num}: IMPLEMENTATION -- Phase {phase_num}"
    elif kind == "SESSION SEAL":
        title = f"### Entry #{num}: SESSION SEAL -- Phase {phase_num} feature substantiated"
    else:
        raise ValueError(kind)
    return (
        f"{title}\n\n"
        f"**Phase**: {kind}\n\n"
        f"**Content Hash**: `{content_hash}`\n"
        f"**Previous Hash**: `{prev_hash}`\n"
        f"**Chain Hash**: `{chain}`\n"
    )


def _ledger(entries: list[str]) -> str:
    """Wrap entries in a minimal META_LEDGER header."""
    header = "# Meta Ledger\n\n"
    body = "\n---\n\n".join(entries)
    return header + body + "\n"


def _zhash(seed: int) -> str:
    """Deterministic 64-char hex from a seed.

    Phase 66 (GH #54) note: pre-Phase-66 used `f"{seed:064x}"` which produces
    low-entropy patterns the new placeholder detector flags. Now derives from
    `hashlib.sha256(seed-bytes)` so fixtures pass placeholder detection
    while remaining deterministic.
    """
    import hashlib
    if seed == 0:
        # Preserve the genesis-anchor convention (all-zeros previous_hash)
        # which the placeholder detector exempts explicitly.
        return "0" * 64
    return hashlib.sha256(f"phase66-seal-fixture-{seed}".encode()).hexdigest()


def _write_ledger(tmp_path: Path, entries: list[str]) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(_ledger(entries), encoding="utf-8")
    return p


def _make_3_entry_chain(
    phase_num: int, start_seed: int = 1
) -> tuple[list[str], str]:
    """Build a valid 3-entry chain (audit, impl, seal) for the given phase.

    Returns (entries, last_chain_hash).
    """
    prev = _zhash(0)  # genesis
    entries = []
    chain = prev
    for i, kind in enumerate(["GATE TRIBUNAL", "IMPLEMENTATION", "SESSION SEAL"]):
        content = _zhash(start_seed + i)
        entries.append(_entry(100 + i, kind, phase_num, content, chain))
        chain = chain_hash(content, chain)
    return entries, chain


def test_check_passes_when_latest_entry_is_seal_for_current_phase(tmp_path):
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger = _write_ledger(tmp_path, entries)

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is True
    assert result.errors == []


def test_check_fails_when_latest_entry_is_not_a_seal(tmp_path):
    # Build chain ending with IMPLEMENTATION (no SEAL appended).
    prev = _zhash(0)
    entries = [
        _entry(100, "GATE TRIBUNAL", 47, _zhash(1), prev),
        _entry(101, "IMPLEMENTATION", 47, _zhash(2), chain_hash(_zhash(1), prev)),
    ]
    ledger = _write_ledger(tmp_path, entries)

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is False
    assert any("IMPLEMENTATION" in err for err in result.errors), result.errors
    assert any("SESSION SEAL" in err for err in result.errors), result.errors


def test_check_fails_when_seal_phase_number_mismatches(tmp_path):
    entries, _ = _make_3_entry_chain(phase_num=46)  # SEAL is for Phase 46
    ledger = _write_ledger(tmp_path, entries)

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is False
    assert any("47" in err and "46" in err for err in result.errors), result.errors


def test_check_fails_when_chain_hash_internally_inconsistent(tmp_path):
    # Build a 3-entry chain, then corrupt the SEAL's chain hash.
    prev = _zhash(0)
    c1, c2, c3 = _zhash(1), _zhash(2), _zhash(3)
    chain1 = chain_hash(c1, prev)
    chain2 = chain_hash(c2, chain1)
    bogus = _zhash(99)

    raw = (
        f"### Entry #100: GATE TRIBUNAL -- Phase 47 Pass 1 -- **PASS** (L1)\n\n"
        f"**Content Hash**: `{c1}`\n**Previous Hash**: `{prev}`\n**Chain Hash**: `{chain1}`\n"
        f"\n---\n\n"
        f"### Entry #101: IMPLEMENTATION -- Phase 47\n\n"
        f"**Content Hash**: `{c2}`\n**Previous Hash**: `{chain1}`\n**Chain Hash**: `{chain2}`\n"
        f"\n---\n\n"
        f"### Entry #102: SESSION SEAL -- Phase 47 feature substantiated\n\n"
        f"**Content Hash**: `{c3}`\n**Previous Hash**: `{chain2}`\n**Chain Hash**: `{bogus}`\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + raw, encoding="utf-8")

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is False
    assert any(bogus[:8] in err for err in result.errors), result.errors


def test_check_tolerates_disclosed_pre_anchor_failure(tmp_path):
    """GH #88: a re-anchored ledger carries disclosed pre-anchor failures by
    design. Entry #100's chain is genuinely broken; #101 and #102 are each
    internally consistent with their recorded predecessor (the post-anchor
    surface). check() must tolerate the pre-anchor failure and pass the
    structurally valid SESSION SEAL — verify_post_anchor classifies #100 as
    DISCLOSED_PRE_ANCHOR rather than tainting every downstream entry.

    Fails against the pre-fix code (strict ledger_hash.verify taints #101/#102
    and returns rc=1); passes once check() consumes verify_post_anchor.
    """
    prev = _zhash(0)
    c1, c2, c3 = _zhash(1), _zhash(2), _zhash(3)
    bogus_chain = _zhash(50)  # genuinely-broken chain for entry #100
    chain2 = chain_hash(c2, bogus_chain)
    chain3 = chain_hash(c3, chain2)

    raw = (
        f"### Entry #100: GATE TRIBUNAL -- Phase 47 Pass 1 -- **PASS** (L1)\n\n"
        f"**Content Hash**: `{c1}`\n**Previous Hash**: `{prev}`\n**Chain Hash**: `{bogus_chain}`\n"
        f"\n---\n\n"
        f"### Entry #101: IMPLEMENTATION -- Phase 47\n\n"
        f"**Content Hash**: `{c2}`\n**Previous Hash**: `{bogus_chain}`\n**Chain Hash**: `{chain2}`\n"
        f"\n---\n\n"
        f"### Entry #102: SESSION SEAL -- Phase 47 feature substantiated\n\n"
        f"**Content Hash**: `{c3}`\n**Previous Hash**: `{chain2}`\n**Chain Hash**: `{chain3}`\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + raw, encoding="utf-8")

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is True, result.errors
    assert result.errors == []


def test_check_fails_on_genuine_post_anchor_break(tmp_path):
    """The other half of the GH #88 contract: a genuine POST-anchor break must
    still fail. The SEAL (#102, the highest entry) carries a low-entropy
    placeholder previous_hash; its chain_hash is computed consistently from
    that placeholder so check()'s latest-entry internal check passes and the
    full-chain step is reached. verify_post_anchor flags the placeholder,
    classifies #102 as a post-boundary failure, and returns rc=1.

    Guard coverage — passes both before and after the fix (strict verify also
    rejects a placeholder); confirms the switch does not lose detection of
    genuine post-anchor breaks.
    """
    prev = _zhash(0)
    c1, c2, c3 = _zhash(1), _zhash(2), _zhash(3)
    chain1 = chain_hash(c1, prev)
    chain2 = chain_hash(c2, chain1)
    placeholder = f"{7:064x}"  # 2 distinct hex chars -> is_placeholder_pattern
    chain3 = chain_hash(c3, placeholder)

    raw = (
        f"### Entry #100: GATE TRIBUNAL -- Phase 47 Pass 1 -- **PASS** (L1)\n\n"
        f"**Content Hash**: `{c1}`\n**Previous Hash**: `{prev}`\n**Chain Hash**: `{chain1}`\n"
        f"\n---\n\n"
        f"### Entry #101: IMPLEMENTATION -- Phase 47\n\n"
        f"**Content Hash**: `{c2}`\n**Previous Hash**: `{chain1}`\n**Chain Hash**: `{chain2}`\n"
        f"\n---\n\n"
        f"### Entry #102: SESSION SEAL -- Phase 47 feature substantiated\n\n"
        f"**Content Hash**: `{c3}`\n**Previous Hash**: `{placeholder}`\n**Chain Hash**: `{chain3}`\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + raw, encoding="utf-8")

    result = seal_entry_check.check(ledger_path=ledger, phase_num=47)

    assert result.ok is False
    assert any("full chain verification" in err for err in result.errors), result.errors


def test_check_replays_phase_46_original_gap(tmp_path):
    """Meta-test: replays Phase 46's pre-remediation state.

    The original Phase 46 substantiate sealed v0.33.0 without writing ledger
    entries; the latest entry was #146 (Phase 44 seal). This is the historical
    gap Phase 47 was designed to catch. The check must report ok=False when
    invoked with phase_num=46 against a ledger whose latest seal is Phase 44.
    """
    prev = _zhash(0)
    c1, c2, c3 = _zhash(10), _zhash(11), _zhash(12)
    chain1 = chain_hash(c1, prev)
    chain2 = chain_hash(c2, chain1)
    chain3 = chain_hash(c3, chain2)
    raw = (
        f"### Entry #144: GATE TRIBUNAL -- Phase 44 Pass 1 -- **PASS** (L1)\n\n"
        f"**Content Hash**: `{c1}`\n**Previous Hash**: `{prev}`\n**Chain Hash**: `{chain1}`\n"
        f"\n---\n\n"
        f"### Entry #145: IMPLEMENTATION -- Phase 44\n\n"
        f"**Content Hash**: `{c2}`\n**Previous Hash**: `{chain1}`\n**Chain Hash**: `{chain2}`\n"
        f"\n---\n\n"
        f"### Entry #146: SESSION SEAL -- Phase 44 hotfix substantiated\n\n"
        f"**Content Hash**: `{c3}`\n**Previous Hash**: `{chain2}`\n**Chain Hash**: `{chain3}`\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + raw, encoding="utf-8")

    result = seal_entry_check.check(ledger_path=ledger, phase_num=46)

    assert result.ok is False
    # The error must name the phase mismatch (latest seal is Phase 44, expected 46).
    assert any("46" in err and "44" in err for err in result.errors), result.errors


def _write_synthetic_plan(tmp_path: Path, phase_num: int) -> Path:
    """Write a minimal plan file matching the plan-qor-phaseNN-slug.md naming convention."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    p = docs / f"plan-qor-phase{phase_num}-test-fixture.md"
    p.write_text(
        f"# Plan: Phase {phase_num} test fixture\n\n**change_class**: feature\n",
        encoding="utf-8",
    )
    return p


def test_cli_resolves_phase_from_plan_path_argv(tmp_path):
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger = _write_ledger(tmp_path, entries)
    plan = _write_synthetic_plan(tmp_path, 47)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qor.reliability.seal_entry_check",
            "--ledger",
            str(ledger),
            "--plan",
            str(plan),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    assert result.returncode == 0, (
        f"expected exit 0 on passing fixture, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "OK" in result.stdout


def test_cli_exits_zero_on_pass_and_one_on_fail(tmp_path):
    # Pass case
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger_pass = _write_ledger(tmp_path, entries)
    plan = _write_synthetic_plan(tmp_path, 47)

    res_pass = subprocess.run(
        [
            sys.executable,
            "-m",
            "qor.reliability.seal_entry_check",
            "--ledger",
            str(ledger_pass),
            "--plan",
            str(plan),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert res_pass.returncode == 0, res_pass.stderr

    # Fail case: phase mismatch (ledger has Phase 47 SEAL; plan declares Phase 99)
    plan_fail = _write_synthetic_plan(tmp_path, 99)
    res_fail = subprocess.run(
        [
            sys.executable,
            "-m",
            "qor.reliability.seal_entry_check",
            "--ledger",
            str(ledger_pass),
            "--plan",
            str(plan_fail),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert res_fail.returncode == 1, (
        f"expected exit 1, got {res_fail.returncode}; stderr={res_fail.stderr!r}"
    )
    assert res_fail.stderr.strip() != ""


def test_cli_rejects_path_with_shell_metacharacters_safely(tmp_path):
    """Confirms argv-form invocation eliminates the OWASP A03 vector flagged
    in Pass 1 V-3. A path containing shell metacharacters is passed via
    argparse, not via shell interpolation; the CLI must either process it
    correctly or fail with a Python-level error — never execute injected code."""
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger = _write_ledger(tmp_path, entries)

    # Build a plan path with a single quote and dollar sign in the filename.
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    weird_name = "plan-qor-phase47-weird's$path-fixture.md"
    plan = docs / weird_name
    plan.write_text(
        "# Plan: Phase 47 weird path\n\n**change_class**: feature\n",
        encoding="utf-8",
    )

    # Sentinel that would only appear if shell injection executed arbitrary code.
    sentinel = tmp_path / "INJECTION_OCCURRED"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qor.reliability.seal_entry_check",
            "--ledger",
            str(ledger),
            "--plan",
            str(plan),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    # The sentinel must NOT exist regardless of the CLI's exit code.
    assert not sentinel.exists(), (
        "shell injection occurred: sentinel file was created during CLI invocation"
    )
    # The CLI either succeeded (path resolves) or failed gracefully with a
    # Python-level error message. It must not have produced a shell error.
    assert result.returncode in (0, 1)
    if result.returncode == 1:
        assert result.stderr.strip() != ""


# --- GH #223: non-conforming plan filename falls back to ledger-derived phase ---

def test_main_nonconforming_plan_name_falls_back_and_passes(tmp_path, capsys):
    """A valid SESSION SEAL whose --plan uses a downstream `plan-<slug>.md` name
    must PASS (rc 0) with a WARN, not hard-fail on the filename pattern."""
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger = _write_ledger(tmp_path, entries)
    rc = seal_entry_check._main(
        ["--ledger", str(ledger), "--plan", "plan-monitor-theme-inheritance.md"]
    )
    assert rc == 0
    err = capsys.readouterr().err
    assert "WARN" in err and "plan filename" in err


def test_main_nonconforming_plan_name_still_fails_broken_entry(tmp_path):
    """The fallback is not a blanket bypass: a non-conforming plan name with a
    latest entry that is NOT a SESSION SEAL still FAILs (rc 1)."""
    prev = _zhash(0)
    entries = [
        _entry(100, "GATE TRIBUNAL", 47, _zhash(1), prev),
        _entry(101, "IMPLEMENTATION", 47, _zhash(2), chain_hash(_zhash(1), prev)),
    ]
    ledger = _write_ledger(tmp_path, entries)
    rc = seal_entry_check._main(
        ["--ledger", str(ledger), "--plan", "plan-no-phase.md"]
    )
    assert rc == 1


def test_main_conforming_plan_name_uses_filename_phase(tmp_path):
    """A conforming plan name still derives the phase from the FILENAME: a
    filename phase (158) that disagrees with the latest entry's phase (47)
    yields a phase-mismatch FAIL, proving the conforming path is unchanged."""
    entries, _ = _make_3_entry_chain(phase_num=47)
    ledger = _write_ledger(tmp_path, entries)
    rc = seal_entry_check._main(
        ["--ledger", str(ledger), "--plan", "plan-qor-phase158-x.md"]
    )
    assert rc == 1
