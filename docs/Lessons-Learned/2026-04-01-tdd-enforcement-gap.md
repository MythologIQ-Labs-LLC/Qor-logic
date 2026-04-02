# Lesson Learned: TDD Not Enforced in Skill Prompts

**Date**: 2026-04-01
**Severity**: MEDIUM (quality + rework)
**Category**: Process, Skill Design, TDD

## What Happened

The `/ql-implement` skill mentions TDD-Light but doesn't enforce it structurally. During the Zo integration, tests were written alongside code (not before), and the substantiation pass found 6 gaps where wiring/integration was missing. The devil's advocate found 7 security issues that tests would have caught if written first.

## Root Cause

The TDD-Light step in `/ql-implement` says "create a minimal failing test before writing core logic" but:
1. No gate prevents implementation from proceeding without a test
2. The skill doesn't verify test existence before allowing code writes
3. Subagents launched for parallel implementation don't inherit the TDD mandate
4. CI configuration changes have no test analog

## Enforcement Changes Needed

### In `/ql-implement`:
- Step 5 (TDD-Light) must be a HARD GATE: implementation files cannot be created until a test file exists for them
- Each phase in the plan should list test files FIRST in affected files
- Subagent prompts must explicitly require "write the test first, then the implementation"

### In `/ql-plan`:
- Unit test descriptions should be BEFORE the changes section, not after
- Each phase should start with "Test files" then "Implementation files"

### In `/ql-repo-release`:
- Add "Local CI mirror" step: run exact CI commands locally before push
- Add "Cost estimate" step: calculate expected CI minutes before triggering
- Add "Single-push policy": batch all fixes, push once

### In `/ql-audit`:
- Add "TDD Evidence" pass: verify every new `.rs` file has a corresponding test
- Fail if implementation exists without test coverage

## Principle

**Write the tests before you write the code** is not a suggestion — it's a structural constraint. The test defines the contract. The implementation fulfills it. If you can't write the test, you don't understand the requirement well enough to implement it.
