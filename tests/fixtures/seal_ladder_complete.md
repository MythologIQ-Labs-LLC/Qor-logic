# Fixture: a well-formed seal gate ladder

Trimmed to four rows. The parser contract is what is under test, not the real
ladder's content.

### Step 4.6: Reliability Sweep

```bash
SESSION_ID=$(python -c "from qor.scripts.session import current; print(current() or 'default')")
qor-logic scripts substantiate_gates --skill qor/skills/governance/qor-substantiate/SKILL.md || ABORT
```

| Step | Gate | Command | Policy | Records | Notes |
|---|---|---|---|---|---|
| 4.6 | intent_lock + skill_admission | `qor-logic reliability intent_lock verify --session "$SESSION_ID" \|\| ABORT`<br>`qor-logic reliability skill_admission qor-substantiate \|\| ABORT` | ABORT | intent_lock_state | session_id_lint runs WARN-only alongside |
| 4.6.5 | secret_scanner | `qor-logic scripts secret_scanner --staged --out dist/secrets.findings.json \|\| ABORT` | ABORT | secret_scanner | requires `module:qor.scripts.secret_scanner` |
| 4.6.9 | skill_size_budget_lint | `qor-logic scripts skill_size_budget_lint --skills-root qor/skills \|\| true` | WARN | skill_size_budget | CLI exits 1 on EXCEEDED |
| 4.6.13 | install_drift_check | `qor-logic scripts install_drift_check --host claude --scope auto \|\| true` | disclose | skill_corpus | disclosure, not ABORT |

### Step 4.7: Next Step

Terminates the ladder region.
