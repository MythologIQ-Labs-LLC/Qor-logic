# AUDIT REPORT — plan-qor-phase15-shadow-genome-doctrine.md

**Tribunal Date**: 2026-04-16
**Target**: `docs/plan-qor-phase15-shadow-genome-doctrine.md`
**Risk Grade**: L1 (spec-level defects in enforcement tests)
**Auditor**: The QorLogic Judge

---

## VERDICT: **VETO**

---

### Executive Summary

Design direction is correct: one canonical doctrine file, repo-skill citing by path, SG-033 enforced by AST static analysis. VETO issued for 4 defects that would ship an unreliable enforcement test and worsen a pre-existing Razor state. V-1: the AST walker's naive `len(node.args) > len(positional)` check produces false positives on star-unpacking (`fn(x, *rest, y=1)`). V-2: doctrine-content tests for SG-032/SG-033 check for keywords anywhere in the file, allowing the relevant section to be missing entirely while tests pass. V-3: Track B adds ~15 lines to `qor/skills/sdlc/qor-plan/SKILL.md` which is already 274 lines (24 over the 250 Razor); plan does not address. V-4: `ast.FunctionDef` walker misses `ast.AsyncFunctionDef`.

### Audit Results

#### Security Pass
**Result**: PASS. Doctrine + tests only; no credentials, auth, or network surfaces.

#### Ghost UI Pass
**Result**: PASS. No UI.

#### Section 4 Razor Pass
**Result**: FAIL — see V-3.

| Check | Limit | Blueprint Proposes | Status |
|---|---|---|---|
| Max function lines | 40 | AST helpers ~15-30 lines each | OK |
| Max file lines | 250 | Doctrine ~70; test file ~100; `qor-plan/SKILL.md` 274 → ~289 | FAIL (V-3) |
| Max nesting depth | 3 | AST walker nesting ~3 | OK |
| Nested ternaries | 0 | 0 | OK |

#### Dependency Pass
**Result**: PASS. Python stdlib `ast` only. No external.

#### Orphan Pass
**Result**: PASS. Doctrine cited by `qor-plan/SKILL.md` (Track B) and `test_shadow_genome_doctrine.py` (Track C). Test file discovered by pytest.

#### Macro-Level Architecture Pass
**Result**: PASS. Single doctrine file; skill references by path; test enforces both doctrine content and code discipline. No cyclic deps. Plan correctly scopes global `~/.claude/skills/qor-plan/SKILL.md` as out-of-scope (operator-owned, outside repo).

### Violations Found

| ID | Category | Location | Description |
|---|---|---|---|
| V-1 | Test spec gap (false positives) | Track C, AST walker implementation outline | The naive check `if len(node.args) > len(positional): violations.append(...)` flags any call containing `ast.Starred` as a violation. Example: `shadow_process.append_event(event, *extra_args, attribution="UPSTREAM")` is a legal call form (star-unpacks into positional slots, then keyword arg), but `node.args = [Name, Starred]` yields `len=2 > len(positional)=1` → false positive. Currently no such callers exist in codebase, so the test would pass on day one, but the first legitimate `*args` caller introduced later would erroneously fail CI. The plan's implementation outline does not handle `ast.Starred` or `ast.keyword` explicitly. Required: skip or bail on calls containing `Starred`, OR compute positional count excluding `Starred`, OR document the limitation explicitly. |
| V-2 | Test spec gap (doctrine tests too loose) | Track C, doctrine-content tests | `test_doctrine_documents_sg033_keyword_only_countermeasure` asserts the body contains `keyword-only` AND `grep`. These are common tokens — a doctrine file missing SG-033 entirely but mentioning `keyword-only` in the Purpose section and `grep` in an unrelated SG's verification hint would pass this test. Same for `test_doctrine_documents_sg032_batch_split_countermeasure` (`batch-split` and `classify` could co-occur outside SG-032's section). Violates W-1 literal-keyword discipline (Phase 13): test substring must anchor to the specific section it claims to verify. Required: rewrite these two tests to check proximity (e.g., regex `SG-033[\s\S]{0,500}keyword-only`) OR parse section headers and verify the SG-033 section contains the countermeasure keywords. |
| V-3 | Razor worsens pre-existing violation | Track B, `qor/skills/sdlc/qor-plan/SKILL.md` | File is currently 274 lines (grep-verified) — already 24 over the 250-line Razor. Track B adds ~15 lines of Step 2b content, taking it to ~289 lines. Plan does not acknowledge the pre-existing overflow or justify worsening it. Required: either (a) state that SKILL.md files are exempt from the 250 Razor with rationale and a one-line doctrine update, (b) trim the existing file by ≥24 lines to net-zero or improve, OR (c) cite Step 2b in a shorter form that fits the budget. |
| V-4 | Test scope gap (async defs) | Track C, `collect_keyword_only_functions` | Walker checks `isinstance(node, ast.FunctionDef)` — misses `ast.AsyncFunctionDef`. Currently no async defs in `qor/scripts/` (grep confirms), so no immediate failure, but the SG-033 rule should apply to async functions too. A future async keyword-only function would escape enforcement. Required: `isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))`. |

### Required Remediation

1. **V-1**: Revise the AST walker implementation outline to handle `ast.Starred` in call args. Two acceptable approaches: (a) skip calls containing any `Starred` with an inline comment "cannot statically verify star-unpacked positional args"; (b) compute `positional_arg_count = len([a for a in node.args if not isinstance(a, ast.Starred)])` and compare against `len(positional)`. Pick one and state it in Track C. Add test `test_star_unpack_call_not_flagged` that creates an AST with `fn(x, *rest, kw=1)` and asserts no violation emitted.
2. **V-2**: Rewrite both doctrine-content tests to anchor to the specific SG section. Pick one of: (a) regex proximity match (e.g., `re.search(r"SG-033.{0,500}keyword-only", body, re.DOTALL)`); (b) parse markdown headers and verify the "SG-033" heading's subsection contains the countermeasure keywords. State the approach in Track C and update test names accordingly.
3. **V-3**: Resolve the SKILL.md Razor state. Either (a) add a §4 "File size exemptions" to `doctrine-test-discipline.md` declaring SKILL.md files exempt with rationale (they are prose instructions, not code); OR (b) delete ≥24 lines from `qor-plan/SKILL.md` elsewhere (verbose sections, duplicated phrasing) to keep net delta ≤0; OR (c) replace Step 2b's full Grounding Protocol prose with a 3-line pointer to the doctrine. Option (c) is smallest change and honors "single source of truth" most cleanly. Pick and document.
4. **V-4**: Change the AST walker's type check to `isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))`. Trivial fix.

### Verdict Hash

**Content Hash**: `6b3bc769555562ed2908f024242acd6cc07c7be602c7dc31e425d6efb0c1f6aa`
**Previous Hash**: `937dec794308dcca09765003004042f8afd622b8b93b438aedad44af9dc66440`
**Chain Hash**: `d9984335ef244f39ae2e9ee53aa25ef1b128808a49b149308d31b0d7963ed1c0`
(sealed as Entry #36)

---
_This verdict is binding._
