"""Phase 119 (GH #148): `qor-logic reconcile propose|authorize` CLI.

Subprocess tests invoke `qor.cli` directly (the code under test), never a
possibly-stale PATH `qor-logic`. The end-to-end test proves the real fix: a
duplicate-previous_hash consumer ledger goes from FAIL to clean strict
verify-ledger after propose -> authorize.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.ledger_hash import chain_hash

REPO_ROOT = Path(__file__).resolve().parent.parent


def _hex(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _entry(num: int, content: str, previous: str, *, chain_override: str | None = None) -> str:
    chain = chain_override if chain_override is not None else chain_hash(content, previous)
    return textwrap.dedent(
        f"""

        ### Entry #{num}: TEST

        **Content Hash**: `{content}`

        **Previous Hash**: `{previous}`

        **Chain Hash**: `{chain}`
        """
    )


def _corpus_ledger(tmp_path: Path) -> Path:
    h1, h2 = _hex("H1"), _hex("H2")
    text = "# META_LEDGER\n" + "".join([
        _entry(16, _hex("c16"), h1, chain_override=_hex("bad16")),
        _entry(17, _hex("c17"), h1, chain_override=_hex("bad17")),
        _entry(18, _hex("c18"), h2, chain_override=_hex("bad18")),
        _entry(19, _hex("c19"), h2, chain_override=_hex("bad19")),
        _entry(20, _hex("c20"), _hex("uniq")),
    ])
    p = tmp_path / "META_LEDGER.md"
    p.write_text(text, encoding="utf-8")
    return p


def _cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "qor.cli", *args],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True,
    )


def test_propose_writes_pending_proposal(tmp_path):
    led = _corpus_ledger(tmp_path)
    before = led.read_bytes()
    out = tmp_path / "p.json"
    r = _cli("reconcile", "propose", "--ledger", str(led), "--out", str(out))
    assert r.returncode == 0, r.stderr
    import json
    proposal = json.loads(out.read_text(encoding="utf-8"))
    assert proposal["status"] == "pending"
    assert sorted(proposal["residual_entry_nums"]) == [16, 17, 18, 19]
    assert led.read_bytes() == before, "propose must not mutate the ledger"


def test_authorize_appends_entry_and_strict_verify_passes(tmp_path):
    led = _corpus_ledger(tmp_path)
    out = tmp_path / "p.json"
    assert _cli("reconcile", "propose", "--ledger", str(led), "--out", str(out)).returncode == 0
    # Raw ledger FAILs strict verify (the consumer blocker).
    pre = _cli("verify-ledger", "--ledger", str(led))
    assert pre.returncode != 0
    # Authorize -> append RECONCILIATION entry.
    auth = _cli("reconcile", "authorize", "--proposal", str(out), "--ledger", str(led))
    assert auth.returncode == 0, auth.stderr
    # Strict verify (no flag) now passes.
    post = _cli("verify-ledger", "--ledger", str(led))
    assert post.returncode == 0, post.stderr
    assert "DISCLOSED_RECONCILED" in post.stdout


def test_authorize_requires_proposal_arg(tmp_path):
    led = _corpus_ledger(tmp_path)
    r = _cli("reconcile", "authorize", "--ledger", str(led))
    assert r.returncode != 0, "authorize without --proposal must fail (two-stage enforced)"


def test_authorize_rejects_stale_proposal(tmp_path):
    led = _corpus_ledger(tmp_path)
    out = tmp_path / "p.json"
    assert _cli("reconcile", "propose", "--ledger", str(led), "--out", str(out)).returncode == 0
    # Mutate the ledger residual after proposing: add a new duplicate pair.
    led.write_text(
        led.read_text(encoding="utf-8")
        + _entry(21, _hex("c21"), _hex("H9"), chain_override=_hex("bad21"))
        + _entry(22, _hex("c22"), _hex("H9"), chain_override=_hex("bad22")),
        encoding="utf-8",
    )
    r = _cli("reconcile", "authorize", "--proposal", str(out), "--ledger", str(led))
    assert r.returncode != 0
    assert "drift" in (r.stdout + r.stderr).lower()
