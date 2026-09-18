---
name: coordinate-codex-claude
description: Explicitly coordinate a task or ordered Issue batch through Codex design, automatic Claude implementation, and Codex review and completion. Use only when this skill is explicitly requested; ordinary coding, manual handoffs, and standalone reviews do not activate it.
---

# Coordinate Codex and Claude

Use one task record to carry an agreed outcome from Codex to Claude and back.
Codex owns significant decisions, design, independent review, and final
acceptance. Claude owns implementation, implementation-level choices, routine
corrections, and verification through a complete reviewable deliverable. The
task record is shared state, not a requirement for the user to relay messages.

## Invocation and dispatch

Activate only on explicit request for this skill. Once invoked, use automatic
dispatch and result collection, then have Codex review and finish the agreed
task. Route implementation corrections back to the same Claude session by
default. The user handles goals, material product decisions, and required approvals, not routine
message relay. Do not ask again for each already-authorized handoff.

Verify the execution route before implementation. If it is unavailable, resolve
what can be fixed within the authorized scope and report the remaining blocker.
Do not silently downgrade to manual relay or call a prepared file a completed
handoff. Manual relay is an exception only for a demonstrated unavoidable
limitation or an explicit user change of mode; record the reason. Routine
manual handoffs do not need this skill.

## Keep the process proportional

Treat one coherent user request as the default handoff unit, including multiple
Issues in a specified order. Normally Codex prepares the whole batch once,
Claude implements and verifies its items sequentially, and Codex reviews the
combined result and finishes it. Issue, test, and commit boundaries do not
require agent handoffs. Preserve useful per-item checks and semantic commits
when committing is authorized.

Add an intermediate Codex decision only when a concrete uncertainty could
invalidate dependent work, such as an unsettled shared API or schema design.
Resolve that uncertainty before dependent implementation; Claude can continue
independent items. Issue count or diff size alone is not a reason to split the
batch. A bounded investigation can settle an unfamiliar integration first.
Choose checkpoints by the rework they can avoid relative to coordination and
repeated-context costs; do not assume extra review cycles improve every metric.

Model selection belongs to the current client session. Follow the user's
current preference and actual account availability; do not pin model IDs,
effort, or tool permissions in this skill or the handoff template. Normally use
the user's strongest available model, with ordinary reasoning for bounded
Codex work and deeper reasoning for uncertain architecture, persistence,
security, or broad integration decisions. Claude follows its own effort
preference. Reconsider effort when the problem changes, not merely when the
diff is large. Do not imply that prompt wording changed a client setting.

## Reduce coordinator usage

Keep Codex work focused on decisions and independent acceptance. Delegate a
complete deliverable, including required captures or artifacts, checks, and
routine recovery. Inspect enough to define the outcome and constraints; leave
implementation discovery to Claude. During implementation, avoid duplicate
investigation, continuous diff review, or taking over routine tool errors.
Continue only useful work outside Claude's assigned scope.

Prefer completion/error notifications or bounded waits within the host's
responsiveness requirements. Inspect compact status when needed; read detailed
logs when a blocker, failed return, or review finding warrants it. Required user
updates do not require a new full-log read or implementation review each time.
A recoverable command error alone is not grounds to interrupt and take over.

Record available Codex usage-limit snapshots before preparation and after
completion, with timestamps, window/reset identity, and known concurrent tasks.
A dispatch-boundary snapshot is useful when cheaply available; do not poll
limits throughout the run. Compare the same window only, and report percentage
point changes as account-wide observations, not task-attributed consumption.
If snapshots are unavailable, a reset intervened, or other work overlaps, state
the limit of the evidence. Do not infer quota savings from delegated work or
raw token totals. Assess savings against a comparable baseline when available;
otherwise leave the efficiency conclusion open.

If reporting tokens, separate uncached input, cache creation/read, and output
using each provider's definitions. Prefer finalized usage; deduplicate message
IDs when reconstructing logs and label incomplete runs. Token totals and CLI
cost estimates are not subscription-limit consumption or a subscription bill.
Keep measurements in the private task record; do not copy account identifiers
or invent a fixed savings target.

## Establish the task record

Use an existing task handoff when provided. Otherwise create one `handoff.md`
in a user-designated private scratch location accessible to both sessions.
Start from [assets/handoff.md](assets/handoff.md); omit irrelevant fields.
Keep this task's decisions and current state there, and link code, contracts,
issues, and evidence instead of copying them. Do not put private handoffs into
a public product repository or mirror chat histories and automatic memories.

Record the actual repository, execution checkout, branch or detached HEAD,
base commit, and existing unrelated changes. Confirm these again on receipt:
Desktop clients may create their own worktrees. Do not infer the execution
path from the selected project name. If a dirty baseline cannot be separated,
resolve it or use an isolated checkout before implementation; never reset or
stash someone else's work to manufacture a clean baseline.

Use one active writer for the task record and one code writer per checkout.
The default is sequential ownership of the agreed task checkout. Before
passing ownership, stop that agent's edits and stateful verification. For
concurrent edits, use separate worktrees and branches; review the implementer's
actual diff. Worktrees do not isolate shared Xcode or Simulator state, so
serialize those operations too. Resume only after confirming the prior owner
is no longer writing; a status label alone is not a filesystem lock.

## Codex: prepare implementation

Inspect the current code and applicable contracts, then write:

- The observable outcome and concrete acceptance examples.
- The chosen design and why its important constraints exist; link durable
  decisions already documented elsewhere.
- Included work, excluded work, and implementation choices Claude can make.
- For a batch, the ordered items, dependencies, acceptance per item, and any
  necessary decision checkpoint. Keep them in the same task record.
- The smallest verification that proves per-item and combined acceptance,
  including relevant failure cases and the required tools or environments.
- Questions that would change the design and should return to Codex.
- Any final operation reserved for Codex because of tool access or authority;
  Claude should still complete its reviewable prerequisites.

Keep open product choices distinct from implementation details. Resolve
material uncertainty before authorizing dependent implementation, while
allowing independent work to continue. Existing user authorization carries
forward; the process does not require another approval for settled decisions.

Increment the brief revision when the agreed scope or design changes. Set
`Stage: implement` and `Next owner: Claude` only when the brief is actionable.
Start or resume Claude through the verified automated route with this skill,
the task-record path, and the recorded checkout. Explicitly include the shared
skill instructions in that task's request so Claude participates in the already
invoked workflow without relying on automatic skill discovery. Collect the
result directly for Codex review.

## Automated dispatch

Use a supported programmatic interface and verify the actual executable,
authentication, model, permissions, and required tools. Do not assume a
Desktop session's login, model selection, or app-provided tools automatically
carry over to an externally started process. Keep machine-specific routing
outside this portable skill, and preserve shared asset sources.

Bind each task to an explicit implementation session ID and checkout. Resume
that session for corrections; do not select an unrelated "most recent" session.
Set proportional time, usage, and invocation limits for the whole batch, rather
than assuming each Issue needs a separate call. Continuation after an execution
limit remains the same batch, not a mandatory per-Issue review. Return
control on authentication errors, permission denials, material product choices,
or exhausted limits, preserving partial work instead of retrying indefinitely.
An automatic run must not bypass approval controls or silently switch to a
separately billed provider to make progress.

Collect structured results and execution errors, confirm Claude has stopped
writing, then perform the same independent review below. The coordinator may
re-delegate grouped corrections when justified below, within the agreed limits.
State whether coordination requires an active Codex task; a skill or task record
alone does not provide a background runner or wake either client.

[references/automatic-dispatch.md](references/automatic-dispatch.md) documents
the bundled [runner](scripts/claude_runner.py): it checks the executable,
login, and flags, then executes a single bounded turn per call and returns a
structured result for review. The active Codex task coordinates completion.
Use this route after its preflight succeeds; do not substitute a manual handoff.

## Claude: implement and return

Read the current brief revision and repository contracts. Confirm the checkout
and baseline, then implement the agreed behavior using the relevant shared
domain skills when available. Runtime tool availability must be checked in
Claude; a shared skill does not supply Codex-only tools. Complete the ordered
batch without waiting for Codex review after each item unless the brief names a
necessary checkpoint or a material blocker arises. Track completed, partial, and
blocked items separately; verify their combined behavior before returning.

Resolve ordinary code details and recoverable command, capture, and check
failures independently within the agreed limits. Complete all requested
artifacts and verification before returning; a successful pilot does not
complete a brief that calls for full coverage. Return material deviations in
product behavior, public API, data/schema semantics, dependencies, or repository
scope to Codex, explaining the evidence and proposed change. Continue work
that does not depend on that decision. Do not rewrite the agreed brief to
retroactively approve a deviation.

Return the brief revision implemented, exact commit range or an identifiable
uncommitted diff, behavior changed, deviations, and checks actually run. In
automated dispatch, the runner captures the return and Git evidence; Codex
updates the shared task record after Claude releases write ownership. Include
per-item status, commands or tool capabilities, checkout/toolchain, results, and
evidence paths where they matter. Separate passed checks from unavailable or
skipped checks. For an uncommitted return, record HEAD, status,
tracked staged/unstaged patches and their hashes, and any untracked deliverable
files needed to identify the review input. Keep code frozen during review.

Return a reviewable result for Codex to record as `Stage: review` and
`Next owner: Codex`. For a design blocker, return the question and preserved
partial work for Codex to record as `Stage: design`.
Publishing and irreversible actions still require the applicable user
authorization; the handoff does not confer new permissions.

## Codex: review and close

Read the result as evidence to check, not as proof of correctness. Confirm the
brief revision and review input still match the checkout. Inspect the actual
diff and relevant surrounding code against acceptance and repository rules.
Check important failure paths and missing behavior, not only style. Reuse
credible checks for the same revision; rerun checks when code, environment,
or unresolved concerns justify it. Separate package tests, surface builds,
runtime/UI evidence, and release gates when those boundaries apply.

For findings, name the concrete behavior, code location, impact, and expected
correction. Group implementation and verification fixes into one request and
resume the same Claude session within the agreed limits, carrying only changed
requirements and relevant evidence. Codex reviews the returned correction and
owns final acceptance of every requested item and their integration.

Codex may make a small bounded correction when another handoff would cost more
than the fix and its verification, perform an explicitly reserved final action,
or take over when Claude is unavailable, cannot resolve a demonstrated blocker,
or has exhausted agreed limits. Record the concrete reason and remaining scope;
an isolated command error or the start of review is not enough. Stop the prior
writer before taking ownership, and preserve approval and verification gates.
Do not extend limits or reduce review quality merely to claim usage savings.

Record the final revision and outcome in the handoff; a later diff invalidates
that review until assessed. Set `Stage: done` only when acceptance is met,
stating any explicitly accepted limitations and remaining release steps.
Summarize actual work by agent, correction rounds or takeovers, and observed
usage-limit changes with attribution limits. When coordination overhead or
Codex reimplementation was substantial, identify the specific next adjustment
instead of claiming successful savings without comparative evidence.
Review acceptance is not itself permission to push, merge, or release.

Keep durable architecture decisions in their repository documents and private
cross-repository principles in their existing archive when recording them is
authorized. Link those sources from the task record; do not maintain parallel
copies of the rules in both clients.
