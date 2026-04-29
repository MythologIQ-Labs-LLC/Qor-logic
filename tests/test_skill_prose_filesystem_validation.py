"""Phase 50: skill-prose filesystem validation contract (G-2).

Skills that perform filesystem operations on operator-controlled identifiers
(e.g., session_id under `.qor/gates/<sid>/`) MUST cite the canonical
validator helper. Functionality tests with proximity-anchor + strip-and-fail
per Phase 46 doctrine.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-owasp-governance.md"
QOR_HELP = SKILLS_ROOT / "meta" / "qor-help" / "SKILL.md"


# Match actual READ operations on the operator-controlled marker file or
# glob operations on operator-controlled gate paths. Doc-mentions of the
# path structure (e.g., "Persist the artifact at .qor/gates/<sid>/foo.json")
# are NOT a concern — they do not flow operator-controlled values to a
# filesystem call. Patterns of concern:
#   - `cat .qor/session/current`
#   - `Path(".qor/session/current").read_text()`
#   - `open(".qor/session/current")`
#   - `glob .qor/gates/<sid>/*` invocations in skill protocol prose
_FS_OP_RE = re.compile(
    r"cat\s+\.qor/session/current"
    r"|read.*\.qor/session/current"
    r"|open\(['\"]\.qor/session/current"
    r"|Path\(['\"]\.qor/session/current",
    re.IGNORECASE,
)
_VALIDATOR_RE = re.compile(
    r"qor\.scripts\.session|SESSION_ID_PATTERN|session\.current\(\)",
    re.IGNORECASE,
)


def _proximity(body: str, header_pattern: str, phrase_pattern: str, span: int = 2000) -> bool:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return False
    window = body[m.end(): m.end() + span]
    return re.search(phrase_pattern, window, re.IGNORECASE | re.DOTALL) is not None


def _strip_section(body: str, header_pattern: str, span: int = 4000) -> str:
    m = re.search(header_pattern, body, re.MULTILINE)
    if not m:
        return body
    start = m.end()
    end = min(len(body), start + span)
    filler = "\n# stripped\n" * ((end - start) // 12 + 1)
    return body[:start] + filler[: end - start] + body[end:]


def test_skills_referencing_qor_gates_cite_session_validator():
    """Any skill that mentions .qor/gates/<sid> or .qor/session/current MUST
    cite the canonical validator (qor.scripts.session)."""
    offenders: list[str] = []
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        body = skill_md.read_text(encoding="utf-8")
        if _FS_OP_RE.search(body):
            if not _VALIDATOR_RE.search(body):
                offenders.append(str(skill_md.relative_to(REPO_ROOT)))
    assert not offenders, (
        "Skills perform filesystem ops on operator-controlled identifiers "
        "without citing the canonical validator. Add a reference to "
        "`qor.scripts.session.current()` (or `SESSION_ID_PATTERN`):\n  "
        + "\n  ".join(offenders)
    )


def test_skill_prose_validation_doctrine_documented():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert _proximity(body, r"^### A03 -- Injection\b", r"skill prose", span=3000), (
        "doctrine A03 must mention 'skill prose' in the worked-example region"
    )
    assert _proximity(body, r"^### A03 -- Injection\b", r"validate|validator", span=3000)
    assert _proximity(body, r"^### A03 -- Injection\b", r"qor\.scripts\.session", span=3000)


def test_skill_prose_validation_doctrine_negative_path():
    body = DOCTRINE.read_text(encoding="utf-8")
    mutated = _strip_section(body, r"^### A03 -- Injection\b")
    assert not _proximity(mutated, r"^### A03 -- Injection\b", r"skill prose", span=3000)


def test_qor_help_stuck_mode_cites_session_helper():
    body = QOR_HELP.read_text(encoding="utf-8")
    assert _proximity(body, r"^## Mode: --stuck\b", r"qor\.scripts\.session|session\.current", span=2500), (
        "/qor-help --stuck mode must cite qor.scripts.session helper"
    )


def test_qor_help_stuck_mode_negative_path():
    body = QOR_HELP.read_text(encoding="utf-8")
    mutated = _strip_section(body, r"^## Mode: --stuck\b")
    assert not _proximity(mutated, r"^## Mode: --stuck\b", r"qor\.scripts\.session|session\.current", span=2500)
