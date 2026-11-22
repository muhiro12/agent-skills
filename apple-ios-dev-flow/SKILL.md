---
name: apple-ios-dev-flow
description: "Orchestrate Apple app and Swift package work using the owner's development principles, MH Swift style, and selected reference architecture. Use for implementation in that personal workflow; use a general specialist for an independent focused audit."
---

# Apple iOS Dev Flow

This is an owner-specific orchestration skill. It combines personal development
judgment with reusable platform specialists; general specialists must not depend
on it. Carry this workflow to another environment by installing its selected
skills and providing the relevant personal records and reference checkouts.
Resolve them from the active skill inventory and explicit paths, not this
machine's layout. Missing context must be reported rather than invented.

Start with the affected code, diagnostics, tests, worktree changes, and the
repository README and applicable contracts. Preserve unrelated work and keep
repository artifacts in the required language.

## Choose Guidance for the Actual Decision

For requested Issue creation, updates, or Project reconciliation in this personal
workflow, use `mh-issue-workflow`. Keep code-grounded plans in
`issue-implementation-planner`.
For implementation or QA already linked to an Issue, also use
`mh-issue-workflow` at actual work start, a confirmed unfinished pause, or
completion with evidence.

- Use current Apple and Swift official guidance, native APIs, and official tools
  as the platform baseline. Verify version-sensitive behavior against the app's
  actual SDK and release toolchain. A newer installed beta is not automatically
  the app's release baseline.
- Consult the relevant developer-principle domain when a reusable architectural,
  product, or workflow tradeoff matters. Current user instructions and hard
  repository constraints take precedence over older principles.
- Prefer matching Xcode-provided skills from the active skill inventory. The
  generated `sync-xcode-skills/state/catalog.md` beside the installed skills is
  an additional discovery source. Check it once when useful; do not repeatedly
  reload it through every specialist.
- Load only specialists that change the current decision. HIG, Swift correctness,
  and local style remain constraints without requiring a full portfolio audit
  for a small edit. Reuse guidance already read in this task.

| Need | Guidance |
| --- | --- |
| UI composition, navigation, accessibility, resizing and platform fit | `apple-hig-ui-guardian`; matching Xcode SwiftUI guidance |
| Swift API, concurrency, ownership, package boundaries | `swift-code-guardian` |
| Shared business behavior or ordering consumed by multiple surfaces | [Operations and ordering](references/operations-and-ordering.md) |
| Local Swift formatting and naming | `mh-swift-style` |
| Framework adoption, lifecycle, entitlements, unfamiliar data wiring | `apple-sample-code-advisor` when a relevant sample clarifies implementation |
| Preview capture or live screen audit | `xcode-preview-auditor` or `xcode-ui-smoke-auditor` |
| Added or changed user-facing text | Apply the lookup and coverage checks in `string-catalog-maintainer` to the affected targets |
| Schema, release risk, release notes | The corresponding focused skill when that is the requested work |
| App Intents, SwiftUI performance, leaks, browser mirroring | A matching installed specialist with the required runtime capabilities |

A plugin's guidance-only skill can remain useful without its execution MCP.
Check dependencies for the selected workflow, rather than rejecting an entire
plugin because one unrelated namespace is absent. Never invent unavailable
APIs or install extra tooling merely because a skill mentions it.

Use `respect-incomes-architecture` to resolve and compare Incomes as a read-only
reference when relevant; use another explicitly selected reference when requested.
Perform that comparison only when current repository evidence and official guidance do not settle a concrete comparison.
Do not turn app-local product behavior into a shared dependency merely to align
repositories. Weigh change cost, tests, release coupling, and demonstrated reuse.

## Implement and Verify

The session working with the user owns implementation, corrections and final
verification. Review each completed unit, even on an implementation-only
request. For behavior shared across surfaces, a past failure that could recur,
or an explicit independent-review request, delegate the review as follows.
For routine, isolated edits, apply `refine-development-changes` directly.

1. Start a reviewer with a fresh context and a read-only assignment using
   `refine-development-changes`. Give it the exact revision range or a stable
   snapshot of the working diff, the agreed behavior, affected surfaces,
   applicable quality criteria and material constraints. Preserve the user's
   actual requirements. Leave out the planning transcript, the implementer's
   verdict and speculative diagnoses. Keep the candidate stable during review.
2. Assess findings against the agreed intent. Fix confirmed in-scope issues in
   the original session and rerun affected checks. If retaining the behavior,
   give the reviewer the deciding evidence. Refer unresolved product choices
   to the user and continue other authorized work.
3. Return the updated candidate and evidence to the same reviewer to recheck
   its findings and inspect the corrective diff for regressions. Repeat for
   actionable issues. Close when the reviewed candidate has no outstanding
   required correction and the applicable checks are complete. Report any
   verification blocker, or a disagreement that requires the user's decision.

If the host cannot provide a fresh reviewer or delegation is disallowed, do
the available local checks and disclose the coverage limit. An explicitly
requested independent check remains open until it can be performed. A
review-only request keeps the entire workflow read-only.

For work intended for publication, include the [pre-commit content review](../git-publication-review/SKILL.md#before-a-public-bound-commit)
before each authorized commit. A later authorized push gets its own outgoing-history review.

Choose the smallest complete change and verify it against the repository contract.
When editing code covered by a documented formatter/autofix, run it before
the final non-destructive checks. Include regression tests added during a fix
in the same repository style checks as the production change.

| Changed boundary | Evidence |
| --- | --- |
| Library/package behavior | Relevant library/package tests and retained repository rules |
| App, widget, watch, extension, or UI adapter | Build the affected surface |
| Public API, persisted schema, wire format, products, adopter wiring | Relevant tests plus an affected consumer/surface build |
| Navigation, lifecycle, persistence, sync, notifications, entitlements, visible UI | Add targeted runtime, logs, Preview, or live UI evidence for the actual risk |

Before repeating a Simulator flow, trace the affected entry points to the code
that decides the outcome. Check that changing that decision would fail a unit or
integration test of the production path. Cover missing behavior there, including
persistence after reopen or edits made while work is pending when relevant.
When adding a write path beside an existing one, check how the existing path
preserves later edits and exercise that behavior through the new entry point.
Then exercise the remaining native interaction on the affected surface, such as
Back followed by reselection or a Shortcut presenting the app. Record what the
interaction established. Follow the repository's test policy; repeated captures
during one redesign do not by themselves justify a new XCUITest suite.

Mixed changes need both relevant test and surface evidence. Do not infer runtime
success from a build, visual acceptance from source, or release approval from a
risk score. Report current-change failures separately from pre-existing failures.

A missing aggregate verify command does not prevent ordinary implementation.
Derive proportionate checks from the real project/package/CI configuration and
state the limits. Use `verify-contract-maintainer` only when verification
setup is requested or necessary to unblock the task; do not add scaffolding as
an unrelated prerequisite. `ci-verify-and-summarize` can summarize an existing
shell or Xcode-native contract without creating another wrapper.

## Xcode Execution

For builds, runs, or runtime verification, read
[the Xcode execution procedure](references/xcode-execution.md). Source-only work
needs no runtime setup. Keep Xcode MCP first; use an official-tool fallback only
for a demonstrated capability gap.

## Report

State what changed, the material decision, checks that actually completed, and
remaining limitations. Link reviewable artifacts when useful. Preserve the
user's requested scope through verification instead of ending after an arbitrary
number of steps. Follow `track-developer-principles` for recording reusable
judgment expressed by the user, honoring read-only, no-record, and host constraints.
