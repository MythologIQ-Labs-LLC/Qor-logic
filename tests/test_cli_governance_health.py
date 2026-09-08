"""Phase 109 D-109.3: governance-health CLI exit-code contract.

0 == all OK, 1 == MISSING/INCOMPLETE/UNINITIALIZED, 2 == DAMAGED. Tests invoke
the module CLI as a subprocess and assert on its real exit code.
"""
from __future__ import annotations

import json
import subprocess
import sys

_HEALTHY = {
    "META_LEDGER.md": "# QoreLogic Meta Ledger\n\n### Entry #1: SEAL\nsealed.\n",
    "CONCEPT.md": "# Project Concept\n\nWhy: ship governed software safely.\n",
    "ARCHITECTURE_PLAN.md": "# Architecture Plan\n\nRisk Grade L2. Modules: cli, scripts.\n",
    "SYSTEM_STATE.md": "# System State\n\nGovernance surfaces documented here.\n",
    "SHADOW_GENOME.md": "# Shadow Genome\n\nNo open failures.\n",
    "BACKLOG.md": "# Backlog\n\nNo open blockers.\n",
    "FEATURE_INDEX.md": "# Feature Index\n\nNo user-facing features yet.\n",
    "GOVERNANCE_INDEX.md": "# Governance Index\n\nLast Reviewed 2026-01-01. Tier 1 canonical docs mapped.\n",
}


def _run(repo_root):
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.governance_health", "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
    )


def test_cli_exit_zero_for_healthy_workspace(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, body in _HEALTHY.items():
        (docs / name).write_text(body, encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode == 0, (result.returncode, result.stdout)


def test_cli_exit_two_for_damaged_workspace(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text("%%% not a ledger %%%\ngarbage\n", encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode == 2, (result.returncode, result.stdout)


# ----- Phase 273 (GH #444): the no-raw-diagnostics contract, at its surfaces -----
#
# GH #268 removed raw FAIL/TAINTED tokens from governance-health output because
# they contradicted an OK verdict when they reached the CLI, the JSON payload
# and the nightly summary. The only assertion guarding that ran IN-PROCESS
# against a function that returns the reason rather than printing it, so the
# contract held at these three surfaces by construction rather than by test.
#
# The fixture matters more than the assertions. A malformed ledger is rejected
# before either verifier call, so the verifiers never run and the tokens can
# never appear -- a test on that fixture stays green even with the suppression
# deleted. This uses the TOLERATED ledger instead: entry #2's chain math fails
# while the file classifies OK, which is precisely the contradiction GH #268
# names, and it is the shape where a bleed does real harm.


def _tolerated_ledger(base):
    """A ledger that classifies OK while its raw verifier reports failures."""
    import hashlib

    def _h(seed):
        return hashlib.sha256(seed.encode()).hexdigest()

    from qor.scripts import ledger_hash

    c1, p1 = _h("c1"), _h("p1")
    ch1 = ledger_hash.chain_hash(c1, p1)
    c2 = _h("c2")
    ch2_wrong = ledger_hash.chain_hash(_h("x"), _h("y"))
    c3 = _h("c3")
    ch3 = ledger_hash.chain_hash(c3, ch2_wrong)

    def entry(n, title, content, prev, recorded):
        return (
            f"### Entry #{n}: {title}\n\n"
            f"**Content Hash**: `{content}`\n"
            f"**Previous Hash**: `{prev}`\n"
            f"**Chain Hash (Merkle seal)**: `{recorded}`\n\n---\n\n"
        )

    docs = base / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "META_LEDGER.md").write_text(
        "# QoreLogic Meta Ledger\n\n"
        + entry(1, "A", c1, p1, ch1)
        + entry(2, "B", c2, ch1, ch2_wrong)
        + entry(3, "C", c3, ch2_wrong, ch3),
        encoding="utf-8",
    )
    conf = base / ".qorlogic"
    conf.mkdir(parents=True, exist_ok=True)
    (conf / "config.json").write_text(
        json.dumps({"ledger": {"post_anchor_boundary": 2}}), encoding="utf-8"
    )


def test_cli_output_carries_no_raw_fail_token(tmp_path):
    """Surface 1. Asserted over BOTH streams: every FAIL/TAINTED message is
    emitted to stderr, so a stdout-only assertion cannot observe the bleed."""
    _tolerated_ledger(tmp_path)
    result = _run(tmp_path)
    assert "FAIL Entry" not in (result.stdout + result.stderr), (
        result.stdout, result.stderr
    )


def test_cli_output_carries_no_tainted_token(tmp_path):
    _tolerated_ledger(tmp_path)
    result = _run(tmp_path)
    assert "TAINTED" not in (result.stdout + result.stderr), (result.stdout, result.stderr)


def test_deleting_the_redirect_makes_the_fixture_bleed(tmp_path, monkeypatch):
    """The row that makes the two above mean anything.

    Runs on the SAME fixture and removes only the suppression, by shadowing the
    MODULE-LOCAL `contextlib` name -- patching attributes on the real module
    would affect every other consumer for the duration. If the tokens still do
    not appear, the fixture cannot bleed and the assertions above pin nothing.
    """
    import contextlib as _real_contextlib
    import io as _io

    from qor.scripts import governance_health

    _tolerated_ledger(tmp_path)

    class _NoSuppression:
        @staticmethod
        def redirect_stdout(_target):
            return _real_contextlib.nullcontext()

        @staticmethod
        def redirect_stderr(_target):
            return _real_contextlib.nullcontext()

    monkeypatch.setattr(governance_health, "contextlib", _NoSuppression)

    buf_out, buf_err = _io.StringIO(), _io.StringIO()
    with _real_contextlib.redirect_stdout(buf_out), _real_contextlib.redirect_stderr(buf_err):
        governance_health._classify_one(tmp_path, "docs/META_LEDGER.md", True)
    bled = buf_out.getvalue() + buf_err.getvalue()

    assert "FAIL Entry" in bled or "TAINTED" in bled, (
        "the fixture cannot produce raw tokens even with suppression removed, "
        "so the assertions guarding them pin nothing"
    )


def test_status_json_governance_health_summary_carries_no_raw_tokens(tmp_path):
    """Surface 2: the JSON payload the nightly workflow posts.

    Scoped to the governance-health check's own `summary`, deliberately, and
    NOT payload-wide. Two things in a wider assertion would be red for correct
    reasons and neither is a bleed: status_json prints its own `FAIL <check-id>`
    vocabulary for any failing check, and the ledger-chain check runs the raw
    verifier directly, so a raw `FAIL Entry #N` legitimately becomes ITS
    summary. Suppression is a governance_health concern only.

    Driven with an explicit single-check registry rather than the default
    ladder, which pulls checks that shell out to git and would couple this to
    environment this phase does not touch.

    Non-vacuous by construction: verification runs inside the check before its
    print loop, and the runner merges stderr into one buffer, so a bleed would
    be the FIRST non-empty line and therefore the summary.
    """
    from qor.scripts import status_json

    _tolerated_ledger(tmp_path)
    registry = [
        status_json.Check(
            id="governance-health",
            module="qor.scripts.governance_health",
            argv=["--repo-root", str(tmp_path)],
        )
    ]
    payload = status_json.run_all(registry)
    summary = next(c["summary"] for c in payload["checks"] if c["id"] == "governance-health")

    assert "FAIL Entry" not in summary, summary
    assert "TAINTED" not in summary, summary
