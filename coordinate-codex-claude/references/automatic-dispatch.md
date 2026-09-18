# Automatic dispatch

Use `scripts/claude_runner.py` when an explicitly invoked workflow actually
needs Claude implementation or substantial incoming-review corrections. An
incoming review with bounded Codex fixes does not require runner preflight.
The active Codex task is the coordinator: it runs Claude, inspects the returned
code, returns grouped implementation findings to the same Claude session, and
accepts the final result. Correction ownership follows the selected entry in
the skill; incoming reviews permit bounded Codex adjustments. The helper makes
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
credential/provider environment variables stop execution. Authentication output
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
necessary dependencies; do not create a task directory or invocation per Issue.
The helper includes the current shared skill text in the request; no automatic skill discovery or user message relay is necessary.
Codex owns the task record and updates it from the automatically collected
result and Git evidence. Claude works in the specified checkout.

```sh
python3 <skill-root>/scripts/claude_runner.py run \
  --checkout <checkout> --task-dir <private-task-directory> \
  --request-file <private-request-file> \
  --model <currently-selected-model> --effort <selected-effort> \
  --permission-mode auto
```

Select the model and effort from the user's current preference and availability.
No model is fixed in the helper. Inspect the actual model and permission mode in
the result. If automatic permission review is unavailable, use the supported
`manual` mode with the smallest task-scoped `--allow-tool` grants, resolving real
approval needs through the coordinator's current controls. The default is
`manual`; unresolved prompts are denied rather than hanging. Never enable a
permission bypass or add permanent rules to make a run finish.

For a controlled test, `--tools` restricts built-in tools; `--mcp-config` together
with `--strict-mcp-config` can select only relevant MCP connections. These are
per-invocation choices. A disconnected MCP server or a permission denial is a
failed return, even when the CLI otherwise exits zero.

Defaults are 600 seconds, 20 agent turns and a CLI-estimated 3 USD ceiling per
invocation, with at most four invocations per task. These are protective defaults,
not a target number of review cycles or a mapping from Issues to calls. Size the
first call for the whole batch using `--timeout`, `--max-turns`,
`--max-budget-usd` and `--max-rounds`; keep any user-set caps. Costs are
CLI estimates, not a subscription bill or a guarantee about billing. The maximum
round count is fixed at first invocation; repeat the same value when resuming.
Failed attempted launches count too. There is no automatic retry.

## Wait without duplicating implementation

After dispatch, wait for completion or a material blocker using the host's
bounded wait or notification mechanism. Observe responsiveness requirements
without repeatedly loading stdout, screenshots, or partial diffs into Codex.
A compact process status is sufficient for routine progress updates. Investigate
detailed output on failure or evidence of a stall, rather than treating every
recoverable command error as a reason to interrupt Claude.

Record available usage-limit snapshots in the private handoff as described in
the skill. The runner's estimated cost and result token counts do not measure
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
Codex reviews every item and their integration. Group implementation findings
into one scoped correction request and call `run` with the same task directory
and checkout within the existing limits. Direct Codex fixes or takeover require
the bounded exception described in the skill. Include the current brief revision, changes since the
last return, and any Codex edits; link evidence rather than repeating transcripts.
The helper uses the saved session ID with `--resume`; it never uses the ambiguous
`--continue` option. If execution limits interrupt a batch, inspect the partial
result and resume the unfinished scope within the remaining limits, without
requiring a review handoff for each completed Issue. Once accepted, record the
final revision, verification and `Stage: done` in `handoff.md`.

The helper serializes its own processes through task and checkout locks. Other
editors and GUI sessions do not honor those locks. Shared Xcode/Simulator state
also needs coordination even across worktrees.

Timeout or interruption terminates the helper's child process group and retains
partial results. If the host itself crashes, verify that the previous process
is no longer writing before another call. The session and attempt count are
saved before launch. A failure before Claude creates that session may make
resume unavailable; retain the failed record, inspect partial work, and create
a new task record explicitly instead of rewriting the saved UUID. Do not evade
an exhausted review limit by silently starting new task records.

## Sources

- [Programmatic execution](https://code.claude.com/docs/en/headless)
- [CLI flags](https://code.claude.com/docs/en/cli-reference)
- [Authentication](https://code.claude.com/docs/en/authentication)
