# Research Brief

**Date**: 2026-09-11
**Analyst**: The Qor-logic Analyst
**Target**: the consumer-to-upstream issue-reporting channel -- its leak rate, its existing mechanisms, and whether it can carry execution evidence
**Scope**: measured failure rate of the live channel; what already exists to automate it; what identity it would carry; relationship to GH #463, #457 and Phase 242

---

## Executive Summary

The channel is live, informal, and has failed every time it was used. Seven
upstream reports from a consuming repository are open in this tracker and **all
seven** named that consumer in prose; all seven were anonymized by hand today.
That is a **100 percent leak rate** on a channel with no control at the point of
filing.

Two mechanisms already exist to automate this channel and **neither applies any
boundary check**. `create_shadow_issue` files GitHub issues from shadow events;
`collect_shadow_genomes` pools events across a configured fleet and files them to
a meta repository. Between them they would industrialize the leak.

An anonymization convention already exists in practice and is applied to exactly
one field. Thirty-two shadow events carry `issue_url` values of the form
`companion-line#108` -- a neutral placeholder -- while the issue bodies those same
cycles produced named the consumer outright. The convention lives in the
operator's head, is applied to the structured field, and is not applied to prose.

Phase 242's execution-evidence contract has a consumer and no producer. A
consuming repository running a governed cycle is the producer its plan specified.
The reporting channel is where that evidence would travel.

## Findings

### 1. The live channel leaks every time

Open issues in this tracker that originate from a consuming repository's cycle:
**#356, #357, #358, #359, #364, #365, #366**. Each carries consumer-report markers
in its body (`Consumer:`, `found while sealing a cycle in`, `alignment`), and each
named the consuming repository in prose until today's anonymization pass.

Seven of seven. There is no sample here in which the channel worked.

The failure is not carelessness. Each report is technically excellent -- they are
the source of several of this repository's better issues. The identity travels
because the context is the value: "found while sealing a cycle in X" is what makes
the report credible, and stripping it is work the reporter must remember to do at
the moment they are thinking about something else.

### 2. Two automated paths exist, and neither has a boundary control

`qor/scripts/create_shadow_issue.py` -- "Create a GitHub issue aggregating
unaddressed process shadow events." Builds a body with per-event details and files
it via `gh`. Boundary references in the module: **zero** -- no `scan_text`, no
`publication_boundary_lint`, no redaction.

`qor/scripts/collect_shadow_genomes.py` -- "Cross-repo Shadow Genome collector."
Reads `~/.qor/repos.json`, subprocesses `check_shadow_threshold` in each enabled
repository, pools unaddressed events, and files them against a meta repository.
Boundary references: **zero**.

Event `details` payloads routinely carry gate names, capability names, skill names
and free-text reasons written during a consumer's cycle. Nothing inspects them
before they become an issue body.

### 3. The fleet path is built and unconfigured here

`~/.qor/repos.json` does not exist on this host, so `collect_shadow_genomes` is
currently wired to nothing. The upstream reports in the tracker were therefore
filed by hand.

That is the more useful reading of the 100 percent leak rate: it is the failure
rate of a **human** doing this carefully, report by report, in a repository whose
doctrine they wrote. Automating the current shape would not introduce the defect;
it would reproduce it at machine speed.

### 4. The identity the automated path would carry

`qor/gates/schema/repos_config.schema.json` requires `path`, `name` and `enabled`
per repository. Both `path` and `name` are identifying, and `path` is a local
filesystem path -- the shape `publication_boundary_lint._ABS_PATH_RE` exists to
catch, and the shape that produced one of today's fourteen findings.

So the fleet configuration is a registry of exactly the identities the boundary
doctrine prohibits, feeding a collector that files issues upstream with no check.

### 5. The convention exists, applied to one field

Thirty-two unaddressed shadow events carry `issue_url` = `companion-line#108`,
plus three more at `#149`, `#150`, `#151`. `companion-line` is a neutral
placeholder, not a repository name. Someone anonymized the structured field
deliberately and consistently.

The same cycles produced issue bodies that named the consumer. One field was
treated as crossing the boundary and the other was not, and nothing in
`qor/references/doctrine-publication-boundary.md` documents either choice -- the
word `upstream` appears once in that file, in an unrelated sentence about
machine-authored dependency bumps.

An undocumented convention applied by hand to one of two fields is the most
fragile possible state: it looks like a policy from the inside and is invisible
from the outside.

### 6. The evidence producer Phase 242 specified already exists

`docs/plan-qor-phase242-governed-procedure-evidence.md:30` assigns evidence
production to "execution hosts / trusted wrappers". A consuming repository running
a governed Qor-logic cycle is precisely that: a separate trust domain, running the
gates, with its own artifacts.

The prior brief (#787) found the contract has a consumer and no producer and
concluded no such host exists. That conclusion was wrong in its premise -- the
hosts exist, they are simply not this repository. What is missing is not a host
but a **channel with a defined shape**, which is the subject of this brief.

### 7. One issue needs re-checking before it is cited

`validate_event_id` is called at `qor/scripts/create_shadow_issue.py:79` and
`:165`. GH #459 states it "ships, is tested, and is called from no production
path". That is not true of this module today. #459's second clause -- "the one
place it is needed returns success on a breached threshold" -- may still hold and
may be the real finding. Recorded as a correction to make, not as a closure.

## Blueprint Alignment

| Claim | Finding | Status |
|---|---|---|
| The upstream channel is informal but works | 7 of 7 reports leaked consumer identity | **DRIFT** |
| No execution host exists for Phase 242's producer half (#787) | Hosts exist; the channel lacks a shape | **DRIFT -- corrects #787** |
| Automated reporting would be a new risk | Both automated paths exist already, unguarded | **DRIFT** |
| An anonymization convention is in force | Applied to `issue_url`, not to bodies; undocumented | **DRIFT** |
| #459: `validate_event_id` has no production caller | Called at `:79` and `:165` | **DRIFT** |

## Recommendations

1. **P0 -- the skill's first contract is anonymization, not reporting.** A
   reporting skill whose tests assert report *shape* and treat boundary
   compliance as a later concern would ship the current defect with better
   formatting. The acceptance property is that a report naming its origin cannot
   be filed.
2. **P0 -- `create_shadow_issue` and `collect_shadow_genomes` are in scope.** They
   are the existing filing paths. A new skill beside them leaves two unguarded
   doors open, which is how the boundary lint ended up scanning tracked files
   while the GitHub surface accumulated thirty-six findings.
3. **P1 -- document the placeholder convention before mechanizing it.**
   `companion-line#N` is already load-bearing in thirty-five events. It belongs in
   `doctrine-publication-boundary.md` as a named form with a rule, so the skill
   implements a written convention rather than inventing a second one.
4. **P1 -- execution evidence rides the same channel, and should be the second
   phase, not the first.** The contract exists and is testable
   (`qor/compliance/procedure_evidence.py`); the value is real but it is the
   reason the channel is worth building well, not the reason to build it now.
5. **P2 -- correct or close #459 on the measured call sites** before it is cited
   in a plan.

## Updated Knowledge

For `qor/references/doctrine-publication-boundary.md`: the doctrine governs what
may enter this repository and says nothing about the act of reporting into it.
That omission is why a convention exists for one field and not the other. The
boundary is currently enforced at rest -- tracked files, and a nightly scan of a
surface already published -- and not at the moment of authorship, which is the
only moment at which the reporter still knows which details are identifying.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
