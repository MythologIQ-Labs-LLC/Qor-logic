"""Phase 52: gate-chain completeness verifier.

Walks META_LEDGER.md SESSION SEAL entries with phase >= phase_min;
extracts the session_id from each; asserts each session has all four
gate artifacts (plan/audit/implement/substantiate).json under
.qor/gates/<sid>/. ABORTs the caller (typically /qor-substantiate
Step 7.8 or pre-merge CI) on any gap.

Closes the bypass surface where Phases 46/48/49/50 sealed without
writing gate artifacts at all (per /qor-debug Phase 1 root cause).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_PHASES = ("plan", "audit", "implement", "substantiate")

SEAL_HEADER_RE = re.compile(r"^### Entry #(\d+):\s*SESSION SEAL", re.MULTILINE)
SESSION_LINE_RE = re.compile(r"^\*\*Session\*\*:\s*`?([0-9a-zA-Z._-]+)`?", re.MULTILINE)
PHASE_NUM_RE = re.compile(r"Phase\s+(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class CompletenessResult:
    ok: bool
    missing: list[tuple[int, str]] = field(default_factory=list)
    sessions_checked: list[str] = field(default_factory=list)


def _extract_seal_sessions(text: str, phase_min: int) -> dict[int, str]:
    """Return {phase_num: session_id} for SESSION SEAL entries with phase >= phase_min."""
    out: dict[int, str] = {}
    for match in SEAL_HEADER_RE.finditer(text):
        body_start = match.end()
        # Body extends until next "^### " or EOF; cap at 2000 chars for parse efficiency
        next_header = re.search(r"^### ", text[body_start:], re.MULTILINE)
        body_end = body_start + (next_header.start() if next_header else 2000)
        body = text[body_start:body_end]
        phase_match = PHASE_NUM_RE.search(body[:300])
        sess_match = SESSION_LINE_RE.search(body)
        if phase_match and sess_match:
            phase_num = int(phase_match.group(1))
            if phase_num >= phase_min:
                out[phase_num] = sess_match.group(1)
    return out


def check(
    repo_root: Path,
    *,
    phase_min: int = 52,
    ledger_path: Path | None = None,
    gates_root: Path | None = None,
) -> CompletenessResult:
    """Assert every sealed phase >= phase_min has all four gate artifacts."""
    ledger = ledger_path or repo_root / "docs" / "META_LEDGER.md"
    gates = gates_root or repo_root / ".qor" / "gates"
    if not ledger.is_file():
        return CompletenessResult(
            ok=False,
            missing=[(0, f"ledger missing: {ledger}")],
            sessions_checked=[],
        )
    text = ledger.read_text(encoding="utf-8")
    by_phase = _extract_seal_sessions(text, phase_min)
    missing: list[tuple[int, str]] = []
    for phase_num, sid in sorted(by_phase.items()):
        sess_dir = gates / sid
        for required in REQUIRED_PHASES:
            artifact = sess_dir / f"{required}.json"
            if not artifact.is_file():
                missing.append((phase_num, f"{sid}/{required}.json"))
    return CompletenessResult(
        ok=not missing,
        missing=missing,
        sessions_checked=list(by_phase.values()),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--phase-min", type=int, default=52)
    args = ap.parse_args(argv)
    result = check(args.repo_root, phase_min=args.phase_min)
    if result.ok:
        print(
            f"OK: gate-chain complete for {len(result.sessions_checked)} "
            f"sessions (phase >= {args.phase_min})"
        )
        return 0
    print(f"FAIL: gate-chain incomplete; {len(result.missing)} missing artifacts:")
    for phase_num, what in result.missing:
        print(f"  phase {phase_num}: {what}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
