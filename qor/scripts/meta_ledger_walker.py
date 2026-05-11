"""Phase 48 (#43): parse META_LEDGER.md SESSION SEAL / AUDIT entries.

V1 surface returns the last N audit-class entries with (verdict, signature,
target, ts) for cross-session pattern detection. Stdlib-only.

Audit entry detection: matches `### Entry #N: AUDIT` and `### Entry #N: GATE
TRIBUNAL` headings. Verdict parsed from `**Verdict**: <V>` line. Signature
parsed from `**Findings signature**: <16-hex>` or `**Findings categories**:
<comma-list>`. Target parsed from `**Target**: <path>` line.

SESSION SEAL entries (verdict PASS) and VETO audit entries both contribute;
RESEARCH BRIEF and BOOTSTRAP entries are skipped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ENTRY_HEADING = re.compile(r"^### Entry #(\d+):\s*(.+?)\s*$", re.MULTILINE)
_VERDICT = re.compile(r"^\*\*Verdict\*\*\s*:\s*([A-Z]+)\b", re.MULTILINE)
_TARGET = re.compile(r"^\*\*Target\*\*\s*:\s*`?([^`\n]+?)`?\s*$", re.MULTILINE)
_TIMESTAMP = re.compile(r"^\*\*Timestamp\*\*\s*:\s*(\S+)\s*$", re.MULTILINE)
_SIG = re.compile(r"^\*\*Findings\s+signature\*\*\s*:\s*([0-9a-f]+|LEGACY)\b", re.MULTILINE)
_FINDINGS_CATS = re.compile(r"^\*\*Findings\s+categories\*\*\s*:\s*(.+?)$", re.MULTILINE)


@dataclass(frozen=True)
class LedgerRecord:
    entry_id: int
    phase_label: str
    target: str | None
    verdict: str | None
    signature: str | None
    ts: str | None


def _signature_from_categories(text: str) -> str | None:
    m = _FINDINGS_CATS.search(text)
    if not m:
        return None
    cats = [c.strip() for c in m.group(1).split(",") if c.strip()]
    if not cats:
        return None
    return ",".join(sorted(cats))


def _parse_entry(entry_id: int, label: str, body: str) -> LedgerRecord:
    verdict_m = _VERDICT.search(body)
    verdict = verdict_m.group(1) if verdict_m else None
    if verdict == "VETO" or verdict == "PASS":
        pass
    target_m = _TARGET.search(body)
    target = target_m.group(1).strip() if target_m else None
    ts_m = _TIMESTAMP.search(body)
    ts = ts_m.group(1) if ts_m else None
    sig_m = _SIG.search(body)
    signature: str | None
    if sig_m:
        signature = sig_m.group(1)
    else:
        signature = _signature_from_categories(body)
    return LedgerRecord(
        entry_id=entry_id,
        phase_label=label.strip(),
        target=target,
        verdict=verdict,
        signature=signature,
        ts=ts,
    )


def walk(ledger_path: str | Path) -> list[LedgerRecord]:
    text = Path(ledger_path).read_text(encoding="utf-8")
    matches = list(_ENTRY_HEADING.finditer(text))
    records: list[LedgerRecord] = []
    for i, m in enumerate(matches):
        entry_id = int(m.group(1))
        label = m.group(2)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        records.append(_parse_entry(entry_id, label, body))
    return records


def _is_audit_class(record: LedgerRecord) -> bool:
    label = record.phase_label.upper()
    if record.verdict not in ("PASS", "VETO"):
        return False
    if "AUDIT" in label or "GATE TRIBUNAL" in label or "SESSION SEAL" in label or "SEAL" in label:
        return True
    return False


def last_n_audit_entries(ledger_path: str | Path, n: int) -> list[LedgerRecord]:
    all_records = walk(ledger_path)
    audit_class = [r for r in all_records if _is_audit_class(r)]
    return audit_class[-n:] if len(audit_class) >= n else audit_class
