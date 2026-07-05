# Research Brief: Full Skills + Components Audit

**Date**: 2026-04-15
**Analyst**: QorLogic Analyst (research mode)
**Target**: 27 SKILL.md files + 13 agents + 13 scripts + governance docs
**Scope**: Systemic patterns + per-item gaps. Categories: gaps, redundancy, ambiguity, missing tool refs, workflow inconsistency, doc rot.
**Supersedes**: `docs/research-brief-qor-audit-2026-04-15.md` (subsumed; the qor-audit-specific findings appear here as instances of broader systemic patterns).

---

## Executive Summary

Counted/verified state: 27 skills (24 single + 3 deep-audit bundle members + 2 onboard/review-cycle bundles), 13 agents, 13 Python scripts, 154 tests passing, ledger Entry #20 sealed.

**Headline finding**: a single systemic gap (S-1) accounts for ~40% of the issues — every skill that declares `gate_writes:` in frontmatter currently lacks an instruction to write the corresponding `.qor/gates/<session>/<phase>.json` artifact. Downstream gates are consequently always "missing prior", forcing override every cycle. Until S-1 is fixed, the gate chain is decorative, not enforcing.

**Trend**: 13 systemic patterns + 11 specific findings = **24 distinct issues**. None are blockers; all are tractable in 1-3 small phases. The audit infrastructure is sound; documentation alignment with the infrastructure has lagged.

---

## Systemic findings (sorted by blast radius)

### S-1 — `gate_writes` declared, no write step (CRITICAL, 9 skills)

Affected: `qor-plan`, `qor-implement`, `qor-refactor`, `qor-substantiate`, `qor-validate`, `qor-repo-audit`, `qor-repo-release`, `qor-repo-scaffold`, `qor-shadow-process`.

Each skill's frontmatter declares `gate_writes: <phase>` (per `qor/gates/chain.md`), but no Step in the body instructs writing the structured artifact at `.qor/gates/<session_id>/<phase>.json`. `qor-audit` has the same gap (documented previously).

**Action**: Add a "Write Gate Artifact" step to each. Recommend a shared helper in `qor/scripts/gate_chain.py`: `write_gate_artifact(phase: str, payload: dict, session_id: str | None = None) -> Path` that wraps `validate_gate_artifact.write_artifact`. Each skill's body adds one snippet invoking it.

**Estimated effort**: 1 small phase. Pattern is identical across 10 skills; can ship as a single sweep.

### S-2 — Stale `processed/skills-output/` paths in metadata (16 skills)

`processed/` was deleted in Phase 7 cutover (Ledger #19). 16 skills still declare `source.path: processed/skills-output/<name>` in frontmatter. Cosmetic but signals doc rot.

**Action**: Sweep replace to canonical `qor/skills/<category>/<name>/`. Same script that fixes S-3 can fix S-2.

### S-3 — Governance skills miscategorized as `development` (5 skills)

`qor-audit`, `qor-substantiate`, `qor-validate` declare `category: development`. `qor-governance-compliance`, `qor-shadow-process` have empty category. All live under `qor/skills/governance/`; sibling skills classify correctly.

**Action**: One-line frontmatter sweep.

### S-4 — Missing `## Delegation` section (13 skills)

Phase 9 Track A added explicit Delegation sections to `qor-research`, `qor-plan`, `qor-implement`, `qor-refactor`, `qor-validate`. Missing in: `qor-audit`, `qor-substantiate`, `qor-debug`, `qor-remediate`, `qor-organize`, `qor-status`, `qor-document`, `qor-bootstrap`, `qor-governance-compliance`, `qor-repo-audit`, `qor-repo-release`, `qor-repo-scaffold`, `qor-deep-audit`, `qor-meta-log-decision`, `qor-meta-track-shadow`, `qor-docs-technical-writing`.

Inconsistent doc structure. `qor-audit` has handoffs inline in audit passes (acceptable); others have nothing.

**Action**: Author Delegation sections for at least the SDLC + governance chain skills. Memory/meta cross-cutting can use a brief "(cross-cutting; no fixed handoff)" note.

### S-5 — Pre-rename "QL" leftovers in 5 reference files

`qor-audit-templates.md:1` (`# QL Audit Templates`), plus similar headers in `qor-substantiate-templates.md`, `qor-validate-reports.md`, `log-decision.md`, `qor-organize-templates.md`. Phase 7 sweep didn't catch standalone uppercase `QL` (no hyphen).

**Action**: Targeted sed sweep for `\bQL\b` in `qor/skills/**/*.md`.

### S-6 — Skills reference non-existent `references/` files (4 skills)

- `qor-audit/SKILL.md` → `references/adversarial-mode.md` (MISSING)
- `qor-deep-audit/SKILL.md` → `references/doctrine-token-efficiency.md` (MISSING — should be `qor/references/...`)
- `qor-help/SKILL.md` → `references/doctrine-token-efficiency.md` (MISSING — same path bug)
- `qor-onboard-codebase/SKILL.md` → `references/doctrine-token-efficiency.md` (MISSING — same)

**Action**: For doctrine references, use absolute path `qor/references/doctrine-token-efficiency.md`. For adversarial-mode.md, author the stub or remove the reference per Phase 9 audit.

### S-7 — `/qor-help` missing 4 skills

Not listed: `qor-governance-compliance`, `qor-docs-technical-writing`, `qor-meta-log-decision`, `qor-meta-track-shadow`. These are migrated qore-* skills; help update missed them.

**Action**: Add a "Migrated skills" subsection in `/qor-help` or fold each into existing categories.

### S-8 — Delegation table missing 16 skills

`qor/gates/delegation-table.md` only has rows for the SDLC chain + remediate paths. Missing: `qor-research` outbound, `qor-substantiate` outbound, `qor-status`, `qor-document`, `qor-organize`, `qor-bootstrap`, `qor-repo-*`, `qor-shadow-process`, `qor-governance-compliance`, all 5 bundles, the 3 migrated qor-meta/docs skills.

Some of these legitimately don't have a fixed handoff (cross-cutting). The table should still **acknowledge** them with "(cross-cutting; invokable from any phase)" to prove they were considered.

**Action**: Add a "Cross-cutting skills (no fixed handoff)" subsection listing the 7-9 cross-cutting skills. For bundles, add 1 row each pointing at their constituent first-phase.

### S-9 — Dead skill reference

`qor-help/SKILL.md` references `/qor-course-correct` somewhere (verified via grep). That skill was retired in Phase 1 (absorbed into `/qor-remediate`).

**Action**: Replace remaining `/qor-course-correct` with `/qor-remediate`.

### S-10 — Vestigial "tools/reliability/" references (2 skills)

`qor-implement/SKILL.md:151` and `qor-substantiate/SKILL.md:167` both contain a deferred-marker block referencing `tools/reliability/` scripts that "are not yet implemented". Verified: `tools/reliability/` doesn't exist anywhere; this is a pre-Phase-1 plan that never landed.

**Action**: Remove the deferred-marker block, or move it to `docs/Lessons-Learned/` as a "considered-but-rejected" record.

### S-11 — `ledger_hash.py` has zero test coverage

13 scripts; 11 tested via `import` in tests. `ledger_hash.py` (CRITICAL infrastructure — every audit/substantiate writes via it) has no tests. `calculate-session-seal.py` (legacy, low-priority) also untested but acceptable.

**Action**: Add `tests/test_ledger_hash.py` covering content_hash determinism, chain_hash recomputation, write_manifest sorted output, verify() detecting tampered entries.

### S-12 — Most agents have no `/qor-*` cross-references (10/13)

Agents `qor-judge`, `documentation-scribe`, `learning-capture`, `agent-architect`, `build-doctor`, `system-architect`, `project-planner`, `qor-fixer`, `qor-specialist`, `qor-ux-evaluator` (partial) lack any `/qor-*` references in their persona docs. Only `qor-governor`, `qor-technical-writer`, `qor-strategist` mention skills they support.

**Effect**: Operators reading an agent persona can't tell which skills the agent is invoked by. Agent-skill mapping is implicit instead of declared.

**Action**: Add a "Used by skills" line at the bottom of each agent .md. Low-effort, high readability win.

### S-13 — `qor/dist/` regenerated yet docstring-untested

The compile pipeline regenerates 119 dist files, but no test asserts a high-level invariant like "every source SKILL.md has a corresponding dist file" or "dist matches source character-for-character". `tests/test_compile.py` covers the compile.py logic but not the produced-tree integrity.

**Action**: Add `test_dist_matches_sources_invariant` to test_compile.py: walk `qor/skills/`, walk `qor/dist/variants/claude/skills/`, assert 1:1 mapping.

---

## Specific findings

### qor-audit (already detailed in superseded brief)

- C-1 ghost adversarial-mode.md — same as S-6 instance
- Inline handoff lines in audit passes (acceptable; document the choice as the doctrine for tribunals)
- See superseded brief for full 23-issue list

### qor-research

- Doc references `<legacy-staging>/RESEARCH_BRIEF.md` and `<legacy-staging>/META_LEDGER.md` — `<legacy-staging>/` doesn't exist; canonical paths are `docs/research-brief-*.md` and `docs/META_LEDGER.md`. **Same class as S-2 (stale paths post-SSoT)**.
- Doctrine reference to "Shadow Genome Entry #2 (API_ASSUMPTION_DRIFT)" — that entry doesn't exist in current `docs/SHADOW_GENOME.md` (the migration archived prior shadow content). Pre-migration cite.

### qor-bootstrap

- References creating `META_LEDGER` Genesis entry, but in current state Genesis was Entry #1 (2026-03-19) — bootstrap on a fresh repo would conflict. Skill assumes virgin repo; doesn't document re-bootstrap behavior.

### qor-organize

- Hard-coded list of "FORBIDDEN_PATHS" includes `.qor/` (correct), `<consumer-governance-dotdir>/` (legacy, OK for compatibility), but NOT `.githooks/` or `tests/` which probably should be excluded too in a typical organize pass.

### qor-deep-audit (and sub-bundles)

- References `qor/references/doctrine-token-efficiency.md` correctly in body but also has a confusing reference under `references/` (caught by S-6).
- Bundle never tests its checkpoint protocol — `tests/test_bundles.py` validates frontmatter + structure but not checkpoint behavior. Future Phase 12+ work.

### qor-help

- S-9 (dead `/qor-course-correct` ref) appears here.
- Doesn't reference `qor/gates/chain.md` despite being the "what command should I use" skill — could pointer-link new users to the canonical chain.

### Scripts

- `gate_chain.py` lacks a `write_gate_artifact` helper; per S-1 fix, this is the natural home.
- `qor_audit_runtime.py` should similarly gain a `write_audit_artifact` wrapper.
- `qor_platform.py` `apply_profile` re-runs `detect_host()` but ignores `host_declared`; documented in `docs/phase10-findings.md` as Gap #1. Worth elevating to a small Phase 11D fix.

### Agents

- `qor-ux-evaluator.md` self-references `/qor-ux-evaluator` (technically circular reference; harmless but unnecessary).
- `qor-judge.md` (governance) lacks any reference to `/qor-audit` or `/qor-substantiate` despite being the persona used by both.

---

## Workflow inconsistency observations

1. **Chain doc claims `audit.json must be PASS` for implement to proceed** (`chain.md:74`), but this is "skill-layer enforcement (future work)". Currently no script reads the verdict. Implement runs regardless of audit verdict if operator doesn't manually check.
2. **Bundles document checkpoints in protocol but no script enforces them**. Operators self-discipline to honor checkpoints. Acceptable for v1; worth noting as conscious choice.
3. **Three skills bundle into `qor-deep-audit`** but the parent's body doesn't document how the operator sequences them when invoking `/qor-deep-audit` directly vs the sub-bundles.
4. **Multiple shadow logs** — `docs/SHADOW_GENOME.md` (audit failures) vs `docs/PROCESS_SHADOW_GENOME.md` (process failures). Naming differs only by "PROCESS_" prefix; new contributors will conflate. Either rename or add a top-of-file disambiguation block to each.

---

## Blueprint Alignment

| Claim | Reality | Status |
|---|---|---|
| All chain skills write gate artifacts | 0 of 9 do | **DRIFT** (S-1) |
| Frontmatter source.path canonical post-Phase-7 | 16 still reference `processed/skills-output/` | **DRIFT** (S-2) |
| Phase 9 added Delegation sections to all chain skills | Only 5 of ~14 have them | **PARTIAL** (S-4) |
| `/qor-help` lists every `qor-*` skill | 4 missing | **DRIFT** (S-7) |
| Delegation table covers all skills | 16 missing | **DRIFT** (S-8) |
| `/qor-course-correct` retired | Still referenced in /qor-help | **DRIFT** (S-9) |
| `tools/reliability/` infrastructure exists | Never built; 2 skills reference it | **DRIFT** (S-10) |
| All scripts test-covered | `ledger_hash.py` not | **DRIFT** (S-11) |
| Agents declare which skills invoke them | 10 of 13 don't | **PARTIAL** (S-12) |

---

## Recommendations (sorted)

### Phase 11D (CRITICAL, single sweep)

1. **S-1 fix**: Add `gate_chain.write_gate_artifact()` helper. Add Step "Write Gate Artifact" to each of 9 affected skills + qor-audit. Add corresponding Success Criteria item. Tests: 1 per skill verifying schema-conforming write.
2. **S-9 fix**: Replace `/qor-course-correct` with `/qor-remediate` in qor-help.
3. **S-10 fix**: Remove `tools/reliability/` deferred blocks from qor-implement and qor-substantiate.
4. **C-1**: Author `qor/skills/governance/qor-audit/references/adversarial-mode.md` as a stub.
5. **S-11**: Add `tests/test_ledger_hash.py`.

### Phase 11E (MEDIUM, doc-rot sweep)

6. **S-2 + S-3**: Sweep frontmatter — fix source.path + category for affected skills.
7. **S-5**: Sweep `\bQL\b` standalone uppercase tokens.
8. **S-6**: Fix doctrine reference paths (use `qor/references/`).
9. **S-7**: Add 4 missing skills to `/qor-help`.
10. **S-8**: Add cross-cutting + bundle rows to delegation-table.

### Phase 11F (MEDIUM, structure sweep)

11. **S-4**: Author `## Delegation` sections for the 13 affected skills (memory/meta can be brief).
12. **S-12**: Add "Used by skills" line to each agent .md.
13. **S-13**: Add `test_dist_matches_sources_invariant` to test_compile.

### Phase 11G (LOW, polish)

14. Specific items per-skill (qor-research stale `<consumer-governance-dotdir>/`, qor-bootstrap re-bootstrap behavior, qor-organize FORBIDDEN_PATHS expansion, qor-judge missing cross-refs, etc.)
15. Workflow inconsistencies #1-#4 (audit.verdict enforcement, checkpoint enforcement, deep-audit sequencing prose, shadow log naming).

### Strategic (defer to Phase 12+)

16. Skill-layer enforcement of `audit.json.verdict == "PASS"` before implement — turns advisory into hard gate (after operator review of UX impact).
17. Bundle checkpoint runtime enforcement (currently markdown-only; could become script-mediated).
18. Subagent-mocked bundle execution tests (referenced in phase10-findings as Phase 12 work).

---

## Updated Knowledge

The Phase 7 SSoT migration was structurally complete but documentation lagged in three dimensions:
1. **Frontmatter** — many skills still cite pre-migration `processed/` paths.
2. **Cross-references** — delegation-table and qor-help didn't keep pace with new skills.
3. **`gate_writes` semantics** — Phase 3 introduced the artifact write contract; Phase 7 added `gate_reads` to skills; nobody added `gate_writes` execution. The chain is therefore advisory-only in practice.

Recording in `docs/Lessons-Learned/2026-04-15-doc-lags-infra.md` (future): *Each phase that introduces new infra must also add the cross-reference + frontmatter sweep step to its scope. Otherwise the infra becomes ghost — present but unused.*

---

_Research advisory. No ledger entry. Recommended next: `/qor-plan` for Phase 11D (critical fixes) — small, focused, auditable. Then 11E (doc rot), then 11F (structure)._
