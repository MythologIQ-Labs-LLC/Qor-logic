<p align="center">
  <strong>QorLogic</strong><br>
  Standards-Aligned Governance for AI Coding Agents
</p>

<p align="center">
  <a href="https://pypi.org/project/qor-logic/"><img src="https://img.shields.io/pypi/v/qor-logic?color=blue&label=PyPI" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-BSL--1.1-orange" alt="License: BSL-1.1">
  <img src="https://img.shields.io/badge/Tests-352%20passing-brightgreen" alt="Tests: 352 passing">
  <img src="https://img.shields.io/badge/NIST-SP%20800--218A%20aligned-004488" alt="NIST SP 800-218A aligned">
  <img src="https://img.shields.io/badge/OWASP-Top%2010%20audited-004488" alt="OWASP Top 10 audited">
  <img src="https://img.shields.io/badge/Skills-27-blue" alt="Skills: 27">
  <img src="https://img.shields.io/badge/Agents-13-blue" alt="Agents: 13">
  <img src="https://img.shields.io/badge/Ledger-69%20entries%20sealed-green" alt="Ledger: 69 entries sealed">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#lifecycle">Lifecycle</a> |
  <a href="#policy-engine">Policy Engine</a> |
  <a href="#skill-catalog">Skills</a> |
  <a href="#governance-model">Governance</a> |
  <a href="#contributing">Contributing</a>
</p>

---

## What QorLogic Does

QorLogic is a governance framework that ships curated skills, doctrines, and runtime enforcement to AI coding agents. It covers the full software development lifecycle with hash-chained evidence, machine-enforceable policies, and a process-failure feedback loop.

Supported hosts: **Claude Code**, **Kilo Code**, **Codex** (provisional), **Gemini CLI**.

Built around **S.H.I.E.L.D.**: Single-purpose, Hash-chained, Idempotent, Explicit, Layered, Delegating.

## Quick Start

### Install from PyPI

```bash
pip install qor-logic
```

### Deploy skills to your AI coding host

By default QorLogic installs into the **current workspace** (`./.<host>/`). Use `--scope global` for user-wide install under `~/.<host>/`.

```bash
# Initialize with host + scope (scope defaults to repo)
qorlogic init --host claude --profile sdlc                 # repo scope
qorlogic init --host gemini --profile sdlc --scope global  # global scope

# Install governance skills and agent personas
qorlogic install --host claude                # -> ./.claude/
qorlogic install --host gemini                # -> ./.gemini/commands/
qorlogic install --host codex --scope global  # -> ~/.codex/

# Verify the installation
qorlogic list --available
```

Supported host layouts:

| Host | Default folder (repo scope) | File format |
|------|-----------------------------|-------------|
| `claude` | `./.claude/skills/`, `./.claude/agents/` | Markdown |
| `kilo-code` | `./.kilo-code/skills/`, `./.kilo-code/agents/` | Markdown |
| `codex` | `./.codex/skills/`, `./.codex/agents/` | Markdown |
| `gemini` | `./.gemini/commands/` | TOML |

Set `QORLOGIC_PROJECT_DIR` to override the repo root.

### Or install to a custom target

```bash
# Non-standard host, filesystem governance, or data pipeline projects
qorlogic install --host claude --target /path/to/custom/dir/
```

### Use in your AI coding session

```
/qor-plan          # author a phased implementation plan
/qor-audit         # adversarial PASS/VETO tribunal
/qor-implement     # build under Section 4 Razor constraints
/qor-substantiate  # seal with Merkle hash evidence
```

## Lifecycle

QorLogic enforces a phased governance lifecycle. Each phase gates the next. Every decision is SHA256-chained in the Meta Ledger.

```mermaid
graph LR
    R["/qor-research"] --> P["/qor-plan"]
    P --> A["/qor-audit"]
    A -->|PASS| I["/qor-implement"]
    A -->|VETO| P
    I --> S["/qor-substantiate"]
    S --> V["/qor-validate"]

    D["/qor-debug"] -.->|cross-cutting| I
    RE["/qor-remediate"] -.->|process recovery| P

    SG["Shadow Genome"] -.->|threshold breach| RE

    style A fill:#c62828,color:#fff
    style S fill:#2e7d32,color:#fff
    style SG fill:#ff8f00,color:#fff
```

Each transition produces a ledger entry. VETO loops back to planning. Process failures accumulate in the Shadow Genome and auto-trigger remediation at configurable thresholds.

## Policy Engine

QorLogic includes a Cedar-inspired policy evaluator written in pure Python. Policies are data files, not hardcoded logic.

```cedar
// qor/policies/gate_enforcement.cedar
permit (
  principal,
  action == Action::"implement",
  resource == Gate::"plan"
) when { resource.verdict == "PASS" };

forbid (
  principal,
  action == Action::"implement",
  resource == Gate::"plan"
) when { resource.verdict == "VETO" };
```

Evaluate policies from the CLI:

```bash
qorlogic policy check request.json
```

The evaluator supports `permit`/`forbid` effects, `==` and `in` constraints, `when` conditions, and default-deny semantics (forbid overrides permit). Designed for compatibility with the [Cedar](https://www.cedarpolicy.com/) language; swap in a native Cedar SDK when Python bindings ship.

## Standards Alignment

### NIST SP 800-218A (SSDF for AI)

QorLogic maps its lifecycle to the Secure Software Development Framework practices defined in [NIST SP 800-218A](https://doi.org/10.6028/NIST.SP.800-218A):

| SSDF Practice Group | QorLogic Implementation |
|---|---|
| **PO** Prepare the Organization | `/qor-bootstrap`, 8 doctrine files, `CLAUDE.md` drop-in |
| **PS** Protect the Software | `/qor-audit` tribunal, reliability scripts, Shadow Genome |
| **PW** Produce Well-Secured Software | `/qor-plan` > `/qor-audit` > `/qor-implement` > `/qor-substantiate` |
| **RV** Respond to Vulnerabilities | `/qor-remediate`, `/qor-debug`, threshold-triggered issue creation |

Full mapping: [`qor/references/doctrine-nist-ssdf-alignment.md`](qor/references/doctrine-nist-ssdf-alignment.md)

### OWASP Top 10

The codebase has been [audited against OWASP Top 10 (2021)](docs/security-audit-2026-04-16.md). Findings: 0 HIGH, 3 MEDIUM (integrity-hardening), 6 LOW (hygiene). No exploitable vulnerabilities. All subprocess calls use list-form argv. No shell injection surface. No unsafe deserialization.

## Skill Catalog

### SDLC Chain (9 skills)

| Skill | Phase | Purpose |
|---|---|---|
| `/qor-research` | research | Investigate before planning |
| `/qor-plan` | plan | Author phased plans with tests |
| `/qor-audit` | gate | Adversarial PASS/VETO tribunal |
| `/qor-implement` | implement | Build under KISS constraints |
| `/qor-refactor` | implement | Section 4 Razor cleanup |
| `/qor-debug` | cross-cutting | Root-cause diagnosis |
| `/qor-substantiate` | substantiate | Seal with Merkle evidence |
| `/qor-validate` | validate | Chain and criteria verification |
| `/qor-remediate` | process recovery | Process-level fix from Shadow Genome |

### Memory and Meta (8 skills)

| Skill | Purpose |
|---|---|
| `/qor-status` | Diagnose lifecycle state and next action |
| `/qor-document` | Update governance documentation |
| `/qor-organize` | Project-level structure reorganization |
| `/qor-bootstrap` | Seed a new workspace with governance DNA |
| `/qor-help` | In-skill command catalog |
| `/qor-repo-audit` | Repository-level compliance audit |
| `/qor-repo-release` | Release ceremony orchestration |
| `/qor-repo-scaffold` | New-repo template generation |

### Workflow Bundles (5 bundles)

| Bundle | Phases | Use When |
|---|---|---|
| `/qor-deep-audit` | recon (3) + remediate (3) | Pre-release readiness, tech-debt sweep |
| `/qor-deep-audit-recon` | research + synthesize + verify | Investigation only; ends at RESEARCH_BRIEF |
| `/qor-deep-audit-remediate` | plan + implement + validate | Action half; consumes RESEARCH_BRIEF |
| `/qor-onboard-codebase` | research > organize > audit > plan | Absorbing an external codebase |
| `/qor-process-review-cycle` | shadow-sweep > remediate > audit | Periodic process health check |

### Governance (1 skill)

| Skill | Purpose |
|---|---|
| `/qor-shadow-process` | Append structured process-failure events |

## Governance Model

1. **Every decision is logged.** Plans, audits, and substantiations land in `docs/META_LEDGER.md` as SHA256-chained entries. Verify the full chain: `qorlogic verify-ledger`.

2. **Gates are advisory with teeth.** Skills check for prior-phase artifacts. Override is permitted but logged as a severity-1 `gate_override` event in the Shadow Genome.

3. **Process failures are append-only.** `docs/PROCESS_SHADOW_GENOME.md` stores JSONL events that flow through stale-expiry rules and aged-high-severity self-escalation. Threshold breach (severity sum >= 10) triggers `/qor-remediate`.

4. **Policies are data.** Cedar-syntax `.cedar` files under `qor/policies/` define permit/forbid rules evaluated at gate check points. The policy engine logs every decision for audit.

5. **Skills delegate explicitly.** When `/qor-audit` finds a Razor violation, it names `/qor-refactor`. No skill reinvents another skill's process. ([delegation-table](qor/gates/delegation-table.md))

6. **Bundles checkpoint and budget.** Multi-phase workflows declare budgets and surface progress between phases. Context windows stay manageable. ([workflow-bundles](qor/gates/workflow-bundles.md))

## Architecture

```
qor-logic/
  qor/
    skills/           27 skills + 5 bundles (governance, sdlc, memory, meta)
    agents/           13 agent personas
    policy/           Cedar-inspired permit/forbid evaluator (pure Python)
    policies/         .cedar policy files (gate enforcement, skill admission)
    scripts/          Runtime: ledger, gates, shadow, platform, compiler, remediate
    reliability/      Intent Lock, Skill Admission, Gate-to-Skill Matrix
    references/       8 doctrines (token efficiency, test discipline, NIST SSDF, ...)
    gates/            Phase chain, delegation table, workflow bundles, 9 JSON schemas
    resources.py      importlib.resources wrapper for packaged assets
    workdir.py        $QOR_ROOT / CWD anchor for consumer-state paths
    hosts.py          Host-to-install-path resolver (claude, kilo, codex, gemini)
    cli.py            qorlogic CLI entry point
    dist/variants/    Pre-compiled per-host outputs (claude, kilo-code, codex, gemini)
  tests/              323 tests (unit, integration, e2e, doctrine, bundle contract)
  .github/workflows/  CI (6-job matrix) + PyPI release (OIDC trusted publisher)
```

## CLI Reference

```
qorlogic install --host <claude|kilo-code|codex|gemini> [--scope <repo|global>] [--target <path>] [--dry-run]
qorlogic uninstall --host <host> [--scope <repo|global>]
qorlogic init --host <host> [--scope <repo|global>] --profile <sdlc|filesystem|data|research>
qorlogic list [--available] [--installed] [--host <host>] [--scope <repo|global>]
qorlogic info <skill-name>
qorlogic compile [--dry-run]
qorlogic verify-ledger [<path>]
qorlogic policy check <request.json>
qorlogic --version
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/                                    # 323 tests
python -m pytest tests/ -m integration                     # +4 install-smoke tests
qorlogic verify-ledger                                     # Merkle chain integrity
BUILD_REGEN=1 python qor/scripts/dist_compile.py           # regenerate variants
python qor/scripts/check_variant_drift.py                  # SSoT vs dist consistency
```

## Key Documentation

| Document | Purpose |
|---|---|
| [`docs/META_LEDGER.md`](docs/META_LEDGER.md) | SHA256-chained governance log (69 entries sealed) |
| [`docs/RESEARCH_BRIEF.md`](docs/RESEARCH_BRIEF.md) | PyPI packaging gap audit (18/18 gaps closed) |
| [`docs/security-audit-2026-04-16.md`](docs/security-audit-2026-04-16.md) | OWASP Top 10 + stability audit |
| [`qor/references/doctrine-nist-ssdf-alignment.md`](qor/references/doctrine-nist-ssdf-alignment.md) | NIST SP 800-218A lifecycle mapping |
| [`qor/references/doctrine-shadow-genome-countermeasures.md`](qor/references/doctrine-shadow-genome-countermeasures.md) | 12 codified failure patterns (SG-016 through SG-038) |
| [`qor/gates/delegation-table.md`](qor/gates/delegation-table.md) | Skill-to-skill handoff matrix |
| [`qor/gates/workflow-bundles.md`](qor/gates/workflow-bundles.md) | Bundle checkpoint and budget protocol |
| [`CLAUDE.md`](CLAUDE.md) | Drop-in token-efficiency defaults for any project |

## Shadow Genome

The Shadow Genome is QorLogic's institutional memory for failure patterns. Every governance failure (plan VETOes, import breakage, arithmetic drift, silent data loss) is recorded, classified, and codified as a countermeasure.

12 patterns codified so far:

| ID | Pattern | Countermeasure |
|---|---|---|
| SG-016 | Generic-convention paths without grounding | Grep/read before citing any path |
| SG-021 | Multi-layer edit compression | Enumerate every file that receives the edit |
| SG-032 | Batch-split-write coverage gap | Classify records at creation, not post-hoc |
| SG-033 | Positional-to-keyword signature breakage | Grep all callers before adding `*` |
| SG-036 | Doctrine adoption grace period | No grace period; inline grounding immediately |
| SG-038 | Prose-code mismatch in plans | Grep plan for every enumeration; update in lockstep |

Full inventory: [`qor/references/doctrine-shadow-genome-countermeasures.md`](qor/references/doctrine-shadow-genome-countermeasures.md)

## License

Business Source License 1.1 (BSL-1.1). Free for non-production use. Production deployment requires a commercial license from [MythologIQ Labs, LLC](https://github.com/MythologIQ-Labs-LLC). See [LICENSE](LICENSE) for details.

## Contributing

Skills live under `qor/skills/<category>/<skill-name>/SKILL.md` (the single source of truth). The `qor/dist/variants/` outputs are generated. Never edit them directly.

To author a new skill:

1. Pick a category: `governance`, `sdlc`, `memory`, or `meta`.
2. Create `qor/skills/<category>/<name>/SKILL.md` with required frontmatter (`name`, `description`, `phase`, `gate_reads`, `gate_writes`).
3. Add a row to [`qor/gates/delegation-table.md`](qor/gates/delegation-table.md).
4. Register in [`/qor-help`](qor/skills/meta/qor-help/SKILL.md).
5. Regenerate: `BUILD_REGEN=1 python qor/scripts/dist_compile.py`
6. Test: `python -m pytest tests/`

For workflow bundles, follow the metadata schema in [`qor/gates/workflow-bundles.md`](qor/gates/workflow-bundles.md). Bundle contract tests in `tests/test_bundles.py` cover new bundles automatically.
