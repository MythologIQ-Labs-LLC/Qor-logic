<p align="center">
  <strong>QorLogic</strong><br>
  S.H.I.E.L.D. Governance for AI Coding Agents
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-BSL--1.1-orange" alt="License: BSL-1.1">
  <img src="https://img.shields.io/badge/Skills-23-blue" alt="Skills: 23">
  <img src="https://img.shields.io/badge/Bundles-5-blue" alt="Bundles: 5">
  <img src="https://img.shields.io/badge/Agents-13-blue" alt="Agents: 13">
  <img src="https://img.shields.io/badge/Tests-154%20passing-brightgreen" alt="Tests: 154 passing">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Ledger-Entry%20%2320-green" alt="Ledger Entry 20">
</p>

---

## What QorLogic is

A governance framework for AI coding agents (Claude Code, Kilo Code, Codex). It supplies a curated set of skills, agents, and runtime infrastructure that enforce a disciplined SDLC — research, plan, audit, implement, substantiate, validate — with hash-chained evidence, advisory gates, and a process-failure feedback loop.

Built around **S.H.I.E.L.D.**: Single-purpose, Hash-chained, Idempotent, Explicit, Layered, Delegating.

## Why use it

- **Skills name skills.** `/qor-audit` finds a Razor violation → it tells you to run `/qor-refactor`. No reinvented inline processes. ([delegation-table](qor/gates/delegation-table.md))
- **Long workflows checkpoint and budget.** Workflow bundles (multi-skill orchestrators) declare phase budgets and pause for operator review between phases. Context windows stay manageable. ([workflow-bundles](qor/gates/workflow-bundles.md))
- **Process drift is recorded and acted on.** Every gate override, capability shortfall, and degradation lands in an append-only Process Shadow Genome. Threshold breaches auto-trigger remediation. ([shadow-process](qor/skills/governance/qor-shadow-process/SKILL.md))
- **Token-efficient by default.** Repo-root [`CLAUDE.md`](CLAUDE.md) drops in terseness rules; full doctrine in [`qor/references/doctrine-token-efficiency.md`](qor/references/doctrine-token-efficiency.md).
- **Cryptographic continuity.** Every governance decision is appended to `docs/META_LEDGER.md` as a SHA256-chained entry. `python qor/scripts/ledger_hash.py verify` validates the entire chain.

## Quick start

### Drop-in for an existing project

```bash
# Copy the canonical skills + agents into your project's Claude Code install
cp -r qor/skills/governance /path/to/your-project/.claude/skills/governance
cp -r qor/skills/sdlc       /path/to/your-project/.claude/skills/sdlc
cp -r qor/skills/memory     /path/to/your-project/.claude/skills/memory
cp -r qor/skills/meta       /path/to/your-project/.claude/skills/meta
cp -r qor/agents/*          /path/to/your-project/.claude/agents/
cp CLAUDE.md                /path/to/your-project/CLAUDE.md
```

Or consume the variant outputs directly: `qor/dist/variants/claude/` (or `kilo-code/`).

### Use a workflow bundle

```bash
# In Claude Code (or any harness with QorLogic skills loaded)
/qor-deep-audit-recon       # investigate before acting
/qor-onboard-codebase       # absorb an external repo
/qor-process-review-cycle   # weekly process health check
```

### Bootstrap a new repo

```bash
/qor-bootstrap              # creates CONCEPT, ARCHITECTURE_PLAN, META_LEDGER
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 QorLogic SSoT (qor/)                     │
│                                                          │
│  skills/ ──┬── governance/   audit, validate, ...        │
│            ├── sdlc/         research, plan, implement   │
│            ├── memory/       status, organize, document  │
│            └── meta/         bootstrap, help, bundles    │
│                                                          │
│  agents/   ── governance, sdlc, memory, meta            │
│  vendor/   ── third-party skills + agents                │
│  scripts/  ── ledger_hash, gate_chain, shadow_process   │
│  gates/    ── chain.md, workflow-bundles.md, schemas    │
│  platform/ ── capability detection + 5 host profiles    │
│  references/  doctrines + patterns                       │
│                                                          │
└──────────────────────┬──────────────────────────────────┘
                       │ compile.py
                       ▼
              ┌────────────────────┐
              │  qor/dist/variants │
              ├────────────────────┤
              │  claude/           │
              │  kilo-code/        │
              │  codex/  (stub)    │
              └────────────────────┘
                       │
                       ▼
                 Consumer projects
                  (.claude/, .kilo/)
```

### Key subsystems

| Subsystem | Module(s) | What it does |
|---|---|---|
| **Skill execution** | `qor/skills/<category>/` | 23 user-invocable skills + 5 workflow bundles |
| **Gate chain** | `qor/scripts/gate_chain.py`, `session.py` | Advisory gates between SDLC phases; session-scoped artifacts |
| **Shadow genome** | `qor/scripts/shadow_process.py`, `check_shadow_threshold.py` | Append-only process-failure log; threshold-triggered issues |
| **Cross-repo collector** | `qor/scripts/collect_shadow_genomes.py` | Pool shadow events across repos; consolidated GitHub issue |
| **Platform detection** | `qor/scripts/qor_platform.py` | Auto-detect host + gh CLI; declare codex-plugin / agent-teams |
| **Compile pipeline** | `qor/scripts/compile.py`, `check_variant_drift.py` | Regenerate variants from SSoT; drift detection in CI |
| **Ledger** | `qor/scripts/ledger_hash.py` + `docs/META_LEDGER.md` | SHA256-chained governance entries; `verify` walks the chain |

## Skill catalog

### SDLC chain

| Skill | Phase | Purpose |
|---|---|---|
| [`/qor-research`](qor/skills/sdlc/qor-research/) | research | Investigate before planning |
| [`/qor-plan`](qor/skills/sdlc/qor-plan/) | plan | Author plan-*.md with phases + tests |
| [`/qor-audit`](qor/skills/governance/qor-audit/) | audit | Adversarial PASS/VETO; Razor → refactor; Orphan/Macro → organize |
| [`/qor-implement`](qor/skills/sdlc/qor-implement/) | implement | Execute under KISS after PASS |
| [`/qor-refactor`](qor/skills/sdlc/qor-refactor/) | implement | File-internal Section 4 cleanup |
| [`/qor-debug`](qor/skills/sdlc/qor-debug/) | (cross-cutting) | Root-cause diagnosis on regression |
| [`/qor-substantiate`](qor/skills/governance/qor-substantiate/) | substantiate | Seal session; Merkle evidence |
| [`/qor-validate`](qor/skills/governance/qor-validate/) | validate | Verify chain + criteria pre-delivery |
| [`/qor-remediate`](qor/skills/sdlc/qor-remediate/) | (process recovery) | Process-level fix; absorbs `/qor-course-correct` |

### Memory & meta

| Skill | Purpose |
|---|---|
| [`/qor-status`](qor/skills/memory/qor-status/) | Diagnose lifecycle + next action |
| [`/qor-document`](qor/skills/memory/qor-document/) | Update governance docs |
| [`/qor-organize`](qor/skills/memory/qor-organize/) | Project-level structure |
| [`/qor-bootstrap`](qor/skills/meta/qor-bootstrap/) | New-workspace DNA seeder |
| [`/qor-help`](qor/skills/meta/qor-help/) | Command catalog (you're reading the README; this is the in-skill version) |
| [`/qor-repo-audit`](qor/skills/meta/qor-repo-audit/) | Repo-level audit |
| [`/qor-repo-release`](qor/skills/meta/qor-repo-release/) | Release ceremony |
| [`/qor-repo-scaffold`](qor/skills/meta/qor-repo-scaffold/) | New-repo template |

### Governance & process

| Skill | Purpose |
|---|---|
| [`/qor-shadow-process`](qor/skills/governance/qor-shadow-process/) | Append process-failure events |

### Workflow bundles

| Bundle | Phases | Use when |
|---|---|---|
| [`/qor-deep-audit`](qor/skills/meta/qor-deep-audit/) | recon (3) + remediate (3) | Pre-release readiness, large tech-debt sweep. Decomposed. |
| [`/qor-deep-audit-recon`](qor/skills/meta/qor-deep-audit-recon/) | research + synthesize + verify | Investigation only; ends at RESEARCH_BRIEF |
| [`/qor-deep-audit-remediate`](qor/skills/meta/qor-deep-audit-remediate/) | plan + implement + validate | Action half; consumes RESEARCH_BRIEF |
| [`/qor-onboard-codebase`](qor/skills/meta/qor-onboard-codebase/) | research → organize → audit → plan | Inheriting / merging an external codebase |
| [`/qor-process-review-cycle`](qor/skills/governance/qor-process-review-cycle/) | shadow-sweep → remediate → audit | Periodic process health check |

## Repository layout

```
Qor-logic/
  qor/                      Single source of truth (edit here)
    skills/<category>/      23 skills + 5 bundles across governance/sdlc/memory/meta
    agents/<category>/      13 qor-scoped agent personas
    vendor/                 Third-party skills + agents (~65 + wshobson collection)
    scripts/                Runtime: ledger, gates, shadow, platform, compile, collector
    gates/                  chain.md, workflow-bundles.md, delegation-table.md, schemas
    platform/               capabilities.md, detect.md, 5 profiles
    references/             doctrines + patterns + examples
    experimental/           non-canonical research
    templates/              doc templates
    dist/variants/          generated outputs (claude, kilo-code, codex stub)
  tests/                    154 tests (unit + integration + e2e + bundle contract)
  docs/                     Plans, ledger, shadow genomes, manifests, archive
  CLAUDE.md                 Drop-in token-efficiency defaults
  pyproject.toml            Python 3.11+, pytest, jsonschema
```

## Governance model

1. **Every decision is logged.** Plans, audits, substantiations land in `docs/META_LEDGER.md` as SHA256-chained entries. The chain is verifiable: `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md`.
2. **Gates are advisory.** Skills check for prior-phase artifacts; missing/invalid prompts the user. Override is permitted but logged as a sev-1 `gate_override` event.
3. **Process failures are append-only.** `docs/PROCESS_SHADOW_GENOME.md` is JSONL; events flow through stale-expiry rules and aged-high-severity self-escalation. Threshold breach (sev sum ≥ 10) triggers `/qor-remediate`.
4. **Skills delegate explicitly.** When `/qor-audit` finds a Razor violation, it names `/qor-refactor`. No skill reinvents another skill's process. ([delegation-table](qor/gates/delegation-table.md))
5. **Bundles checkpoint.** Multi-phase workflows surface progress between phases for operator decision. No silent runaway.

## Development

```bash
pip install -e ".[dev]"                                  # install runtime + dev deps
python -m pytest tests/                                  # 154 tests
python qor/scripts/check_variant_drift.py                # SSoT vs dist consistency
python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md  # chain integrity
git config core.hooksPath .githooks                      # one-time hook install
```

## Documentation

- [`docs/SYSTEM_STATE.md`](docs/SYSTEM_STATE.md) — current snapshot of the file tree + ledger head
- [`docs/SKILL_REGISTRY.md`](docs/SKILL_REGISTRY.md) — category-organized skill index
- [`docs/META_LEDGER.md`](docs/META_LEDGER.md) — hash-chained governance log (20 entries sealed)
- [`qor/gates/chain.md`](qor/gates/chain.md) — SDLC phase sequence + per-phase reads/writes
- [`qor/gates/delegation-table.md`](qor/gates/delegation-table.md) — explicit handoff matrix
- [`qor/gates/workflow-bundles.md`](qor/gates/workflow-bundles.md) — bundle metadata + checkpoint protocol
- [`qor/references/doctrine-token-efficiency.md`](qor/references/doctrine-token-efficiency.md) — long-session rules
- [`docs/Lessons-Learned/`](docs/Lessons-Learned/) — postmortems and corrections

## License

Business Source License 1.1 (BSL-1.1). Free for non-production use; production deployment requires a commercial license. See LICENSE for details.

## Contributing

Skills are authored under `qor/skills/<category>/<skill>/SKILL.md` (the SSoT). The dist outputs under `qor/dist/variants/` are **generated** — never hand-edit them. The pre-commit hook enforces this; CI drift check is authoritative.

To author a new skill:

1. Pick a category that fits (governance, sdlc, memory, meta).
2. Write `qor/skills/<category>/<skill-name>/SKILL.md` with required frontmatter (`name`, `description`, `phase`, `gate_reads`, `gate_writes`).
3. Add a row to [`qor/gates/delegation-table.md`](qor/gates/delegation-table.md) if your skill is a destination of any other skill's handoff.
4. Add the skill to [`/qor-help`](qor/skills/meta/qor-help/SKILL.md).
5. `BUILD_REGEN=1 python qor/scripts/compile.py` to refresh dist.
6. Test: `python -m pytest tests/`.

To author a workflow bundle, follow the same flow plus the metadata schema in [`qor/gates/workflow-bundles.md`](qor/gates/workflow-bundles.md). Bundles get covered by `tests/test_bundles.py` automatically via the contract tests.
