# Research Brief

**Date**: 2026-08-11
**Analyst**: The Qor-logic Analyst
**Target**: GH #314 (rescoped) -- the installed skill corpus can diverge from the repo, undetected
**Scope**: Why the existing check did not fire, what it proves about local gate evidence, and what a seal currently omits

---

## Executive Summary

**27 of 30 skills currently differ between this repository and the operator's installed copies.** The detection tool for exactly this condition has existed since Phase 32, works correctly, and did not fire -- because it is wired at the wrong scope, in the wrong phase, and cannot block.

The consequence is larger than stale files. Every gate observation made locally this session was produced by skills that are not the skills under version control. GH #314 was filed against the repository on the strength of text that exists only in the installed copy; the repo never contained it. That issue is the first known instance of this defect causing a false governance finding, and it will not be the last, because nothing distinguishes the two sources at the point of use.

## Findings

### 1. The check exists and is correct

`qor/scripts/install_drift_check.py` (Phase 32) does byte-identical SHA256 comparison between `qor/skills/**/SKILL.md` and the installed counterpart under the host's skills directory. Run against the operator's actual install:

```
$ python -m qor.scripts.install_drift_check --host claude --scope global
  - SHA256 mismatch: qor/skills/sdlc/qor-plan/SKILL.md differs from <host-skills-dir>/qor-plan/SKILL.md
  ... 27 findings ...
  rc=1
```

27 findings against 30 source skills. The tool is not the problem.

### 2. Three wiring defects, each sufficient alone

The only invocation anywhere in the skill corpus is `qor-plan/SKILL.md:125`:

```bash
qor-logic scripts install_drift_check --host claude --scope repo || \
  echo "WARNING: Local skill install differs from repo source. ..."
```

- **Wrong scope, producing pure noise.** It checks `--scope repo` (`<repo>/.claude/skills/`), a directory that does not exist here. The operator's install is `--scope global`. So every run emits **30 findings -- one "missing install" per source skill -- all of them expected and none of them meaningful**, while the 27 real global-scope mismatches go unexamined. This is worse than a silent check: it is a control that cries wolf on every invocation, guaranteeing the operator learns to ignore it. Alarm fatigue by construction.
- **Cannot block.** `|| echo` collapses all 30 findings into one WARNING line. Nothing downstream reads it, and no artifact records that it fired.
- **Wrong phase.** It runs at `/qor-plan` only. Drift introduced after planning -- or present the whole time, as here -- is never re-examined before the seal that depends on it.

The three compound: a check pointed at an unused scope produces guaranteed-irrelevant output, which is then suppressed to a single ignorable line, at a phase that does not gate anything. Correcting any one alone leaves it inert.

Each defect independently defeats the control. Together they make it decorative.

### 3. The installed corpus violates the repo's own limits

| | repo | installed |
|---|---|---|
| `qor-substantiate/SKILL.md` | 39,623 B | **40,512 B** |
| differing lines | -- | 204 |
| `instruction_hygiene_lint` references | 0 | 3 |

40,512 bytes is over the 40,000-byte EXCEEDED ceiling **and** over the 39,936-byte headroom lock that `tests/test_substantiate_staging_gates.py` enforces on every CI run. The repository proves a property about a file the operator does not execute.

Phase 215 spent an entire governed cycle recovering 1,027 and 760 bytes to stay under that lock. The skill actually running seals was over it the whole time.

### 4. This invalidates local gate evidence

The correction on #314 is the general case, not a one-off. When a gate is observed locally, the observation is about the installed skill. Attributing it to the repository is a category error, and nothing at the point of observation signals which source is in play.

This has a precedent worth naming: Phase 209 defended a fix with twelve local passes from a host structurally incapable of exhibiting the bug, which made the evidence not weak but absent. Same failure shape, different axis -- there the host could not produce the signal, here the artifact under test is not the artifact under governance.

### 5. A seal records nothing about the skills that produced it

`substantiate.schema.json` and `seal_artifacts.py` contain no skill-corpus digest, hash, or version. A SESSION SEAL entry establishes what the plan promised, what the tests proved, and what the ledger chains -- but not which ceremony executed.

Two seals with identical entries could have been produced by materially different skill corpora, and the ledger cannot tell them apart. For an artifact whose purpose is proving Reality matched Promise, the procedure that did the proving is unrecorded.

This is the gap that makes the other three findings compounding rather than merely annoying: there is no forensic trail. Nothing in 540 sealed entries answers "which skills ran this seal?"

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| Install drift is detected | tool exists, works, finds 27/30 | MATCH |
| Detection is wired into the lifecycle | one call; wrong scope emits 30 irrelevant findings; WARN-only; plan-phase only | **DRIFT** |
| Local gate runs evidence repo behavior | 27/30 skills differ; #314 filed on installed-only text | **DRIFT** |
| Seals identify their own ceremony | no skill-corpus digest anywhere | **DRIFT** |
| The 39,936 lock governs what executes | installed copy is 40,512 B | **DRIFT** |

## Recommendations

1. **Check the scope the operator actually uses.** Resolve scope from host config, or check every scope that has an install and report an absent scope as "not installed here" rather than as 30 individual defects. A check whose default output is 30 irrelevant findings trains the operator to ignore it, which is how a correct tool becomes decorative.
2. **Move the check to the seal and make it recorded.** Whether it ABORTs or discloses is a judgment call for the plan; that it must appear in the seal entry is not. A seal produced by a drifted corpus should say so.
3. **Record a skill-corpus digest in the seal entry.** One hash over the installed `SKILL.md` set makes every seal attributable to the ceremony that produced it, and makes drift retroactively visible across the ledger.
4. **Do not fix by reinstalling and moving on.** The reinstall clears today's drift and leaves the detection gap intact. The defect is that nothing noticed for 27 skills.
5. **Treat the #314 correction as the motivating test case.** Any remedy should be evaluated against it: would this have prevented a governance finding filed against the repo on the strength of installed-only text?

## Updated Knowledge

`docs/SHADOW_GENOME.md` warrants an entry: a control that exists, is correct, and is wired so it cannot fire -- distinct from `SG-HalfSealedClaim-A` (prerequisite genuinely absent) and from the #319 family (claim with no checker at all). Here the checker exists and was rendered inert by scope, posture, and placement. Suggested `SG-InertControl-A`.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
