# Delegated implementation

## Keep the process proportional

Treat one coherent user request as the default handoff unit, including multiple
Issues in a specified order. Normally Codex prepares the whole batch once,
Claude implements and verifies its items sequentially, and Codex reviews the
combined result and finishes it, including bounded final adjustments. Normally this needs one
implementation dispatch and return; substantial rework may justify one grouped
follow-up. More exchanges need a concrete remaining blocker and a revised plan,
not an automatic review loop. Issue, test, and commit boundaries do not
require agent handoffs. Preserve useful per-item checks and semantic commits
when committing is authorized.

Add an intermediate Codex decision only when a concrete uncertainty could
invalidate dependent work, such as an unsettled shared API or schema design.
Resolve that uncertainty before dependent implementation; Claude can continue
independent items. Issue count or diff size alone is not a reason to split the
batch. A bounded investigation can settle an unfamiliar integration first.
Choose checkpoints by the rework they can avoid relative to coordination and
repeated-context costs; do not assume extra review cycles improve every metric.

Normally use the user's strongest available Codex model; the current Astra
baseline is medium reasoning effort. The user's selection or expressed intent
at session start or in the current prompt takes precedence over this default,
including an explicitly chosen lower effort. Never downgrade the user's chosen
model or reasoning effort on your own to save usage or because work seems easy.

When a concrete quality need warrants deeper reasoning, increasing Codex's
reasoning effort is allowed unless the user explicitly fixed or capped it.
Explain the reason briefly and use a supported setting control if available;
do not claim prompt wording changed a client setting. If no such control is
available, state that limitation and request a user-side adjustment when needed.
Do not automatically change the selected model or revert an increased effort;
follow subsequent user direction.

For Claude delegation, use the rolling `opus` alias for the latest Opus and
fixed `high` effort. Pass `--model opus --effort high` on launch and resume.
Keep these settings independent of Codex's model and reasoning effort.

## Codex: prepare implementation

Inspect the current code and applicable contracts, then write:

- The observable outcome and concrete acceptance examples.
- The chosen design and why its important constraints exist; link durable
  decisions already documented elsewhere.
- Included work, excluded work, and implementation choices Claude can make.
- Relevant development contracts, principle sources, and commit conventions
  from [the common review](review-and-close.md). Name the required files and
  sections with a reason; distinguish initial reading from conditional references.
  Do not ask Claude to recursively read every linked skill or reference.
- For a batch, the ordered items, dependencies, acceptance per item, and any
  necessary decision checkpoint. Keep them in the same task record.
- The smallest verification that proves per-item and combined acceptance,
  including relevant failure cases and the required tools or environments.
- Questions that would change the design and should return to Codex.
- Any final operation reserved for Codex because of tool access or authority;
  Claude should still complete its reviewable prerequisites.

Keep the initial brief focused on decisions, acceptance, and affected boundaries.
Reuse already-known API changes and evidence paths rather than copying a full
release diff or asking Codex to duplicate all implementation discovery. Claude
can start from a changed-file/symbol inventory and expand only relevant hunks.
Include enough exact source evidence for safe implementation; a summary does not
replace checking the code that will actually change.

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
that session for immediate grouped rework; use a fresh session for new scope or
a long gap under the [runner session policy](automatic-dispatch.md#review-and-resume).
Keep the same task record and round limits; never select an unrelated "most recent" session.
Size time and usage limits for the whole batch, while counting the default
three Claude dispatches separately per Issue or agreed deliverable. A batch
does not require separate calls for each Issue. Continuation after an execution
limit remains the same batch, not a mandatory per-Issue review. Return
control on authentication errors, permission denials, material product choices,
or exhausted limits, preserving partial work instead of retrying indefinitely.
An automatic run must not bypass approval controls or silently switch to a
separately billed provider to make progress.

Collect structured results and execution errors, confirm Claude has stopped
writing, then perform [independent review](review-and-close.md). The coordinator may
re-delegate grouped corrections when justified below, within the agreed limits.
State whether coordination requires an active Codex task; a skill or task record
alone does not provide a background runner or wake either client.

[references/automatic-dispatch.md](automatic-dispatch.md) documents
the bundled [runner](../scripts/claude_runner.py): it checks the executable,
login, and flags, then executes a single bounded turn per call and returns a
structured result for review. The active Codex task coordinates completion.
Use this route after its preflight succeeds; do not substitute a manual handoff.

## Claude: implement and return

Read the current brief revision, applicable repository contracts, and the
specified relevant principle sections. Follow conditional references when their
trigger applies; a link is not a requirement to read its entire reference tree. Apply the common review criteria to your own work, including commit
messages and boundaries when committing is authorized. Confirm the checkout
and baseline, then implement the agreed behavior using the relevant shared
domain skills when available. Runtime tool availability must be checked in
Claude; a shared skill does not supply Codex-only tools. Complete the ordered
batch without waiting for Codex review after each item unless the brief names a
necessary checkpoint or a material blocker arises. Track completed, partial, and
blocked items separately; verify their combined behavior before returning.

Keep a short checkpoint at the runner-provided private path, separate from the
Codex-owned handoff. Update it after a coherent implementation milestone, a
verification phase, or a material blocker; do not write per tool call or ask
Codex to acknowledge it. Include the brief revision, completed behavior, checks
and evidence paths, remaining work, and blockers. Replace the complete contents with the Write tool; the runner grants that
specific file for the invocation. Do not require shell or rename permissions
just to save progress. An interrupted write may leave incomplete content;
verify it against the actual diff and evidence when resuming. It is partial self-report,
not acceptance or proof that Claude stopped writing. Do not duplicate transcripts.

Keep large command outputs in local artifacts. Return counts, relevant failures,
and evidence paths; inspect selected ranges when more detail is needed. A tool
truncating output or saving it to a file is not a reason to read that whole file
back. For broad diffs, start with names/statistics, then affected APIs and hunks.
Batch independent reads and searches when supported, but keep dependent edits,
stateful Xcode operations, and verification in their required order. Do not trade
away evidence, approval boundaries, or meaningful source context for fewer calls.

Run inexpensive repository format/rule checks early enough to fix routine
violations before final verification. For stateful changes, exercise relevant
next actions after invalidation, failure, or cancellation against the brief's
acceptance examples; avoid adding a universal exhaustive test checklist.

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
