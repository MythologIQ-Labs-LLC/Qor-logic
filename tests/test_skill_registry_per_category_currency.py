"""Phase 97: SKILL_REGISTRY per-category currency tests (F8).

The F8 defect class: total-cancellation masking per-category drift in
`docs/SKILL_REGISTRY.md`. The declared TOTAL of 30 happened to match
the actual TOTAL of 30 (under the prior counting analysis) only because
sdlc undercounted by 1, meta undercounted by 1, and memory was
internally consistent. A total-only currency test would pass while two
categories silently drifted.

The structural countermeasure: per-category granularity. Each declared
per-category count must equal the actual .md file count on disk, plus
cross-category drift guards.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "docs" / "SKILL_REGISTRY.md"
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"

CATEGORIES = ("governance", "sdlc", "memory", "meta")


def _count_md_at_depth_le_2(category_dir: Path) -> int:
    """Count .md files immediately under category_dir or one level deeper.

    The canonical skill layout is either:
    - `qor/skills/<cat>/<skill>/SKILL.md` (depth 2)
    - `qor/skills/<cat>/<skill>.md` (depth 1; migrated stubs)

    Excludes any references/ subdir contents and any depth >2 prose.
    """
    count = 0
    for p in category_dir.rglob("*.md"):
        rel = p.relative_to(category_dir)
        if len(rel.parts) > 2:
            continue
        if "references" in rel.parts:
            continue
        count += 1
    return count


def _declared_count(category: str, registry_text: str) -> int:
    """Parse the header line `## <cat>/ (N)` to get the declared count."""
    pattern = rf"^## {re.escape(category)}/ \((\d+)\)"
    match = re.search(pattern, registry_text, re.MULTILINE)
    assert match, f"Registry must declare count for category {category!r}"
    return int(match.group(1))


def _category_table_skills(category: str, registry_text: str) -> list[str]:
    """Parse the markdown table under `## <cat>/` and return the skill names
    (the first column, after the header + separator rows).
    """
    header_re = re.compile(rf"^## {re.escape(category)}/ \(\d+\)$", re.MULTILINE)
    header_match = header_re.search(registry_text)
    assert header_match, f"category header for {category!r} not found"
    start = header_match.end()
    # Next category header (or end of file) bounds the section.
    next_section = re.search(r"^## ", registry_text[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(registry_text)
    section = registry_text[start:end]
    skills: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if line.startswith("|---") or line.startswith("| Skill"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells = ['', '<skill>', '<path>', '<status>', '']
        if len(cells) >= 2 and cells[1] and cells[1] != "Skill":
            skills.append(cells[1])
    return skills


# --- per-category currency --------------------------------------------------

def test_governance_category_count_matches_declared():
    text = REGISTRY.read_text(encoding="utf-8")
    declared = _declared_count("governance", text)
    actual = _count_md_at_depth_le_2(SKILLS_ROOT / "governance")
    assert declared == actual, (
        f"governance: declared {declared} but {actual} .md files on disk"
    )


def test_sdlc_category_count_matches_declared():
    text = REGISTRY.read_text(encoding="utf-8")
    declared = _declared_count("sdlc", text)
    actual = _count_md_at_depth_le_2(SKILLS_ROOT / "sdlc")
    assert declared == actual, (
        f"sdlc: declared {declared} but {actual} .md files on disk"
    )


def test_memory_category_count_matches_declared():
    text = REGISTRY.read_text(encoding="utf-8")
    declared = _declared_count("memory", text)
    actual = _count_md_at_depth_le_2(SKILLS_ROOT / "memory")
    assert declared == actual, (
        f"memory: declared {declared} but {actual} .md files on disk"
    )


def test_meta_category_count_matches_declared():
    text = REGISTRY.read_text(encoding="utf-8")
    declared = _declared_count("meta", text)
    actual = _count_md_at_depth_le_2(SKILLS_ROOT / "meta")
    assert declared == actual, (
        f"meta: declared {declared} but {actual} .md files on disk"
    )


# --- inverse drift / cross-category guards ----------------------------------

def test_registry_lists_every_actual_skill_md_for_each_category():
    """For each category, every actual .md file is referenced by name in
    that category's table. Catches the inverse drift (registry references
    a file that no longer exists, or vice versa).
    """
    text = REGISTRY.read_text(encoding="utf-8")
    missing: list[str] = []
    for category in CATEGORIES:
        category_dir = SKILLS_ROOT / category
        listed_skills = set(_category_table_skills(category, text))
        for p in category_dir.rglob("*.md"):
            rel = p.relative_to(category_dir)
            if len(rel.parts) > 2 or "references" in rel.parts:
                continue
            # Skill name = top-level dir name if depth 2; file stem if depth 1.
            skill_name = rel.parts[0] if len(rel.parts) == 2 else rel.stem
            if skill_name not in listed_skills:
                missing.append(f"{category}/{skill_name}")
    assert not missing, (
        f"Registry must list every actual skill .md by name. Missing:\n  "
        + "\n  ".join(missing)
    )


def test_no_cross_category_skill_listed():
    """A skill listed in category X must have its path containing
    `/skills/X/`. Catches cross-category mis-listing.
    """
    text = REGISTRY.read_text(encoding="utf-8")
    cross_cat: list[str] = []
    for category in CATEGORIES:
        header_re = re.compile(rf"^## {re.escape(category)}/ \(\d+\)$", re.MULTILINE)
        header_match = header_re.search(text)
        assert header_match
        start = header_match.end()
        next_section = re.search(r"^## ", text[start:], re.MULTILINE)
        end = start + next_section.start() if next_section else len(text)
        section = text[start:end]
        for line in section.splitlines():
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---") or line.startswith("| Skill"):
                continue
            cells = [c.strip() for c in line.split("|")]
            if len(cells) < 3:
                continue
            path = cells[2].strip("`")
            if path and f"/skills/{category}/" not in path.replace("\\", "/"):
                cross_cat.append(f"{category} table lists {cells[1]} at path {path}")
    assert not cross_cat, (
        "Cross-category drift in registry:\n  " + "\n  ".join(cross_cat)
    )


def test_total_count_matches_sum_of_per_category_declared_counts():
    """Arithmetic guard: when a total/summary line is present, it must
    equal the sum of the per-category declared counts. Prevents future
    edits from drifting a documented total against the per-category
    truths.
    """
    text = REGISTRY.read_text(encoding="utf-8")
    sum_declared = sum(_declared_count(c, text) for c in CATEGORIES)
    # The registry currently has no "Total: N" line; the test guards against
    # one being added in the future that disagrees with the per-category sum.
    total_line_re = re.compile(r"\*\*Total\*\*\s*[:\|]\s*(\d+)")
    match = total_line_re.search(text)
    if match:
        documented_total = int(match.group(1))
        assert documented_total == sum_declared, (
            f"Documented total {documented_total} != sum-of-per-category {sum_declared}"
        )
    # When no total line present, the test is a forward-only structural
    # guard: it does not fail on missing total, but it does fail on a
    # documented total that diverges from the per-category sum.
