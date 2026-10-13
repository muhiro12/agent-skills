---
name: mh-issue-workflow
description: "Apply the owner's GitHub Issue and Project workflow across repositories, including non-development requests. Use for requested Issue creation or updates, Project association, and resumption inventories; implementation planning belongs to issue-implementation-planner."
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
mapping embedded in the skill. Resolve live repository/project IDs and visibility.
Missing private configuration must not cause a guess or a public fallback.

The routing document supplies repository/project selectors, expected visibility,
content language, activity-only versus managed-work mode, and any allowed status
field/default. Actual private URLs, IDs, mappings, personal context, and Issue
content stay out of this public skill, examples, metadata, and commit history.
Public procedural knowledge can be used even when learned from private work.

Use Japanese for the owner's private content and English for public repository
content unless the requested locale or current instructions require otherwise.
Keep private planning and background out of public Issue bodies, comments, and
Project fields. A private Project does not make its source public Issue private.

## Perform the Requested Operation

Use an available GitHub connection, official API, or `gh`; do not add credentials,
permissions, auto-add workflows, GitHub Actions, or a resident process for this flow.
Check existing Issues and associations before creating or adding another copy.
Execute only the requested Issue changes. Re-read after a timeout or ambiguous
write before retrying. Read back the Issue and each Project association/state.

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

An activity-only public Project displays repository facts; leave its project-only
status and planning fields untouched. In managed work, initialize only an unset
status on an open Issue to the configured not-started option when authorized.
Preserve existing values. Account for reverse workflows before status writes;
Project Done is not permission to close the source Issue.

## Resume and Reconcile

Inventory unfinished Issues first and compare their existing Project relations.
Add only missing authorized associations and permitted unset defaults. Preserve
closed reasons and existing status; do not reopen cancelled work or overwrite
ongoing work as Todo. Include older closed work only when requested.
Report the actual Issue/Project links and read-back state, with any pending step.
Installing this local profile does not establish activation or API access in
another host, dot conversation, or ordinary mobile ChatGPT session.
