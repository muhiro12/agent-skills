---
name: verify-contract-maintainer
description: "Create, audit, or maintain repository verification contracts. Use when defining first-pass Apple build/test evidence, aligning AGENTS.md with real checks, or repairing verification scripts and hooks; use ci-verify-and-summarize to run an existing contract."
---

# Verify Contract Maintainer

Make verification usable from a fresh clone, with the smallest evidence set that
proves the repository's actual boundaries. Preserve working entrypoints and
intentional conventions. A missing preferred filename is not a defect.

## Select the work

- **Create:** no coherent contract exists and the user requests verification
  setup. For an Apple repository, read [Apple bootstrap](references/apple-bootstrap.md)
  to discover its real app, extension, and package surfaces.
- **Audit:** compare documented expectations with actual configuration; report
  concrete gaps without editing unless fixes are also requested.
- **Maintain:** repair the selected gaps with compatible, scoped changes. Do not
  redesign an existing workflow merely because another repository differs.

Read `AGENTS.md`, project/package manifests, CI configuration, documented commands,
and relevant hooks. Apply workflow constraints supplied by the request and
applicable contracts; do not require a personal principle archive. Ordinary
feature work does not require creating a verification system.

## Define the evidence contract

For each relevant boundary, identify its check, configuration, and evidence:

| Boundary | Typical evidence |
| --- | --- |
| Library or package behavior | Relevant tests |
| App, widget, watch, or extension wiring | Affected surface build |
| Public API, persisted schema, wire format, package products | Tests plus an affected consumer build; targeted compatibility evidence |
| Visible UI, lifecycle, persistence, synchronization | Targeted runtime, logs, Preview, or live UI evidence matching the changed risk |
| Repository rules | Retained lint/static checks not covered by native tools |

Document real paths, schemes, destination families, and test plans or targeted
identifiers where relevant. Resolve volatile tool actions and runtime handles
from the active inventory; keep them out of durable contracts. Prefer matching
Xcode-provided guidance when available, without requiring an unrelated skill.

Before changing Xcode selection, record scheme, destination, and active test plan.
Serialize operations sharing a workspace or Simulator. Restore scheme, test plan,
then destination and confirm restoration, without overwriting a later user change.
State unavailable evidence and restoration failures separately from code defects.

## Keep infrastructure proportional

Preserve repository-standard command names and external behavior. A documented
shell entrypoint must resolve and run from the documented location. Keep formatting
or autofix separate from final non-destructive checks. Do not require `ci_scripts`,
SwiftLint, an aggregate wrapper, or artifact directories when they add no capability.

Prefer Xcode-native capabilities and official Apple tools for Apple evidence.
Retain scripts for uncovered rules, format/lint, deliberate compatibility, or an
observed native-tool gap. Do not migrate a working interface just for naming
symmetry. Check callers before renaming or retiring a command; preserve compatibility
when there are actual consumers, rather than inventing unused aliases.

Keep commit-time hooks lightweight or absent. Change hook behavior only within
the requested scope, and never install user-level hooks or alter global Git
configuration as an incidental repair. Broad changes to verification semantics
need an explicit task scope; finish independently authorized fixes meanwhile.

Use current-run output as evidence. If the contract intentionally produces
`.build/ci/runs/<RUN_ID>`, inspect only the newest relevant run; do not scan older
runs or recursively enumerate generated/cache trees.

## Verify and report

Run the created or changed contract through the available capabilities and retained
checks. Check documented paths and callers as well as the changed scripts. Separate
introduced failures, pre-existing failures, and checks that could not run. A build,
static scan, or heuristic score does not establish runtime or release acceptance.

Report the contract changes or audit findings, actual checks, and remaining gaps.
Use a compact boundary-to-evidence map when useful, without mandatory empty sections.
