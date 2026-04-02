# Lesson Learned: Alpha Release CI Waste

**Date**: 2026-04-01
**Severity**: HIGH (cost + time)
**Category**: Release Process, CI/CD, TDD

## What Happened

The alpha release required ~12 CI iterations and ~5 release build attempts before all checks passed. Each iteration burned 30-60 minutes of GitHub Actions compute. Estimated total: **660 minutes** (~33% of monthly free tier).

## Root Causes

### 1. No local CI parity
Clippy, cargo audit, and tests were not run with the same flags locally as CI uses. CI had `-D warnings` (RUSTFLAGS), newer Rust (1.94 vs local), and different platform targets (macOS/Linux). Errors that passed locally failed on CI.

### 2. Premature tagging
Tag `v5.0.0-alpha.2` was pushed before CI passed on the PR. This triggered broken release builds that wasted ~300 minutes. The correct order is: PR green → merge → tag → release.

### 3. Fix-push-wait anti-pattern
Each fix was pushed individually, triggering a full 3-platform CI run (~15 min wait) for a 1-line change. Fixes should be batched: run clippy locally with CI flags, fix ALL issues, push once.

### 4. No TDD for CI configuration
Workflow YAML changes were written without testing. There's no local equivalent of "run the CI workflow" — but the individual steps (cargo test, cargo clippy, cargo audit) can all be run locally first.

### 5. Release workflow not validated
The release workflow had never been tested:
- `cargo-tauri` vs `tauri-cli` crate name
- MSI version format requirements (no alpha/beta strings)
- macOS icon requirements (specific PNG sizes + .icns)
- Bundle output path differences across platforms
- `macos-13` runner deprecation

## Enforcement Rules

### Before pushing ANY code to CI:
1. `cargo clippy --workspace -p <our-crates> -- -D warnings`
2. `cargo test --workspace --lib --exclude <vendor>`
3. `cargo audit --deny yanked`
4. Verify all files under 250 lines: `find crates/*/src -name "*.rs" | xargs wc -l | awk '$1 > 250'`

### Before tagging a release:
1. ALL PR checks must be green
2. PR must be merged to master
3. Release workflow must be triggered manually (workflow_dispatch)
4. Never tag before merge

### Before modifying CI workflows:
1. Run every CI step command locally first
2. Batch all fixes into one commit
3. Test with `act` (local GitHub Actions runner) if available

## TDD Mandate

**Write the tests before you write the code.** This applies to:
- Rust code (unit tests before implementation)
- CI configuration (run commands locally before pushing)
- Release workflows (validate each step manually before automating)
- Infrastructure (test Worker endpoints before deploying)

If a test can't be written first, the design isn't clear enough to implement.

## Cost Prevention

Future `/ql-repo-release` must include:
- Estimated CI cost for the release pipeline
- Local pre-flight checklist that mirrors CI exactly
- Single-push policy: all fixes batched before triggering CI
- Release dry-run step before tagging
