"""Phase 66 (#55): qor-logic verify-ledger CLI flags.

Adds three flags to the existing verify-ledger subcommand:
- --ledger PATH: explicit ledger path override.
- --post-anchor: route to verify_post_anchor mode.
- --boundary N: pin post-anchor boundary.

Locks the CLI contract so skill prose can document these invocations
and downstream consumer workspaces can adopt the post-anchor wrapper
pattern from Issue #55 directly via the canonical CLI.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor import cli
from qor.scripts import ledger_hash as lh


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


def _write_clean_one_entry_ledger(tmp: Path) -> Path:
    content = _digest(b"phase66-cli-fixture")
    prev = "0" * 64
    chain = lh.chain_hash(content, prev)
    body = (
        f"### Entry #1: CLI TEST\n\n"
        f"**Content Hash**: `{content}`\n\n"
        f"**Previous Hash**: `{prev}`\n\n"
        f"**Chain Hash**: `{chain}`\n\n"
    )
    p = tmp / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_cli_accepts_explicit_ledger_path(tmp_path, capsys):
    """`qor-logic verify-ledger --ledger PATH` reads the explicit ledger."""
    ledger = _write_clean_one_entry_ledger(tmp_path)
    rc = cli.main(["verify-ledger", "--ledger", str(ledger)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Entry #1: chain hash verified" in out


def test_cli_post_anchor_flag_routes_to_post_anchor_verify(tmp_path, capsys):
    """`--post-anchor` produces the post-anchor 'boundary=#N' summary line."""
    ledger = _write_clean_one_entry_ledger(tmp_path)
    rc = cli.main(["verify-ledger", "--ledger", str(ledger), "--post-anchor"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "post-anchor clean" in out
    assert "boundary=#1" in out


def test_cli_boundary_flag_overrides_auto_detection(tmp_path, capsys):
    """`--boundary 1` pins the boundary at entry #1 regardless of content."""
    ledger = _write_clean_one_entry_ledger(tmp_path)
    rc = cli.main(["verify-ledger", "--ledger", str(ledger), "--post-anchor", "--boundary", "1"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "boundary=#1" in out
