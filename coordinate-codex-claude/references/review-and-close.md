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

For findings, name the behavior or development-contract violation, code or
commit location, impact, governing source, and expected correction. For delegated
implementation, group implementation and verification fixes into one request
and resume the same Claude session within the agreed limits. For incoming work,
use its review entry's routing: Codex handles bounded adjustments and Claude
handles substantial rework. Carry changed requirements and relevant evidence,
then review the correction. Codex owns final acceptance in both entries.

In delegated implementation, Codex may make a small bounded correction when
another handoff would cost more than the fix and its verification, perform an
explicitly reserved final action,
or take over when Claude is unavailable, cannot resolve a demonstrated blocker,
or has exhausted agreed limits. Record the concrete reason and remaining scope;
an isolated command error or the start of review is not enough. In either entry,
stop the prior writer before taking ownership and preserve approval and
verification gates. Review authority alone does not authorize commits or history
rewrites; follow the incoming-review history safeguards whenever rewriting.
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
