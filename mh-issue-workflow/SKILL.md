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
content language, activity-only versus managed-work mode, and any allowed status
field/default. Actual private URLs, IDs, mappings, personal context, and Issue
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
reconcile private aggregate themes, or change layouts, views, workflows, or
priorities. If Project updates are unavailable, report the specific pending
update without opening a GUI or adding authentication.

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
  proceeding. It is not an open state or a Project option. Preserve other supported
  reasons, such as `duplicate`, and use the provider's current API contract.
- **Project Status:** independently configured workflow metadata. Do not infer
  In Progress or Waiting from an open Issue or incomplete context.

An activity-only public Project displays repository facts. Update a configured
state-derived field only from the source Issue state, within the same authorized
Issue operation and association read-back; leave independent planning fields
untouched. In managed work, initialize an unset status only for an open Issue
confirmed not started, using the configured option when authorized and preserving
existing values. Verify reverse-workflow safety when establishing routing or when its
configuration changes; reuse that verified result within the task.
Project Status is not permission to change source Issue state or its close reason.

For configured managed progress, update status within the same linked Issue task:
active only as actual scoped work or verification begins, paused only on a
confirmed unfinished stop, and finished only with completion evidence. Queue
remaining work without claiming it is unimplemented. For closure without
completion, follow the configured clear/archive policy instead of marking work
finished. Keep private reasons and context out of public progress updates.

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
