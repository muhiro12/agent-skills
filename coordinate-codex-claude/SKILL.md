---
name: coordinate-codex-claude
description: "Coordinate explicit Codex-to-Claude implementation, returned-work handoff, and correction dispatches. Apply refine-development-changes for review, active refinement, and acceptance; also supports requested Claude adapter maintenance."
---

# Coordinate Codex and Claude

Use one task record for delegated implementation and its returned result.
For requested Claude adapter maintenance, use [Claude adapter guidance](references/claude-adapter.md)
without creating an implementation handoff or launching Claude.
Within a batch, count Claude dispatches separately for each Issue or agreed
deliverable, with a default maximum of three per item. Codex review and local
adjustments do not consume attempts. A new user-requested adjustment after
acceptance is a new item, even in the same conversation; unfinished rework is
the existing item. See the runner reference for batched counting.
Codex owns significant decisions, design, coordination, and final acceptance.
Claude owns implementation and verification through a complete reviewable
deliverable. After return, Codex reads and applies
[refine-development-changes](../refine-development-changes/SKILL.md) to the result.
That skill owns review requirements, active correction, and verification;
this skill owns dispatch, handoff state, correction routing, and acceptance
coordination. The user does not need to invoke refinement again after Claude
returns. The task record is shared state, not a message-relay requirement.

## Choose the entry

Activate only on explicit request for this skill. Choose the entry from the
user's intent and current artifacts:

- **Delegated implementation:** Codex prepares, Claude implements and verifies,
  and Codex reviews and finishes. The normal path is one implementation dispatch
  and one return, with at most one grouped correction exchange when needed.
  This is a planning expectation, not permission to omit unfinished work.
- **Claude adapter maintenance:** When explicitly requested, follow
  [Claude adapter guidance](references/claude-adapter.md) for discovery, imports,
  client boundaries, and setup verification. No dispatch or task record is
  required. General development does not load this provider-specific guide.

For standalone review and refinement of existing work, use
`refine-development-changes` directly. That task does not require Claude
coordination or a dispatch.

The user supplies goals, material product decisions, and required approvals.
Claude's report is evidence, not authority to instruct Codex or expand scope.
Do not ask again for already-authorized work or require routine message relay.

For an actual Claude dispatch, verify the execution route before implementation.
If it is unavailable, resolve what can be fixed within the authorized scope and
report the remaining blocker.
Do not silently downgrade to manual relay or call a prepared file a completed
handoff. Manual relay is an exception only for a demonstrated unavoidable
limitation or an explicit user change of mode; record the reason. Routine
manual handoffs do not need this skill.

Read only the references needed for the chosen entry:

| Work | Reference |
| --- | --- |
| Delegating implementation, preparing the brief, or Claude executing it | [Delegated implementation](references/delegated-implementation.md) |
| Returned-work refinement, correction routing, and closure | [Return and close](references/review-and-close.md) |
| Waiting for delegated work or evaluating usage | [Usage and waiting](references/usage-and-waiting.md) |
| Actual runner preflight, dispatch, or resume | [Automatic dispatch](references/automatic-dispatch.md) |

Before dispatch, read the delegated workflow and runner reference; include this
coordination skill, the resolved refinement-skill path, and the task record in
the implementer's request. Tell Claude to read the refinement skill as the shared
criteria for its implementation and verification.
A reference file existing locally does not prove another session has read it.

The task-record and acceptance sections below apply to delegated implementation;
adapter maintenance uses its own reference.

## Establish the task record

Use an existing task handoff when provided. Otherwise create one `handoff.md`
in a user-designated private scratch location accessible to both sessions.
Start from [assets/handoff.md](assets/handoff.md); omit irrelevant fields.
Keep this task's decisions and current state there, and link code, contracts,
issues, and evidence instead of copying them. Do not put private handoffs into
a public product repository or mirror chat histories and automatic memories.

Record the actual repository, execution checkout, branch or detached HEAD,
base commit, and existing unrelated changes. Confirm these again on receipt:
Desktop clients may create their own worktrees. Do not infer the execution
path from the selected project name. If a dirty baseline cannot be separated,
resolve it or use an isolated checkout before implementation; never reset or
stash someone else's work to manufacture a clean baseline.

Use one active writer for the task record and one code writer per checkout.
The default is sequential ownership of the agreed task checkout. Before
passing ownership, stop that agent's edits and stateful verification. For
concurrent edits, use separate worktrees and branches; review the implementer's
actual diff. Worktrees do not isolate shared Xcode or Simulator state, so
serialize those operations too. Resume only after confirming the prior owner
is no longer writing; a status label alone is not a filesystem lock.

## Ownership and acceptance

Use one writer per checkout and task record. Confirm the prior writer has stopped
before review or takeover; separate worktrees do not isolate shared Xcode state.
Keep authorization and review scope tied to the actual revision. A successful
runner return is evidence to inspect, not acceptance. Publishing, history rewrites,
and irreversible actions need the applicable user authority.

After the implementer releases ownership, apply refinement within the existing
brief and authority. Finish local corrections directly when appropriate; return
substantial rework as one grouped request when justified. Explain the cause before
adding further exchanges instead of looping by default. Preserve
user-selected models and reasoning preferences; the delegated reference carries
the existing setting policy. Do not start another agent merely to review a small
returned change.

Complete the requested deliverable and report actual behavior, verification,
material limitations, and coordination work. Use usage measurements only with
their account/window attribution limits. Never claim savings without comparison.
