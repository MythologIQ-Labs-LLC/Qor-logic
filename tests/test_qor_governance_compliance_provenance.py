"""Phase 81: qor-governance-compliance F244/FX359 provenance schema (GH #77).

The skill's YAML frontmatter must declare metadata.source.repository (an
https?:// URL) and metadata.source.path. Without these the FailSafe
extension's skill-provenance-schema.test.ts walker fails on every machine
where qor-logic has been installed.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

SKILL = Path("qor/skills/governance/qor-governance-compliance/SKILL.md")


def _load_frontmatter() -> dict:
    text = SKILL.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert match, "qor-governance-compliance SKILL.md must open with a YAML frontmatter block"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse as a mapping"
    return data


def test_metadata_source_block_present():
    fm = _load_frontmatter()
    metadata = fm.get("metadata")
    assert isinstance(metadata, dict), "frontmatter must declare a `metadata:` mapping"
    source = metadata.get("source")
    assert isinstance(source, dict), (
        "metadata.source must be a nested object (per F244/FX359; scalar form is rejected)"
    )
    assert "repository" in source, "metadata.source.repository is required by F244/FX359"
    assert "path" in source, "metadata.source.path is required by F244/FX359"
    assert source["path"] == "qor/skills/governance/qor-governance-compliance", (
        "metadata.source.path must point at this skill's directory in the Qor-logic repo"
    )


def test_metadata_source_repository_is_https_url():
    fm = _load_frontmatter()
    repo = fm["metadata"]["source"]["repository"]
    assert isinstance(repo, str) and re.match(r"^https?://", repo), (
        "metadata.source.repository must be an https?:// URL per F244/FX359"
    )
    assert "Qor-logic" in repo, (
        "repository must point at the Qor-logic source-of-truth, not a downstream consumer"
    )
