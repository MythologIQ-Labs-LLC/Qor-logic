# Research Brief

**Date**: 2026-07-13
**Analyst**: The Qor-logic Analyst
**Target**: GH #282 -- cross-gate governance-path resolution and ledger-dialect divergence
**Scope**: doc_integrity.check_topology, prompt_injection_canaries path validation, the three
divergent ledger parsers (ledger_hash / seal_entry_check / governance_health), and
version-applicability timing across plan -> audit -> substantiate.

---

## Executive Summary

Four downstream-reproduced regressions share two root causes: (1) several gates hardcode a
single governance-path assumption instead of resolving the repository's registered authority,
and (2) three independent ledger parsers disagree about which hash-markup dialect is canonical.
Governance-health can report a repository clean and admit its plan/audit artifacts, then a
downstream gate deterministically aborts because it applied a stricter, divergent assumption.
All four are fixable with one shared canonical-path resolver, one shared versioned ledger-dialect
parser, and an early version-applicability check, without weakening any fail-closed behavior and
without rewriting an adopter's append-only history.

## Findings

### Regression 1: system-tier topology ignores the registered architecture authority

- **Location**: `qor/scripts/doc_integrity.py:27-36` (`_TIER_REQUIREMENTS["system"]`),
  `qor/scripts/doc_integrity.py:52-62` (`check_topology`).
- The `system` tier hardcodes the literal `docs/architecture.md`. `check_topology` only tests
  `(root / rel_path).exists()`; it never consults the governance index.
- The governance index already carries the registration: `docs/GOVERNANCE_INDEX.md:19`
  registers `docs/ARCHITECTURE_PLAN.md` (Tier 1 "Architecture Plan"), and
  `docs/GOVERNANCE_INDEX.md:71` registers `docs/architecture.md` as a system-tier living doc.
- **This repo has BOTH files** (`docs/architecture.md` present, 9204 bytes; `docs/ARCHITECTURE_PLAN.md`
  present). A downstream adopter registered `docs/ARCHITECTURE_PLAN.md` as its sole architecture
  authority and did not create a duplicate `docs/architecture.md`; strict topology then rejects it
  even though governance-health accepts the repo.
- **Existing reusable machinery**: `qor/scripts/governance_index.py:50-76` already parses registered
  backtick paths (`_registered_paths`, `_is_registered`). The resolver must reuse this, not fork it.

### Regression 2: three ledger parsers disagree about the accepted hash-markup dialect

- **Parsers today** (three, independent):
  - `qor/scripts/ledger_hash.py:151-157` -- `CONTENT/PREV/CHAIN_HASH_RE` with
    `_HASH_VALUE = (?:`<hex>`|=\s*<hex>)`.
  - `qor/reliability/seal_entry_check.py:31-40` -- its own `_ENTRY_HEADER_RE` and `_HASH_FIELD_RE`.
  - `qor/scripts/governance_health.py:158-167` -- delegates to `ledger_hash.verify` /
    `verify_post_anchor` (so it inherits ledger_hash's dialect, but wraps the result in a
    post-anchor tolerance the strict `verify-ledger` CLI does not apply -> the "disagree" symptom).
- **Empirically confirmed gap** (probe run 2026-07-13):
  - inline-backtick `**Content Hash**: `<hex>`` -> MATCH
  - fenced block with a bare 64-hex line (```` ``` `` + `<hex>` + ``` ``` ````) -> **NO MATCH**
  - fenced block with `= <hex>` -> MATCH
- `verify()` (`ledger_hash.py:434-441`) FAILs any entry `>= markup_required_cutoff (123)` whose
  markup does not resolve, with exactly the reported message
  `missing canonical hash markup`. A fenced bare-hex entry at/after 123 therefore hard-fails
  strict `verify-ledger`, while governance-health tolerates it via the post-anchor band.
- **Separate `**Phase**:` line**: this repo's own entries put `Phase <N>` in the header title AND
  carry a `**Phase**:` line (e.g. `META_LEDGER.md:15251`). `seal_entry_check._ENTRY_HEADER_RE`
  requires `Phase\s*(\d+)` on the header line (`[^\n]*?Phase`). An adopter whose header is bare
  (`### Entry #123: SESSION SEAL`) and whose phase lives only on a separate `**Phase**: 4` line
  yields no header match -> `_parse_latest_entry` returns None -> seal check fails.
- **Compatibility boundary already exists** as `markup_required_cutoff=123`
  (`ledger_hash.py:382,434`) and grandfather cutoff 207. The shared parser must preserve an explicit
  historical boundary, recognize the fenced bare-hex and separate-`**Phase**:` dialect at/after it,
  and continue to reject malformed hashes, content mismatch, chain mismatch, post-boundary duplicate
  previous hashes, tampering, and ambiguous parses.

### Regression 3: version-applicability validated too late

- **Location**: `qor/scripts/governance_helpers.py:107-125` (`bump_version`) and
  `qor/scripts/version_backends.py:55-74` (`_bump_generic`). The downgrade guard
  (`target vX <= current highest tag`) only fires at `/qor-substantiate` Step 7.5, after audit PASS
  and implementation.
- Qor-logic derives the target version from `**change_class**:` (`hotfix|feature|breaking`,
  `governance_helpers.py:19-22`); there is no explicit non-release classification. A governance-only
  cycle that legitimately should not bump has no first-class way to declare that, and a release-class
  plan missing a valid target is not caught until seal.
- The substantiate SKILL already names the contract: `qor-substantiate/SKILL.md:150-154` "If Target
  Version <= Current Tag -> ABORT". The fix moves an equivalent check before audit PASS and adds an
  audited non-release class that plan/audit/substantiate interpret identically.

### Regression 4: prompt-injection scanning rejects a validated active plan path

- **Location**: `qor/scripts/prompt_injection_canaries.py:31-36` (`_GOVERNANCE_FILE_RE`),
  `:122-130` (`_validate_path`).
- The allowlist admits only `docs/plan-qor-phase\d+...md` plus the four canonical files, research
  briefs, and doctrines. A registered active plan named `docs/plan-<slug>.md` (no `qor-phase`
  segment) is rejected with `path not in governance allowlist` BEFORE any content is read, hard-
  aborting the audit's canary step (`qor-audit/SKILL.md:252-253` scans `${PLAN_PATH}`).
- `governance_helpers.current_phase_plan_path` (`:57-67`) already globs `plan-qor-phase{nn}*.md`;
  downstream adopters name plans `plan-<slug>.md` (see `seal_entry_check.py:230-247`, GH #223, which
  already softened the seal path for this exact naming). The canary path validation must consume the
  validated active plan path via the shared resolver (registered + within-root + governance
  extension) rather than a filename family, while still rejecting traversal, outside-root,
  unsupported-extension, and unregistered paths, and still detecting a real canary.

## Blueprint Alignment

| Blueprint / doctrine claim | Actual finding | Status |
|---|---|---|
| Governance-health is the authoritative pre-gate (`doctrine-governance-enforcement`) | Downstream gates apply stricter, divergent path/dialect assumptions than health | DRIFT |
| One canonical ledger dialect | Three parsers; fenced bare-hex + separate-`**Phase**:` unrecognized by two of them | DRIFT |
| Version downgrade guard protects releases | Guard exists but only at seal; audit can PASS a plan that will inevitably fail | DRIFT |
| Architecture authority is index-registered | `check_topology` ignores the index and hardcodes `docs/architecture.md` | DRIFT |
| `plan-<slug>.md` is a supported downstream name (GH #223) | Seal path honors it; canary path validation does not | DRIFT |

## Recommendations

1. **[P0] Shared canonical-path resolver** (new module, e.g. `qor/scripts/governance_paths.py`),
   reusing `governance_index._registered_paths`/`_is_registered`:
   - `resolve_architecture_authority(repo_root) -> Path`. With an index present, legacy literal
     `docs/architecture.md` takes precedence when it exists and is registered (this repo: zero
     behavior change); otherwise resolve the single registered architecture doc (adopter:
     `docs/ARCHITECTURE_PLAN.md`). Fail closed on missing / multiple / unregistered / outside-root /
     non-governance. Without an index, fall back to the legacy literal if present, else fail.
   - `resolve_governance_plan_path(raw, repo_root) -> Path`. Normalize within root; require a
     governance extension and index registration; reject traversal, outside-root, unsupported
     extension, and unregistered before reading.
   - `check_topology` consumes `resolve_architecture_authority`; canaries consume
     `resolve_governance_plan_path`.

2. **[P0] Shared versioned ledger-dialect parser** (single module consumed by ledger_hash,
   seal_entry_check, governance_health):
   - Recognize inline-backtick, `= <hex>`, and fenced bare-hex forms, plus a separate `**Phase**:`
     line as a phase source when the header lacks `Phase <N>`.
   - Declare one explicit historical compatibility boundary (preserve current 123 semantics).
   - Preserve every rejection: malformed hashes, content-hash mismatch, chain mismatch, invalid
     post-boundary duplicate previous hashes, tampering, ambiguous parses. No history rewrite.

3. **[P1] Early version-applicability validation** shared by plan/audit/substantiate:
   - Release-class (`feature`/`breaking`) plans must yield a target > current highest tag; validated
     before audit PASS.
   - Add an explicit, audited non-release / version-not-applicable classification for governance-only
     cycles; all three phases interpret it identically (no bump, no downgrade-guard abort).

4. **[P2]** Update `docs/architecture.md`, CHANGELOG, and the relevant doctrines for the changed
   contracts. Record a bootstrap-conflict note: this cycle edits the very gates that gate it; if a
   gate blocks its own remediation, disclose rather than bypass.

## Updated Knowledge

Add to `docs/SHADOW_GENOME.md`: "Gate-assumption divergence" pattern -- a downstream gate that
re-derives a governance path or ledger dialect with a stricter local assumption than the
authoritative governance-health pre-gate produces a health-clean-but-gate-aborts contradiction.
Remedy: shared resolvers/parsers, never parallel per-gate assumptions.

---

_Research complete. Findings are advisory; implementation decisions remain with the Governor._
