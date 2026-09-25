# Coordination usage and waiting

## Reduce coordinator usage

Apply delegation guidance when Claude is actually assigned work; an incoming
review does not need a delegation cycle solely to use this skill.

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
Use the longest host-permitted responsive wait, not short sleeps followed by
repeated log parsing. An unchanged status needs no new investigation. Read
Claude's checkpoint on a failed return, a material blocker, or resumption, not
at every update; saving progress does not require a coordinator acknowledgement.

Record available Codex usage-limit snapshots before preparation and after
completion, with timestamps, window/reset identity, and known concurrent tasks.
During initial workflow evaluation, also capture dispatch and Claude-return
boundaries when cheaply available, before Codex starts corrections or takeover.
Record preparation, waiting/review, and takeover scope separately. These are
boundary observations, not continuous polling or a permanent acceptance gate;
reconsider the extra measurements once the workflow is established. Compare the
same window only and label percentage-point changes as account-wide measurements.
If the user confirms no concurrent work, treat the observed increase as a
reasonable approximation of this task's consumption, while retaining the
account-level measurement label. If snapshots are unavailable, a reset
intervened, or other work overlaps, state the limit of the evidence. Do not infer quota savings from delegated work or
raw token totals. Assess savings against a comparable baseline when available;
otherwise leave the efficiency conclusion open.

If reporting tokens, separate uncached input, cache creation/read, and output
using each provider's definitions. Prefer finalized usage; deduplicate message
IDs when reconstructing logs and label incomplete runs. Token totals and CLI
cost estimates are not subscription-limit consumption or a subscription bill.
Keep measurements in the private task record; do not copy account identifiers
or invent a fixed savings target.
