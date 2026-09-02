"""Phase 250 (GH #406): layout-bound gates resolve through .qorlogic/config.json.

Several `/qor-substantiate` gates read truth from paths that exist only in the
Qor-logic repository, so a consumer workspace's only available outcome was a
Phase 75 disclosed skip. The mechanism to fix that already existed --
`qorlogic_config.load_section` plus `badge_layout`'s per-key precedence -- and
these gates simply resolved their paths as constants.

Half 2 makes the remaining skips legible: a gate whose path does not resolve
fails unless the operator declared the key absent, and the skip event names the
key rather than carrying free text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from qor.scripts import badge_layout, doc_integrity, doc_integrity_strict
from qor.scripts import skill_size_budget_lint as ssbl

SUBSTANTIATE_SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")
SEAL_LADDER = Path("qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md")


def _workspace(tmp_path: Path, layout: dict | None = None) -> Path:
    if layout is not None:
        cfg = tmp_path / ".qorlogic"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "config.json").write_text(json.dumps({"layout": layout}), encoding="utf-8")
    return tmp_path


def _args(repo_root: Path, **kw) -> argparse.Namespace:
    ns = argparse.Namespace(repo_root=repo_root, skills_root=None, skills_pattern=None,
                            agents_root=None, agents_pattern=None,
                            doctrines_root=None, doctrines_pattern=None,
                            glossary_path=None)
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_glossary_path_defaults_to_the_qor_topology(tmp_path):
    """A workspace declaring nothing behaves exactly as before."""
    layout = badge_layout.layout_from_args(_args(_workspace(tmp_path)))

    assert layout.glossary_path == Path("qor/references/glossary.md")


def test_glossary_path_resolves_from_the_layout_config(tmp_path):
    """A declared `layout.glossary_path` moves the resolved path."""
    root = _workspace(tmp_path, {"glossary_path": "docs/00-glossary.md"})

    layout = badge_layout.layout_from_args(_args(root))

    assert layout.glossary_path == Path("docs/00-glossary.md")


def _glossary_text(term: str, home: str) -> str:
    """A glossary entry in the fenced-YAML shape `parse_glossary` reads."""
    return (
        "# Glossary\n\n"
        "```yaml\n"
        f"term: {term}\n"
        f"definition: {term} names the thing this test declares.\n"
        f"home: {home}\n"
        f"referenced_by: [{home}]\n"
        "```\n"
    )


def _consumer_workspace(tmp_path: Path, glossary_rel: str) -> Path:
    """A workspace whose glossary is NOT at the Qor-logic path."""
    root = _workspace(tmp_path, {"glossary_path": glossary_rel})
    (root / "README.md").write_text("# consumer\n", encoding="utf-8")
    g = root / glossary_rel
    g.parent.mkdir(parents=True, exist_ok=True)
    g.write_text(_glossary_text("Widget", "README.md"), encoding="utf-8")
    return root


def test_doc_integrity_reads_the_configured_glossary(tmp_path):
    """The reporter's exact case: a glossary at docs/00-glossary.md.

    Red before the fix: `run_all_checks_from_plan` builds the Qor-logic literal,
    so a term registered in the consumer's own glossary reads as unregistered
    and the strict tier is unreachable.
    """
    root = _consumer_workspace(tmp_path, "docs/00-glossary.md")
    plan = {"doc_tier": "standard", "terms": [{"term": "Widget", "home": "README.md"}]}

    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(root))


def test_doc_integrity_rejects_an_unregistered_term_under_the_configured_glossary(tmp_path):
    """Redirecting the path must not weaken the check it points at."""
    root = _consumer_workspace(tmp_path, "docs/00-glossary.md")
    plan = {"doc_tier": "standard", "terms": [{"term": "Absent", "home": "README.md"}]}

    with pytest.raises(ValueError, match="Absent"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(root))


def test_doc_integrity_strict_reads_the_configured_glossary(tmp_path):
    """The strict tier resolves the same configured path."""
    root = _consumer_workspace(tmp_path, "docs/00-glossary.md")

    resolved = doc_integrity_strict.resolve_glossary_path(str(root))

    assert Path(resolved).name == "00-glossary.md"


def _skills_tree(root: Path, rel: str) -> Path:
    d = root / rel / "demo"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("x" * (26 * 1024), encoding="utf-8")
    return d / "SKILL.md"


def test_skill_size_budget_lint_resolves_skills_root_from_config(tmp_path):
    """A declared `layout.skills_root` makes the lint walk that tree."""
    root = _workspace(tmp_path, {"skills_root": "packages/skills"})
    _skills_tree(root, "packages/skills")

    findings = ssbl.scan(ssbl.resolve_skills_root(_args(root)))

    assert findings, "the lint must find the oversized skill under the configured root"


def test_skills_flag_still_beats_config(tmp_path):
    """Precedence is flag > config > default, so the flag never becomes inert."""
    root = _workspace(tmp_path, {"skills_root": "packages/skills"})
    _skills_tree(root, "packages/skills")
    _skills_tree(root, "other/skills")

    resolved = ssbl.resolve_skills_root(_args(root, skills_root=Path("other/skills")))

    assert resolved.as_posix().endswith("other/skills")


def test_seal_ladder_does_not_hardcode_a_skills_root():
    """Prompt-contract assertion (tribunal ground V-1, entry #686).

    Scoped deliberately to the invocation shape: a hardcoded `--skills-root` in
    the seal ladder makes the config channel inert no matter what the resolver
    does. This is a prompt-text contract with no unit behind it, and does not
    stand in for the resolver tests above.
    """
    for path in (SUBSTANTIATE_SKILL, SEAL_LADDER):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "skill_size_budget_lint" in line:
                assert "--skills-root" not in line, (
                    f"{path}: seal ladder hardcodes a skills root, which makes the "
                    f"layout config channel inert: {line.strip()!r}"
                )


def test_typed_skip_names_the_layout_key():
    """The skip event must be groupable without parsing prose."""
    event = ssbl.layout_skip_event("skills_root", session="2026-09-02T0000-aaaaaa")

    assert event["event_type"] == "gate_skipped_prerequisite_absent"
    assert event["details"]["layout_key"] == "skills_root"
    assert event["details"]["gate"] == "skill_size_budget_lint"


def test_unresolvable_layout_path_without_a_declaration_fails(tmp_path):
    """An undeclared, unresolvable path is a hard failure naming the key.

    A silent pass here is the vacuous-gate shape; a failure naming the key is
    actionable.
    """
    root = _workspace(tmp_path)  # no layout section at all

    with pytest.raises(ssbl.LayoutUndeclaredError, match="skills_root"):
        ssbl.resolve_skills_root(_args(root), require=True)


def test_unresolvable_layout_path_declared_absent_records_a_typed_skip(tmp_path):
    """Declaring the key absent converts the failure into a typed skip."""
    root = _workspace(tmp_path, {"skills_root": None})

    resolved = ssbl.resolve_skills_root(_args(root), require=True)

    assert resolved is None, "an explicitly-absent declaration resolves to no root"
