"""Phase 221 (GH #314 residual): every declared prerequisite must exist.

`/qor-substantiate` declares `module:<dotted.path>` prerequisites per step. Phase
75 declarative-tolerance degrades a missing prerequisite to a disclosed SKIP,
which is right for a host that lacks a toolkit and wrong for a module absent from
the project that declares it -- there the SKIP fires for every operator on every
seal and the gate has never once run.

GH #314 was filed about exactly that. Phase 217's research proposed this check,
measured 12 declarations resolving 12, used it to disprove the issue's premise --
and shipped no test. This is that check, made standing.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"

_MODULE_RE = re.compile(r"module:([A-Za-z_][A-Za-z0-9_.]*)")


def _declarations(text: str) -> set[str]:
    return set(_MODULE_RE.findall(text))


def _all_skill_declarations() -> dict[str, set[str]]:
    out = {}
    for skill in sorted(SKILLS_ROOT.rglob("SKILL.md")):
        declared = _declarations(skill.read_text(encoding="utf-8"))
        if declared:
            out[skill.parent.name] = declared
    return out


def test_every_declared_module_imports():
    """THE COUNTERFACTUAL against the defect GH #314 was filed about.

    Would have failed while `qor.scripts.instruction_hygiene_lint` was declared
    by a Step Prerequisites row and existed nowhere in the tree.
    """
    missing = {}
    for skill, modules in _all_skill_declarations().items():
        for module in sorted(modules):
            try:
                importlib.import_module(module)
            except Exception:
                missing.setdefault(skill, []).append(module)

    assert missing == {}, (
        f"declared prerequisites that do not import: {missing}. A declared-but-"
        "absent gate reads as coverage in the ceremony while providing none."
    )


def test_declarations_are_discovered_not_hardcoded():
    """The check must read what the skill declares now, not a stale list.

    A hardcoded expectation would pass while the skill declared something new
    and absent -- reintroducing the failure this test closes.
    """
    declared = _all_skill_declarations()

    assert declared, "expected at least one skill to declare module: prerequisites"
    assert "qor-substantiate" in declared
    assert len(declared["qor-substantiate"]) >= 10, (
        f"expected the seal ladder's prerequisites to be discovered, got "
        f"{sorted(declared['qor-substantiate'])}"
    )


def test_a_fabricated_declaration_is_caught():
    """Proves the check can fail.

    A parser that never reports would satisfy the other two tests forever. This
    feeds it a body naming a module that cannot exist.
    """
    body = "| 9.9 phantom | module:qor.scripts.definitely_not_a_real_module | x |"

    found = _declarations(body)
    assert "qor.scripts.definitely_not_a_real_module" in found

    unresolvable = []
    for module in found:
        try:
            importlib.import_module(module)
        except Exception:
            unresolvable.append(module)

    assert unresolvable == ["qor.scripts.definitely_not_a_real_module"]
