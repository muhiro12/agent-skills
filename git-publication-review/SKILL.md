---
name: git-publication-review
description: Audit and push Git changes to a public or potentially public repository. Use for publishing commits or checking whether they are safe to push; resolve destination visibility and outgoing history, then push when the audit passes. Honor explicit review-only or no-push requests.
---

# Git Publication Review

Complete publication of the intended commits, with a mandatory pre-push audit.
Use the current request and repository contract; require no personal archive,
sibling skill, particular Git host, or owner-specific policy. Tool access and
credentials belong to the active environment, not this skill.

## Invocation and Intent

Invoking this workflow explicitly, or asking in natural language to publish or
check whether commits are safe to push, means audit and then push if the gate
passes. Do not stop at a favorable report or ask again for routine push approval.
An explicit review-only, no-push, or dry-run constraint overrides this default.
Mere discussion, explanation, or editing of this skill does not request a push.
Automatic skill selection alone must not expand an unrelated task into publishing.

This is an agent workflow with a pre-push gate, not an installed Git hook. Do not
install hooks, alter global Git settings, or imply that every external push is
protected. Preserve active tool permissions and repository requirements.

## Establish the Publication Boundary

- Resolve the repository, worktree/index state, intended source revision and
  destination repository/ref. Inspect push URLs and applicable refspecs; do not
  assume `origin`, the fetch URL, or the upstream is the push destination.
  Account for multiple destinations or refs when they are actually in scope.
- Determine destination visibility from current host metadata or a verified
  repository settings surface when available. Record the source and observation
  time. A remote URL, successful authentication, local visibility cache, or
  failed unauthenticated request does not establish public/private status.
  Distinguish public, private, internal/restricted, and unknown.
- Honor intended future publication even if the destination is currently
  private. If visibility cannot be established, continue content inspection
  under an explicitly stated public-exposure assumption, but leave destination
  confirmation unresolved. Ask only when target ambiguity prevents selecting
  the relevant history or giving the requested conclusion.
- Compare against freshly observed destination refs using available read-only
  host/Git access. Local remote-tracking refs may be stale. Record immutable
  source and destination object IDs and the reviewed commit set. A branch diff
  alone is not the full set of content introduced by a push.
- Inspect every newly reachable commit, including merged side histories, and
  its relevant tree content. For a new destination or a change from private to
  public, review the full reachable history in scope; do not substitute a
  recent release range. Identify additional refs, LFS objects, submodules, or
  host artifacts whose disclosure is outside the inspected Git content.
  A visibility change can expose existing issues, releases, and other host
  content too; Git review alone cannot clear that operation.
- Keep uncommitted and untracked proposed additions separate from committed
  outgoing history. They are not sent by pushing existing commits. Ignored
  private directories are not a reason to inspect unrelated local data.

## Inspect What Will Be Exposed

Review the final content and intermediate history; a later deletion does not
remove a secret or private file from an earlier outgoing commit. Use bounded
inventories and available scanners as aids, then inspect relevant context.
Do not execute repository code merely to scan it or send material to an external
scanner without authorization.

Check for credentials and authentication material, private personal/customer
information, internal endpoints and documents, machine-specific paths or
configuration, real identifiers in examples, generated reports/logs/media,
and unexpected large or binary artifacts. Inspect commit messages, author and
committer metadata, and annotated tag messages where in scope. An email address
or identifier is not automatically a leak: distinguish intended public identity
and documented public examples from unintended disclosure. Never change identity
or invent a universal naming, language, or commit-format policy.

Consider whether third-party source or assets have an evident publication
restriction or missing attribution; report concrete uncertainty instead of
claiming a legal clearance. Flag uninspected binary/LFS content and truncated
history as coverage gaps, not clean results. Avoid echoing sensitive values in
commands, logs, or reports; cite the commit and path with a redacted explanation.

Keep exposure findings separate from code correctness, verification, and release
readiness. Reuse trustworthy verification for the same revision and relevant
repository requirements. Run appropriate checks if the requested readiness
assessment needs them, including required repository pre-push checks. Missing
build evidence does not by itself prove a leak, but an unmet required check
prevents declaring the push gate passed.
Other skills can provide evidence when available, but are not prerequisites.

## Push After the Gate Passes

Push when the intended destination/ref and audience are established, the outgoing
content has been inspected, no publication blocker remains, and required
repository checks have passed or have an explicitly accepted exception. No
findings is not the same as no audit: unresolved visibility, incomplete relevant
history, or uninspected outgoing artifacts leave the gate incomplete. Finish
available checks and ask only for a material missing decision or permission.
If the destination already contains the intended commits, report up to date.

Before pushing, recheck the source object ID and destination ref. If either
changed, reassess the affected range; never publish unreviewed replacement
commits. Use an explicit reviewed source object ID and destination refspec,
limited to the selected destination. Avoid defaults that push other branches,
follow tags, mirror refs, or recursively push submodules. Account for LFS content
and existing hook side effects before invoking the command; do not bypass hooks.

Use a normal fast-forward push (or create the intended new ref). A rejection is
not permission to force, merge, rebase, or rewrite history. If such work is needed,
explain the concrete conflict and proceed only within existing authorization.
Do not stage or commit unrelated working-tree content just to enable a push.

After the command, read the destination ref back and confirm it points to the
reviewed source object ID. If the response is ambiguous, inspect remote state
before retrying. If multiple explicitly selected refs/destinations are involved,
report success and failure separately; do not claim an atomic operation across
destinations or roll back completed writes automatically. A later remote change
must be reported instead of being overwritten to reproduce the expected state.

## Report and Handle Blockers

Lead with pushed and verified, already up to date, blocked, or review-only.
Include the destination/ref, visibility evidence, reviewed and published object
IDs, checks performed, remaining findings, and relevant exclusions. Keep pending
uncommitted additions separate. A successful command without remote read-back
is not verified completion. A clean scanner result is not a safety guarantee.

If a blocker remains, do not push. Cite safe commit/path references and the
necessary correction without echoing sensitive values. When fixes are also
requested, perform authorized ordinary edits and re-review. If sensitive material
remains in history, explain why a new deletion commit is insufficient. Establish
which refs are already shared before any separately authorized history rewrite.
Recommend credential revocation/rotation separately when exposure may already
have occurred. The default push intent does not authorize destructive rewrites,
force pushes, ref deletion, visibility changes, or credential operations.
