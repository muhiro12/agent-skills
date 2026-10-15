# <Task name>

- Entry: delegated implementation
- Origin: <accepted Codex brief and any existing work included in its scope>
- Stage: design | implement | review | done
- Next owner: Codex | Claude
- Brief revision: <number>
- Refinement skill: <resolved path to refine-development-changes/SKILL.md; shared with Claude>
- Updated: <date and time>
- Repository: <absolute path>
- Execution checkout: <actual absolute path; confirm after session start>
- Branch / base commit: <branch or detached HEAD / full SHA>
- Existing unrelated changes: <none or exact paths and ownership>
- Dispatch: pending | automated | blocked
- Execution route: <verified executable or adapter reference>
- Implementation session: <explicit session ID; optional until started>
- Run limits: <effective time/turn/budget limits per invocation, sized for the batch; default maximum three calls per work item; inspect plan before dispatch>
- Work items: <stable IDs, assigned scope, attempts used, acceptance; link later user-requested follow-ups to accepted items>
- Codex model / effort: <user-selected baseline; observed or user-reported; actual quality-driven increases and reasons, if any>
- Claude model / effort: <actual launch flags and returned model; distinguish requested from observed settings>
- Reserved Codex operations: <none, or exact operation and tool/authority reason>

## Brief — Codex

### Outcome and acceptance

<Observable result, concrete success/failure examples, and scope boundaries.>

### Ordered work items (omit for a single item)

| Order / Issue | Outcome and acceptance | Depends on | Status / evidence |
| --- | --- | --- | --- |
| <item> | <observable result> | <item or none> | <pending / partial / implemented; evidence link> |

### Design and discretion

<Important decisions and rationale; choices Claude may make independently.>
<Name required contract/principle files and sections with their relevance.>
<Separate conditional references and their triggers; do not require recursive reading.>
<For broad release changes, list affected APIs/files and exact diff references.>

### Verification

<Per-item and combined checks that prove acceptance; environment and evidence.>

### Return questions

<Material blockers or necessary intermediate decisions and the dependent work
they affect. Default: return once the whole batch is implemented and checked.>

## Implementation result — Claude (omit if no dispatch)

- Brief revision implemented: <number>
- Actual checkout and review input: <base..head SHAs, or HEAD and diff artifacts>
- Item coverage: <completed, partial, blocked items; update the table when present>
- Changes: <behavior and relevant paths>
- Deviations / questions: <none or evidence and proposed decision>
- Verification: <what ran, result, environment, evidence links>
- Not verified: <missing evidence and reason>
- Write ownership released: <edits and stateful verification stopped>

## Review and final result — Codex

- Refinement input: <exact revision/diff and accepted brief revision>
- Refinement result: <result and evidence from refine-development-changes>
- Correction routing: <Codex adjustments, grouped Claude rework, or takeover; reason>
- Final revision and outcome: <Codex acceptance of every item and their integration>
- Accepted limitations: <none or explicitly accepted remaining limitations>
- Remaining integration / release work: <only what applies>

## Usage and coordination evidence

- Codex limit snapshots: <start / dispatch / Claude return / finish during initial evaluation; timestamps, used percentages, window/reset; unavailable boundaries omitted>
- Concurrent work / resets: <known overlap or reset; attribution limits>
- Observed change: <percentage points in the same account-wide window, account-wide; reasonable task approximation when no concurrent work is confirmed>
- Measurement phase: <initial workflow evaluation; revisit extra boundaries once established>
- Agent work: <actual Claude/Codex scope; launches/resumes, correction exchanges and reasons; distinguish internal tool turns from coordinator waits>
- Token evidence, if available: <provider definitions, cache/input/output breakdown, source and completeness>
- Efficiency assessment: <comparable baseline and result, or not established; concrete adjustment if warranted>
