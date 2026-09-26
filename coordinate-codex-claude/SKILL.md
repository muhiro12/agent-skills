---
name: coordinate-codex-claude
description: "Explicitly coordinate Codex-to-Claude implementation or review existing unpushed Claude or manual work in Codex, including development contracts and commit quality. Use only when requested; ordinary coding and uninvoked reviews do not activate it."
---

# Coordinate Codex and Claude

Use one task record for delegated implementation or incoming work review.
Codex owns significant decisions, design, independent review, and final
acceptance. Claude owns implementation, implementation-level choices, and verification
through a complete reviewable deliverable. After return, Codex reviews, makes
bounded final adjustments, and closes the task. Delegate substantial rework only
when a grouped follow-up is justified. The
task record is shared state, not a requirement for the user to relay messages.

## Choose the entry

Activate only on explicit request for this skill. Choose the entry from the
user's intent and current artifacts:

- **Delegated implementation:** Codex prepares, Claude implements and verifies,
  and Codex reviews and finishes. The normal path is one implementation dispatch
  and one return, with at most one grouped correction exchange when needed.
  This is a planning expectation, not permission to omit unfinished work.
- **Incoming work review:** The user already has unpushed work from Claude or
  manual edits and wants Codex to assess and finish it. Start at review without
  a Claude launch or an invented prior Codex brief. Follow
  [incoming review](references/incoming-review.md) for scope and correction routing.

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
| Reviewing existing unpushed or manual work | [Incoming review](references/incoming-review.md) |
| Independent acceptance, correction routing, and closure in either entry | [Review and close](references/review-and-close.md) |
| Waiting for delegated work or evaluating usage | [Usage and waiting](references/usage-and-waiting.md) |
| Actual runner preflight, dispatch, or resume | [Automatic dispatch](references/automatic-dispatch.md) |

An incoming review does not require dispatch, model-setting changes, or historical
usage measurements. Before dispatch, read the delegated workflow and runner
reference; include the relevant instructions in the implementer's request.
A reference file existing locally does not prove another session has read it.

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

Codex handles bounded final corrections in both entries after the implementer
releases ownership. Return substantial rework as one grouped request; explain
the cause before adding further exchanges instead of looping by default. Preserve
user-selected models and reasoning preferences; the delegated reference carries
the existing setting policy. Do not start another agent merely to review a small
incoming change.

Complete the requested deliverable and report actual behavior, verification,
material limitations, and coordination work. Use usage measurements only with
their account/window attribution limits. Never claim savings without comparison.
