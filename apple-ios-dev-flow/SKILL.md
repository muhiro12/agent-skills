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

Start with the affected code, diagnostics, tests, worktree changes, and repository
`AGENTS.md`. Complete the requested outcome, preserve unrelated work, and explain
results concisely. Keep repository artifacts in the required language.

## Choose Guidance for the Actual Decision

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
| Local Swift formatting and naming | `mh-swift-style` |
| Framework adoption, lifecycle, entitlements, unfamiliar data wiring | `apple-sample-code-advisor` when a relevant sample clarifies implementation |
| Preview capture or live screen audit | `xcode-preview-auditor` or `xcode-ui-smoke-auditor` |
| Localization, schema, release risk, release notes | The corresponding focused skill when that is the requested work |
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

Choose the smallest complete change and verify it against the repository contract.
When editing code covered by a documented formatter/autofix, run it before
the final non-destructive checks.

| Changed boundary | Evidence |
| --- | --- |
| Library/package behavior | Relevant library/package tests and retained repository rules |
| App, widget, watch, extension, or UI adapter | Build the affected surface |
| Public API, persisted schema, wire format, products, adopter wiring | Relevant tests plus an affected consumer/surface build |
| Navigation, lifecycle, persistence, sync, notifications, entitlements, visible UI | Add targeted runtime, logs, Preview, or live UI evidence for the actual risk |

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
number of steps. Do not persist new principles without an explicit request.
