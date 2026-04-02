# Force Push Governance — Multi-User Repository

**Origin**: Session 2026-04-01. Sprint 2 work was invalidated when `origin/main` was force-pushed to scrub leaked credentials, orphaning all active branches. This document extracts lessons learned and establishes governance rules to prevent recurrence.

---

## Incident Timeline

1. **Sprint 1** (prior session): Security audit identified service role key committed to `.factory/settings.local.json`. Remediation plan treated this as a `.gitignore` fix (prevent future exposure) rather than a history rewrite (remove past exposure). The key remained recoverable from git history.

2. **Sprint 2** (this session): Branch `sprint-2/main` created from `origin/main` at `0e0bed3b`. Six commits applied (security fixes, test infrastructure, Stripe integrity, AI security). PR #126 opened.

3. **Force push** (same day): External QA engineer (`briborg`) force-pushed `origin/main` and `origin/staging` to scrub leaked credentials from history. This was the correct remediation for the credential exposure — but it was uncoordinated.

4. **Impact**: PR #126 became unmergeable (9,751 divergent commits, merge base fell back to repo's first commit). All work had to be re-applied onto the new history via cherry-pick. PR #126 closed, PR #138 opened.

---

## Lessons Learned

### 1. Credential exposure requires history rewrite, not just .gitignore

**Rule**: When a secret is committed to git, the remediation is **three steps in this order**:
1. **Rotate the credential immediately** — assume it's compromised the moment it was pushed
2. **Rewrite git history** — `git filter-repo` or BFG to remove the file/content from all commits
3. **Prevent recurrence** — `.gitignore`, pre-commit hooks, secret scanning

Adding the path to `.gitignore` is step 3, not step 1. Steps 1 and 2 must happen before any other remediation work begins, because history rewrite invalidates all branches.

### 2. Force pushes to shared branches require coordination protocol

**Rule**: Before force-pushing `main` or `staging`:
1. **Announce** in the team channel with 24-hour notice (or immediate if credential exposure requires urgency)
2. **List all open PRs and active branches** that will be affected
3. **Wait for acknowledgment** from all active contributors, or explicitly document who was not reachable
4. **Perform the force push**
5. **Post instructions** for rebasing/re-applying affected branches
6. **Verify** all open PRs are either closed, rebased, or re-opened against new history

### 3. Audit remediation plans must triage by blast radius, not just severity

**Rule**: When prioritizing audit findings, consider:
- **Immediate blast radius**: Does the fix itself invalidate other work? (History rewrites do.)
- **Dependency ordering**: Which fixes must happen first because other fixes depend on a stable base?
- **Coordination cost**: Which fixes require multi-person coordination?

A credential scrub is lower severity than auth guards in terms of runtime risk, but higher blast radius because it rewrites history. It should be sequenced first.

### 4. Branch lineage must be verified before opening PRs

**Rule**: Before opening a PR, verify:
```bash
git merge-base HEAD origin/main  # Should be recent, not the repo's first commit
git rev-list HEAD --not origin/main | wc -l  # Should be a small number (your commits)
```

If the merge base is older than your branch creation date, main's history has diverged. Do not open a PR — rebase first.

---

## Governance Rules

### GR-1: Secret Exposure Response Protocol

**Trigger**: Any credential, API key, or secret detected in git history.

**Response** (must be sequential):
1. Rotate the credential within 1 hour
2. Announce force-push to all contributors
3. Rewrite history to remove the secret
4. Force push with `--force-with-lease` (not `--force`)
5. Verify rotation by testing old credential fails
6. Post rebase instructions for all open branches

**Owner**: Whoever discovers the exposure. Escalate to repo admin if rotation requires dashboard access.

### GR-2: Force Push Announcement Protocol

**Trigger**: Any force push to `main`, `staging`, or any branch with open PRs.

**Requirements**:
- 24-hour advance notice (waived for active credential exposure — immediate notice instead)
- List of affected branches/PRs
- Rebase instructions
- Post-push verification that all PRs are remediated

**Enforcement**: Enable GitHub branch protection rule `Restrict force pushes` on `main` and `staging`. Only repo admins can force push after following the protocol.

### GR-3: Pre-PR Lineage Check

**Trigger**: Before creating any pull request.

**Check**:
```bash
# Verify branch is based on recent main
MERGE_BASE=$(git merge-base HEAD origin/main)
MAIN_HEAD=$(git rev-parse origin/main)
BEHIND=$(git rev-list $MERGE_BASE..$MAIN_HEAD --count)

if [ "$BEHIND" -gt 50 ]; then
  echo "WARNING: Branch is $BEHIND commits behind main. Rebase before PR."
fi
```

**Enforcement**: Can be added as a CI check or pre-push hook.

### GR-4: Credential Scanning

**Trigger**: Every commit (pre-commit hook) and every PR (CI check).

**Tools**: `git-secrets`, `detect-secrets`, or GitHub's built-in secret scanning.

**Rule**: PRs with detected secrets are auto-blocked. Commits with detected secrets are rejected by pre-commit hook.

---

## Implementation Checklist

- [ ] Enable `Restrict force pushes` on main and staging branch protection rules
- [ ] Add `detect-secrets` or equivalent to pre-commit hooks
- [ ] Add secret scanning CI step to `.github/workflows/ci.yml`
- [ ] Verify service role key has been rotated post-history-rewrite
- [ ] Add GR-3 lineage check to CI or document as team practice
- [ ] Share this document with all contributors (Brian, Kevin, agents)
