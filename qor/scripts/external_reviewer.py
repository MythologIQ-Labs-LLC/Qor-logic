"""External-reviewer subprocess bridge (Phase 123; GH #160).

Dispatches the #50 reviewer I/O contract (qor-audit/references/adversarial-mode.md)
to an operator-configured external reviewer process and ingests its verdict, with
graceful fallback to in-harness review when the reviewer is absent or fails.

The command is resolved from `.qorlogic/config.json` -> `external_reviewer.command`
(an argv list, operator-trusted). Transport is JSON over stdin/stdout. The command
runs list-form (no shell), is timeout-bounded, and its output is contract-validated
before use. Any failure is returned as a `ReviewOutcome(status="fallback")` value,
never raised — the audit then proceeds solo and logs `capability_shortfall`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_TIMEOUT = 120.0


@dataclass(frozen=True)
class ReviewOutcome:
    status: str          # "ok" | "fallback"
    reason: str
    review: dict | None


def resolve_reviewer_command(config_path: Path) -> list[str] | None:
    """Read `.qorlogic/config.json` -> external_reviewer.command (argv list).
    Tolerant parse (mirrors qor.tone._config_tone): None on absent file/field or
    malformed JSON."""
    if not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    section = data.get("external_reviewer")
    if not isinstance(section, dict):
        return None
    command = section.get("command")
    if isinstance(command, list) and command and all(isinstance(x, str) for x in command):
        return command
    return None


def validate_review_output(obj: object) -> bool:
    """True iff obj matches the adversarial-mode output contract."""
    if not isinstance(obj, dict):
        return False
    if not isinstance(obj.get("critiques"), list):
        return False
    if not isinstance(obj.get("confidence"), (int, float)) or isinstance(obj.get("confidence"), bool):
        return False
    if not isinstance(obj.get("model"), str):
        return False
    return isinstance(obj.get("ts"), str)


def dispatch_review(
    review_input: dict, command: list[str], *, timeout: float = _DEFAULT_TIMEOUT
) -> dict | None:
    """Run command (list-form, no shell), write review_input JSON to stdin, parse
    stdout as JSON. None on nonzero exit, timeout, OSError, or non-contract JSON."""
    try:
        proc = subprocess.run(
            command,
            input=json.dumps(review_input),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    try:
        parsed = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if validate_review_output(parsed) else None


def run_external_review(
    review_input: dict, config_path: Path, *, timeout: float = _DEFAULT_TIMEOUT
) -> ReviewOutcome:
    """Single entry point. Resolve the command and dispatch; any miss/failure is a
    `fallback` outcome (never an exception)."""
    command = resolve_reviewer_command(config_path)
    if command is None:
        return ReviewOutcome("fallback", "no reviewer configured", None)
    review = dispatch_review(review_input, command, timeout=timeout)
    if review is None:
        return ReviewOutcome("fallback", "reviewer unavailable or returned invalid output", None)
    return ReviewOutcome("ok", "", review)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="external_reviewer")
    parser.add_argument("--config", default=".qorlogic/config.json")
    parser.add_argument("--input", required=True, help="path to reviewer-input JSON")
    parser.add_argument("--timeout", type=float, default=_DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)

    try:
        review_input = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"status": "fallback", "reason": f"bad input: {exc}", "review": None}))
        return 0

    outcome = run_external_review(review_input, Path(args.config), timeout=args.timeout)
    print(json.dumps({"status": outcome.status, "reason": outcome.reason, "review": outcome.review}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
