## Phase 15 — Shadow Genome Countermeasures Doctrine

**change_class**: feature
**Status**: Active
**Author**: QorLogic Governor
**Date**: 2026-04-16
**Branch**: `phase/15-shadow-genome-doctrine`

## Open Questions

None. Design locked in dialogue: (a) one canonical doctrine file; (b) doctrine + SG-033 static analysis; (b) full migration of SG-016–021 from global skill into the doctrine.

## Context

SG-016–021 exist in the user-global `~/.claude/skills/qor-plan/SKILL.md` but are absent from the repo's `qor/skills/sdlc/qor-plan/SKILL.md` (verified via grep). SG-032 and SG-033 were surfaced during Phase 14 (ledger Entry #32) and live only in the narrative `docs/SHADOW_GENOME.md` Entry #12. No existing doctrine file consolidates them. This phase creates one and wires the repo's `qor-plan` skill to cite it, closing the global/repo drift and enforcing SG-033 by static analysis.

## Track A — Doctrine file (new)

### Affected Files

- `qor/references/doctrine-shadow-genome-countermeasures.md` (new)

### Changes

7-section doctrine file. Each section: the SG ID, failure pattern, countermeasure rule, and a verification hint (grep pattern, AST check, or review prompt). Structure modeled on `qor/references/doctrine-governance-enforcement.md`.

1. **Purpose** — why this doctrine exists; relationship to `/qor-plan` Step 2b and `/qor-audit` adversarial sweep.
2. **SG-016: generic-convention paths** — writing `src/migrations/versions/` without checking `alembic.ini`. Countermeasure: grep/read the actual config before citing any path. Verification hint: `{{verify: <mechanism>}}` tag in draft pass.
3. **SG-017 / SG-020: inventing security controls** — role-based privilege, SECURITY DEFINER. Countermeasure: survey existing mechanism before proposing one. Verification hint: grep existing schema/code for the concrete control.
4. **SG-019: CLI flag portability** — assuming `-k` works on both ruff and mypy. Countermeasure: read each tool's `--help` before citing flags. Verification hint: `<tool> --help | grep <flag>`.
5. **SG-021: multi-layer edit compression** — "add to RLS_POLICIES" hiding which file needs editing. Countermeasure: enumerate every file that receives the edit before writing the verb. Verification hint: grep the target symbol, list all files, disposition each.
6. **SG-032: batch-split-write coverage gap** — lookup-table-based filter drops records created mid-cycle. Countermeasure: classify records at creation, OR provide an explicit fallback bucket in the split. Verification hint: review-time question "can any event in this batch have no prior identity in the lookup?"
7. **SG-033: positional-to-keyword breakage** — changing a signature to keyword-only (`*`) without grepping callers. Countermeasure: enumerate all callers (production + tests) before the change; update positional calls to keyword form. Verification hint: `grep "<fn_name>(" --include=*.py` after the signature change; AST test enforces it.

Each worked example names a real prior incident (Phase 14 for SG-032/033; migrations work for SG-016).

## Track B — Wire `qor-plan` to cite the doctrine

### Affected Files

- `qor/skills/sdlc/qor-plan/SKILL.md`

### Changes

Insert a new Step 2b between current Step 2 (Research Existing Code, line 150) and Step 3 (Create Plan File, line 154):

```markdown
### Step 2b: Grounding Protocol (MANDATORY)

Before writing any prose that names a mechanism (security control, CLI flag, file path, layer boundary, DB role, API surface, trigger/event wiring), run the specific grep/read and cite the verified result inline. See `qor/references/doctrine-shadow-genome-countermeasures.md` for full failure-mode inventory.

**Two-pass authoring**:
1. **Draft pass** — tag every named mechanism with `{{verify: <what>}}`.
2. **Resolve pass** — run the grep/read; replace each tag with a verified citation.

**Residual tags block plan submission.**

**When the plan is a remediation**: quote the audit's "Required Remediation" section verbatim; every prescription must appear with verification grep attached.
```

This mirrors the global skill's Step 2b but references the doctrine by path instead of embedding the SG list. Maintains one source of truth.

## Track C — SG-033 static analysis test

### Affected Files

- `tests/test_shadow_genome_doctrine.py` (new)

### Changes

Two test categories:

**Doctrine content tests** (literal-keyword discipline; W-1 from Phase 13):

- `test_doctrine_shadow_genome_countermeasures_exists` — file at `qor/references/doctrine-shadow-genome-countermeasures.md`.
- `test_doctrine_lists_all_sg_ids` — body contains `SG-016`, `SG-017`, `SG-019`, `SG-020`, `SG-021`, `SG-032`, `SG-033` (7 literal substrings).
- `test_doctrine_documents_sg033_keyword_only_countermeasure` — body contains `keyword-only` and `grep` (SG-033 section enforces the grep discipline).
- `test_doctrine_documents_sg032_batch_split_countermeasure` — body contains `batch-split` or `batch split` and `classify` (SG-032 countermeasure).
- `test_qor_plan_skill_cites_countermeasures_doctrine` — `qor/skills/sdlc/qor-plan/SKILL.md` references `doctrine-shadow-genome-countermeasures.md`.

**SG-033 static analysis test** (AST-based; closes SG-033 as enforceable rule):

- `test_no_positional_calls_to_keyword_only_functions` — for each `.py` file in `qor/scripts/`, parse the AST, find every `FunctionDef` with a `*` (i.e., `args.kwonlyargs` non-empty). For each such function, scan all `.py` files in `qor/scripts/` AND `tests/` for `Call` nodes whose `func.attr` or `func.id` matches the function name. Assert that no positional arg at an index corresponding to a keyword-only parameter exists. Failure mode: "function `<name>` declared keyword-only at `<file>:<line>`, called positionally at `<caller_file>:<line>`."

Implementation outline:

```python
import ast
from pathlib import Path

def collect_keyword_only_functions(root: Path) -> dict[str, tuple[Path, int, list[str]]]:
    """Return {fn_name: (def_file, lineno, positional_arg_names)}."""
    out = {}
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.args.kwonlyargs:
                positional = [a.arg for a in node.args.args]
                out[node.name] = (py, node.lineno, positional)
    return out

def find_positional_violations(
    kwonly_fns: dict, search_roots: list[Path]
) -> list[tuple[Path, int, str]]:
    violations = []
    for root in search_roots:
        for py in root.rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node)
                if name not in kwonly_fns:
                    continue
                _, _, positional = kwonly_fns[name]
                if len(node.args) > len(positional):
                    violations.append((py, node.lineno, name))
    return violations
```

Test asserts `violations == []`. Iterates `qor/scripts/` for definitions and `qor/scripts/ + tests/` for call sites.

## Affected Files (summary)

### New (2)
- `qor/references/doctrine-shadow-genome-countermeasures.md`
- `tests/test_shadow_genome_doctrine.py`

### Modified — skills (1)
- `qor/skills/sdlc/qor-plan/SKILL.md`

## Constraints

- **W-1 literal-keyword discipline**: doctrine body must contain the literal SG IDs and keyword substrings that tests check.
- **Rule 4 (Rule = Test)**: every countermeasure has a test. SG-016/017/019/020/021/032 have doctrine-content tests (keyword presence). SG-033 additionally has an enforceable AST test.
- **Tests before code** for `test_shadow_genome_doctrine.py`.
- **No changes to the user-global `~/.claude/skills/qor-plan/SKILL.md`** (outside repo; operator-owned).
- **No new dependencies**: use Python stdlib `ast` module.
- **Reliability**: pytest 2x consecutive identical results before commit.

## Success Criteria

- [ ] Doctrine file exists with 7 sections; all literal-keyword tests green.
- [ ] Repo's `qor-plan` SKILL.md Step 2b exists and references the doctrine.
- [ ] `test_no_positional_calls_to_keyword_only_functions` green (verifies current codebase; `append_event` is the one known keyword-only function).
- [ ] Tests: +7 new. Baseline 219 → 226 passing, skipped unchanged.
- [ ] `check_variant_drift.py` clean after `BUILD_REGEN=1` (skill text changed).
- [ ] `ledger_hash.py verify` chain valid.
- [ ] Substantiation: `0.4.0 → 0.5.0`; annotated tag `v0.5.0`.

## CI Commands

```bash
python -m pytest tests/test_shadow_genome_doctrine.py -v
python -m pytest tests/
BUILD_REGEN=1 python qor/scripts/check_variant_drift.py
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md
git tag --list 'v*' | tail -3
```
