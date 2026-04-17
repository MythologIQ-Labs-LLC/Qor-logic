"""Repeated-VETO pattern detector (B18).

Parses ``docs/META_LEDGER.md``, groups AUDIT entries by phase, flags the
pattern when the last N consecutive sealed phases each required more than
one audit pass to reach PASS. When the pattern fires, a severity-3
``repeated_veto_pattern`` event is appended to the Process Shadow Genome.

Pure functions; only I/O is ``Path.read_text`` at the module entry point.
Downstream emission via ``qor.scripts.shadow_process.append_event``.
"""
from __future__ import annotations

import re
from collections import namedtuple
from pathlib import Path

from qor.scripts import shadow_process


PatternResult = namedtuple(
    "PatternResult", ["detected", "recent_phases", "max_pass_count"]
)

_PATTERN_WINDOW = 2
_SEVERITY = 3
_EVENT_TYPE = "repeated_veto_pattern"
_SKILL = "qor-audit"

# Match `### Entry #N: TYPE -- description`; capture N, type, and description.
_ENTRY_HEADER = re.compile(
    r"^###\s+Entry\s+#(\d+):\s+([A-Z][A-Z\s]*?)\s*--\s*(.+?)\s*$",
    re.MULTILINE,
)
_PHASE_REF = re.compile(r"Phase\s+(\d+)")


def parse_phase_audit_counts(ledger_text: str) -> dict[int, int]:
    """Return {phase_num: audit_count} restricted to SEAL-closed phases."""
    sealed: set[int] = set()
    audits: dict[int, int] = {}
    for match in _ENTRY_HEADER.finditer(ledger_text):
        _, entry_type_raw, desc = match.groups()
        entry_type = entry_type_raw.strip()
        phase_match = _PHASE_REF.search(desc)
        if phase_match is None:
            continue
        phase_num = int(phase_match.group(1))
        if "SEAL" in entry_type:
            sealed.add(phase_num)
        elif entry_type == "AUDIT":
            audits[phase_num] = audits.get(phase_num, 0) + 1
    return {p: c for p, c in audits.items() if p in sealed}


def detect_repeated_veto_pattern(
    counts: dict[int, int], window: int = _PATTERN_WINDOW,
) -> PatternResult:
    """Pattern fires when the last ``window`` sealed phases each had >1 audit."""
    sorted_phases = sorted(counts.keys())
    if len(sorted_phases) < window:
        return PatternResult(False, [], 0)
    recent = sorted_phases[-window:]
    all_multi_pass = all(counts[p] > 1 for p in recent)
    if not all_multi_pass:
        return PatternResult(False, [], 0)
    return PatternResult(
        detected=True,
        recent_phases=recent,
        max_pass_count=max(counts[p] for p in recent),
    )


def build_event_payload(result: PatternResult, session_id: str) -> dict:
    """Render the shadow-event payload for a fired pattern."""
    return {
        "ts": shadow_process.now_iso(),
        "skill": _SKILL,
        "session_id": session_id,
        "event_type": _EVENT_TYPE,
        "severity": _SEVERITY,
        "details": {
            "recent_phases": list(result.recent_phases),
            "max_pass_count": result.max_pass_count,
        },
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def maybe_emit_pattern_event(result: PatternResult, session_id: str) -> bool:
    """Append a shadow-event when the pattern fires. Returns True iff emitted."""
    if not result.detected:
        return False
    event = build_event_payload(result, session_id)
    shadow_process.append_event(event, attribution="LOCAL")
    return True


def render_advisory_text(result: PatternResult) -> str:
    """Return the markdown body that fills the `Process Pattern Advisory` slot."""
    if not result.detected:
        return "No repeated-VETO pattern detected in the last 2 sealed phases."
    phases = ", ".join(str(p) for p in result.recent_phases)
    return (
        f"Repeated-VETO pattern detected in phases {phases} "
        f"(max pass count: {result.max_pass_count}). "
        "Recommend invoking `/qor-remediate` to address the process-level "
        "drift. The current-audit verdict stands independently; this "
        "advisory is non-blocking."
    )


def check(
    ledger_path: Path | None = None,
    session_id: str | None = None,
) -> PatternResult:
    """Convenience entry point: read ledger, detect, optionally emit."""
    if ledger_path is None:
        from qor import workdir
        ledger_path = workdir.meta_ledger()
    text = Path(ledger_path).read_text(encoding="utf-8")
    counts = parse_phase_audit_counts(text)
    result = detect_repeated_veto_pattern(counts)
    if session_id is not None:
        maybe_emit_pattern_event(result, session_id)
    return result
