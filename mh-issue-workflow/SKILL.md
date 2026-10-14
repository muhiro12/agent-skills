---
name: mh-issue-workflow
description: "Apply the owner's GitHub Issue and Project workflow across repositories, including non-development requests. Use for requested Issue operations, linked work lifecycle updates, Project association, and resumption inventories; implementation planning belongs to issue-implementation-planner."
---

# MH Issue Workflow

This is a personal operating profile, not a universal repository policy.
Use one installed profile across repositories; do not copy it into each repo.
It records requested work and maintains associations, not implementation plans
or automatic captures of conversations, personal records, or local archives.

## Resolve the Private Routing

Use the current task's approved routing or this skill's optional ignored
`records/configuration.json`. Its `configuration_url` points to the private
operating document; that document is the single source of truth, not a second
mapping embedded in the skill. Resolve the selected routing and visibility once
for the task; reuse verified routing within that task, and re-resolve when
configuration changes or access errors require it. Use official CLI selectors
when available; resolve node/option IDs only when the chosen API requires them.
Missing private configuration must not cause a guess or a public fallback.

The routing document supplies repository/project selectors, expected visibility,
content language, approved progress options, and any verified status default. Actual private URLs, IDs, mappings, personal context, and Issue
content stay out of this public skill, examples, metadata, and commit history.
Public procedural knowledge can be used even when learned from private work.

Use English for classification labels, tags, and status/field names.
Prefer GitHub's recommended/default names and adapt only for a concrete workflow
need. Use English for public Issue titles and explanations. Use Japanese for
private task titles, bodies, and status summaries, unless the requested locale or
current instructions require otherwise.
Keep private planning and background out of public Issue bodies, comments, and
Project fields. A private Project does not make its source public Issue private.

## Perform the Requested Operation

Use an available GitHub connection, official API, or `gh`; do not add credentials,
permissions, auto-add workflows, GitHub Actions, or a resident process for this flow.
Check existing Issues and associations before creating or adding another copy.
Execute only the requested Issue changes. Re-read after a timeout or ambiguous
write before retrying. Read back the Issue and each affected Project
association/state.

For routine linked work, limit reads and writes to the target Issue and its
configured item. Apply only the required Status transition supported by current
work evidence; skip unchanged fields. Do not inventory unrelated repositories,
reconcile private aggregate themes, change layouts, views or workflows, or
independently reprioritize work. If Project updates are unavailable, report the
specific pending update without opening a GUI or adding authentication.

For an explicitly requested Priority change, the configured public Project is
canonical for a public Issue; the private Project is canonical for a private
Issue. A private mirror may copy the same public Issue's canonical value for
display, without independent ranking or inheritance from private aggregate
themes. Copy the value only when its approved option exists in the mirror;
otherwise report that target copy as pending. Update only that target and any
required display copy in the same task, then read back both; do not add continuous
synchronization or a routine inventory.

Associate the same Issue with the configured Project rather than duplicating it.
Manual/API item-add is separate from auto-add workflow quotas; ordinary item,
Project, access, and API limits still apply. If Project operations are unavailable,
keep a successfully recorded Issue and mark association/status as pending.
If even Issue writes are unavailable, return a draft and the concrete access gap.

For requested code-grounded implementation planning, use
`issue-implementation-planner`; ordinary Issue operations need no code audit.
Do not close or reopen an Issue merely to make Project presentation consistent.

## Keep the Three State Layers Separate

- **Issue state:** `open` or `closed`, changed only as authorized.
- **Close reason:** `completed` means finished; `not_planned` means closed without
  proceeding. This is distinct from Issue state and configured Project Status.
  Preserve other supported reasons, such as `duplicate`, using the provider's
  current API contract.
- **Project Status:** independently configured workflow metadata. Do not infer
  In Progress or Paused from an open Issue or incomplete context.

For the configured Issue-based workflow, use Backlog for explicitly unselected
ideas or candidate work, Todo only for selected work with an agreed next action,
In Progress only as actual scoped work or verification begins, and Paused only
on a confirmed unfinished stop. A queued task may already have implementation.
Leave unknown progress unset; do not bulk classify existing unset or Todo items
from their status alone.

Use a verified native Backlog default when available. If it is unavailable, leave
unknown new items unset. Read back additions for automatic defaults; clear an
unconfirmed automatic Todo only on the newly added target item. Preserve existing
values and never treat automatic initialization as evidence of selection.

Issue close reason is authoritative for outcomes. A configured Completed option
mirrors only an Issue closed as completed, with completion evidence; finishing
one phase of an open Issue is not full completion. Closure without completion,
including not_planned, must not become Completed. In the authorized close task,
map completed to Completed and not_planned to the configured Not planned option.
On reopening, replace a terminal outcome with an appropriate unfinished Status
supported by current work evidence; leave unknown progress unset and do not infer
In Progress from reopening alone. Preserve other supported close reasons without
inventing a mapping. Retain the association for History; do not archive or delete
it merely for presentation. Read back the source reason and target Status.

Use the configured Work view for unfinished Issues and History for all closed
Issues. Work uses source open state; History preserves source close reasons and
keeps completion distinct from closure without completion. Do not claim grouping
or removal of obsolete views until configured and verified. Display-only filters
do not authorize closing, reopening, or reclassifying source Issues. Verify
reverse-workflow safety when establishing routing or when its configuration
changes; reuse that verified
result within the task. Project Status is not permission to change source state.
Keep private reasons and context out of public progress updates.

## Resume and Reconcile

Use this section only for an explicitly requested resumption inventory, initial
backfill, or reconciliation. Ordinary single-Issue work needs no cross-repository
inventory.

Inventory unfinished Issues first and compare their existing Project relations.
Add only missing authorized associations and permitted unset defaults. Preserve
closed reasons and managed-work status. Reconcile a configured state-derived
field with source facts only when authorized; do not reopen cancelled work or
overwrite ongoing work as Todo. Include older closed work only when requested.
Report the actual Issue/Project links and read-back state, with any pending step.
Installing this local profile does not establish activation or API access in
another host, dot conversation, or ordinary mobile ChatGPT session.
