# Independent review and closure

## Common review: behavior and development practice

Review the work against current user instructions, applicable global and local
`AGENTS.md`, and the relevant current developer-principle records referenced by
those contracts. Carry portable source links and task-relevant constraints in
the brief so Claude can follow the same standards. Do not invent preferences
from agent identity or copy private principle archives into public repositories.
Current user instructions and hard repository rules take precedence.

Check these dimensions in proportion to the actual change:

- Behavior, failure cases, architecture and ownership boundaries, native platform
  guidance, source style, naming, and useful documentation.
- Required tools and verification evidence for the exact revision; distinguish
  observed behavior from inferred results and missing evidence.
- Scope and authorization, unrelated changes, temporary/generated artifacts,
  secrets and personal paths, and portability of public files.
- Each selected commit's full message and actual patch: factual description,
  applicable language and formatting conventions, and coherent work units.
  Where the active contract requires a single concise English sentence in
  present tense with no body or trailing period, enforce that exact contract.
  For uncommitted work, assess proposed commit units without inventing messages
  that have not yet been written. Check author/committer metadata and attribution
  against the applicable policy and existing history; never falsify authorship.

A successful build does not establish compliance with all these dimensions.
Report concrete violations with the governing source and practical correction;
distinguish mandatory rules from preferences and avoid cosmetic churn. When
workflow evidence is absent, mark it unverified instead of asserting misconduct.
Inspect individual commits as well as the final tree: material removed in a
later commit remains in the history proposed for publication.

## Codex: review and close

Read the result as evidence to check, not as proof of correctness. Confirm the
brief revision or reconstructed incoming scope and frozen review input still
match the checkout. Inspect the actual
diff and relevant surrounding code against acceptance and repository rules.
Check important failure paths and missing behavior, not only style. Reuse
credible checks for the same revision; rerun checks when code, environment,
or unresolved concerns justify it. Separate package tests, surface builds,
runtime/UI evidence, and release gates when those boundaries apply.

For findings, name the behavior or contract violation, code/commit location,
impact, governing source, and expected correction. In both entries, Codex handles
bounded final adjustments and their relevant verification after confirming the
prior writer has stopped. A new implementation exchange is not required for
small corrections, metadata, or a check Codex can complete directly.

For substantial rework or a change best handled with the implementer's detailed
context, group findings into one scoped follow-up using the same Claude session
within agreed limits. Carry changed requirements and evidence, then review the
returned correction. The normal target is one implementation exchange, with one
additional correction exchange if necessary. If another is needed, identify why
the prior cycle did not settle it and revise the remaining plan; do not silently
repeat a review loop or stop with required work unfinished.

Codex owns final acceptance and can take over when Claude is unavailable or has
exhausted agreed limits. State the remaining scope and reason. Preserve one
writer per checkout and all approval and verification gates. Review authority
does not authorize commits or history rewrites; follow the incoming-review
history safeguards whenever rewriting. Do not extend caps or weaken review
quality merely to claim usage savings.

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
