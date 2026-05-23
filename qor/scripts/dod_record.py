"""Parse a plan's `## Definition of Done` section into structured records (Phase 92).

The plan-section format (V1; see ``qor/references/doctrine-definition-of-done.md``):

```
## Definition of Done

### Deliverable: <name>

- **D1**: <vision/spec>
- **D2**: <code acceptance>
- **D3**: <governance acceptance>
- **D4**: <test name + observed behavior>
  OR
- **D4.d**: <waiver rationale; follow-up phase>
```

Permissive: ``parse_plan`` returns the empty list when the section is
absent. Substantiate Step 4.6.7 (``dod_check``) surfaces the absence as
a finding -- the absence is operator-visible, not silently tolerated.

Closes the plan-emission half of GH #86; the validation half is in
``qor.scripts.dod_check``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DodRecord:
    """One Definition-of-Done row per plan deliverable."""

    deliverable: str
    d1: str | None
    d2: str | None
    d3: str | None
    d4: str | None
    d4_waiver_rationale: str | None
    d4_waiver_followup: str | None


_DOD_SECTION_RE = re.compile(
    r"^##\s+Definition of Done\s*$", re.MULTILINE
)
_DELIVERABLE_RE = re.compile(
    r"^###\s+Deliverable:\s*(.+?)\s*$", re.MULTILINE
)
_NEXT_HEADER_RE = re.compile(r"^##\s+\S", re.MULTILINE)
# Tier bullet: `- **D1**: text` (or D2/D3/D4/D4.d). The text payload
# may span the rest of the line plus continuation indent; V1 captures
# only the first line to keep the parser bounded.
_TIER_BULLET_RE = re.compile(
    r"^[-*]\s+\*\*(?P<tier>D[1-4](?:\.d)?)\*\*\s*:\s*(?P<text>.*?)\s*$",
    re.MULTILINE,
)
# Multi-line tolerant: a follow-up phase reference may span lines when the
# rationale is verbose. Capture from after the ":" up to the next paragraph
# break (blank line) or end-of-block. DOTALL lets `.` match newlines.
_FOLLOWUP_RE = re.compile(
    r"\*\*Follow-up phase\*\*\s*:\s*(?P<phase>.+?)(?:\n\s*\n|\Z)",
    re.DOTALL,
)


def _strip_fenced_code_blocks(text: str) -> str:
    """Replace fenced code blocks with blank lines so headings illustrated
    inside example fences (e.g., a plan's design-notes template that quotes
    a literal ``## Definition of Done`` for documentation) do not confuse
    the section-header scan. Preserves line count so error positions remain
    operator-recoverable.
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def _extract_section_body(text: str) -> str | None:
    """Return the text between '## Definition of Done' and the next '## ' header,
    or None if the section is absent. Fenced code blocks are stripped so
    illustrated headings inside examples don't shadow the real section.
    """
    scan_text = _strip_fenced_code_blocks(text)
    m = _DOD_SECTION_RE.search(scan_text)
    if not m:
        return None
    start = m.end()
    next_header = _NEXT_HEADER_RE.search(scan_text[start:])
    end = start + (next_header.start() if next_header else len(scan_text) - start)
    return scan_text[start:end]


def _split_deliverable_blocks(body: str) -> list[tuple[str, str]]:
    """Split the section body on '### Deliverable: <name>' sub-headers.
    Returns [(name, block_body), ...] in document order."""
    matches = list(_DELIVERABLE_RE.finditer(body))
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        name = m.group(1)
        block_start = m.end()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        blocks.append((name, body[block_start:block_end]))
    return blocks


def _parse_tier_bullets(block: str) -> dict[str, str]:
    """Map tier label ('D1'..'D4', 'D4.d') -> text payload."""
    found: dict[str, str] = {}
    for m in _TIER_BULLET_RE.finditer(block):
        tier = m.group("tier")
        text = m.group("text")
        if tier in found:
            continue  # first occurrence wins
        found[tier] = text
    return found


def _record_from_block(name: str, block: str) -> DodRecord:
    tiers = _parse_tier_bullets(block)
    d4 = tiers.get("D4")
    has_d4_d = "D4.d" in tiers
    d4_d_text = tiers.get("D4.d", "")
    rationale: str | None = None
    followup: str | None = None
    if has_d4_d:
        rationale = d4_d_text or ""  # preserve empty string so check sees "waiver present but empty"
        m = _FOLLOWUP_RE.search(block)
        if m:
            followup = m.group("phase").strip()
    return DodRecord(
        deliverable=name,
        d1=tiers.get("D1") or None,
        d2=tiers.get("D2") or None,
        d3=tiers.get("D3") or None,
        d4=d4 or None if not has_d4_d else None,
        d4_waiver_rationale=rationale,
        d4_waiver_followup=followup,
    )


def parse_plan(plan_path: Path) -> list[DodRecord]:
    """Walk plan's `## Definition of Done` section; return one record
    per `### Deliverable:` block. Returns [] when section absent.
    """
    if not plan_path.is_file():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    body = _extract_section_body(text)
    if body is None:
        return []
    return [_record_from_block(name, block) for name, block in _split_deliverable_blocks(body)]
