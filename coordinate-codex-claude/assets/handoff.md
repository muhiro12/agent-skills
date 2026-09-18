# <Task name>

- Stage: design | implement | review | done
- Next owner: Codex | Claude
- Brief revision: <number>
- Updated: <date and time>
- Repository: <absolute path>
- Execution checkout: <actual absolute path; confirm after session start>
- Branch / base commit: <branch or detached HEAD / full SHA>
- Existing unrelated changes: <none or exact paths and ownership>
- Dispatch: automated
- Execution route: <verified executable or adapter reference>
- Implementation session: <explicit session ID; optional until started>
- Run limits: <per-call time/usage and maximum calls; sized for the whole batch>
- Session model / effort: <observed or user-reported; optional, not a selector>
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
<Link applicable repository contracts and durable decisions.>

### Verification

<Per-item and combined checks that prove acceptance; environment and evidence.>

### Return questions

<Material blockers or necessary intermediate decisions and the dependent work
they affect. Default: return once the whole batch is implemented and checked.>

## Implementation result — Claude

- Brief revision implemented: <number>
- Actual checkout and review input: <base..head SHAs, or HEAD and diff artifacts>
- Item coverage: <completed, partial, blocked items; update the table when present>
- Changes: <behavior and relevant paths>
- Deviations / questions: <none or evidence and proposed decision>
- Verification: <what ran, result, environment, evidence links>
- Not verified: <missing evidence and reason>
- Write ownership released: <edits and stateful verification stopped>

## Review and final result — Codex

- Reviewed input: <exact revision/diff and brief revision>
- Findings / disposition: <acceptance or grouped Claude corrections; direct Codex fixes and reason>
- Final adjustments and verification: <changes and evidence, if any>
- Final revision and outcome: <Codex acceptance of every item and their integration>
- Accepted limitations: <none or explicitly accepted remaining limitations>
- Remaining integration / release work: <only what applies>

## Usage and coordination evidence

- Codex limit snapshots: <before/after timestamps, used percentages, window and reset identity; unavailable if not exposed>
- Concurrent work / resets: <known overlap or reset; attribution limits>
- Observed change: <percentage points in the same account-wide window, not task-specific consumption>
- Agent work: <actual Claude and Codex scope; correction rounds and takeover reasons>
- Token evidence, if available: <provider definitions, cache/input/output breakdown, source and completeness>
- Efficiency assessment: <comparable baseline and result, or not established; concrete adjustment if warranted>
