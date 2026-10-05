# Plan: Phase 303 - Two shipped skill references invoke this repository's CLI, the boundary lint ignores a terms-file BOM, and CI asserts the boundary scope it intends

**change_class**: hotfix

**doc_tier**: standard

**terms**: `[]` (this plan introduces no new term; the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: CI still scans no identity terms, because no terms list is committed or provided to CI; `--expect-scope structural` makes that intent explicit and fail-closed, it does not add identity coverage (LD-8); only a byte-order mark at the very start of the terms file is removed (LD-4); the CLI-name fix covers exactly the two shipped skill reference lines named in GH #457 and their compiled variant copies, and other tracked files that still carry the same outside name in any letter case are left as they are (LD-3); the Phase 89 self-application test maps exactly one CI line, the Phase 303 boundary command, back to the form the sealed Phase 89 plan covers, and compares every other CI line unmapped (LD-6)
- non_goals: a committed or CI-provided identity terms list; editing or rewriting sealed plans (the Phase 89 plan included), gate artifacts, intent-lock records, the ledger or the shadow genome; changing `github_surface` or `advisory_filing_control`; changing the doctrine text; release publication
- exclusions: identity terms in CI (left open by the owner, LD-8); the other occurrences of the outside name, sealed history and one live test (left open by the owner, LD-3)

**iteration**: 2 (on branch `phase/303-boundary-lint-scope`). Iteration 1 was vetoed (V1, `specification-drift`): it edited a bullet of the sealed Phase 89 plan, whose bytes a ledger entry commits by content hash, without disclosing that binding. The owner decided on 2026-10-05 that no sealed plan text is edited; the test that reads that plan changes instead. Iteration 2 therefore drops the Phase 89 plan edit, changes `tests/test_ci_coverage_lint.py` narrowly (LD-6), restates LD-3 with a case-insensitive count (advisory A1), and specifies the CLI-form tests so that a failing run cannot print the outside name (advisory A2, LD-7). Everything else is unchanged from iteration 1.

**Issue**: GH #457 ("publication_boundary_lint cannot enforce identity terms in CI: the term list lives at a gitignored path"). Scope is narrowed by the owner's decision of 2026-10-02: fix only the two unbound shipped skill files, the BOM comment bug, and make the CI step assert the scope it reached; the committed term list and the sealed-history rewrite stay open. The defect statements below are derived from the code at the base and reproduced in scratch clones.

**Current base**: `25babc0e31fb7ad0b64d5690b3740d3bc9322d28` (`main` after Phase 302 merged; project version `0.175.6`, sealed at META_LEDGER #835)

**Target version**: `0.175.7` (hotfix bump from `0.175.6`)

**Public-boundary note**: the CLI name being removed in Phase 4 belongs to an outside project. This plan never writes it; it is called "an outside project's CLI name" throughout. Every citation of the two affected lines is chosen so that neither the command nor its printed output contains it, and the Phase 1 tests assert the repository's own CLI form at those lines without spelling the outside name; they reduce each line to a boolean inside a helper, so a failing run prints only the file path (LD-7).

**Citation currency**: every `git show ... | grep ... ->` evidence statement below (45 in all) cites `25babc0e31fb7ad0b64d5690b3740d3bc9322d28` and was re-executed against it for iteration 2 (one observed line per statement, 0 mismatches); so was every quoted `prints` command, one of which reads the Phase 89 seal commit `4a34b08e` (LD-6). Each statement's pattern is written exactly as it is run: the patterns use `.` or a bracket class in place of regex metacharacters, so no statement depends on a backslash escape. Lines whose text would carry the outside name, an arrow, or a non-ASCII character are not quoted as `->` evidence; they are cited by line number in prose, or by a `grep -noE` or `grep -c` command whose printed output is quoted in full and contains neither. Commands that must match the outside name take it into a shell variable `N` from the base line LD-3 names, so neither the command nor its output spells it. The other command outputs quoted (`git ls-tree`, `git grep`, `git ls-remote`, scratch runs) were observed on 2026-10-05. Scratch runs used clones of the base outside the repository, with the Phase 1 test changes and the Phase 2 to Phase 5 edits applied exactly as specified below. For iteration 2 a fresh scratch clone re-ran the compile (15 files under `qor/dist/`, drift check OK), the Phase 1 to Phase 4 test, mutation and lint runs, the CI-step runs of LD-6 and the full suite; the base full-suite count and the Phase 5 release-state observations are iteration 1 observations that the iteration 1 audit reproduced, and no iteration 2 change touches them.

## Open Questions

None. The owner's narrowing decision fixes the scope to three changes: the two shipped lines (LD-1 to LD-3), the BOM (LD-4) and the CI scope assertion (LD-5, LD-6). The committed term list and the sealed-history rewrite are declared residuals (LD-3, LD-8), not open questions.

## Problem

Three faults, each reproduced at the base.

1. Two shipped skill references name an outside project's CLI where this repository's `qor-logic` is meant: the ledger-entry template comment in `qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md` (line 151) tells the reader which verifier skips an unbackticked hash, and the ledger-commitment step of `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` (line 457) is the command the seal runs. The compiled copies under `qor/dist/variants/` for claude, codex, cursor and kilo-code carry the same two lines. A reader or an agent following either line runs a command this package does not install.
2. `_load_terms` reads the operator terms file as plain UTF-8, so a leading byte-order mark (U+FEFF) stays on the first line, and `str.strip` does not remove it (`python -c "print(chr(0xFEFF).isspace())"` prints `False`). Observed at the base with the synthetic term `example-outside-cli`: a file holding a BOM, the line `# comment` and that term loads as two terms, the comment with the mark attached and the term; a file holding a BOM and the term alone loads one term with the mark attached, and a tree whose only text names that term gives `findings=[]` with `scope='structural+identity'`; a file holding a BOM and a comment only gives `scope='structural+identity'` with no real term. So a BOM turns a first-line comment into a claimed identity scope and silently disables a first-line term.
3. CI runs the lint with no statement of the scope it intends. The printed `[scope: ...]` label is informational: nothing fails if the scope reached differs from the one CI means to enforce, in either direction.

With the Phase 1 test file applied to the base, `python -B -m pytest tests/test_boundary_lint_expected_scope.py -q` gives `19 failed, 2 passed` (Phase 1).

## Locked Decisions

### LD-1: the two shipped lines and the CLI they should invoke (GH #457, part a)

The bootstrap template line sits in an HTML comment directly below this line:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md | grep -nE 'line matches none of them, so the entry is'` -> `150:     on a **Previous Hash**: line matches none of them, so the entry is`

Its next line holds the file's only `verify-ledger`: `git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md | grep -noE 'verify-ledger'` prints `151:verify-ledger`, and `git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md | grep -cE 'qor-logic verify-ledger'` prints `0`. The token before ` verify-ledger` inside that line's backtick span is the outside project's CLI name.

The seal-ladder line is the one command of Step 3:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -nE '^## Step 3 -- ledger-commitment integrity'` -> `448:## Step 3 -- ledger-commitment integrity (Phase 251; GH #408)`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -noE 'scripts ledger_commitment --session'` prints `457:scripts ledger_commitment --session` (the file's only `ledger_commitment` line), and `git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -cE '^qor-logic scripts ledger_commitment'` prints `0`. The first whitespace-delimited token of line 457 is the outside project's CLI name.

This package installs two console scripts, `qor-logic` and its alias `qorlogic`, both the same entry point, and the outside name is neither; both commands exist under them:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:pyproject.toml | grep -nE '^qor-logic = '` -> `59:qor-logic = "qor.cli:main"`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:pyproject.toml | grep -nE '^qorlogic = '` -> `60:qorlogic = "qor.cli:main"`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/cli.py | grep -nE 'add_parser."verify-ledger"'` -> `194:    sp_verify = sub.add_parser("verify-ledger", help="verify META_LEDGER.md chain")`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/cli.py | grep -nE '"scripts": lambda: _do_module_dispatch'` -> `332:        "scripts": lambda: _do_module_dispatch(args.command, args),`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/ledger_commitment.py | grep -nE 'add_argument."--repo-root"'` -> `196:    ap.add_argument("--repo-root", type=Path, default=Path("."))`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/ledger_commitment.py | grep -nE 'add_argument."--session"'` -> `197:    ap.add_argument("--session", default=None)`

Decision: in each of the two source files, replace exactly that one token with `qor-logic`, the form the same ladder uses for its other commands (`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -cE 'qor-logic (scripts|reliability) '` prints `6`, and `qor/skills/governance/qor-validate/SKILL.md` documents `qor-logic verify-ledger`): on line 151 of the bootstrap template, the token before ` verify-ledger` inside the backtick span, and on line 457 of the seal ladder, the first token. The rest of both lines, and every other line, is unchanged. The edits are made in the two source files only (LD-2).

### LD-2: the compiled copies are regenerated, not edited

The same two lines ship in four variants: `git ls-tree -r --name-only 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 qor/dist/variants | grep -cE 'references/(qor-bootstrap-templates|seal-gate-ladder)[.]md$'` prints `8` (claude, codex, cursor and kilo-code, one of each file). The compile writes the committed dist by default:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/dist_compile.py | grep -nE '^DEFAULT_OUT = '` -> `23:DEFAULT_OUT = Path(str(_resources.asset("dist")))`

Decision: after the LD-1 source edits, run `PYTHONPATH=. python -m qor.cli compile` (the `qor-logic compile` command) at the repository root and commit what it writes under `qor/dist/`. Observed in the scratch clone: it rewrites the 8 variant copies (one changed line each) and the 7 manifests (`qor/dist/manifest.json` and the claude, cline, codex, cursor, gemini and kilo-code variant manifests): two sha256 values change in each of the top-level, claude, codex, cursor and kilo-code manifests, and every manifest's `generated_ts` changes; 15 files under `qor/dist/` in all. After it, `python qor/scripts/check_variant_drift.py` prints `OK: 413 files, no drift`. No file under `qor/dist/` is edited by hand.

### LD-3: the other occurrences stay as they are (owner decision)

The outside name is counted without spelling it, by taking it from the seal-ladder line of LD-1 into a shell variable. That line is the one command of the ladder's Step 3:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -nE '^## Step 3 -- ledger-commitment integrity'` -> `448:## Step 3 -- ledger-commitment integrity (Phase 251; GH #408)`

It is the file's only `ledger_commitment` line (`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -noE 'scripts ledger_commitment --session'` prints `457:scripts ledger_commitment --session`). Then with `N=$(git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md | grep -E 'scripts ledger_commitment --session' | awk '{print $1}')`, the case-sensitive `git grep -l -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 | wc -l` prints `69` and the case-insensitive `git grep -il -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 | wc -l` prints `72`. Neither the commands nor their printed counts contain the name. Iteration 1 gave only the case-sensitive count.

The 72 files are the 2 source files and 8 compiled copies of LD-1 and LD-2 and 62 others. With the same `N`, `git grep -il -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- .qor/gates | wc -l` prints `30`, `git grep -il -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- .qor/intent-lock | wc -l` prints `11` and `git grep -il -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- 'docs/plan-*.md' | wc -l` prints `18`. The remaining three are `docs/META_LEDGER.md`, `docs/PROCESS_SHADOW_GENOME.md` and `tests/test_portable_governance_boundary.py`. Three of the 62 match only case-insensitively, because they carry a different-case form of the name: one intent-lock plan snapshot, the Phase 268 plan, and the live test. `git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_portable_governance_boundary.py | grep -niF -e "$N" | cut -d: -f1` prints `118` and `119`, two lines that assert that the name is absent from two governance documents. Under `qor/`, `git grep -ic -e "$N" 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- qor | wc -l` prints `10`, and each of those 10 lines ends in `:1`: one matching line in each of the 10 files LD-1 and LD-2 change, so no other shipped skill, reference or script carries the name in any case.

Decision: none of the 62 is edited. The 61 sealed or historical records are governance evidence, and the owner left the sealed-history rewrite open. The live test is not one of the two shipped lines GH #457 names, and the owner's narrowing keeps it out of scope. It is a regression guard that asserts the name's absence; it does not ship it. This is a declared residual: after this phase, those 62 files still carry the outside name in some letter case.

### LD-4: a leading BOM on the terms file is ignored (GH #457, part b)

The terms file is read as plain UTF-8 and a line starting with `#` is a comment:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'read_text.encoding="utf-8".[.]splitlines'` -> `98:    for line in terms_file.read_text(encoding="utf-8").splitlines():`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'if line and not line.startswith."#".:'` -> `100:        if line and not line.startswith("#"):`

Any loaded term sets the identity scope:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'return BoundaryResult.findings, "structural.identity" if terms else "structural".'` -> `173:    return BoundaryResult(findings, "structural+identity" if terms else "structural")`

Problem item 2 gives the observed consequences. Decision: line 98 reads with `encoding="utf-8-sig"`, which removes one leading BOM and is otherwise UTF-8, with a three-line comment naming Phase 303 and GH #457. Nothing else in `_load_terms` changes. Two other modules load terms through the same function and get the fix unchanged:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/github_surface.py | grep -nE 'from qor.scripts.publication_boundary_lint import _load_terms, scan_text'` -> `31:from qor.scripts.publication_boundary_lint import _load_terms, scan_text`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/advisory_filing_control.py | grep -nE 'from qor.scripts.publication_boundary_lint import _ALLOW_RE, _load_terms, scan_text'` -> `35:from qor.scripts.publication_boundary_lint import _ALLOW_RE, _load_terms, scan_text`

`_load_terms` keeps its signature and return type. A U+FEFF anywhere other than the start of the file is not removed (residual; a BOM is by definition a leading mark).

### LD-5: `--expect-scope` makes the achieved scope a fail-closed assertion (GH #457, part c)

The lint prints its scope and exits on findings only:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'print.f"publication_boundary_lint: .len.result.findings.. finding.s. "'` -> `188:    print(f"publication_boundary_lint: {len(result.findings)} finding(s) "`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'return 1 if result.findings else 0'` -> `190:    return 1 if result.findings else 0`

The default overlay path is gitignored, so a CI checkout cannot hold it:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/publication_boundary_lint.py | grep -nE 'terms_file = repo_root / ".qor" / "private" / "boundary-terms.txt"'` -> `158:        terms_file = repo_root / ".qor" / "private" / "boundary-terms.txt"`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:.gitignore | grep -nE '^.qor/private/'` -> `37:.qor/private/`

Decision: a module constant `SCOPES = ("structural", "structural+identity")`; `collect_findings` returns `SCOPES[1] if terms else SCOPES[0]` (the same two strings as today); `main` gains `--expect-scope` with `choices=SCOPES` and default `None`. After the existing summary line, if `--expect-scope` is given and `result.scope` differs from it, `main` prints `publication_boundary_lint: scope mismatch: expected <expected>, achieved <achieved>` and returns 1, whatever the finding count. Otherwise the exit code is the existing one (1 on findings, else 0). Without the flag, output and exit codes are unchanged.

Why this option. It is the smallest change that turns the scope label into a checked statement, it compares in both directions (an unreached identity scope and an unintended one both fail), and it leaves every caller that does not pass the flag as it is (the audit Step 0.6 ladder, the seal's Step 4.6.14, `github_surface`, `advisory_filing_control`). Exit 1 is the lint's one failure code; the mismatch line says which failure it is. A value outside `SCOPES` is an argparse usage error and exits 2 (observed in the scratch clone with `--expect-scope identity`). At the base the flag does not exist, so any run passing it exits 2 (observed): Phase 2 must land before Phase 3.

### LD-6: CI states the scope it intends, structural

The CI step today:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:.github/workflows/ci.yml | grep -nE 'name: publication boundary$'` -> `122:      - name: publication boundary`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:.github/workflows/ci.yml | grep -nE 'so CI enforces the structural'` -> `130:        # (.qor/private/ is gitignored), so CI enforces the structural`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:.github/workflows/ci.yml | grep -nE 'run: python -m qor.scripts.publication_boundary_lint --repo-root .$'` -> `132:        run: python -m qor.scripts.publication_boundary_lint --repo-root .`

The step's own comment (lines 129 to 131) already states the intent: structural detectors only. Decision: after line 131 add a two-line comment (Phase 303, GH #457: `--expect-scope` states that intent, so the step fails if the achieved scope ever differs from it) and change line 132 to `run: python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural`. Observed in a fresh clone of the scratch implementation commit, running the step's `run` text as CI would: with no overlay, `0 finding(s) [scope: structural]` and exit 0; with a one-term overlay written at `.qor/private/boundary-terms.txt` (a term absent from the tree), `0 finding(s) [scope: structural+identity]`, then `scope mismatch: expected structural, achieved structural+identity` and exit 1; with the step's value changed to `structural+identity` and no overlay, `scope mismatch: expected structural+identity, achieved structural` and exit 1.

The CI-surface self-test requires every CI command to appear inside a bullet of the Phase 89 plan's `## CI Commands` list:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/ci_coverage_lint.py | grep -nE 'if any.match_form in plan_bullet for plan_bullet in ci_bullets.:'` -> `248:        if any(match_form in plan_bullet for plan_bullet in ci_bullets):`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_ci_coverage_lint.py | grep -nE 'plan = REPO_ROOT / "docs" / "plan-qor-phase89-ci-commands-reconciliation.md"'` -> `270:    plan = REPO_ROOT / "docs" / "plan-qor-phase89-ci-commands-reconciliation.md"`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_ci_coverage_lint.py | grep -nE 'warnings = ci_coverage_lint.check_plan.plan, workflows_dir.'` -> `272:    warnings = ci_coverage_lint.check_plan(plan, workflows_dir)`

It is the only code that reads that plan: `git grep -nE 'phase89|ci-commands-reconciliation' 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- tests qor/scripts qor/reliability .github | wc -l` prints `1`. That plan's bullet for this step holds the base command (`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/plan-qor-phase89-ci-commands-reconciliation.md | grep -noE 'publication_boundary_lint --repo-root [.]'` prints `316:publication_boundary_lint --repo-root .`; the line itself carries a non-ASCII dash and is not quoted). With the Phase 3 `ci.yml` change and the base test file, `test_lint_self_applies_to_phase_89_plan` fails on the new command (observed in the scratch clone as mutation M7: `1 failed, 216 passed`; the one warning is the boundary step's command).

The Phase 89 plan is sealed and ledger-bound. META_LEDGER Entry #237 commits its bytes by content hash:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/META_LEDGER.md | grep -nE '^### Entry #237'` -> `9048:### Entry #237: IMPLEMENTATION -- Phase 89 (plan ci_commands reconciliation against .github/workflows)`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/META_LEDGER.md | grep -noE 'b98d4ff926a655fa[0-9a-f]{48}'` prints `9077:b98d4ff926a655fa1e7f78a4a003428ac066f223a969eb842210f1826d6baaf4`, and `git show 4a34b08e:docs/plan-qor-phase89-ci-commands-reconciliation.md | sha256sum` prints `b98d4ff926a655fa1e7f78a4a003428ac066f223a969eb842210f1826d6baaf4  -` (`4a34b08e` is the Phase 89 seal commit and an ancestor of the base). That binding is verifiable at the seal commit. The live file has not matched it since later phases appended to it: `git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/plan-qor-phase89-ci-commands-reconciliation.md | sha256sum` prints `239a282039f3c972aa428ea3aa3b25cc01a60e5d72a6058c6789aedf9fe47460  -`. That older divergence predates this phase, and this phase does not change it. Decision (owner, 2026-10-05): this phase does not edit the Phase 89 plan or any other sealed plan text, and it modifies no ledger-bound artifact. Entry #237's binding is untouched. No AMENDMENT is needed, because no committed artifact changes. Iteration 1's precedent statement is withdrawn: this phase no longer maintains that plan's bullet list.

Decision: the test changes instead, in the narrowest way that keeps its intent (every live CI command is covered by the Phase 89 plan or exempted there). In `tests/test_ci_coverage_lint.py`:

- Two module constants, `_PHASE_303_CI_COMMAND = "python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural"` and `_PHASE_89_COVERED_COMMAND = "python -m qor.scripts.publication_boundary_lint --repo-root ."`, under a comment naming Phase 303, GH #457 and why the sealed plan is not edited. Two path constants, `LIVE_WORKFLOWS` (`.github/workflows`) and `PHASE_89_PLAN`.
- A helper `_apply_phase_303_allowance(src, dest) -> int` copies every `src/*.yml` into `dest`. It rewrites each line whose stripped text is exactly `run: ` followed by `_PHASE_303_CI_COMMAND` to the same indentation followed by `run: ` and `_PHASE_89_COVERED_COMMAND`, and returns how many lines it rewrote. Every other line is copied unchanged. A line that differs in any character, such as another `--expect-scope` value or an added argument, is not rewritten.
- `test_lint_self_applies_to_phase_89_plan(tmp_path)` builds the mapped copy of the live workflows. It asserts the helper rewrote exactly one line, so the allowance cannot outlive the line it exists for, and it runs `ci_coverage_lint.check_plan` on the Phase 89 plan against that copy. It still asserts `warnings == []` with the same message. `ci_coverage_lint` itself does not change.
- A new `test_phase_303_allowance_does_not_hide_other_ci_drift`, parametrized three ways, copies the live workflows into a scratch source and applies one drift there, then applies the helper and runs `check_plan`. It asserts the warnings are exactly the drifted command, so the allowance hides nothing else:
  - `boundary-scope-value-changed`: the Phase 303 line with `structural+identity` as its scope value;
  - `boundary-flag-added`: the Phase 303 line with ` --no-git` appended;
  - `unrelated-command-added`: an extra workflow file whose one step runs `python -m example_uncovered_check`; here the helper still rewrites exactly one line.

Why this option. Normalizing the `--expect-scope` argument in general, or accepting any form of the boundary step, would also hide a later change to the step's scope; the exact-line mapping does not, and the drift test proves it (mutation M8). Exempting the command through the plan's `## CI Coverage Exemptions` section would edit the sealed plan. Changing `ci_coverage_lint` would change the lint's behavior for every plan. The mapping lives in the one test that reads the sealed plan and changes nothing else.

### LD-7: tests, determinism and file sizes

The new tests go in a new file, `tests/test_boundary_lint_expected_scope.py`. They build their trees and terms files under `tmp_path` with `write_bytes`, use only synthetic terms (`example-outside-cli`, built into the file as a constant; the BOM is `chr(0xFEFF)`), call `publication_boundary_lint` in process, and use no network and no clock. Three tests read this checkout: the CI-wiring test parses `.github/workflows/ci.yml` with `yaml.safe_load`; the overlay test runs `git check-ignore`; the CLI-form tests read the two source files and their eight compiled copies. None reads a ledger, gate or sealed record. The file was observed green twice in a row with Phases 2 to 4 applied (`21 passed`, twice). The LD-6 change to `tests/test_ci_coverage_lint.py` reads the live workflows and the Phase 89 plan, as the test it changes already did, and writes its copies under `tmp_path`; that file was observed green twice in a row with Phases 2 to 4 applied (`16 passed`, twice).

`qor/scripts/publication_boundary_lint.py` is 194 lines at the base and 207 after (observed in the scratch clone); the new test file is 200 lines; `tests/test_ci_coverage_lint.py` is 276 lines at the base and 351 after. All new and changed source is ASCII.

The tests that check the shipped lines do not contain the outside name, and a failing run does not print it. Under pytest's assertion rewriting, an assert that compares the token (`assert tok == "qor-logic"`) prints the compared token, and a helper assert on the matched lines prints those lines. So each check is a helper that reads the file, finds the single line holding its marker and returns one boolean (`_template_names_our_verifier(rel)`, `_ladder_step_invokes_our_cli(rel)`; a missing or repeated marker line returns `False`). The test binds that boolean to a local and asserts it with the path as the message (`ours = _ladder_step_invokes_our_cli(rel)`, then `assert ours, rel`). The failing frame then holds only `rel` and `ours`, so even `--showlocals` has nothing else to show. Observed at the base in a scratch clone with both changed test files copied in: `python -B -m pytest tests/test_boundary_lint_expected_scope.py tests/test_ci_coverage_lint.py -q -p no:cacheprovider` gives `23 failed, 14 passed`. The same run with `-vv`, with `-l`, and with `--tb=long -vv -l` gives the same counts. Each of the four captured outputs was searched case-insensitively for the outside name, with `N` set as in LD-3, using `grep -ci -- "$N" <output>`; each printed `0`. As a control, the same search on the base seal ladder printed `1`.

### LD-8: residuals and limits

- CI scans no identity terms. No terms list is committed or provided to CI, and the owner left that open; `--expect-scope structural` records that CI's intended scope is structural and fails if that ever changes unannounced. Identity scanning in CI still needs a committed or CI-provided term list.
- 62 tracked files still carry the outside name in some letter case: 61 sealed or historical records and one live test that asserts its absence (LD-3).
- Only a leading BOM is removed from the terms file (LD-4).
- Runs that do not pass `--expect-scope` (the audit and seal ladders, local runs) keep reporting the scope without asserting it.

### LD-9: no spec delta and no documentation change

The only capability specs are `qor/specs/execution-context-governance` and `qor/specs/spec-corpus`; neither covers the boundary lint. The doctrine's statement of CI's scope stays true after this phase:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/references/doctrine-publication-boundary.md | grep -nE 'CI runs the structural detectors only; the'` -> `119:is a control nobody enforces. CI runs the structural detectors only; the`

No README, doctrine or skill text mentions `--terms-file`, `--no-git` or `--expect-scope` (`git grep -nE -e '--expect-scope|--terms-file|--no-git' 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 -- README.md 'qor/references/*.md' 'qor/skills/**/*.md'` prints nothing), and the skills' own invocations of the lint (the seal's Step 4.6.14 runs it with `--repo-root .` only) are unchanged. The two skill reference files of LD-1 are edited only at the named token.

### LD-10: version target is 0.175.7

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.6"`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:CHANGELOG.md | grep -nE '^## .0.175.6. - '` -> `13:## [0.175.6] - 2026-10-02`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/META_LEDGER.md | grep -nE '^### Entry #835'` -> `24603:### Entry #835: SESSION SEAL -- Phase 302 the install receipt records only sha256 values checked against the installed bytes, and dist manifests are drift-checked (v0.175.6)`

`change_class: hotfix` bumps `0.175.6` to `0.175.7` at `/qor-substantiate`.

### LD-11: CHANGELOG Unreleased note

`/qor-implement` writes the user-facing note under `## [Unreleased]`; the seal stamps it and refuses an empty section:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:CHANGELOG.md | grep -nE '^## .Unreleased.'` -> `11:## [Unreleased]`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

Lines 14 to 16 exclude internal refactors, ledger entry numbers and hash values from the CHANGELOG; line 32 continues the rule that an empty `Unreleased` section raises `ValueError` at the stamp; line 9 allows `Fixed` as a subsection label (lines 9, 13, 16 and 31 carry inline code spans and are paraphrased).

The note is one `### Fixed` bullet with exactly this text:

```markdown
- **Phase 303 (hotfix; two shipped skill references invoke `qor-logic`, the publication-boundary lint ignores a byte-order mark on its terms file, and CI asserts the boundary scope it intends, GH #457)**: The ledger-entry template comment in the `qor-bootstrap` references and the ledger-commitment step of the `qor-substantiate` seal ladder, and their compiled variant copies, named a different project's command-line tool where this repository's `qor-logic` command was meant; both now invoke `qor-logic`. `publication_boundary_lint` read its operator terms file without removing a UTF-8 byte-order mark, so the mark stayed on the first line: a first-line comment was loaded as a term, which reported `structural+identity` scope with no real term, and a first-line term never matched. The terms file is now read with a leading mark removed. The lint gains `--expect-scope structural|structural+identity`: when the scope it reached differs from the one given, it prints `scope mismatch: expected <scope>, achieved <scope>` and exits 1. The CI publication-boundary step now passes `--expect-scope structural`, so it fails if the scope it reaches ever differs from the structural scope it states. CI still does not scan identity terms, because no terms list is committed or provided to CI. `docs/release-state.json` records `0.175.6` as `sealed_unpublished`.
```

It is ASCII only, does not spell the outside name, and states only what Phases 2 to 5 implement. It names the residual that matters to a reader (CI scans no identity terms) instead of implying identity coverage, says "a leading mark" rather than any U+FEFF, and claims the CLI fix only for the two named references and their copies. Its only `#` number is the issue reference `GH #457`; it carries no ledger entry number and no hash value. Clause to proof:

- both references and their copies now invoke `qor-logic`: `test_the_bootstrap_ledger_template_names_this_repositorys_verifier` and `test_the_seal_ladder_commitment_step_invokes_this_repositorys_cli` (5 items each);
- a first-line comment no longer loads as a term, no false identity scope, a first-line term matches: `test_a_bom_does_not_turn_a_comment_into_a_term`, `test_a_bom_comment_only_overlay_claims_no_identity_scope`, `test_a_bom_does_not_hide_the_first_term`;
- `--expect-scope` prints the mismatch and exits 1, both directions; a match passes; findings are not masked: `test_expect_scope_fails_closed_when_the_achieved_scope_differs` (2 items), `test_expect_scope_passes_when_the_achieved_scope_matches` (2 items), `test_expect_scope_does_not_mask_findings`;
- the CI step passes `--expect-scope structural` and fails when the scope differs: `test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states`;
- CI scans no identity terms: `test_the_default_overlay_path_is_not_committed` (the default overlay path is ignored, so a CI checkout has no terms);
- the release-state record: LD-12.

Its last sentence has the form of the sealed Phase 302 bullet under `## [0.175.6]`, which ends by recording `0.175.5` as `sealed_unpublished`.

### LD-12: release-state continuity for 0.175.6

Once the seal bumps the project version to `0.175.7`, `0.175.6` stops being the implicit candidate, and the coverage rule treats it as an orphan unless a reachable tag or a disposition covers it:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set.exceptions. - .project_version.'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/release_state.py | grep -nE 'if _semver.v. <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.6` has no release tag on the remote. Line 24625 of `docs/META_LEDGER.md` at the base is the `**Version**:` line of Entry #835 (it carries an arrow and is cited in prose). While authoring, `git ls-remote --tags origin` listed no `v0.173` or later tag; the highest remote tag was `v0.172.2` (observation, 2026-10-05; not a test expectation).

The record at the base ends with `0.175.5` and has no `0.175.6` entry:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/release-state.json | grep -nE '"version": "0.175.(5|6)"'` -> `90:      "version": "0.175.5",`

This phase appends exactly one entry after the `0.175.5` entry, mirroring how Phase 302 recorded `0.175.5`:

- `version`: `0.175.6`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #835); no release tag was pushed to the remote, so the version is sealed but not published.`

The immediate precedent:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:docs/release-state.json | grep -nE 'META_LEDGER #832'` -> `92:      "reason": "Sealed by /qor-substantiate (META_LEDGER #832); no release tag was pushed to the remote, so the version is sealed but not published."`

The changelog rule that excludes ledger entry numbers (LD-11) governs `CHANGELOG.md`, not this record; `qor/references/doctrine-changelog.md` lines 78 and 79 give the record's closed shape (each entry exactly `version`, `state`, `reason`), and lines 91 to 93 make every state an operator-asserted disposition whose validator checks the shape and the dated CHANGELOG section (cited in prose; the lines carry inline code spans). `0.175.6` has a dated section (LD-10), which the validator requires:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.6` is reachable from the base in a local checkout (`git merge-base --is-ancestor v0.175.6 25babc0e31fb7ad0b64d5690b3740d3bc9322d28` exits 0). It is not on the remote, so CI does not see it, and it does not void the disposition:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.6` locally, the plain local tag-coverage run cannot tell whether the entry is present. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 5): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. The suite consumes the live record:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state.RELEASE_STATE, versions.'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The rule the entry relies on is already unit-tested:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 5), not written by hand at seal time. No entry is recorded for `0.175.7`: after the seal it is the implicit candidate. No ledger entry, seal, gate artifact or dated CHANGELOG section is edited.

### LD-13: canonical governance shape

This file is the canonical `docs/plan-qor-phase303-*.md` plan on branch `phase/303-boundary-lint-scope`, created from the base:

`git show 25babc0e31fb7ad0b64d5690b3740d3bc9322d28:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase.nn'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No other `docs/plan-qor-phase303*.md` exists at the base. The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored.

## Feature Inventory Touches

- `entry_id`: `FX017` (`qor-logic scripts` / `reliability` module dispatch, row 28 of `docs/FEATURE_INDEX.md` at the base; the row carries inline code spans and is paraphrased)
- `operation`: `n/a-justified`
- `test_path`: `tests/test_boundary_lint_expected_scope.py`
- `test_descriptor`: `publication_boundary_lint with --expect-scope exits 1 and prints the scope mismatch when the achieved scope differs from the expected one, in both directions, and exits 0 on a clean tree whose achieved scope matches`

The lint is reached through that dispatch (`qor-logic scripts publication_boundary_lint`); the dispatch itself does not change and the row is not edited. No other Feature Index row covers the two skill references or the lint.

## Phase 1: Regression tests

### Affected Files

- `tests/test_boundary_lint_expected_scope.py` - new file, eleven test functions (21 items), written before Phases 2 to 4 (LD-7).
- `tests/test_ci_coverage_lint.py` - the Phase 303 allowance helper, the changed `test_lint_self_applies_to_phase_89_plan` and the new `test_phase_303_allowance_does_not_hide_other_ci_drift` (3 items), written before Phase 3 (LD-6). No other test in the file changes.

### Changes

Module constants: `REPO` (the repository root, two parents above the test file), `CI` (`.github/workflows/ci.yml` under it), `TERM = "example-outside-cli"`, `BOM = chr(0xFEFF)`. Helpers: `_tree(tmp_path, text)` writes `docs/a.md` (default a one-line heading) under `tmp_path / "repo"` with `write_bytes` and returns that root; `_overlay(path, body)` writes a terms file with `write_bytes` (creating parents) and returns it; `_main(argv)` calls `publication_boundary_lint.main(argv)` with stdout captured and returns the exit code and stdout; `_ci_boundary_argv()` loads the workflow with `yaml.safe_load`, collects every step `run` containing `publication_boundary_lint`, asserts there is exactly one, splits it with `shlex.split`, asserts it starts with `python -m qor.scripts.publication_boundary_lint` and returns the remaining arguments; `_single_line(rel, marker)` returns the single line of `REPO / rel` containing `marker`, or `None` when there is not exactly one; `_template_names_our_verifier(rel)` and `_ladder_step_invokes_our_cli(rel)` return the boolean each CLI-form test asserts (LD-7). The CLI-form tests are parametrized over the source path and the four compiled copies (claude, codex, cursor, kilo-code) of each file.

In `tests/test_ci_coverage_lint.py`: the constants, the helper `_apply_phase_303_allowance` and the two tests of LD-6, and `import pytest` for the parametrization.

### Unit Tests

- `tests/test_boundary_lint_expected_scope.py::test_a_bom_does_not_turn_a_comment_into_a_term` - a terms file of BOM, `# operator note`, `TERM`; asserts `_load_terms` returns exactly `[TERM]`. RED at the base (the comment with the mark is loaded too).
- `tests/test_boundary_lint_expected_scope.py::test_a_bom_does_not_hide_the_first_term` - a tree whose one line names `TERM`, and a terms file of BOM and `TERM`; asserts the scope is `structural+identity` and the findings are exactly one identity-term finding for `docs/a.md` line 1. RED at the base (no finding).
- `tests/test_boundary_lint_expected_scope.py::test_a_bom_comment_only_overlay_claims_no_identity_scope` - a terms file of BOM and a comment only; asserts the scope is `structural`. RED at the base.
- `tests/test_boundary_lint_expected_scope.py::test_expect_scope_passes_when_the_achieved_scope_matches`, parametrized `structural` (no terms file) and `structural+identity` (a one-term file) on a clean tree - asserts exit 0 and `0 finding(s) [scope: <expected>]` in stdout. RED at the base (argparse rejects the flag).
- `tests/test_boundary_lint_expected_scope.py::test_expect_scope_fails_closed_when_the_achieved_scope_differs`, parametrized `identity-expected-not-reached` (expect `structural+identity`, no terms file) and `structural-expected-exceeded` (expect `structural`, a one-term file) on a clean tree - asserts exit 1, `0 finding(s)` in stdout (so the exit is the mismatch, not a finding) and `scope mismatch: expected <expected>, achieved <achieved>`. Both directions. RED at the base.
- `tests/test_boundary_lint_expected_scope.py::test_expect_scope_does_not_mask_findings` - a tree holding one absolute home-directory path (the fixture line carries the per-line allow marker the existing lint tests use), expect `structural`; asserts exit 1, `1 finding(s) [scope: structural]` and no `scope mismatch`. RED at the base.
- `tests/test_boundary_lint_expected_scope.py::test_without_expect_scope_the_exit_code_is_unchanged` - a clean tree and a one-term file, no flag; asserts exit 0 and `0 finding(s) [scope: structural+identity]`. GREEN at the base and after (pin: the flag is opt-in).
- `tests/test_boundary_lint_expected_scope.py::test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states` - takes CI's own arguments from `_ci_boundary_argv()`; asserts `--expect-scope` is present with value `structural`; runs them with `--repo-root` pointed at a clean `_tree` and `--no-git` appended: exit 0; then writes a one-term file at `.qor/private/boundary-terms.txt` under that tree and runs them again: exit 1 with `scope mismatch: expected structural, achieved structural+identity`. RED at the base (no flag in the step).
- `tests/test_boundary_lint_expected_scope.py::test_the_default_overlay_path_is_not_committed` - runs `git check-ignore -q .qor/private/boundary-terms.txt` in the repository; asserts exit 0. GREEN at the base and after (pin: the fact that makes `structural` CI's honest intent).
- `tests/test_boundary_lint_expected_scope.py::test_the_bootstrap_ledger_template_names_this_repositorys_verifier`, 5 items - `_template_names_our_verifier(rel)` finds, in the single line containing `verify-ledger`, the backtick span ending in ` verify-ledger` and returns whether the token before it is `qor-logic`; the test asserts that boolean with the file path as the message. RED at the base for all 5.
- `tests/test_boundary_lint_expected_scope.py::test_the_seal_ladder_commitment_step_invokes_this_repositorys_cli`, 5 items - `_ladder_step_invokes_our_cli(rel)` returns whether the first whitespace-delimited token of the single line containing `scripts ledger_commitment --session` is `qor-logic`; the test asserts that boolean with the file path as the message. RED at the base for all 5.
- `tests/test_ci_coverage_lint.py::test_lint_self_applies_to_phase_89_plan` (changed, LD-6) - the Phase 303 allowance rewrites exactly one live CI line, and `check_plan` on the Phase 89 plan against the mapped workflows returns no warning. RED at the base (the line does not exist yet, so the helper rewrites none); RED with the Phase 3 `ci.yml` change and the base version of the test (M7).
- `tests/test_ci_coverage_lint.py::test_phase_303_allowance_does_not_hide_other_ci_drift`, 3 items (LD-6) - with one drift applied to a copy of the live workflows, `check_plan` returns exactly the drifted command: the boundary step with another scope value, the boundary step with an added argument, and an unrelated new CI command. RED at the base (each item first checks that the Phase 303 line exists).

TDD: observed RED at the base before Phases 2 to 4: the new file alone gives `19 failed, 2 passed`, and with the changed `tests/test_ci_coverage_lint.py` the two files give `23 failed, 14 passed` (4 of its 16 items fail). The failing runs' output does not contain the outside name in any letter case (LD-7). Discrimination is proven after Phase 4 by local, uncommitted mutations, each run with `python -B -m pytest` over `tests/test_boundary_lint_expected_scope.py` and the seventeen consumer files of the second `## CI Commands` entry (220 items) and then reverted:

- M1: in `_load_terms`, change `encoding="utf-8-sig"` back to `encoding="utf-8"` -> the three BOM tests FAIL.
- M2: delete the `return 1` after the scope-mismatch print -> both `test_expect_scope_fails_closed_when_the_achieved_scope_differs` items FAIL.
- M3: change the mismatch condition to `args.expect_scope == SCOPES[1] and result.scope != args.expect_scope` (one direction only) -> the `structural-expected-exceeded` item and `test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states` FAIL.
- M4: remove ` --expect-scope structural` from the CI step's `run` -> `test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states`, `test_lint_self_applies_to_phase_89_plan` and the three `test_phase_303_allowance_does_not_hide_other_ci_drift` items FAIL (the allowance has no line to map).
- M5: restore the base blob of `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` (`git show` of the base path into the file) -> the source item of `test_the_seal_ladder_commitment_step_invokes_this_repositorys_cli` FAILS.
- M6: restore the base blob of `qor/dist/variants/codex/skills/qor-bootstrap/references/qor-bootstrap-templates.md` -> the codex item of `test_the_bootstrap_ledger_template_names_this_repositorys_verifier` FAILS.
- M7: restore the base blob of `tests/test_ci_coverage_lint.py` -> `test_lint_self_applies_to_phase_89_plan` FAILS: without the allowance, the sealed plan does not cover the new CI command.
- M8: widen the allowance, rewriting any line that starts with `run: python -m qor.scripts.publication_boundary_lint` to the indentation followed by `run: ` and `_PHASE_89_COVERED_COMMAND` -> the `boundary-scope-value-changed` and `boundary-flag-added` items FAIL: a wider allowance hides boundary-step drift.
- M9: drop the rewrite from the helper, so the copied line keeps the Phase 303 command -> `test_lint_self_applies_to_phase_89_plan` and the `unrelated-command-added` item FAIL.

Observed in the scratch clone: M1 `3 failed, 217 passed`; M2, M3, M8 and M9 each `2 failed, 218 passed`; M4 `5 failed, 215 passed`; M5 and M6 each `1 failed, 219 passed`; M7 `1 failed, 216 passed` (the base test file has 3 fewer items). Each failing set is exactly the one named above, and no mutation's output contains the outside name in any letter case. After each mutation the implementer restores the content and runs the set twice GREEN (`220 passed`, twice). The consumer entry alone (the seventeen files) gives `196 passed` at the base, `4 failed, 195 passed` at the base with the changed `tests/test_ci_coverage_lint.py`, and `199 passed` in the scratch clone with Phases 2 to 5 applied.

## Phase 2: The lint ignores a terms-file BOM and can assert its scope

### Affected Files

- `qor/scripts/publication_boundary_lint.py` - `SCOPES`; `_load_terms` reads `utf-8-sig` (LD-4); `collect_findings` returns a `SCOPES` value; `main` gains `--expect-scope` (LD-5).

`_load_terms`, `scan_text`, `collect_findings` and `main` keep their signatures and return types; `github_surface` and `advisory_filing_control` import `_load_terms` and `scan_text` unchanged (LD-4).

### Changes

- After the `_ALLOW_RE` definition (line 51 at the base), add a blank line, a two-line comment (Phase 303, GH #457: the two scopes a run can achieve; `--expect-scope` accepts exactly these) and `SCOPES = ("structural", "structural+identity")`.
- Replace line 98 at the base with a three-line comment (Phase 303, GH #457: `utf-8-sig` drops a leading BOM; plain `utf-8` kept it on the first line, so a first-line comment loaded as a term and a first-line term never matched) and `for line in terms_file.read_text(encoding="utf-8-sig").splitlines():`.
- Replace line 173 at the base with `return BoundaryResult(findings, SCOPES[1] if terms else SCOPES[0])`.
- In `main`, after the `--terms-file` argument (lines 179 and 180 at the base), add:

  ```python
      ap.add_argument("--expect-scope", choices=SCOPES, default=None,
                      help="exit 1 unless the achieved scope equals this one (Phase 303)")
  ```

- In `main`, between the summary print (lines 188 and 189 at the base) and line 190, add:

  ```python
      if args.expect_scope is not None and result.scope != args.expect_scope:
          print(f"publication_boundary_lint: scope mismatch: expected "
                f"{args.expect_scope}, achieved {result.scope}")
          return 1
  ```

### Unit Tests

- The nine lint items of `tests/test_boundary_lint_expected_scope.py` (the BOM and `--expect-scope` tests) turn GREEN; the pin stays GREEN; mutations M1 to M3 (Phase 1).
- The existing lint consumers stay GREEN unchanged: `tests/test_publication_boundary_lint.py`, `tests/test_boundary_scope_disclosure.py`, `tests/test_boundary_untracked_coverage.py`, `tests/test_github_surface_boundary.py`, `tests/test_advisory_filing_control.py`, `tests/test_substantiate_boundary_wiring.py` and `tests/test_publication_boundary_policy.py`, all in the consumer entry of `## CI Commands` (part of the `196 passed` at the base and the `199 passed` after; the three added items are the LD-6 tests).

## Phase 3: CI states the boundary scope it intends

### Affected Files

- `.github/workflows/ci.yml` - the `publication boundary` step passes `--expect-scope structural` (LD-6).

The sealed Phase 89 plan is not an affected file: no sealed plan text and no ledger-bound artifact is modified (LD-6). The test that reads it changes in Phase 1.

### Changes

- In `.github/workflows/ci.yml`, after line 131 at the base insert, at the comment indentation of lines 129 to 131:

  ```yaml
          # Phase 303 (GH #457): --expect-scope states that intent, so the step
          # fails if the achieved scope ever differs from it.
  ```

  and change line 132 to `run: python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` (same indentation).

### Unit Tests

- `test_the_ci_boundary_step_fails_when_its_scope_is_not_the_one_it_states`, `test_lint_self_applies_to_phase_89_plan` and the three `test_phase_303_allowance_does_not_hide_other_ci_drift` items turn GREEN; mutations M4, M7, M8 and M9 (Phase 1).
- The rest of `tests/test_ci_coverage_lint.py`, `tests/test_ci_workflow_gate_chain_completeness.py` and `tests/test_ruff_adoption.py` (in the consumer entry of `## CI Commands`) stay GREEN.
- `git diff --name-only 25babc0e31fb7ad0b64d5690b3740d3bc9322d28 HEAD -- docs/plan-qor-phase89-ci-commands-reconciliation.md docs/META_LEDGER.md` prints nothing on the implementation commit (observed in the scratch clone): the sealed plan and the ledger are untouched before the seal.
- `python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` on the committed tree prints `publication_boundary_lint: 0 finding(s) [scope: structural]` and exits 0 (observed in the scratch clone and in a fresh clone of its implementation commit).

## Phase 4: The two shipped references invoke `qor-logic`

### Affected Files

- `qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md` - line 151, the one token of LD-1.
- `qor/skills/governance/qor-substantiate/references/seal-gate-ladder.md` - line 457, the one token of LD-1.
- `qor/dist/` - regenerated by the compile (LD-2): the 8 compiled copies and the 7 manifests.

### Changes

- Make the two one-token edits of LD-1 in the source files.
- Run `PYTHONPATH=. python -m qor.cli compile` at the repository root and keep what it writes under `qor/dist/` (15 files, LD-2). No compiled file is edited by hand.

### Unit Tests

- The ten CLI-form items of `tests/test_boundary_lint_expected_scope.py` turn GREEN; mutations M5 and M6 (Phase 1).
- `python qor/scripts/check_variant_drift.py` prints `OK: 413 files, no drift` (observed in the scratch clone).
- `tests/test_skill_corpus_consolidation.py`, `tests/test_qor_bootstrap_feature_index_template.py`, `tests/test_layout_configurability.py`, `tests/test_seal_ladder_tokens_survived.py`, `tests/test_bootstrap_seed_correctness.py`, `tests/test_compile.py` and `tests/test_install_sync_with_source.py` (in the consumer entry of `## CI Commands`) stay GREEN (part of the `196 passed` at the base and the `199 passed` after).
- Full suite: `python -m pytest tests/ -q` stays GREEN (observed in the scratch clone with Phases 1 to 5 applied: `3665 passed, 3 skipped, 4 deselected`; base `3641 passed, 3 skipped, 4 deselected`). After it the drift check still prints `OK: 413 files, no drift`, `python -m ruff check qor/ tests/` prints `All checks passed!`, and `python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` reports `0 finding(s) [scope: structural]`.

## Phase 5: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.6` `sealed_unpublished` entry (LD-12).
- `CHANGELOG.md` - the Phase 303 bullet under `## [Unreleased]` (LD-11). No dated section is edited.

### Changes

Append the LD-12 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-11 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.7]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-12).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` and `python -m pytest tests/test_changelog_format.py -q` stay GREEN.
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.7`, remote tags only). At the base, before the entry exists, it prints `{'0.175.6'} {'0.175.6'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.6'}`: no orphan with the entry, exactly `{'0.175.6'}` with the entry removed in memory (observed in the scratch clone). That shows the entry is what keeps coverage green.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.7` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The command is the Phase 302 proof with `0.175.7` in place of `0.175.6` and `printf '%s'` in place of Phase 302's newline-terminated `printf` format: the remote tag list in `R` is already newline-separated, so the line match is the same and the command holds no backslash (the four discrimination runs below were observed with this exact command). The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.6` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in scratch clones outside the repository with `origin` set to the real remote and `TMPDIR` inside the scratch area; the simulated commits never entered this repository):
  - base commit (`version = "0.175.6"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.7 (project version 0.175.6)`;
  - a commit with Phases 1 to 5 that bumps `version` to `0.175.7` without the `[0.175.7]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.7 (project version 0.175.7)`;
  - simulated seal commit (`version = "0.175.7"`, `## [0.175.7] - ` section, local `v0.175.7` tag) with Phases 1 to 4 but no `0.175.6` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.6`;
  - the same seal commit with the LD-12 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: the two shipped references invoke this repository's CLI

- **D1**: line 151 of the bootstrap template and line 457 of the seal ladder, and their compiled copies in the claude, codex, cursor and kilo-code variants, invoke `qor-logic`; no other text in those files changes, and the 62 files of LD-3 are untouched.
- **D2**: two one-token source edits; `qor/dist/` holds exactly what `PYTHONPATH=. python -m qor.cli compile` writes (15 files).
- **D3**: no compiled file is hand-edited; the drift check prints `OK: 413 files, no drift`. No sealed record is edited.
- **D4**: the ten CLI-form items are RED at the base and GREEN after Phase 4, without the outside name in any letter case in the test file or its failure output (default, `-vv` and `-l` runs; LD-7); M5 and M6 turn exactly their named items RED.

### Deliverable: a terms-file BOM no longer changes which terms load

- **D1**: a leading BOM on the terms file is ignored, so a first-line comment is not a term, a comment-only file claims no identity scope, and a first-line term matches. The same holds for `github_surface` and `advisory_filing_control`, which load terms through `_load_terms`.
- **D2**: `qor/scripts/publication_boundary_lint.py` line 98 at the base reads `encoding="utf-8-sig"`; `_load_terms` keeps its signature.
- **D3**: no documentation change (LD-9).
- **D4**: the three BOM tests are RED at the base and GREEN after Phase 2; M1 turns exactly them RED.

### Deliverable: CI fails when the boundary scope it reaches is not the one it states

- **D1**: `publication_boundary_lint --expect-scope <scope>` exits 1 with `scope mismatch: expected <scope>, achieved <scope>` whenever the achieved scope differs, in both directions, and otherwise keeps its exit code; the CI step passes `--expect-scope structural`. CI still scans no identity terms (LD-8), and the LD-11 bullet says so.
- **D2**: `SCOPES = ("structural", "structural+identity")`; `main` gains `--expect-scope` with `choices=SCOPES`; `.github/workflows/ci.yml` line 132 at the base gains the flag; `tests/test_ci_coverage_lint.py` maps exactly that one CI line back to the Phase 89 form (LD-6).
- **D3**: callers that do not pass the flag are unchanged (LD-5). The declared residual is in LD-8 and the plan boundaries. No sealed plan text and no ledger-bound artifact is modified; Entry #237's content-hash binding of the Phase 89 plan, verifiable at seal commit `4a34b08e`, is untouched, and no AMENDMENT is recorded because no committed artifact changes (LD-6).
- **D4**: the `--expect-scope`, CI-wiring and Phase 89 self-application items are RED at the base and GREEN after Phases 2 and 3; M2 to M4 and M7 to M9 turn exactly their named items RED, and M8 proves that a wider allowance fails the drift test; a fresh clone of the implementation passes the CI step and fails it when the overlay is present or the stated scope is changed (LD-6).

### Deliverable: release-state continuity for 0.175.6

- **D1**: after the Phase 303 seal bumps the project version to `0.175.7`, `0.175.6` (sealed on `main` at META_LEDGER #835, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.6` / `sealed_unpublished` with the LD-12 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.6` to `0.175.7` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.6'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.7` with a dated `[0.175.7]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_boundary_lint_expected_scope.py -q` - verifies the BOM fix, `--expect-scope` in both directions, the CI step's stated scope and the two shipped references (21 test items).
- `python -m pytest tests/test_publication_boundary_lint.py tests/test_boundary_scope_disclosure.py tests/test_boundary_untracked_coverage.py tests/test_github_surface_boundary.py tests/test_advisory_filing_control.py tests/test_substantiate_boundary_wiring.py tests/test_publication_boundary_policy.py tests/test_ci_coverage_lint.py tests/test_ci_workflow_gate_chain_completeness.py tests/test_ruff_adoption.py tests/test_skill_corpus_consolidation.py tests/test_qor_bootstrap_feature_index_template.py tests/test_layout_configurability.py tests/test_seal_ladder_tokens_survived.py tests/test_bootstrap_seed_correctness.py tests/test_compile.py tests/test_install_sync_with_source.py -q` - verifies the existing lint, workflow, skill-reference and compile consumers are unchanged.
- `python qor/scripts/check_variant_drift.py` - verifies the committed dist, manifests included, matches a fresh compile.
- `python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` - the CI step: verifies the publication-boundary surface is clean and that the scope reached is the structural scope CI states.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-11 bullet keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.7'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.7', ex).orphans, rs.coverage_violations(versions, tags, '0.175.7', {k: v for k, v in ex.items() if k != '0.175.6'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.6'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.7' and '## [0.175.7] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.7 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.7`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed module and the new test file.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `python -m qor.scripts.github_surface` - nightly GitHub-surface scan; it loads terms through `_load_terms` and gains the LD-4 fix, but its own command and flags do not change.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.
- `python -m qor.scripts.dependency_admission_lint` - PR Dependency Review admission steps; no dependency or lockfile changes in this plan.

## Non-goals

- a committed or CI-provided identity terms list, or identity scanning in CI (LD-8);
- editing any of the 62 files that still carry the outside name in some letter case: sealed plans, gate artifacts, intent-lock records, `docs/META_LEDGER.md`, `docs/PROCESS_SHADOW_GENOME.md` and `tests/test_portable_governance_boundary.py` (LD-3);
- editing the sealed Phase 89 plan or any other sealed plan text (LD-6);
- removing a U+FEFF other than a leading one (LD-4);
- changing `github_surface`, `advisory_filing_control`, the audit or seal ladder invocations of the lint, or the doctrine (LD-5, LD-9);
- hand-editing any compiled file under `qor/dist/` (LD-2);
- release-state dispositions for any version other than `0.175.6`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- hand-issuing governance evidence;
- unrelated repository cleanup.
