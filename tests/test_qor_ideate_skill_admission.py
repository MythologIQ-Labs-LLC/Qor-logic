"""Phase 59: /qor-ideate skill admission + frontmatter integrity."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-ideate" / "SKILL.md"


def _frontmatter() -> dict[str, str]:
    body = SKILL_PATH.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    assert m, "qor-ideate SKILL.md missing frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def test_qor_ideate_skill_passes_admission_check():
    """Phase 55 admission rule: invoke admission CLI subprocess."""
    import subprocess
    import sys
    proc = subprocess.run(
        [sys.executable, "-m", "qor.reliability.skill_admission", "qor-ideate"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"admission failed: {proc.stdout}\n{proc.stderr}"
    assert "ADMITTED" in proc.stdout


def test_qor_ideate_skill_frontmatter_declares_required_fields():
    fm = _frontmatter()
    assert fm.get("phase") == "ideation"
    assert fm.get("gate_writes") == "ideation"
    assert "name" in fm
    assert fm.get("name") == "qor-ideate"


def test_qor_ideate_skill_declares_permitted_tools_list():
    body = SKILL_PATH.read_text(encoding="utf-8")
    assert "permitted_tools:" in body
    assert "permitted_subagents:" in body


def test_qor_ideate_dialogue_protocol_reference_exists():
    proto = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-ideate" / "references" / "dialogue-protocol.md"
    assert proto.exists()
    body = proto.read_text(encoding="utf-8")
    # Heading-tree integrity: 10 sections
    sections = re.findall(r"^## Section \d+", body, re.MULTILINE)
    assert len(sections) >= 10
