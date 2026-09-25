---
name: git-publication-review
description: Review Git changes for publication to a public or potentially public repository. Resolve destination visibility and outgoing history, inspect disclosure risks, and report whether the selected content is suitable to publish; a review request does not authorize pushing.
---

# Git Publication Review

Assess the content that would become accessible at the intended destination.
Use the current request and repository contract; require no personal archive,
sibling skill, particular Git host, or owner-specific policy. Tool access and
credentials belong to the active environment, not this skill.

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
assessment needs them; missing build evidence does not by itself prove a leak.
Other skills can provide evidence when available, but are not prerequisites.

## Report and Follow Through

Lead with whether the reviewed content has a publication blocker, no identified
blocker within the stated coverage, or an unresolved boundary. Include:

- Destination/ref, observed visibility and intended audience.
- Reviewed object IDs/history scope, separate pending additions, and exclusions.
- Concrete findings and remedies, with safe commit/path references.
- Actual verification evidence and remaining conditions before publication.

A clean scanner result is not a guarantee that publication is safe. Bind the
conclusion to the reviewed content and destination; recheck changed refs or
content before a later authorized push.

A review-only request authorizes neither push nor history rewrite, visibility
change, credential revocation, or deletion. When fixes are also requested,
perform authorized ordinary edits and re-review. If a finding remains in
history, explain why a new deletion commit is insufficient. Before rewriting,
establish which refs are already shared and obtain authorization when it is
not already present. If credentials may already be exposed, recommend their
revocation/rotation separately from history cleanup. Never run a trial push or
change hosting visibility to determine whether publication would succeed.
