# Automatic dispatch

Use `scripts/claude_runner.py` when an explicitly invoked workflow actually
needs Claude implementation or substantial incoming-review corrections. An
incoming review with bounded Codex fixes does not require runner preflight.
The active Codex task is the coordinator: it runs Claude, inspects the returned
code, makes bounded final adjustments, and accepts the result. Substantial
rework can return as one grouped request using the session policy below. The helper makes
one bounded implementation call; it neither calls a second Codex model nor
provides a daemon, scheduler, or a wake-up mechanism after Codex finishes.

For incoming work created outside this runner, do not fabricate a saved runner
state or replace its session UUID with an external session ID. Resume only a
matching runner-managed task whose identity and checkout have been verified.
Otherwise create a new bounded correction task with the exact incoming diff,
user outcome, development constraints, and grouped findings. This is a new
implementation session, not a resumption of the original author's session.

## Resolve the runtime

```sh
python3 <skill-root>/scripts/claude_runner.py probe --checkout <checkout>
```

The helper uses an explicit `--claude-bin` first, then `claude` on PATH, then the
newest numeric macOS Desktop runtime under the current user's Application
Support directory. Desktop discovery is a local compatibility adapter, not a
vendor-guaranteed installation path. It never installs a CLI or falls back to
an older version on failure. Inspect `probe` before proceeding after an update.
`--max-turns` is documented but may be absent from the CLI's visible help.

Only a logged-in first-party `claude.ai` subscription is accepted. Alternate
credential/provider environment variables stop execution before any CLI probe.
The exact value `https://api.anthropic.com` is accepted for
`ANTHROPIC_BASE_URL` and `ANTHROPIC_API_URL`, including when inherited from
Desktop. Other values (including URL suffixes) remain refused; an official URL
does not exempt API keys, custom headers, or alternate-provider flags. Values
are neither logged nor rewritten, and subscription authentication is still checked.
Authentication output
is restricted to login state, method, provider and subscription type. The helper
does not read or copy credential stores. A successful login does not establish
that the account has remaining model usage; quota errors are implementation
failures and keep the partial artifacts.

## Prepare and run

Choose an idle Git checkout and a private task directory outside it. Inspect
the checkout's Claude configuration before the first run: ordinary `-p` loads
hooks and MCP servers without a workspace trust dialog. This workflow retains
shared skills and instructions, so it intentionally does not use `--bare`, which
also skips subscription login. Do not run two editors on the same checkout.

Write the whole batch brief into one `handoff.md` and the current bounded request
into a file in the task directory. Include ordered Issues, their acceptance and
necessary dependencies, and named must-read sections versus conditional references; do not create a task directory or invocation per Issue.
The helper includes the current shared skill text in the request; no automatic skill discovery or user message relay is necessary.
Codex owns the task record and updates it from the automatically collected
result and Git evidence. Claude works in the specified checkout.

```sh
python3 <skill-root>/scripts/claude_runner.py run \
  --checkout <checkout> --task-dir <private-task-directory> \
  --request-file <private-request-file> \
  --model opus --effort high \
  --permission-mode auto
```

The flags above select Claude only; they do not change Codex or Desktop settings.
Use the same model and effort flags on resume. Record the requested alias and
returned model separately; a resolved model ID does not pin future runs.
Do not claim effective effort is verified when the CLI does not report it.
Inspect the actual
permission mode in the result. If automatic permission review is unavailable,
use the supported `manual` mode with the smallest task-scoped `--allow-tool` grants, resolving real
approval needs through the coordinator's current controls. The runner supplies
`--add-dir <task-dir>` for the private task records and an exact absolute-path
`Edit` allow rule for this round's `checkpoint.md`. This covers the Write tool too;
path-qualified `Write(...)` rules are not consulted by Claude Code.
Directory access and tool approval are separate requirements; neither substitutes for the other. The
checkpoint grant is invocation-local, not a blanket Write grant or a change to
client settings. It does not authorize editing the handoff, logs, or runner state;
existing broader user grants remain in effect. Deny/ask rules still take
precedence. Paths containing permission-pattern metacharacters are refused
rather than accidentally broadening the rule. Source changes and other task
operations still need their own scoped grants or automatic approval. The default is
`manual`; unresolved prompts are denied rather than hanging. Never enable a
permission bypass or add permanent rules to make a run finish.

For a controlled test, `--tools` restricts built-in tools; `--mcp-config` together
with `--strict-mcp-config` can select only relevant MCP connections. These are
per-invocation choices. A disconnected MCP server or a permission denial is a
failed return, even when the CLI otherwise exits zero.

For a new task, protective defaults are 600 seconds, 20 agent turns and a
CLI-estimated 3 USD ceiling per invocation, with at most three invocations per work item. These are protective defaults,
not a target number of review cycles or a mapping from Issues to calls. Size the
first call for the whole batch using `--timeout`, `--max-turns`,
`--max-budget-usd` and `--max-rounds`; keep any user-set caps. Costs are
CLI estimates, not a subscription bill or a guarantee about billing. On resume, omitted time, turn, and budget flags inherit the previous invocation's
recorded effective limits; explicit flags override them. The per-item maximum
is fixed at first invocation and can be omitted on resume. Older task records
inherit from the previous round summary. Missing or invalid saved limits cause a
refusal instead of silently reverting to smoke-test defaults. Failed attempted
launches count too. There is no automatic retry.

Count work items independently of the conversation, session UUID, and total
launch count. Pass a stable `--work-item issue-a` on both `plan` and `run`;
repeat it for each item actually assigned in a batched call. A call covering
A/B/C consumes one attempt for each; a correction covering only A consumes only
A's next attempt. Codex review, edits, waits, and Claude's internal tool turns
consume none. Failed attempted launches still consume an attempt for each
assigned item. Three independent items can therefore use nine calls in total,
although one combined implementation call is preferred when appropriate.

Record acceptance per item. A later user request for additional adjustment of
accepted A gets a new identifier such as `issue-a-followup-1` and three fresh
attempts; record the request and link the accepted item in the handoff. An
unfinished correction keeps its identifier. New scope also uses `--new-session`.
Changing the UUID or waiting an hour never resets an item's counter. Omitted
`--work-item` repeats the previous selection, or uses one default item initially.
Legacy records without item counters remain one item with their saved cap and
attempt count; do not invent per-Issue historical attribution. For a new user
request after accepting legacy work, start a linked new record with the current
default cap. Preserve the old record as evidence.

Before dispatch or resume, inspect the read-only execution plan with the intended
limit overrides (if any):

```sh
python3 <skill-root>/scripts/claude_runner.py plan \
  --checkout <checkout> --task-dir <private-task-directory>
```

`plan` does not probe or run Claude, read its stream, or create a task/round.
It reports effective limits and their source, the previous result subtype and
process status, finish/idle time when recorded, and checkpoint metadata. Repeat
selected overrides on `run`; the plan does not save them. Result subtype alone
is not acceptance or proof that quota is available. Check the actual return on
failure, even when a provider labels it successful. Checkpoint age/size cannot
prove it reflects current progress; compare it with the actual Git evidence on
resumption. Legacy finish times can be unavailable. Do not infer a cache-expiry
threshold or subscription balance from these fields, and do not enlarge caps
automatically. Record initial limits for the complete intended deliverable.

## Wait without duplicating implementation

After dispatch, wait for completion or a material blocker using the host's
bounded wait or notification mechanism. Observe responsiveness requirements
without repeatedly loading stdout, screenshots, or partial diffs into Codex.
Use the longest wait allowed by the host's responsiveness requirements. If a
routine update needs metadata, use this command instead of reading the stream:

```sh
python3 <skill-root>/scripts/claude_runner.py status --task-dir <private-task-directory>
```

It reads only persisted runner metadata and checkpoint existence/mtime; it does
not start Claude, load logs, or prove process liveness. Do not repeatedly poll it
when the host already reports the process running. A recorded running state can
be stale after a host crash. Verify ownership before any takeover. Investigate
detailed output on failure or evidence of a stall, rather than treating every
recoverable command error as a reason to interrupt Claude.

Claude replaces `rounds/<round>/checkpoint.md` with the Write tool at meaningful
milestones. No Bash or rename permission is required for this record.
Codex continues waiting without reading or acknowledging each save.
On interruption or resumption, read the latest available checkpoint with the Git
evidence; it can be missing, incomplete, or stale and never replaces final review.
This separate file preserves one writer per record. No checkpoint watcher, daemon,
or background wake-up mechanism is introduced.

Capture Claude usage at dispatch and return in the private handoff as described in
[usage and waiting](usage-and-waiting.md). The runner's estimated cost and result token counts do not measure
Codex subscription-limit consumption. A missing final result after interruption
must remain visible; partial streaming usage is not a finalized token total.

## Review and resume

`runner-state.json` binds the task directory, checkout and explicit session UUID.
Each numbered `rounds/` directory contains the prompt, stdout JSONL, stderr,
summary, before/after Git snapshots and staged/unstaged patches. Ordinary
untracked files are identified by hashes, with recorded size/count limits.
Keep these private. The helper writes no product-repository process documents.

Read `summary.json`, the final result and actual Git diff. Successful transport
means implementation returned; it does not mean Codex accepted the behavior.
Codex reviews every item and their integration. Complete bounded final adjustments in Codex. For substantial rework, group
findings into one correction request and call `run` with the same task directory
and checkout within the existing limits. Include the current brief revision, changes since the
last return, and any Codex edits; link evidence rather than repeating transcripts.
For a new work scope, add `--new-session` to both `plan` and `run`. Otherwise the
helper resumes the saved UUID when less than one hour has passed since the
previous round finished, and starts a fresh UUID after that gap. The finish time
is an operational proxy for last model activity, not proof of cache validity;
never measure from the start of a long-running round. For older records without
a finish time, inspect the handoff and use `--new-session` if the gap is unknown
or long. Immediate grouped corrections can resume. The helper never uses the
ambiguous `--continue` option.

Before a fresh session, update the handoff and include its path and the previous
checkpoint path in the current request, together with remaining work, decisions,
and relevant evidence. Inspect stale or missing checkpoints against the actual
work first. Do not copy the entire transcript. A new UUID retains the task
directory, item counters, inherited limits, and all previous round evidence; it
does not reset the maximum calls. `plan` reports the selection before execution.

If execution limits interrupt a batch, inspect the partial
result and continue the unfinished scope within the remaining limits, without
requiring a review handoff for each completed Issue. Once accepted, record the
final revision, verification and `Stage: done` in `handoff.md`.

The helper serializes its own processes through task and checkout locks. Other
editors and GUI sessions do not honor those locks. Shared Xcode/Simulator state
also needs coordination even across worktrees.

Timeout or interruption terminates the helper's child process group and retains
partial results. If the host itself crashes, verify that the previous process
is no longer writing before another call. The session and attempt count are
saved before launch. A failure before Claude creates that session may make
resume unavailable; retain the failed record, inspect partial work, and use
`--new-session` within the same task instead of manually rewriting its UUID. Do not evade
an exhausted item limit by renaming unfinished work or starting new task records.
At the limit, Codex finishes the remaining work after taking ownership, or
reports the concrete blocker; do not abandon the requested deliverable.

## Sources

- [Programmatic execution](https://code.claude.com/docs/en/headless)
- [CLI flags](https://code.claude.com/docs/en/cli-reference)
- [Permission rules and working directories](https://code.claude.com/docs/en/permissions)
- [Authentication](https://code.claude.com/docs/en/authentication)
- [Prompt caching and cache lifetime](https://code.claude.com/docs/en/prompt-caching)
