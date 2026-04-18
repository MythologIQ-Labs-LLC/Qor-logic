# Qor-logic Operations

Operator runbook. Covers CLI usage, seal ceremony, failure recovery, CI considerations, and dist-variant management.

## CLI (`qorlogic`)

The `qorlogic` CLI is the primary install/operation surface. Subcommands:

| Subcommand | Purpose |
|---|---|
| `init` | Write `.qorlogic/config.json` with host + profile + scope selections |
| `install --host <claude\|kilo-code\|codex\|gemini>` | Copy variant skills/agents to the host's conventional directory |
| `uninstall` | Reverse `install` |
| `list` | List installed skills and agents |
| `compile` | Rebuild `qor/dist/variants/*` from source skills; emit per-variant manifest |
| `verify-ledger` | Run `qor/scripts/ledger_hash.py verify` against `docs/META_LEDGER.md` |
| `seed` | Scaffold governance workspace: `docs/META_LEDGER.md`, `docs/SHADOW_GENOME.md`, `docs/ARCHITECTURE_PLAN.md`, `CONCEPT.md`, `SYSTEM_STATE.md`, `.agent/staging/`, `.qor/gates/`, `.qor/session/`, `.gitignore` section |
| `policy check <request.json>` | Evaluate a request against `qor/policies/*.cedar` |
| `compliance report` | Emit a NIST SP 800-218A practice-tag report |

All subcommands accept `--scope {repo,global}` (default `repo`); this determines whether the install/uninstall/init writes to the project directory or to the user's home directory.

## Seal ceremony (operator's view of `/qor-substantiate`)

1. Operator invokes `/qor-substantiate` after successful `/qor-implement`.
2. Skill runs Steps 0-4.7: gate check, identity activation, state verification, version validation, Reality Audit, blocker check, functional verification (tests), Skill File Integrity Check, Reliability Sweep (intent-lock verify + skill-admission + gate-skill-matrix), Documentation Integrity Check.
3. On any abort in Steps 0-4.7, the session stays unsealed. Operator resolves the drift (re-audit, fix missing glossary entry, unwire broken handoff, etc.) and re-runs.
4. Step 5 runs Section 4 Razor final check.
5. Step 6 syncs `docs/SYSTEM_STATE.md`.
6. Step 7 calculates the Merkle seal (SHA256 chain of session artifacts).
7. Step 7.5 calls `bump_version(change_class)` FIRST, then `create_seal_tag(...)` (order matters per Phase 30 constraint; inverted order interdicts on tag-already-exists).
8. Step 7.6 stamps `CHANGELOG.md`: `## [Unreleased]` -> `## [X.Y.Z] - YYYY-MM-DD`.
9. Step 8 clears `.failsafe/governance/` staging.
10. Step 8.5 runs `python -m qor.scripts.dist_compile` (Phase 30 wiring) so variant outputs stay in sync.
11. Step 9 writes the final report. Step 9.5 auto-stages CHANGELOG + META_LEDGER + SYSTEM_STATE + plan + BACKLOG + src/.
12. Step 9.6 prompts the operator with four push/merge options.
13. Step Z writes `substantiate.json` gate artifact and calls `session.rotate()` to issue a fresh session_id for the next phase.

## Push/merge decision (Step 9.6)

| Option | Command | When |
|---|---|---|
| 1. Push only | `git push origin <branch>` | Branch lives remote; merge happens via PR reviewer cycle |
| 2. Push + PR | above + `gh pr create` with plan path, ledger entry, Merkle seal in description | External contributor review cycle |
| 3. Merge local (dry-run first) | `git merge --no-commit --no-ff <branch>` + commit | Solo operator cycle; main stays ahead locally until manual push |
| 4. Hold local | no remote action | Operator wants to defer the decision |

See [governance-enforcement §6](../qor/references/doctrine-governance-enforcement.md) for the PR description template (plan file + ledger entry + Merkle seal citations).

## Failure recovery

### Gate check fails

Operator override is permitted (advisory gate) but logged. To override: continue with the skill; a `gate_override` event is appended to the shadow genome at severity 1. To resolve: run the prior phase's skill to produce the missing artifact.

### Reality != Promise at substantiate

`/qor-substantiate` Step 3 Reality Audit fails if planned files are missing. Resolution: return to `/qor-implement`, deliver the missing files, re-run substantiate.

### Section 4 Razor violation at Step 5

Per [audit-report-language](../qor/references/doctrine-audit-report-language.md), the correct remediation is `/qor-refactor`. Do not inline a refactor inside substantiate; halt, invoke `/qor-refactor`, then re-run substantiate.

### Documentation Integrity Check ABORTs at Step 4.7

Typically means either topology missing (tier-required file absent) or glossary drift (declared term without entry). Resolution: update glossary entry (add `referenced_by:` consumer per [documentation-integrity §4](../qor/references/doctrine-documentation-integrity.md)) or raise/lower tier and re-run substantiate. The `legacy` tier is the sole documented escape and requires `doc_tier_rationale`.

### Reliability sweep ABORT at Step 4.6

One of three sub-gates fired: intent-lock drift, skill-admission failure, or gate-skill-matrix broken handoff. Each produces a distinct error message naming the specific failure. Resolution depends on the specific gate.

### Ledger chain integrity broken

`qor/scripts/ledger_hash.py verify` reports the first failing entry. Typically caused by hand-editing an entry after seal. Resolution: never hand-edit sealed entries; new decisions get new entries.

## CI considerations

The `.github/workflows/` files configure GitHub Actions:

- `ci.yml`: runs the full test suite + variant drift check + ledger hash verify on every push / PR.
- `release.yml`: publishes to PyPI on tag push.

Both workflows use `actions/checkout@v4` with `fetch-depth: 0, fetch-tags: true` (Phase 30 wiring) so `git tag` is populated for `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag`. Prior absence of tag fetch produced CI failures with "CHANGELOG sections without git tags".

## Dist variant management

Source skills live under `qor/skills/`. Variant outputs for each host live under `qor/dist/variants/<host>/`. The compile pipeline (`qor/scripts/dist_compile.py`) emits:

- **claude**: copies skills as-is into `claude/skills/` + agents into `claude/agents/`.
- **kilo-code**: same structure as claude.
- **codex**: same structure.
- **gemini**: emits TOML command files under `commands/` with frontmatter (`trigger`, `phase`, `persona`) preserved.

Run `python -m qor.scripts.dist_compile` after modifying any source skill; Phase 30's substantiate Step 8.5 runs this automatically at seal time.

## Session reset

To manually rotate a session:

```bash
python qor/scripts/session.py end     # removes current marker
python qor/scripts/session.py new     # creates a fresh session_id
```

The substantiate Step Z auto-rotate (Phase 30) is the canonical path; manual rotation is for edge cases (mid-phase debugging, abandoned session cleanup).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError: prior-phase artifact missing` at gate check | Prior phase didn't produce the artifact, or session rotated mid-flow | Run prior phase skill; or override with documented rationale |
| `ValueError: Malformed YAML in glossary entry` | YAML fence with syntax error or custom tag | Inspect the entry; rewrite as plain YAML types |
| `Tag v<X.Y.Z> already exists` | `create_seal_tag` called before `bump_version`, or bump_version called twice | Manual pyproject edit per Phase 30 constraint; re-run with correct ordering |
| `test_every_changelog_section_has_tag` fails in CI only | CI checkout without tags | Confirm `actions/checkout@v4` uses `fetch-tags: true` (Phase 30 fix) |
| Dist drift at seal | `dist_compile` not run post-edit | Phase 30 Step 8.5 runs it automatically; for legacy flows run manually |

## Related docs

- [architecture.md](architecture.md)
- [lifecycle.md](lifecycle.md)
- [policies.md](policies.md)
- [../qor/references/skill-recovery-pattern.md](../qor/references/skill-recovery-pattern.md)
- [../CONTRIBUTING.md](../CONTRIBUTING.md)
