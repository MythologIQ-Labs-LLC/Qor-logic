"""Phase 57: doctrine round-trip integrity for hook-contract."""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from qor.scripts.gate_hooks import GateWrittenEvent

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-hook-contract.md"


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
                         re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else ""


def test_doctrine_hook_contract_declares_phase_57_section_with_non_empty_body():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Phase 57 changes vs. PR #12 origin")
    collapsed = re.sub(r"\s+", " ", body).strip()
    assert len(collapsed) >= 20, f"section body too thin: {collapsed!r}"
    for keyword in ("except Exception", "except BaseException", "KeyboardInterrupt"):
        assert keyword in body, f"doctrine body missing literal {keyword!r}"


def test_doctrine_event_payload_section_lists_all_GateWrittenEvent_fields():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Event payload")
    for field in dataclasses.fields(GateWrittenEvent):
        assert field.name in body, f"event payload section missing field {field.name!r}"
