"""SKILL.md doctrine compliance tests (Phase 11D).

Static analyses over the SKILL.md tree. No skill execution; pure markdown
invariants. These tests catch documentation drift that 154 module/integration
tests cannot — they verify SKILL.md content matches declared doctrine.

Pattern surfaced by docs/research-brief-full-audit-2026-04-15.md V-5
(systemic gap S-14: tests pass while 24 doctrine gaps exist because no
test category validates SKILL.md compliance).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"

QOR_REF_RE = re.compile(r"/qor-[a-z][a-z0-9-]*")
LOCAL_REF_FILE_RE = re.compile(r"(?<![\w/])references/[a-z0-9-]+\.md")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _all_skill_md() -> list[Path]:
    return sorted(SKILLS_ROOT.rglob("SKILL.md"))


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = FM_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        # Top-level key=value (skip nested keys with leading whitespace)
        if line.startswith(" "):
            # Capture nested category under metadata
            key, _, val = line.lstrip().partition(":")
            val = val.strip()
            if val:
                out.setdefault(key.strip(), val.strip('"').strip("'"))
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        out[key.strip()] = val.strip('"').strip("'")
    return out


def _frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    m = FM_RE.match(text)
    body = text[m.end():] if m else text
    return fm, body


# ----- S-1: gate_writes implies write step -----

def test_gate_writes_implies_write_step():
    """Every skill with non-empty gate_writes must reference how it writes the artifact."""
    failures = []
    for skill_md in _all_skill_md():
        fm, body = _frontmatter_and_body(skill_md)
        gw = fm.get("gate_writes", "").strip().strip('"').strip("'")
        # Skip empty or shadow-process's free-form path
        if not gw or "PROCESS_SHADOW_GENOME" in gw or gw in ("", '""'):
            continue
        has_write = (
            ".qor/gates/" in body
            or "write_artifact" in body
            or "write_gate_artifact" in body
        )
        if not has_write:
            failures.append(f"{skill_md.relative_to(REPO_ROOT)} declares gate_writes={gw!r} but body has no .qor/gates/ or write_artifact reference")
    assert not failures, "Skills with gate_writes that don't document the write:\n  " + "\n  ".join(failures)


# ----- S-9: no dead skill references -----

def test_no_dead_skill_references():
    """Every /qor-* reference in any SKILL.md must resolve to an existing skill."""
    # Collect all extant qor-* skill names
    extant: set[str] = set()
    for skill_dir in SKILLS_ROOT.rglob("*"):
        if skill_dir.is_dir() and skill_dir.name.startswith("qor-"):
            extant.add(skill_dir.name)
    # Loose .md skills (memory/log-decision.md, track-shadow-genome.md)
    for f in SKILLS_ROOT.rglob("*.md"):
        if f.name.startswith("qor-") and f.name != "SKILL.md":
            extant.add(f.stem)

    failures = []
    for skill_md in _all_skill_md():
        body = skill_md.read_text(encoding="utf-8")
        refs = set(QOR_REF_RE.findall(body))
        # Drop self-reference based on parent dir name
        self_name = skill_md.parent.name
        for ref in refs:
            target = ref.lstrip("/")
            if target == self_name:
                continue
            if target not in extant:
                failures.append(f"{skill_md.relative_to(REPO_ROOT)} references {ref} (does not exist)")
    assert not failures, "Dead /qor-* references:\n  " + "\n  ".join(failures)


# ----- S-2: no stale processed/skills-output paths -----

def test_no_stale_processed_paths():
    failures = []
    for skill_md in _all_skill_md():
        text = skill_md.read_text(encoding="utf-8")
        if "processed/skills-output" in text:
            failures.append(str(skill_md.relative_to(REPO_ROOT)))
    assert not failures, "Skills citing pre-Phase-7 processed/ path:\n  " + "\n  ".join(failures)


# ----- S-3: governance skills have governance category -----

def test_governance_skills_have_governance_category():
    failures = []
    gov_dir = SKILLS_ROOT / "governance"
    for skill_md in gov_dir.rglob("SKILL.md"):
        fm, _ = _frontmatter_and_body(skill_md)
        cat = fm.get("category", "")
        if cat != "governance":
            failures.append(f"{skill_md.relative_to(REPO_ROOT)} category={cat!r} (expected 'governance')")
    assert not failures, "Governance skills with wrong category:\n  " + "\n  ".join(failures)


# ----- S-6: local references files exist -----

def test_skill_local_references_files_exist():
    failures = []
    for skill_md in _all_skill_md():
        body = skill_md.read_text(encoding="utf-8")
        for ref in set(LOCAL_REF_FILE_RE.findall(body)):
            target = skill_md.parent / ref
            if not target.is_file():
                failures.append(f"{skill_md.relative_to(REPO_ROOT)} cites {ref} (does not exist locally)")
    assert not failures, "Missing local references/* files:\n  " + "\n  ".join(failures)


# ----- S-7: qor-help lists every qor-* skill -----

def test_qor_help_lists_every_skill():
    help_md = SKILLS_ROOT / "meta" / "qor-help" / "SKILL.md"
    assert help_md.exists(), "qor-help/SKILL.md missing"
    help_text = help_md.read_text(encoding="utf-8")

    # Collect all qor-* skill dir names (exclude qor-help itself)
    expected = set()
    for skill_dir in SKILLS_ROOT.rglob("*"):
        if skill_dir.is_dir() and skill_dir.name.startswith("qor-") and skill_dir.name != "qor-help":
            # Only skills with a SKILL.md inside (not just any qor-* directory)
            if (skill_dir / "SKILL.md").exists():
                expected.add(skill_dir.name)

    missing = sorted(s for s in expected if s not in help_text)
    assert not missing, "qor-* skills missing from qor-help:\n  " + "\n  ".join(missing)


# ----- S-5: no QL uppercase leftovers -----

QL_RE = re.compile(r"\bQL\b")

def test_no_QL_uppercase_leftovers():
    failures = []
    for f in SKILLS_ROOT.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for m in QL_RE.finditer(text):
            # Show context for clarity
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            line = text[line_start:line_end if line_end != -1 else len(text)]
            failures.append(f"{f.relative_to(REPO_ROOT)}: {line.strip()}")
            break  # one per file is enough
    assert not failures, "Pre-rename 'QL' uppercase leftovers:\n  " + "\n  ".join(failures)


# ----- S-8: delegation-table acknowledges every skill -----

def test_delegation_table_lists_every_skill():
    """Every qor-* skill must appear (as detector or destination) in delegation-table.md
    or in its 'Cross-cutting / bundles' acknowledgement section."""
    table = REPO_ROOT / "qor" / "gates" / "delegation-table.md"
    assert table.exists(), "qor/gates/delegation-table.md missing"
    text = table.read_text(encoding="utf-8")

    expected = set()
    for skill_dir in SKILLS_ROOT.rglob("*"):
        if skill_dir.is_dir() and skill_dir.name.startswith("qor-"):
            if (skill_dir / "SKILL.md").exists():
                expected.add(skill_dir.name)

    missing = sorted(s for s in expected if s not in text)
    assert not missing, "qor-* skills missing from delegation-table:\n  " + "\n  ".join(missing)


# ----- S-10: no tools/reliability vestigial references -----

def test_no_tools_reliability_references():
    failures = []
    for skill_md in _all_skill_md():
        text = skill_md.read_text(encoding="utf-8")
        if "tools/reliability/" in text:
            failures.append(str(skill_md.relative_to(REPO_ROOT)))
    assert not failures, "Vestigial tools/reliability/ references (tools never built):\n  " + "\n  ".join(failures)


# ----- Phase 13: governance enforcement doctrine tests -----

DOCS_ROOT = REPO_ROOT / "docs"
GOV_DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-governance-enforcement.md"
QOR_PLAN_SKILL = SKILLS_ROOT / "sdlc" / "qor-plan" / "SKILL.md"
QOR_SUBSTANTIATE_SKILL = SKILLS_ROOT / "governance" / "qor-substantiate" / "SKILL.md"

_PHASE_NN_RE = re.compile(r"^plan-qor-phase(\d+)")
_CHANGE_CLASS_BOLD_RE = re.compile(
    r"^\*\*change_class\*\*:\s+(hotfix|feature|breaking)\s*$", re.MULTILINE,
)


def test_plan_skill_documents_branch_creation():
    skill = QOR_PLAN_SKILL.read_text(encoding="utf-8")
    extensions = (SKILLS_ROOT / "sdlc" / "qor-plan" / "references" / "step-extensions.md")
    combined = skill + (extensions.read_text(encoding="utf-8") if extensions.exists() else "")
    assert "phase/" in combined, "qor-plan skill surface must document phase/ branch creation"


def test_substantiate_skill_documents_version_bump():
    text = QOR_SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    assert "bump_version" in text or "create_seal_tag" in text, (
        "qor-substantiate/SKILL.md must reference bump_version or create_seal_tag"
    )


def test_plans_declare_change_class():
    missing: list[str] = []
    for plan in sorted(DOCS_ROOT.glob("plan-qor-phase*.md")):
        m = _PHASE_NN_RE.match(plan.name)
        if not m:
            continue
        nn = int(m.group(1))
        if nn < 13:
            continue  # grandfathered forward-boundary (W-2)
        text = plan.read_text(encoding="utf-8")
        if not _CHANGE_CLASS_BOLD_RE.search(text):
            missing.append(plan.name)
    assert not missing, (
        "Plans with phase>=13 must declare `**change_class**: <hotfix|feature|breaking>` "
        "(bold per V-2):\n  " + "\n  ".join(missing)
    )


def test_governance_doctrine_documents_github_hygiene():
    text = GOV_DOCTRINE.read_text(encoding="utf-8").lower()
    import re as _re
    for keyword in ("issue label", "pr description", "branch name", "tag annotation"):
        assert _re.search(rf"github hygiene.{{0,1500}}{_re.escape(keyword)}", text, _re.DOTALL), (
            f"doctrine-governance-enforcement.md 'GitHub hygiene' section must contain: {keyword!r}"
        )


# ----- Phase 14: shadow attribution skill wiring -----

SHADOW_PROCESS_SKILL = SKILLS_ROOT / "governance" / "qor-shadow-process" / "SKILL.md"
TRACK_SHADOW_SKILL = SKILLS_ROOT / "memory" / "track-shadow-genome.md"
META_TRACK_SHADOW_SKILL = SKILLS_ROOT / "meta" / "qor-meta-track-shadow" / "SKILL.md"


def test_shadow_process_skill_documents_attribution():
    text = SHADOW_PROCESS_SKILL.read_text(encoding="utf-8")
    assert "doctrine-shadow-attribution.md" in text or "UPSTREAM" in text, (
        "qor-shadow-process/SKILL.md must reference attribution doctrine or UPSTREAM"
    )


def test_shadow_process_skill_documents_both_log_files():
    text = SHADOW_PROCESS_SKILL.read_text(encoding="utf-8")
    assert "PROCESS_SHADOW_GENOME.md" in text, "Must reference LOCAL log file"
    assert "PROCESS_SHADOW_GENOME_UPSTREAM.md" in text, "Must reference UPSTREAM log file"


def test_shadow_tracking_skills_reference_attribution_doctrine():
    for path in (TRACK_SHADOW_SKILL, META_TRACK_SHADOW_SKILL):
        text = path.read_text(encoding="utf-8")
        assert "doctrine-shadow-attribution.md" in text, (
            f"{path.name} must reference doctrine-shadow-attribution.md"
        )
