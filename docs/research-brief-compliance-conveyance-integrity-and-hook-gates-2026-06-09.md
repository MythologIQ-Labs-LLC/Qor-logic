# Research Brief

**Date**: 2026-06-09
**Analyst**: The Qor-logic Analyst
**Target**: (A) CI/regression protection of the compliance-conveyance surface; (B) feasibility of deterministic gates via Claude Code hooks; (C) cross-platform portability of those gates
**Scope**: `.github/workflows/*`, `qor/scripts/*` gate CLIs, `qor/scripts/host_capability.py`, `qor/scripts/check_variant_drift.py`, `qor-bootstrap`, Claude Code hooks (`code.claude.com/docs/en/hooks.md`)

---

## Executive Summary

The asset to protect is not this repo -- it is the **compliance-conveyance machinery** Qor-logic
ships to every downstream system (gate scripts, doctrines, schemas, provenance manifests, the
installed skill/variant payload). A Qor-logic update that silently weakens a gate strips that
protection from every consumer on their next seal. Today that surface is guarded substantially but
not provably: behavioral gate tests + wiring tests + variant-drift run in CI, but framework-doctrine
tests are presence-only, there is no completeness invariant or compliance ratchet, and nothing
asserts the conveyed payload still carries each control. Separately, **deterministic hooks are a
viable in-session enforcement layer** -- Claude Code's `PreToolUse` can block a tool call
deterministically (harness-executed, not model-decided) -- but Claude Code hooks are **not portable
across coding platforms**. The portable substrate that already exists is the gate-CLI layer
(`qor-logic scripts <module>`) triggered by **git hooks + CI**; Claude Code hooks are a premium,
Claude-only convenience on top.

## Findings

### A. Compliance-conveyance integrity (what CI does and does not protect)

CI runs four workflows (`.github/workflows/ci.yml`, `pr-lint.yml`, `pr-dependency-review.yml`,
`release.yml`). `ci.yml` runs the full `pytest` suite, `check_variant_drift.py`,
`ledger_hash.py verify`, and `gate_chain_completeness --phase-min 52`. The compliance frameworks
themselves (OWASP, NIST SSDF/AI-RMF, EU AI Act) are **not** standalone CI jobs; they are enforced at
the `/qor-audit` + `/qor-substantiate` skill gates and recorded in the seal. CI is the
tamper-evidence backstop, not an independent re-runner.

Guard strength by layer (all execute in CI via `pytest`):

| Layer | Mechanism | Strength for conveyance |
|---|---|---|
| Behavioral gate tests | `test_data_api_acl_lint`, `test_ai_provenance_*`, `test_gate_chain_phase52_provenance_still_enforced` (asserts `ProvenanceError` actually blocks the write), SSDF tag extraction on real ledgers | Strong -- proves the gate does what it claims |
| Wiring tests (~15 `*_wiring.py`) | lock that each gate is invoked by its skill at the declared posture | Strong -- main defense against a silent ABORT->WARN downgrade |
| Variant-drift (`check_variant_drift.py`, CI job) | installed claude/codex/kilo/gemini variants must match source byte-for-byte | Strong -- protects what is conveyed from drifting off tested source |
| gate-chain + provenance | sealed phases must carry all four gate artifacts (which embed EU AI Act Art. 13/50 manifests) | Medium -- process integrity |
| Doctrine-anchored tests | `test_owasp_governance`, `test_nist_ssdf`, `test_doctrine_eu_ai_act_anchored` assert file/section/Article presence | Weak -- presence/structure only |

**The four holes for conveyance integrity:**

1. **Doctrine tests are presence-only.** `test_owasp_governance` asserts `"OWASP Top 10 Pass" in
   body` and category names exist. A PR that weakens the enforcement language (loosens a threshold,
   turns a MUST into a SHOULD) while keeping the heading passes green. Semantics are not pinned.
2. **No completeness invariant.** Posture is locked gate-by-gate by individual wiring tests; nothing
   asserts the set is complete -- "every framework-required control is wired into every skill/variant
   that must carry it." A new skill or a refactor that drops a gate from one variant only fails CI if
   a dedicated wiring test happened to exist for that exact pairing.
3. **No conveyance conformance test.** Variant-drift proves variants equal source; it does not assert
   the conveyed payload still contains the OWASP/EU/NIST gate invocations and preflight markers. If a
   control were removed from source, drift stays green (source and variants agree -- both now weaker).
4. **No compliance ratchet.** Nothing fails a release that ships fewer enforced controls than the
   prior tag. Compliance can regress monotonically and no gate notices.

### B. Deterministic gates via Claude Code hooks -- feasible, with caveats

Claude Code hooks are shell commands the harness executes deterministically (not the model), wired in
`settings.json`. Relevant facts (`code.claude.com/docs/en/hooks.md`, `hooks-guide.md`):

- **`PreToolUse` can block a tool call.** The hook receives the tool call on stdin
  (`{tool_name, tool_input, cwd, ...}`) and blocks by returning
  `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`.
  Blocking is JSON-based, not exit-code-2.
- **Matchers + `if` rules target narrowly.** A matcher of `Bash` plus `if: "Bash(git commit*)"`
  fires only on git-commit calls; `Write`/`Edit` matchers can gate writes to `docs/META_LEDGER.md`.
- **Other useful events:** `Stop` (gate the end of a turn -- e.g., refuse to finish until
  gate-chain completeness passes; uses top-level `{"decision":"block","reason":...}`),
  `UserPromptSubmit` (inject the governance-health preflight as context), `PostToolUse`
  (read-only; surface `ledger_hash verify` drift after a ledger edit -- cannot block, too late).
- **Team-shareable via `.claude/settings.json`** (git-committed); `.claude/settings.local.json` is
  per-developer. The repo currently has only `settings.local.json` and **no hooks block**.
- **Deterministic + unconditional:** a hook in shared config fires on every matching event; the model
  cannot skip or rationalize around it. This is exactly what converts "the skill is supposed to run
  the gate" into "the harness runs the gate regardless."

The gates are already standalone, exit-code CLIs (`qor-logic scripts <module>`), so wiring them into a
hook is a thin shim: run the CLI, map non-zero exit to a `deny` JSON. High-value immediate candidates
(all deterministic, already shipping): `secret_scanner --staged`, `prompt_injection_canaries`,
`badge_currency`, `ledger_hash verify`, `data_api_acl_lint`.

**Caveats:**
- **Claude-Code-only.** No equivalent in the Claude API/SDK CLI surface; the Agent SDK has a separate
  hooks system. Codex / Kilo Code / Gemini do not consume `.claude/settings.json`.
- **Bypassable.** A developer can disable hooks or edit `settings.local.json`. Hooks are
  defense-in-depth, not the authoritative gate.
- **Trust model.** Shared-config hooks run with no per-use approval prompt; a malicious
  `.claude/settings.json` hook would execute. Vetting the shared hooks block is required.
- **`Stop`/`SubagentStop` blocking semantics are under-documented** -- verify with `/hooks` debug
  before relying on a Stop gate for anything load-bearing.

### C. Cross-platform portability -- not as Claude hooks; yes as git hooks + CI

Claude Code hooks do **not** apply regardless of platform. The portable enforcement substrate is the
layer every platform already shares, invoking the identical gate CLIs:

- **Tier 1 -- CI (portable, authoritative, unbypassable).** `qor-logic scripts <gate>` jobs run on
  the server regardless of which editor/agent produced the commit. This is the load-bearing
  guarantee and the natural home for the Part A conformance matrix + ratchet.
- **Tier 2 -- git hooks (portable, local, bypassable with `--no-verify`).** A `pre-commit` /
  `pre-push` hook that runs the same CLIs works under any AI coding tool because git is the common
  substrate. Qor-logic already gestures at this: `qor-bootstrap` references installing a `pre-commit`
  hook into consumer repos, and a `.git/hooks/pre-commit` exists in this repo. `git config
  core.hooksPath .githooks` lets a tracked, version-controlled hooks dir convey to every clone.
- **Tier 3 -- per-platform in-session hooks (premium UX, not portable).** Claude Code
  `.claude/settings.json` hooks give pre-action, in-session blocking with the best feedback loop;
  equivalent adapters exist only where a platform offers them (the `host_capability.py` /
  variant-compiler abstraction is the right place to emit per-host hook config). Codex/Kilo/Gemini
  get Tier 1+2 unconditionally and Tier 3 only if/when their config supports it.

The decisive architectural fact: the gates are **write-once platform-neutral CLIs**. Only the
*trigger* is per-platform. Portability is achieved by installing Tier 1 (CI) + Tier 2 (git hooks)
from `qor-bootstrap`/the variant compiler; Tier 3 is an additive convenience for Claude users.

## Blueprint Alignment

| Intent | Reality | Status |
|---|---|---|
| Conveyed compliance is non-regressable across Qor-logic versions | No completeness invariant, no ratchet, conveyance not asserted | DRIFT (gap) |
| Framework doctrines pinned to enforced semantics | Doctrine tests are presence-only | DRIFT (weak) |
| Deterministic gates can fire in-session before an action | Feasible via Claude `PreToolUse`; not yet wired (`.claude/settings.json` has no hooks) | OPPORTUNITY |
| Enforcement conveys regardless of coding platform | Achievable via git hooks + CI (gate CLIs already neutral); Claude hooks are Claude-only | PARTIAL (substrate exists, not wired) |

## Recommendations

1. **Compliance control matrix + conformance test (CI, Tier 1)** -- a declarative registry
   `framework -> control -> enforcing module -> required posture (ABORT/WARN) -> wired-into [skills, variants]`,
   and a CI test that fails when any cell is unsatisfied (control missing, posture downgraded, or
   absent from a conveyed variant). Converts many hope-complete tests into one provable invariant and
   upgrades the presence-only doctrine tests to posture-pinned. Priority P1.
2. **Compliance ratchet (CI, Tier 1)** -- compare the enforced-control set against the prior release
   tag; a shrink fails unless an explicit, justified waiver entry exists. Makes conveyed compliance
   monotonic (hold-or-strengthen). Priority P1; depends on (1).
3. **Portable git-hook installer (Tier 2)** -- have `qor-bootstrap` install a tracked
   `core.hooksPath` `pre-commit`/`pre-push` that runs the deterministic gate CLIs
   (`secret_scanner --staged`, `prompt_injection_canaries`, `ledger_hash verify`, `badge_currency`).
   Works under any platform; the cross-platform answer to the hooks question. Priority P2.
4. **Claude Code hook pack (Tier 3, opt-in)** -- ship a `.claude/settings.json` hooks block
   (emitted by the variant compiler) with a `PreToolUse` matcher on `Bash(git commit*)` and on
   `Write`/`Edit` to `docs/META_LEDGER.md`, mapping gate-CLI non-zero exit to `permissionDecision:
   deny`. Premium in-session enforcement for Claude users; documents the trust/bypass caveats.
   Priority P3 (after Tier 1/2). 

**Sequencing**: (1)->(2) first -- they make conveyance non-regressable and are the core of the stated
intent. (3 git hooks)->(4 Claude hooks) are the trigger layers that push that same enforcement closer
to the developer; they are additive and depend only on the gate CLIs that already exist.

## Updated Knowledge

Candidate doctrine note: **conveyed-compliance ratchet** -- Qor-logic's compliance guarantee is a
property of the *conveyed* payload, not of this repo; it must be (a) provably complete via a control
matrix, (b) monotonic via a release-over-release ratchet, and (c) triggerable at three tiers
(CI / git hooks / per-platform session hooks) over one platform-neutral gate-CLI library. Hooks are a
trigger, not the gate; the gate is the CLI. Portability lives in git+CI, not in any one editor's hook
format.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
