# Qor-logic Architecture

Qor-logic is a prompt system for governance-driven software development. The repository ships skill prompts, doctrines, and helper scripts that a host (Claude Code, Kilo Code, Codex, Gemini) executes to enforce a phased governance lifecycle on a consumer project. This document describes the layers, their responsibilities, and how they interact.

## System layers

```
+---------------------------------------------------------------+
|  ENTRY POINTS                                                 |
|  CLAUDE.md, README.md, CONTRIBUTING.md                        |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  REFERENCE LAYER (qor/references/)                            |
|  14 doctrines + 7 patterns + 7 ql-templates + glossary        |
|  = binding rules + non-binding references                     |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  GATE LAYER (qor/gates/)                                      |
|  chain.md          -- canonical SDLC phase sequence           |
|  delegation-table  -- skill-to-skill handoff matrix           |
|  workflow-bundles  -- multi-phase meta-skill protocol         |
|  schema/*.json     -- gate-artifact validators                |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  SKILL LAYER (qor/skills/)                                    |
|  sdlc/       research, plan, implement, refactor, debug,      |
|              remediate                                        |
|  governance/ audit, substantiate, validate, shadow-process,   |
|              process-review-cycle                             |
|  meta/       bundles (deep-audit, onboard-codebase,           |
|              repo-*, plus workflow-bundle parents)            |
|  memory/     status, organize, tone, document                 |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  SCRIPT LAYER (qor/scripts/)                                  |
|  gate_chain.py       -- write/read gate artifacts             |
|  session.py          -- session_id lifecycle                  |
|  shadow_process.py   -- append-only shadow event log          |
|  ledger_hash.py      -- SHA256 chain verification             |
|  governance_helpers  -- version bump, tag, plan metadata      |
|  changelog_stamp.py  -- seal-time CHANGELOG rename            |
|  doc_integrity.py    -- doctrine-documentation-integrity core |
|  doc_integrity_strict -- Check Surface D + E extensions       |
|  ... and ~15 more helpers                                     |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  POLICY LAYER (qor/policies/)                                 |
|  gate_enforcement.cedar   -- Cedar-flavored phase rules       |
|  owasp_enforcement.cedar  -- OWASP Top 10 mapping             |
|  skill_admission.cedar    -- SKILL.md frontmatter rules       |
+---------------------------------------------------------------+
                         |
                         v
+---------------------------------------------------------------+
|  ARTIFACT / STATE                                             |
|  docs/META_LEDGER.md      -- SHA256-chained decision history  |
|  docs/SHADOW_GENOME.md    -- narrative failure patterns       |
|  docs/PROCESS_SHADOW_GENOME.md -- structured JSONL events     |
|  docs/SYSTEM_STATE.md     -- current repo snapshot            |
|  .qor/session/current     -- active session_id marker         |
|  .qor/gates/<sid>/*.json  -- per-phase gate artifacts         |
|  CHANGELOG.md             -- user-facing release narrative    |
+---------------------------------------------------------------+
```

## Component responsibilities

**Reference layer** is the authority. Skills cite doctrines; doctrines cite each other; nothing else in the system overrides them. Doctrines are binding; `patterns-*` and `ql-*` files are non-binding references. See [doctrines inventory](../qor/references/) (complete list indexed in [README.md](../README.md)).

**Gate layer** is orchestration. `chain.md` defines the canonical phase sequence. `delegation-table.md` names every cross-skill handoff and the ground-class that triggers it. `workflow-bundles.md` specifies the protocol for multi-phase meta-skills (checkpoints, budget, decomposition). `schema/*.json` validate gate artifacts before they land on disk; schema violations raise `ValueError` at write time.

**Skill layer** is the execution surface. Each SKILL.md carries YAML frontmatter (`phase`, `gate_reads`, `gate_writes`, `autonomy`, `tone_aware`) plus an `<skill>` block + execution protocol. Skills invoke script-layer helpers and write artifacts via the gate layer. Skills never write directly to code files outside their scope; refactoring belongs to `/qor-refactor`, topology changes to `/qor-organize`.

**Script layer** is the mechanism. All deterministic logic lives here, tested by `tests/test_*.py`. Scripts have no side effects on governance files except through the gate-artifact helpers (`gate_chain.write_gate_artifact`, `shadow_process.append_event`, `changelog_stamp.apply_stamp`, etc.).

**Policy layer** expresses invariants as Cedar-flavored declarative policies. Enforced by [doctrine-owasp-governance](../qor/references/doctrine-owasp-governance.md) and [doctrine-nist-ssdf-alignment](../qor/references/doctrine-nist-ssdf-alignment.md).

**Artifact / state** is where governance manifests on disk. Every skill that writes (plan, audit, implement, substantiate, remediate) produces structured artifacts validated against the schema layer.

## Layering rules

- **No reverse imports**. Scripts may not import from skills; skills may not "know" which scripts implement them beyond the imports declared in the skill's execution protocol.
- **Single source of truth per concept.** [documentation-integrity](../qor/references/doctrine-documentation-integrity.md) mandates one `home:` file per glossary entry. [audit-report-language](../qor/references/doctrine-audit-report-language.md) mandates one authoritative ground-class-to-skill mapping.
- **Cross-cutting concerns centralized.** Logging via `shadow_process.append_event`; session tracking via `session.py`; ledger via `ledger_hash.py`. No skill implements its own.
- **Build path is intentional.** No orphan files; every new file is linked from the plan's Affected Files block and verified by `/qor-audit` Orphan Detection.

## Extension points

| Add | How |
|---|---|
| New skill | Plan declares SKILL.md + `references/` dir; tests in `tests/`; skill-admission lint validates frontmatter; handoffs declared in delegation-table |
| New doctrine | Plan declares `qor/references/doctrine-<name>.md` with sections per the existing pattern; cited by one or more skills |
| New script helper | Plan declares `qor/scripts/<name>.py` plus tests; skill execution protocol imports it |
| New schema | Plan declares `qor/gates/schema/<phase>.schema.json`; gate_chain validates before write |
| New host variant | Plan extends `qor/scripts/dist_compile.py` emitter for the host; variant output lands in `qor/dist/variants/<host>/` |

## Dependency rules

- No runtime dependency on a specific LLM provider. Skills are markdown prompts; any sufficiently capable LLM with the declared tools can execute them.
- Scripts use only stdlib + two declared dependencies: `PyYAML>=6` (frontmatter parsing, `yaml.safe_load` only) and `jsonschema>=4` (gate artifact validation).
- No network I/O at gate time. `/qor-substantiate` staging may invoke `git push` / `gh pr create` but only at operator choice in Step 9.6.

## Related docs

- [lifecycle.md](lifecycle.md) -- phase sequence and per-phase contracts
- [operations.md](operations.md) -- operator runbook
- [policies.md](policies.md) -- policy layer details
- [../qor/gates/chain.md](../qor/gates/chain.md) -- canonical phase chain
- [../qor/references/glossary.md](../qor/references/glossary.md) -- term registry
