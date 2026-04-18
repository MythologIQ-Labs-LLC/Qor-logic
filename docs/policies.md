# Qor-logic Policies

The policy layer expresses invariants as Cedar-flavored declarative policies and standards-framework mappings. Policies are evaluated by the CLI (`qorlogic policy check <request.json>`) and cited by doctrines at audit time.

## Policy files

Under `qor/policies/`:

| File | Scope | Enforces |
|---|---|---|
| `gate_enforcement.cedar` | Phase transitions | Every SDLC phase transition requires a PASS verdict in the prior-phase audit artifact; overrides are permitted as advisory gates but logged as severity-1 shadow events |
| `owasp_enforcement.cedar` | Security at audit | OWASP Top 10 category-specific forbids (A03 injection via `shell=True`, A08 deserialization via `yaml.load` / `pickle.load`, etc.) |
| `skill_admission.cedar` | Skill registration | Every SKILL.md must carry valid frontmatter: `name` matches the directory, `phase` matches a chain.md phase, `gate_reads` / `gate_writes` align with the phase, `autonomy` is one of the allowed values |

Policies evaluate against a request payload describing the action being proposed. `permit` and `forbid` are the two outcomes, with `when` conditions for context-sensitive rules. Default is deny.

## Evaluator

`qor/policy/` (Python) implements a minimal Cedar-flavored evaluator (`permit` / `forbid`, `==` and `in` constraints, `when` conditions, default-deny). Not a full Cedar implementation; only the subset Qor-logic needs.

## Standards alignment

### OWASP Top 10 (2021)

See [doctrine-owasp-governance](../qor/references/doctrine-owasp-governance.md) for the full mapping. Summary of active categories:

| Category | Qor-logic enforcement |
|---|---|
| A03 Injection | `/qor-audit` OWASP pass checks subprocess calls use list-form argv; no `shell=True`; user input validated. `tests/test_yaml_safe_load_discipline.py` bans `yaml.load` / `yaml.load_all` / `yaml.full_load` / `yaml.unsafe_load` repo-wide |
| A04 Insecure Design | `/qor-audit` flags fail-open on error, silent drops of security events |
| A05 Security Misconfiguration | No hardcoded secrets; temp files use `tempfile.NamedTemporaryFile` with secure permissions |
| A08 Software/Data Integrity | No unsafe deserialization (pickle, eval, exec, yaml.load without SafeLoader). Plan-text ground at audit per SG-Phase24-B countermeasure |

### NIST SP 800-218A (SSDF)

See [doctrine-nist-ssdf-alignment](../qor/references/doctrine-nist-ssdf-alignment.md) for the full practice-tag mapping. Meta Ledger entries carry practice tags; `qorlogic compliance report` emits a coverage report against the SSDF practices.

## Change class contract

Per [governance-enforcement §3](../qor/references/doctrine-governance-enforcement.md):

Every plan header declares `**change_class**: hotfix | feature | breaking` (bold markdown, enforced by V-2 doctrine test). At substantiate time:

- `hotfix` -> patch bump (0.2.0 -> 0.2.1)
- `feature` -> minor bump (0.2.0 -> 0.3.0)
- `breaking` -> major bump (0.2.0 -> 1.0.0)

`governance_helpers.bump_version` interdicts two conditions: target tag already exists (`v<new>` in `git tag --list`); target is a downgrade (`<=` highest existing tag). Both interdictions raise `InterdictionError` and force operator intervention.

## Shadow genome rubric

See [shadow-genome-countermeasures](../qor/references/doctrine-shadow-genome-countermeasures.md) for the full failure-pattern catalog. Severity ratings (1-5) drive the Process Shadow Genome threshold; when unaddressed severity-sum >= 10, `qor/scripts/check_shadow_threshold.py` auto-triggers `/qor-remediate`.

Pattern IDs span SG-016 through SG-Phase30-B as of this writing; the catalog grows with incident history (entries never shrink, per test-discipline Rule 4: Rule = Test + update protocol).

## Exception and escape paths

- **Advisory gate override**: any Step 0 gate check allows operator override, logged as severity-1 `gate_override` shadow event. Use sparingly; repeated overrides in one session trigger the `gate-loop` pattern at `/qor-remediate`.
- **Legacy doc tier**: [documentation-integrity](../qor/references/doctrine-documentation-integrity.md) allows plans to declare `doc_tier: legacy` to bypass topology + glossary + orphan checks. Requires `doc_tier_rationale` (schema-enforced). Emits severity-2 `degradation` event at plan time.
- **Section 4 Razor exception**: none documented. Always split/refactor rather than exceed limits.
- **Test-discipline regression-coverage-backfill**: explicit exception for backfilling tests against pre-existing modules (e.g., `ledger_hash.py` was written in Phase 1.5 but tested in Phase 12). Must be classified in-plan and in-commit-message.

## Policy evolution

Policies are amended through plans, not hand-edits. The flow is:

1. `/qor-plan` proposes a policy change.
2. `/qor-audit` reviews against existing doctrines (plan-text ground if the change contradicts a binding doctrine without amending the doctrine).
3. `/qor-implement` updates the `.cedar` file + any wired skills.
4. `/qor-substantiate` seals with a test that exercises the new policy against a known-good and known-bad request.

See [change_class](../qor/references/glossary.md) for the version impact a policy change produces; typically `feature` unless the change removes prior coverage (then `breaking`).

## Related docs

- [architecture.md](architecture.md) -- where policies sit in the layer stack
- [lifecycle.md](lifecycle.md) -- when policies are evaluated
- [operations.md](operations.md) -- `qorlogic policy check` usage
- [../qor/references/doctrine-owasp-governance.md](../qor/references/doctrine-owasp-governance.md)
- [../qor/references/doctrine-nist-ssdf-alignment.md](../qor/references/doctrine-nist-ssdf-alignment.md)
