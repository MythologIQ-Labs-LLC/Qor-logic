# Doctrine: Verification & Closure Integrity (Phase 114; GH #166, #158)

Counter-control for the half-measure pattern (`SG-HalfMeasureClosure`, umbrella GH #147): work must be *proven* done, not asserted done. Realized as the fail-closed promotion and seal-time wiring of existing surfaces, NOT a new QA skill.

## Terms

- **QA Evidence Artifact**: a compact, off-chain `qa.json` gate artifact (`qor/gates/schema/qa.schema.json`) recording per-pillar verification status plus an overall `verdict` (PASS|FAIL). Built by `qor.scripts.qa_evidence`; read by the close guard via `gate_chain.read_phase_artifact("qa", session_id)`.
- **Acceptance-Criteria Close Guard**: `qor.scripts.ac_close_guard` — refuses (under enforcement) to treat an issue as closed when an acceptance criterion is neither met nor split into a filed follow-on.

## QA evidence contract

Four pillars: `regression`, `security`, `stability`, `coverage`. Each is `{status: pass|fail|skip, evidence?, metric?, note?}`. `verdict` is FAIL iff any pillar is `fail`; `skip` is visible per-pillar but does not fail the verdict.

- **SAST Backend** (Phase 115; #167): the `security` pillar's evidence source. `qor.scripts.sast_scan` is tool-agnostic — a backend is a callable `(paths) -> list[normalized finding dict]`; the default is **bandit** (pure-Python, low supply-chain surface), and a future semgrep backend normalizes into the same shape. When the backend tool is absent the pillar is `status: "skip"` with a note (Phase 75 prerequisite-absent semantics) — never a crash, never a false pass. A finding at/above the `fail_on` severity (default HIGH) sets the pillar `fail`, which fails the overall qa verdict.

Partial coverage is explicit, never silent: a pillar not wired to real evidence emits `status: "skip"` with a `note` naming its follow-on. (Spine slice: `regression` is real, derived from `feature_index_verify.tally`; `security`/`stability`/`coverage` are skip+note pending their follow-ons.) This is the anti-half-measure invariant in artifact form.

## Met-or-split rule (close guard)

"Met-ness" comes from the QA evidence verdict, NOT from checkbox state (a closing issue legitimately still shows unchecked boxes). The mechanical invariant: an unmet acceptance criterion must have a linked follow-on issue. Inputs: the issue's acceptance-criteria checklist (parsed) + whether a follow-on references it (`gh issue list --search "in:body #N"`) + the `qa.json` verdict.

Fallback: an issue with no machine-checkable checklist is ALLOWED with a warning (do not block legitimate closures on format variance).

## WARN-first -> enforce graduation

Both the FEATURE_INDEX regression ABORT and the close guard sit on the seal control path. They ship WARN-first (exit 0; print findings) and graduate to blocking only after the false-positive rate is measured:
- `feature_index_verify`: blocks by default, `--warn-only` for rollout.
- `ac_close_guard`: WARN-only by default, `--enforce` reserved for V2.

When `gh` is unavailable the close guard records a skip (Phase 75 prerequisite-absent semantics), never a crash.

## Pillar evidence sources (Phase 116; #168, #169, #170)

The four qa.json pillars draw on consolidated existing surfaces, not parallel tooling:

- **coverage** (#168): `qa_evidence.run_coverage` reads an existing coverage data file (`coverage` package) and emits a `metric` (pct) vs a configurable `min_pct` threshold. No data file present -> `skip` (never a fabricated number).
- **stability** (#169): `qa_evidence.run_stability` re-invokes `runtime_contract_walk.walk_plan` (#108) at seal time to attest the plan's runtime contract still holds; findings -> `fail`, none -> `pass`, plan absent -> `skip`. Reuses the existing walk; no new smoke check.
- **security** (#167): see the SAST Backend section above.
- **regression** (#155/#40): the FEATURE_INDEX tally.

## Prose-Behavior Test Lint (#170)

`qor.scripts.prose_test_lint` scans `tests/*.py` source (AST) and flags tests whose only assertion is substring membership in a SKILL.md — the presence-not-behavior anti-pattern that shipped in #56/#58/#83 and that the plan-text `plan_test_lint` could not catch. Enforces the `doctrine-test-functionality.md` acceptance question at the test-source level.

**Hardened heuristic (Phase 117; #174):** a finding is raised only when an `assert "<literal>" in <X>` has `<X>` tracing to a SKILL.md read — a var assigned from a `.read_text()` whose path mentions `SKILL.md` (including module-level path constants like `SUBSTANTIATE_SKILL = .../SKILL.md`), or an inline SKILL.md read. This eliminates false positives where `<X>` is subprocess stderr, a non-SKILL.md source file, or an emitted dict, even when the function mentions `SKILL.md`. (V1's broad heuristic over-flagged ~20%.)

**Allowlist:** an assertion carrying a trailing `# prose-lint: ok=<reason>` (non-empty reason) is recorded as *exempted*, not *unexplained*. Legitimate prose-contract checks on prompt structure/instructions (section headers, agent directives, frontmatter field labels, persona framing, documented shell commands) are exempted with a stated reason. Convertible findings (the prompt cites a real module/file) keep the citation assert (allowlisted) AND add a behavioral check (`find_spec(...)` / `Path(...).exists()` / compare to the live constant).

**ENFORCED (Phase 117):** wired into `/qor-audit` Test Functionality Pass with `--enforce` — a non-zero exit (any UNEXPLAINED finding) VETOs. `tests/test_prose_lint_floor.py` locks the suite at zero unexplained. Exempted-with-reason findings do not VETO.
