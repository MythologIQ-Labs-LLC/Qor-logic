# Doctrine: Shadow Genome Countermeasures

Canonical inventory of recurring failure patterns surfaced during audit tribunals and the mechanical countermeasures that prevent their recurrence. Cited by `qor/skills/sdlc/qor-plan/SKILL.md` Step 2b (Grounding Protocol) and consulted during `/qor-audit` adversarial sweeps.

Each entry names the failure pattern, the countermeasure rule, and a verification hint (grep/read/test) an agent can run to detect the antipattern.

## SG-016: generic-convention paths without grounding

Writing `src/migrations/versions/` because "most repos use that" without checking `alembic.ini` or `ls tests/` or `ls infra/`.

**Countermeasure**: Before citing any file path, run the specific grep/read that proves the path exists in this repo. Tag unverified paths with `{{verify: <mechanism>}}` in the draft pass.

**Verification hint**: `ls <proposed_root>` or `grep <symbol> --include=*.toml` before the plan cites a path.

## SG-017 / SG-020: inventing security controls without surveying existing mechanism

Claiming "role-based privilege" or `SECURITY DEFINER` enforces tenant isolation without reading the schema or existing policies.

**Countermeasure**: Grep the existing schema/code for the concrete security mechanism before proposing one. If the mechanism is absent, state that clearly — do not invent one that sounds plausible.

**Verification hint**: `grep -rn "SECURITY DEFINER\|REVOKE\|RLS_POLICIES" src/` before any security claim.

## SG-019: CLI flag portability assumption

Assuming `-k` works on both `ruff` and `mypy` because pytest accepts it. Tool CLIs disagree on flag semantics.

**Countermeasure**: Read each tool's `--help` output before citing any flag. Do not generalize across tool families.

**Verification hint**: `<tool> --help | grep <flag>` for every flag cited.

## SG-021: multi-layer edit compression

Writing "add to `RLS_POLICIES`" in a plan, which compresses "edit these 4 files" into a single verb that hides which files actually receive the edit.

**Countermeasure**: Enumerate every file that receives the edit before writing the verb. Map "add to X" → "edit `path1.py` line N; edit `path2.py` line M; ..." with grep evidence.

**Verification hint**: `grep -rn "<target_symbol>" --include=*.py` produces the file list; the plan disposes of each.

## SG-032: batch-split-write coverage gap

Lookup-table-based write-back (e.g., `src_map.get(e["id"])`) drops records created mid-cycle. Newly minted records have no prior identity in the lookup and silently fall through the filter.

**Countermeasure**: Either (a) classify records at creation time with explicit file/bucket assignment; or (b) add a default bucket in the split for unmatched records. Never rely on a post-hoc lookup to assign records that didn't exist when the lookup was built.

**Verification hint**: review-time question — "can any record in this batch have no prior identity in the lookup?" If yes, the plan must specify the fallback. Source incident: Phase 14 v2 (Entry #32 V-1).

## SG-033: positional-to-keyword breakage

Changing a function signature from `(x, y=None)` to `(x, *, y=None)` (keyword-only) without updating existing positional callers. Runtime breaks silently until called.

**Countermeasure**: Before introducing `*` in a signature, grep all call sites (production + tests) and update positional calls to keyword form in the same commit. "Existing body unchanged" does not mean "existing callers unchanged."

**Verification hint**: `grep "<fn_name>(" --include=*.py` after the signature change. Enforced by `tests/test_shadow_genome_doctrine.py::test_no_positional_calls_to_keyword_only_functions` (AST-based). Source incident: Phase 14 v2 (Entry #32 V-2).

## SG-034: AST walker node-family omission

AST-based code analysis walkers that check only `ast.FunctionDef` miss `ast.AsyncFunctionDef`; walkers that count `Call.args` by length miss `ast.Starred` unpacking. Either omission produces false positives or false negatives.

**Countermeasure**: Enumerate every relevant node family: `FunctionDef + AsyncFunctionDef`; `Call.args` filtered for `Starred`; `Call.func` dispatched between `Name` and `Attribute`. A walker that misses a family produces unreliable results.

**Verification hint**: ast-based tests should include a Rule-4 negative-path test with each family (e.g., `test_star_unpack_call_not_flagged`, `test_async_keyword_only_functions_detected`). Source incident: Phase 15 v1 (Entry #36 V-1 + V-4).

## SG-035: doctrine-content test unanchored

Tests asserting `"keyword-only" in body` pass when the doctrine section they claim to verify is missing entirely but the keyword co-occurs elsewhere. Violates W-1 literal-keyword discipline.

**Countermeasure**: Anchor keyword checks to the section header (regex proximity or markdown header parsing). A doctrine test that passes with its subject section removed does not enforce what it claims.

**Verification hint**: use `re.search(r"<SG-ID>.{0,500}<keyword>", body, re.DOTALL)` or parse headers. Include a negative-path test (e.g., `test_proximity_anchor_fails_when_section_missing`) that strips the section and proves the test fails. Source incident: Phase 15 v1 (Entry #36 V-2).
