"""Aggregate governance-health status with a machine-readable JSON contract.

Phase 165 (GH #240 + #250 part a): runs the read-only check ladder in-process
and prints human lines followed by exactly ONE JSON object as the final stdout
line (extractable via `grep '^{' | tail -1`, the drift-detection contract of
an external QA exemplar). Exit 0 iff every check passed. `--self-test` validates the
aggregation logic against a synthetic pass+fail registry before any consumer
trusts a live verdict.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import importlib
import inspect
import io
import json
import sys
import unittest.mock
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

_SUMMARY_LIMIT = 200


@dataclass
class Check:
    """One health check: a callable returning (exit_code, output_text)."""

    id: str
    fn: Callable[[], tuple[int, str]] | None = None
    module: str = ""
    argv: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.fn is None:
            if not self.module:
                raise ValueError(f"check {self.id}: needs fn or module")
            self.fn = _module_main_runner(self.module, self.argv)


def _module_main_runner(module: str, argv: list[str]) -> Callable[[], tuple[int, str]]:
    def run() -> tuple[int, str]:
        mod = importlib.import_module(module)
        takes_argv = bool(inspect.signature(mod.main).parameters)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                if takes_argv:
                    rc = mod.main(list(argv))
                else:  # main() parses sys.argv itself (e.g., ledger_hash)
                    with unittest.mock.patch.object(sys, "argv", [module, *argv]):
                        rc = mod.main()
            except SystemExit as exc:  # argparse errors / sys.exit paths
                rc = int(exc.code or 0)
        return int(rc or 0), buf.getvalue()

    return run


def run_check(check: Check) -> dict:
    """Execute one check; never raises (an exception records exit 3)."""
    try:
        rc, output = check.fn()
    except Exception as exc:  # noqa: BLE001 -- aggregate must survive any check
        rc, output = 3, f"{type(exc).__name__}: {exc}"
    first_line = next((ln for ln in output.splitlines() if ln.strip()), "")
    return {
        "id": check.id,
        "ok": rc == 0,
        "exit": rc,
        "summary": first_line[:_SUMMARY_LIMIT],
    }


def run_all(checks: list[Check]) -> dict:
    results = [run_check(c) for c in checks]
    return {
        "schema_version": "1",
        "ts": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": results,
        "overall_ok": all(r["ok"] for r in results),
    }


def default_registry(repo_root: Path) -> list[Check]:
    """The bare-main-valid read-only ladder (plan LD-1)."""
    root = str(repo_root)
    ledger = str(Path(repo_root) / "docs" / "META_LEDGER.md")
    return [
        Check(id="governance-health", module="qor.scripts.governance_health",
              argv=["--repo-root", root, "--profile", "skill-entry"]),
        Check(id="ledger-chain", module="qor.scripts.ledger_hash",
              argv=["verify", ledger]),
        Check(id="seal-artifacts", module="qor.scripts.seal_artifacts",
              argv=["--check", "--skip-tests", "--repo-root", root]),
        Check(id="gate-chain-completeness", module="qor.reliability.gate_chain_completeness",
              argv=["--repo-root", root, "--phase-min", "52"]),
        Check(id="gate-provenance", module="qor.scripts.gate_provenance",
              argv=["verify-committed", "--repo-root", root, "--phase-min", "158"]),
        Check(id="governance-index", module="qor.scripts.governance_index",
              argv=["--repo-root", root, "--cross-check-ledger"]),
    ]


def _self_test() -> int:
    report = run_all([
        Check(id="synthetic-pass", fn=lambda: (0, "OK: synthetic")),
        Check(id="synthetic-fail", fn=lambda: (1, "FAIL: synthetic")),
    ])
    checks = {c["id"]: c for c in report["checks"]}
    failures = []
    if report["overall_ok"] is not False:
        failures.append("overall_ok should be False with a failing check")
    if checks["synthetic-pass"]["ok"] is not True or checks["synthetic-pass"]["exit"] != 0:
        failures.append("passing check misreported")
    if checks["synthetic-fail"]["ok"] is not False or checks["synthetic-fail"]["exit"] != 1:
        failures.append("failing check misreported")
    if report["schema_version"] != "1" or "ts" not in report:
        failures.append("schema fields missing")
    if failures:
        for f in failures:
            print(f"self-test FAILED: {f}")
        return 1
    print("self-test PASSED")
    return 0


def main(argv: list[str] | None = None, registry: list[Check] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--self-test", action="store_true",
                    help="validate aggregation logic against a synthetic registry")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    checks = registry if registry is not None else default_registry(args.repo_root)
    report = run_all(checks)
    for c in report["checks"]:
        state = "OK" if c["ok"] else "FAIL"
        print(f"{state} {c['id']}: {c['summary']}")
    print(json.dumps(report))
    return 0 if report["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
