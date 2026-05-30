"""reconcile subcommand handlers (Phase 119; GH #148).

Two-stage, operator-authorized, forward-only META_LEDGER reconciliation,
mirroring the Phase 36 B19 pending->authorized contract:

  reconcile propose   -> writes a pending proposal artifact (read-only)
  reconcile authorize -> appends the RECONCILIATION entry (the explicit
                         --proposal <path> arg is the sole operator signal)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qor.scripts import reconcile, shadow_process


def _default_proposal_path(ledger: Path) -> Path:
    return Path(ledger).resolve().parent / "reconcile-proposal.json"


def do_propose(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    if not ledger.exists():
        print(f"ERROR: ledger not found: {ledger}", file=sys.stderr)
        return 1
    proposal = reconcile.build_proposal(ledger, ts=shadow_process.now_iso())
    out = Path(args.out) if args.out else _default_proposal_path(ledger)
    out.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    nums = proposal["residual_entry_nums"]
    if not nums:
        print(f"No duplicate-previous_hash residual found in {ledger}. Nothing to reconcile.")
        return 0
    print(f"Reconciliation proposal (pending) written to {out}")
    print(f"  residual entries: {', '.join('#' + str(n) for n in nums)}")
    print(f"  shared previous-hashes: {len(proposal['previous_hashes'])}")
    print(f"  proposal_id: {proposal['proposal_id']}")
    print("Authorize with: qor-logic reconcile authorize "
          f"--proposal {out} --ledger {ledger}")
    return 0


def do_authorize(args: argparse.Namespace) -> int:
    proposal_path = Path(args.proposal)
    if not proposal_path.exists():
        print(f"ERROR: proposal not found: {proposal_path}", file=sys.stderr)
        return 1
    ledger = Path(args.ledger)
    if not ledger.exists():
        print(f"ERROR: ledger not found: {ledger}", file=sys.stderr)
        return 1
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    # Drift guard: the proposal's residual must still match the current ledger.
    current = reconcile.build_proposal(ledger, ts=proposal.get("ts", ""))
    if sorted(current["residual_entry_nums"]) != sorted(proposal.get("residual_entry_nums", [])):
        print(
            "ERROR: ledger residual drifted since proposal was written; re-run "
            "`reconcile propose` before authorizing.",
            file=sys.stderr,
        )
        return 1
    result = reconcile.append_reconciliation_entry(
        ledger, proposal, ts=shadow_process.now_iso()
    )
    proposal["status"] = "authorized"
    proposal["reconciliation_entry_num"] = result["entry_num"]
    proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    print(f"Authorized. Appended RECONCILIATION Entry #{result['entry_num']} "
          f"(entry_id {result['entry_id']}) to {ledger}.")
    print(f"  reconciled: {', '.join('#' + str(n) for n in result['reconciled_entry_nums'])}")
    print("Verify with: qor-logic verify-ledger --ledger " + str(ledger))
    return 0


def register(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the reconcile subcommand group."""
    sp = sub.add_parser(
        "reconcile",
        help="forward-only operator-authorized META_LEDGER reconciliation (GH #148)",
    )
    rec_sub = sp.add_subparsers(dest="reconcile_command", metavar="<subcommand>")

    sp_propose = rec_sub.add_parser("propose", help="detect duplicate-previous_hash residual; write a pending proposal")
    sp_propose.add_argument("--ledger", required=True, help="path to the META_LEDGER.md to reconcile")
    sp_propose.add_argument("--out", default=None, help="proposal output path (default: alongside the ledger)")

    sp_auth = rec_sub.add_parser("authorize", help="append the RECONCILIATION entry for a pending proposal")
    sp_auth.add_argument("--proposal", required=True, help="path to the pending proposal JSON (operator signal)")
    sp_auth.add_argument("--ledger", required=True, help="path to the META_LEDGER.md to reconcile")

    return sp


def dispatch(args: argparse.Namespace) -> int | None:
    cmd = getattr(args, "reconcile_command", None)
    if cmd == "propose":
        return do_propose(args)
    if cmd == "authorize":
        return do_authorize(args)
    return None
