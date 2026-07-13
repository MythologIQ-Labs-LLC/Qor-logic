"""Phase 192 (GH #277): per-requirement structural verify over declared deltas.

Produces the qa_evidence coverage-pillar payload the module defers by
design. Verifies structure and declared-surface existence, never scenario
semantics (correctness stays a Judge duty -- no fabricated verification):
every ADDED/MODIFIED requirement in a declared delta must pass the grammar
lint, and when the declaration carries ``evidence`` the path must exist.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from qor.scripts.spec_lint import check

_REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.MULTILINE)
_SECTION_RE = re.compile(r"^## (ADDED|MODIFIED) Requirements\s*$", re.MULTILINE)


def _added_modified_requirements(delta_text: str) -> list[tuple[str, str]]:
    """[(requirement_name, block_body)] from ADDED/MODIFIED sections."""
    out: list[tuple[str, str]] = []
    sections = list(_SECTION_RE.finditer(delta_text))
    bounds = [m.end() for m in sections] + [len(delta_text)]
    for idx, section in enumerate(sections):
        body = delta_text[bounds[idx]:
                          sections[idx + 1].start() if idx + 1 < len(sections)
                          else len(delta_text)]
        reqs = list(_REQUIREMENT_RE.finditer(body))
        for r_idx, req in enumerate(reqs):
            end = reqs[r_idx + 1].start() if r_idx + 1 < len(reqs) else len(body)
            out.append((req.group(1), body[req.start():end]))
    return out


def verify_deltas(repo_root: Path, session_id: str) -> dict:
    """Return the coverage-pillar payload for the session's declared deltas."""
    repo_root = Path(repo_root)
    plan_path = repo_root / ".qor" / "gates" / session_id / "plan.json"
    entries: list[dict] = []
    if plan_path.is_file():
        entries = json.loads(plan_path.read_text(encoding="utf-8")).get("spec_deltas") or []

    checked = 0
    unverified: list[str] = []
    for entry in entries:
        delta_path = repo_root / entry["delta_path"]
        if not delta_path.is_file():
            checked += 1
            unverified.append(f"{entry['capability']}: declared delta missing")
            continue
        text = delta_path.read_bytes().decode("utf-8", errors="replace")
        evidence = entry.get("evidence")
        evidence_ok = evidence is None or (repo_root / evidence).is_file()
        for name, block in _added_modified_requirements(text):
            checked += 1
            reasons = [f.code for f in check(block)]
            if not evidence_ok:
                reasons.append(f"evidence missing: {evidence}")
            if reasons:
                unverified.append(f"{name} ({'; '.join(reasons)})")

    verified = checked - len(unverified)
    return {
        "status": "pass" if checked and not unverified else
                  ("fail" if unverified else "skip"),
        "checked": checked,
        "verified": verified,
        "unverified": unverified,
    }
